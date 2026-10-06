// Firmware do Arcia Axle-E — ESP32-S3, Arduino + FreeRTOS.
//
// Núcleo 1: laço de controle a 50 Hz (lê o quadro de sensores, roda o supervisor, escreve os atuadores).
// Núcleo 0: aquisição (ultrassom, HX711, GPS, bateria), vigia do laço de controle e console serial.
//
// Toda a lógica de decisão está em lib/axle_core e é testada no PC (pio test -e native).

#include <Arduino.h>
#include <Preferences.h>
#include <esp_idf_version.h>
#include <esp_task_wdt.h>
#include <esp_timer.h>

#include <cstdarg>
#include <cstdio>

#include "axle/config.h"
#include "axle/controller.h"
#include "axle/protocol.h"
#include "axle/route.h"
#include "axle/ubx.h"
#include "hal.h"
#include "pins.h"

namespace {

constexpr uint32_t kControlPeriodMs = static_cast<uint32_t>(1000.0f / axle::cfg::kControlHz);
constexpr uint32_t kSensorPeriodMs = 5;
constexpr uint32_t kRangeGroupPeriodMs = 50;   // JSN-SR04T pede ≥50 ms entre disparos
constexpr uint32_t kBatteryPeriodMs = 500;
constexpr uint32_t kTelemetryPeriodMs = 200;
constexpr uint32_t kStatusPeriodMs = 50;
constexpr int64_t kHeartbeatTimeoutUs = 100000;  // laço de controle parado há 100 ms = estado seguro
constexpr uint32_t kWatchdogS = 1;               // vigia de hardware: reinicia o chip
constexpr std::size_t kLineMax = 96;
constexpr std::size_t kReplyMax = 120;

struct Reply {
  char text[kReplyMax];
  // O que mudou e deve ser gravado na NVS pelo console (núcleo 0), fora do laço de controle.
  bool saveCalibration = false;
  axle::WeightCalibration calibration;
  bool saveOrigin = false;
  double lat = 0.0, lon = 0.0;
};

// ---- estado compartilhado entre núcleos (protegido por gMux) ----
struct Shared {
  int32_t loadRaw = 0;
  int64_t loadStampUs = 0;
  bool gnssNew = false;
  axle::GnssSample gnss;
  float batteryPct = 0.0f;  // até a primeira leitura, o autônomo não parte
  axle::Telemetry telemetry;
  axle::StatusLight light = axle::StatusLight::SysOk;
  axle::Buzzer buzzer = axle::Buzzer::Off;
  int64_t heartbeatUs = 0;
};
Shared gShared;
portMUX_TYPE gMux = portMUX_INITIALIZER_UNLOCKED;

QueueHandle_t gCommands;  // console -> controle
QueueHandle_t gReplies;   // controle -> console

axle::SiteRoute gRoute;
axle::Controller* gController = nullptr;  // criado em setup(), usado só pela tarefa de controle
Preferences gPrefs;

// ---------------------------------------------------------------- persistência (NVS)

axle::WeightCalibration loadCalibration() {
  axle::WeightCalibration cal;
  const float scale = gPrefs.getFloat("kgCounts", cal.countsPerKg);
  if (!axle::isPlausibleScale(scale)) {
    Serial.println("aviso: calibracao de peso invalida na memoria; refaca 'tara' e 'calibrar'");
    return cal;
  }
  cal.tareOffset = gPrefs.getInt("tare", cal.tareOffset);
  cal.countsPerKg = scale;
  return cal;
}

void saveCalibration(const axle::WeightCalibration& cal) {
  gPrefs.putInt("tare", cal.tareOffset);
  gPrefs.putFloat("kgCounts", cal.countsPerKg);
}

// ---------------------------------------------------------------- tarefa de controle (núcleo 1)

struct ManualState {
  axle::ManualCommand cmd;
  int64_t stampUs = 0;
};

void reply(const char* fmt, ...) {
  Reply r;
  va_list args;
  va_start(args, fmt);
  vsnprintf(r.text, sizeof r.text, fmt, args);
  va_end(args);
  xQueueSend(gReplies, &r, 0);  // fila cheia: perde a resposta, nunca trava o controle
}

void replyCalibration(const char* what, bool ok) {
  Reply r;
  snprintf(r.text, sizeof r.text, "%s: %s", what, ok ? "ok" : "recusada (so no manual, parado, com leitura valida)");
  r.saveCalibration = ok;
  r.calibration = gController->weightCalibration();
  xQueueSend(gReplies, &r, 0);
}

void replyOrigin(bool ok, double lat, double lon) {
  Reply r;
  snprintf(r.text, sizeof r.text, "origem: %s", ok ? "ok" : "recusada (so no manual e parado)");
  r.saveOrigin = ok;
  r.lat = lat;
  r.lon = lon;
  xQueueSend(gReplies, &r, 0);
}

// Comandos que mexem no supervisor rodam aqui, entre dois ciclos, para não haver corrida.
void applyCommand(const axle::Command& c, ManualState& manual, int64_t nowUs) {
  axle::Controller& ctl = *gController;
  switch (c.type) {
    case axle::CommandType::Auto: reply("auto: %s", axle::toString(ctl.requestAuto())); break;
    case axle::CommandType::Manual: ctl.requestManual(); reply("manual: ok"); break;
    case axle::CommandType::Reset: reply("reset: %s", ctl.resetFaults() ? "ok" : "recusado"); break;
    case axle::CommandType::Tare: replyCalibration("tara", ctl.tare()); break;
    case axle::CommandType::Calibrate: replyCalibration("calibrar", ctl.calibrateWeight(static_cast<float>(c.a))); break;
    case axle::CommandType::Origin: replyOrigin(ctl.setOrigin(c.a, c.b), c.a, c.b); break;
    case axle::CommandType::SetPose: {
      const axle::Pose p{static_cast<float>(c.a), static_cast<float>(c.b), static_cast<float>(c.c * DEG_TO_RAD)};
      reply("pose: %s", ctl.setPose(p) ? "ok" : "recusada (so no manual e parado)");
      break;
    }
    case axle::CommandType::Drive:
      manual.cmd.throttle = static_cast<float>(c.a);
      manual.cmd.steer = static_cast<float>(c.b);
      manual.cmd.dump = c.dump;
      manual.stampUs = nowUs;
      break;
    default: break;
  }
}

void fillFrame(axle::SensorFrame& f, const ManualState& manual, int64_t nowUs) {
  hal::readRanges(f.ranges, nowUs);
  const float meters = hal::encoderTake() / hw::kEncoderCountsPerMeter;
  f.encoderDistance = meters;
  f.encoderSpeed = meters / f.dt;
  f.bucketUp = hal::limitUp();
  f.bucketDown = hal::limitDown();
  f.estopPressed = hal::estopPressed();
  f.manual = manual.cmd;
  f.manual.ageS = manual.stampUs == 0 ? 1e9f : static_cast<float>(nowUs - manual.stampUs) * 1e-6f;

  portENTER_CRITICAL(&gMux);
  f.loadRaw = gShared.loadRaw;
  f.loadAgeMs = static_cast<float>(nowUs - gShared.loadStampUs) * 1e-3f;
  f.batteryPct = gShared.batteryPct;
  f.gnssNew = gShared.gnssNew;
  f.gnss = gShared.gnss;
  gShared.gnssNew = false;
  portEXIT_CRITICAL(&gMux);
}

void writeActuators(const axle::ActuatorOutputs& out) {
  hal::writeMotor(out.motorDuty, out.motorEnable);
  hal::writeBrake(out.parkingBrake);
  hal::writeSteer(out.steer);
  hal::writeBucket(out.bucket);
}

void controlTask(void*) {
  esp_task_wdt_add(nullptr);
  ManualState manual;
  axle::SensorFrame frame;
  int64_t prevUs = esp_timer_get_time();
  TickType_t wake = xTaskGetTickCount();

  for (;;) {
    vTaskDelayUntil(&wake, pdMS_TO_TICKS(kControlPeriodMs));
    const int64_t nowUs = esp_timer_get_time();
    frame.dt = static_cast<float>(nowUs - prevUs) * 1e-6f;
    prevUs = nowUs;

    axle::Command cmd;
    while (xQueueReceive(gCommands, &cmd, 0) == pdTRUE) applyCommand(cmd, manual, nowUs);

    fillFrame(frame, manual, nowUs);
    const axle::ActuatorOutputs out = gController->step(frame);
    writeActuators(out);

    const axle::Telemetry t = gController->telemetry();
    portENTER_CRITICAL(&gMux);
    gShared.telemetry = t;
    gShared.light = out.light;
    gShared.buzzer = out.buzzer;
    gShared.heartbeatUs = nowUs;
    portEXIT_CRITICAL(&gMux);
    esp_task_wdt_reset();
  }
}

// ---------------------------------------------------------------- aquisição (núcleo 0)

void sensorTask(void*) {
  axle::UbxParser ubx;
  bool frontNext = true;
  uint32_t lastRange = 0, lastBattery = 0;
  TickType_t wake = xTaskGetTickCount();

  for (;;) {
    vTaskDelayUntil(&wake, pdMS_TO_TICKS(kSensorPeriodMs));
    const uint32_t nowMs = millis();
    const int64_t nowUs = esp_timer_get_time();

    if (nowMs - lastRange >= kRangeGroupPeriodMs) {  // frente e trás alternados: evita eco cruzado
      hal::fireRangeGroup(frontNext);
      frontNext = !frontNext;
      lastRange = nowMs;
    }
    int32_t raw = 0;
    const bool haveLoad = hal::hx711Read(raw);
    const bool haveFix = hal::gnssPoll(ubx);
    const bool readBattery = nowMs - lastBattery >= kBatteryPeriodMs;
    const float battery = readBattery ? hal::batteryPercent() : 0.0f;
    if (readBattery) lastBattery = nowMs;

    portENTER_CRITICAL(&gMux);
    if (haveLoad) { gShared.loadRaw = raw; gShared.loadStampUs = nowUs; }
    if (haveFix) { gShared.gnss = ubx.sample(); gShared.gnssNew = true; }
    if (readBattery) gShared.batteryPct = battery;
    const int64_t heartbeat = gShared.heartbeatUs;
    portEXIT_CRITICAL(&gMux);

    // Segunda camada além do watchdog: se o laço de controle travou, desliga tudo daqui.
    if (heartbeat != 0 && nowUs - heartbeat > kHeartbeatTimeoutUs) hal::safeState();
  }
}

// ---------------------------------------------------------------- console serial (núcleo 0)

void printTelemetry() {
  axle::Telemetry t;
  portENTER_CRITICAL(&gMux);
  t = gShared.telemetry;
  portEXIT_CRITICAL(&gMux);
  char buf[512];
  if (axle::formatTelemetry(t, buf, sizeof buf)) Serial.println(buf);
}

void handleLine(const char* line) {
  const axle::Command c = axle::parseCommand(line);
  switch (c.type) {
    case axle::CommandType::Empty: return;
    case axle::CommandType::Invalid: Serial.printf("erro: comando invalido '%s'\n%s\n", line, axle::kHelpText); return;
    case axle::CommandType::Help: Serial.println(axle::kHelpText); return;
    case axle::CommandType::Status: printTelemetry(); return;
    default: break;
  }
  if (xQueueSend(gCommands, &c, pdMS_TO_TICKS(20)) != pdTRUE) Serial.println("erro: fila de comandos cheia");
}

void consoleTask(void*) {
  char line[kLineMax + 1];
  std::size_t len = 0;
  bool overflow = false;
  uint32_t lastTelemetry = 0, lastStatus = 0;

  for (;;) {
    while (Serial.available() > 0) {
      const char ch = static_cast<char>(Serial.read());
      if (ch == '\r') continue;
      if (ch != '\n') {
        if (len < kLineMax) line[len++] = ch; else overflow = true;
        continue;
      }
      line[len] = '\0';
      if (overflow) Serial.println("erro: linha longa demais"); else handleLine(line);
      len = 0;
      overflow = false;
    }

    Reply r;
    while (xQueueReceive(gReplies, &r, 0) == pdTRUE) {
      Serial.println(r.text);
      if (r.saveCalibration) saveCalibration(r.calibration);
      if (r.saveOrigin) {
        gPrefs.putDouble("lat", r.lat);
        gPrefs.putDouble("lon", r.lon);
      }
    }

    const uint32_t nowMs = millis();
    if (nowMs - lastStatus >= kStatusPeriodMs) {
      portENTER_CRITICAL(&gMux);
      const axle::StatusLight light = gShared.light;
      const axle::Buzzer buzzer = gShared.buzzer;
      portEXIT_CRITICAL(&gMux);
      hal::writeStatus(light, buzzer, nowMs);
      lastStatus = nowMs;
    }
    if (nowMs - lastTelemetry >= kTelemetryPeriodMs) {
      printTelemetry();
      lastTelemetry = nowMs;
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

}  // namespace

void setup() {
  hal::begin();  // primeiro de tudo: saídas no estado seguro
  Serial.begin(115200);
  gPrefs.begin("axle", false);

  axle::buildSiteRoute(gRoute);
  static axle::Controller controller(gRoute, loadCalibration());
  gController = &controller;
  // Sem origem gravada o autônomo recusa partir ("sem_origem"). O rumo não é presumido: vem do comando
  // "pose" ou é confirmado pelo GPS depois de alguns metros em linha reta no manual.
  if (gPrefs.isKey("lat") && gPrefs.isKey("lon")) {
    controller.setOrigin(gPrefs.getDouble("lat", 0.0), gPrefs.getDouble("lon", 0.0));
  }

  gCommands = xQueueCreate(8, sizeof(axle::Command));
  gReplies = xQueueCreate(8, sizeof(Reply));
  gShared.loadStampUs = esp_timer_get_time();  // dá ao HX711 o prazo normal desde o boot

  // O core já iniciou o watchdog de tarefas: aqui só encurtamos o prazo e ligamos o reinício por pânico.
#if ESP_IDF_VERSION_MAJOR >= 5
  const esp_task_wdt_config_t wdt = {kWatchdogS * 1000, 0, true};
  esp_task_wdt_reconfigure(&wdt);
#else
  esp_task_wdt_init(kWatchdogS, true);
#endif

  xTaskCreatePinnedToCore(controlTask, "controle", 8192, nullptr, configMAX_PRIORITIES - 2, nullptr, 1);
  xTaskCreatePinnedToCore(sensorTask, "sensores", 4096, nullptr, 5, nullptr, 0);
  xTaskCreatePinnedToCore(consoleTask, "console", 6144, nullptr, 2, nullptr, 0);
  Serial.println("Arcia Axle-E pronto. 'ajuda' lista os comandos.");
}

void loop() { vTaskDelete(nullptr); }  // tudo roda nas tarefas acima
