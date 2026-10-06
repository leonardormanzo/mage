#include "hal.h"

#include <Adafruit_NeoPixel.h>
#include <Arduino.h>
#include <driver/pcnt.h>
#include <esp_arduino_version.h>
#include <esp_timer.h>
#include <hal/gpio_ll.h>
#include <soc/gpio_struct.h>

#include <cmath>

#include "axle/config.h"
#include "pins.h"

namespace hal {

namespace {

// ---------- pulsos de servo (LEDC), compatível com o core Arduino 2.x e 3.x ----------
enum PwmChannel : uint8_t { kChMotor = 0, kChSteer = 1 };
constexpr uint32_t kPulseHz = 50;
constexpr uint8_t kPulseBits = 14;
constexpr float kPulsePeriodUs = 1e6f / kPulseHz;

void pwmAttach(uint8_t pin, uint8_t ch, uint32_t hz, uint8_t bits) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)ch;
  ledcAttach(pin, hz, bits);
#else
  ledcSetup(ch, hz, bits);
  ledcAttachPin(pin, ch);
#endif
}

void pwmWrite(uint8_t pin, uint8_t ch, uint32_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)ch;
  ledcWrite(pin, duty);
#else
  (void)pin;
  ledcWrite(ch, duty);
#endif
}

// k de -1 a +1 vira 1000–2000 µs; valores inválidos viram o neutro.
void writePulse(uint8_t pin, uint8_t ch, float k) {
  if (!std::isfinite(k)) k = 0.0f;
  k = k > 1.0f ? 1.0f : (k < -1.0f ? -1.0f : k);
  const float us = hw::kPulseCenterUs + k * hw::kPulseSpanUs;
  pwmWrite(pin, ch, static_cast<uint32_t>(us / kPulsePeriodUs * ((1u << kPulseBits) - 1)));
}

// ---------- ultrassom: medição do eco por interrupção ----------
constexpr float kMetersPerUs = 343.0f / 2.0f * 1e-6f;  // ida e volta, 20 °C
constexpr int64_t kMinEchoUs = 100;                    // mais curto que isso é ruído
constexpr int64_t kNoEchoUs = 30000;                   // pulso longo = sem eco no alcance
constexpr int64_t kMaxEchoUs = 60000;                  // mais longo = borda perdida: descarta

struct Echo {
  int64_t riseUs = 0;    // 0: nenhuma borda de subida pendente
  int64_t stampUs = -1;  // -1: o sensor nunca respondeu
  float meters = 0.0f;
};
Echo gEcho[axle::kRangeSensorCount];
portMUX_TYPE gEchoMux = portMUX_INITIALIZER_UNLOCKED;
// Cópia dos pinos na RAM: a interrupção não pode ler tabelas da flash (cache desligado ao gravar a NVS).
DRAM_ATTR const uint8_t kEchoPinsRam[axle::kRangeSensorCount] = {pins::kEcho[0], pins::kEcho[1], pins::kEcho[2],
                                                                 pins::kEcho[3], pins::kEcho[4]};

void IRAM_ATTR onEcho(void* arg) {
  const auto i = reinterpret_cast<uintptr_t>(arg);
  const int64_t now = esp_timer_get_time();
  const bool high = gpio_ll_get_level(&GPIO, static_cast<gpio_num_t>(kEchoPinsRam[i]));
  portENTER_CRITICAL_ISR(&gEchoMux);
  Echo& e = gEcho[i];
  if (high) {
    e.riseUs = now;
  } else if (e.riseUs > 0) {
    const int64_t width = now - e.riseUs;
    e.riseUs = 0;  // cada subida vale para uma única descida
    // Fora da faixa plausível = borda perdida ou ruído: não carimba, e o sensor envelhece até frear.
    if (width >= kMinEchoUs && width <= kMaxEchoUs) {
      e.meters = width >= kNoEchoUs ? axle::cfg::kRangeMax : static_cast<float>(width) * kMetersPerUs;
      e.stampUs = now;
    }
  }
  portEXIT_CRITICAL_ISR(&gEchoMux);
}

// ---------- HX711 ----------
portMUX_TYPE gHxMux = portMUX_INITIALIZER_UNLOCKED;
constexpr int kHxBits = 24;
constexpr int kHxGainPulses = 1;  // canal A, ganho 128

// ---------- encoder ----------
constexpr pcnt_unit_t kPcntUnit = PCNT_UNIT_0;
constexpr uint16_t kPcntFilter = 100;  // ciclos de APB (~1,25 µs) para filtrar ruído
// O contador volta a 0 ao atingir ±kPcntWrap. Lendo sem zerar (nenhuma borda se perde) e corrigindo a volta.
constexpr int16_t kPcntWrap = 30000;
int16_t gLastCount = 0;

void setupEncoder() {
  pcnt_config_t c = {};
  c.unit = kPcntUnit;
  c.counter_h_lim = kPcntWrap;
  c.counter_l_lim = -kPcntWrap;
  // Canal 0: bordas de A, sentido por B. Canal 1: bordas de B, sentido por A. Juntos = quadratura x4.
  c.channel = PCNT_CHANNEL_0;
  c.pulse_gpio_num = pins::kEncoderA;
  c.ctrl_gpio_num = pins::kEncoderB;
  c.pos_mode = PCNT_COUNT_INC;
  c.neg_mode = PCNT_COUNT_DEC;
  c.lctrl_mode = PCNT_MODE_REVERSE;
  c.hctrl_mode = PCNT_MODE_KEEP;
  pcnt_unit_config(&c);
  c.channel = PCNT_CHANNEL_1;
  c.pulse_gpio_num = pins::kEncoderB;
  c.ctrl_gpio_num = pins::kEncoderA;
  c.pos_mode = PCNT_COUNT_DEC;
  c.neg_mode = PCNT_COUNT_INC;
  pcnt_unit_config(&c);
  pcnt_set_filter_value(kPcntUnit, kPcntFilter);
  pcnt_filter_enable(kPcntUnit);
  pcnt_counter_pause(kPcntUnit);
  pcnt_counter_clear(kPcntUnit);
  pcnt_counter_resume(kPcntUnit);
}

// ---------- interface ----------
Adafruit_NeoPixel gLeds(hw::kStatusLedCount, pins::kStatusLeds, NEO_GRB + NEO_KHZ800);
HardwareSerial gGnss(1);
float gBatteryPct = -1.0f;
constexpr float kBatteryFilter = 0.05f;

uint32_t colorFor(axle::StatusLight light, uint32_t nowMs) {
  const bool blink = (nowMs / 250) % 2 == 0;
  switch (light) {
    case axle::StatusLight::SysOk: return Adafruit_NeoPixel::Color(0, 160, 40);
    case axle::StatusLight::Auto: return Adafruit_NeoPixel::Color(0, 90, 220);
    case axle::StatusLight::Alert: return Adafruit_NeoPixel::Color(230, 140, 0);
    case axle::StatusLight::Brake: return Adafruit_NeoPixel::Color(230, 0, 0);
    case axle::StatusLight::Fault: return blink ? Adafruit_NeoPixel::Color(230, 0, 0) : 0;
  }
  return 0;
}

bool buzzerOn(axle::Buzzer b, uint32_t nowMs) {
  switch (b) {
    case axle::Buzzer::Off: return false;
    case axle::Buzzer::Slow: return nowMs % 800 < 200;
    case axle::Buzzer::Fast: return nowMs % 200 < 100;
    case axle::Buzzer::Continuous: return true;
  }
  return false;
}

}  // namespace

void begin() {
  // Saídas primeiro, já no estado seguro.
  for (uint8_t p : {pins::kMotorEnable, pins::kBrakeRelease, pins::kBucketUpRelay, pins::kBucketDownRelay,
                    pins::kBuzzer, pins::kTrigFront, pins::kTrigRear}) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  pwmAttach(pins::kMotorPpm, kChMotor, kPulseHz, kPulseBits);
  pwmAttach(pins::kSteerPwm, kChSteer, kPulseHz, kPulseBits);
  safeState();
  writeSteer(0.0f);

  pinMode(pins::kLimitUp, INPUT_PULLUP);
  pinMode(pins::kLimitDown, INPUT_PULLUP);
  pinMode(pins::kEstopSense, INPUT_PULLUP);
  pinMode(pins::kHx711Data, INPUT);
  pinMode(pins::kHx711Clock, OUTPUT);
  digitalWrite(pins::kHx711Clock, LOW);
  analogReadResolution(12);

  for (uintptr_t i = 0; i < axle::kRangeSensorCount; ++i) {
    pinMode(pins::kEcho[i], INPUT);
    attachInterruptArg(pins::kEcho[i], onEcho, reinterpret_cast<void*>(i), CHANGE);
  }
  setupEncoder();
  gLeds.begin();
  gLeds.show();
  gGnss.begin(pins::kGnssBaud, SERIAL_8N1, pins::kGnssRx, -1);
}

void safeState() {
  digitalWrite(pins::kMotorEnable, LOW);
  writePulse(pins::kMotorPpm, kChMotor, 0.0f);
  digitalWrite(pins::kBrakeRelease, LOW);  // relé desligado = mola aplica o freio
  digitalWrite(pins::kBucketUpRelay, LOW);
  digitalWrite(pins::kBucketDownRelay, LOW);
}

void fireRangeGroup(bool front) {
  const uint8_t pin = front ? pins::kTrigFront : pins::kTrigRear;
  digitalWrite(pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(pin, LOW);
}

void readRanges(std::array<axle::RangeReading, axle::kRangeSensorCount>& out, int64_t nowUs) {
  portENTER_CRITICAL(&gEchoMux);
  for (std::size_t i = 0; i < axle::kRangeSensorCount; ++i) {
    out[i].meters = gEcho[i].meters;
    out[i].ageMs = gEcho[i].stampUs < 0 ? 1e9f : static_cast<float>(nowUs - gEcho[i].stampUs) * 1e-3f;
  }
  portEXIT_CRITICAL(&gEchoMux);
}

bool hx711Read(int32_t& raw) {
  if (digitalRead(pins::kHx711Data) == HIGH) return false;
  uint32_t v = 0;
  // O HX711 desliga se o clock ficar alto >60 µs: a leitura não pode ser interrompida.
  portENTER_CRITICAL(&gHxMux);
  for (int i = 0; i < kHxBits + kHxGainPulses; ++i) {
    digitalWrite(pins::kHx711Clock, HIGH);
    delayMicroseconds(1);
    if (i < kHxBits) v = (v << 1) | static_cast<uint32_t>(digitalRead(pins::kHx711Data));
    digitalWrite(pins::kHx711Clock, LOW);
    delayMicroseconds(1);
  }
  portEXIT_CRITICAL(&gHxMux);
  if (v & 0x800000u) v |= 0xFF000000u;  // estende o sinal de 24 para 32 bits
  raw = static_cast<int32_t>(v);
  return true;
}

int32_t encoderTake() {
  int16_t count = 0;
  pcnt_get_counter_value(kPcntUnit, &count);
  int32_t delta = static_cast<int32_t>(count) - gLastCount;
  gLastCount = count;
  // Em 20 ms o encoder anda bem menos que meia volta do contador: um salto grande é a volta pelo limite.
  if (delta > kPcntWrap / 2) delta -= kPcntWrap;
  if (delta < -kPcntWrap / 2) delta += kPcntWrap;
  return delta;
}

bool limitUp() { return digitalRead(pins::kLimitUp) == LOW; }      // NA: fechado = no fim do curso
bool limitDown() { return digitalRead(pins::kLimitDown) == LOW; }
bool estopPressed() { return digitalRead(pins::kEstopSense) == HIGH; }  // laço NF aberto (ou cabo rompido)

float batteryPercent() {
  const float volts = analogReadMilliVolts(pins::kBatteryAdc) * 1e-3f * hw::kBatteryDivider;
  float pct = (volts - hw::kBatteryEmptyV) / (hw::kBatteryFullV - hw::kBatteryEmptyV) * 100.0f;
  pct = pct < 0.0f ? 0.0f : (pct > 100.0f ? 100.0f : pct);
  gBatteryPct = gBatteryPct < 0.0f ? pct : gBatteryPct + kBatteryFilter * (pct - gBatteryPct);
  return gBatteryPct;
}

void writeMotor(float duty, bool enable) {
  writePulse(pins::kMotorPpm, kChMotor, enable ? duty : 0.0f);
  digitalWrite(pins::kMotorEnable, enable ? HIGH : LOW);
}

void writeBrake(bool applied) { digitalWrite(pins::kBrakeRelease, applied ? LOW : HIGH); }

void writeSteer(float rad) { writePulse(pins::kSteerPwm, kChSteer, rad / axle::cfg::kMaxSteer); }

void writeBucket(int8_t direction) {
  // Nunca os dois relés juntos.
  digitalWrite(pins::kBucketUpRelay, direction > 0 ? HIGH : LOW);
  digitalWrite(pins::kBucketDownRelay, direction < 0 ? HIGH : LOW);
}

void writeStatus(axle::StatusLight light, axle::Buzzer buzzer, uint32_t nowMs) {
  gLeds.fill(colorFor(light, nowMs));
  gLeds.show();
  digitalWrite(pins::kBuzzer, buzzerOn(buzzer, nowMs) ? HIGH : LOW);
}

bool gnssPoll(axle::UbxParser& parser) {
  bool fresh = false;
  while (gGnss.available() > 0) fresh |= parser.feed(static_cast<uint8_t>(gGnss.read()));
  return fresh;
}

}  // namespace hal
