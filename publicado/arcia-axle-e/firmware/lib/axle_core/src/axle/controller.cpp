#include "axle/controller.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

namespace {
constexpr float kStandstill = 0.05f;  // m/s
constexpr float kIntentDeadband = 0.01f;

float clampf(float v, float lo, float hi) {
  if (!std::isfinite(v)) return 0.0f;  // comando corrompido vira "parado"
  return v < lo ? lo : (v > hi ? hi : v);
}
}  // namespace

const char* toString(AutoStartResult r) {
  switch (r) {
    case AutoStartResult::Started: return "iniciado";
    case AutoStartResult::Faulted: return "falha_ativa";
    case AutoStartResult::EstopActive: return "emergencia_acionada";
    case AutoStartResult::LowBattery: return "bateria_baixa";
    case AutoStartResult::NoRtk: return "sem_rtk";
    case AutoStartResult::NoOrigin: return "sem_origem";
    case AutoStartResult::NoHeading: return "rumo_nao_confirmado";
    case AutoStartResult::OffRoute: return "longe_da_rota";
    case AutoStartResult::Moving: return "em_movimento";
  }
  return "?";
}

Controller::Controller(const SiteRoute& route, WeightCalibration cal) : mission_(route), weight_(cal) {}

ActuatorOutputs Controller::step(const SensorFrame& in) {
  last_ = in;
  updateFaults(in);
  localizer_.predict(in.encoderDistance, steer_.value());
  localizer_.tick(in.dt);
  if (in.gnssNew) localizer_.correct(in.gnss);

  MissionOutputs intent;
  if (fault_ == Fault::None) intent = mode_ == Mode::Auto ? autoIntent(in) : manualIntent(in);
  lastOut_ = actuate(in, intent);
  return lastOut_;
}

void Controller::updateFaults(const SensorFrame& in) {
  weight_.update(in.loadRaw, in.dt);
  if (in.estopPressed) latch(Fault::EmergencyStop);
  if (!(in.dt > 0.0f) || in.dt > cfg::kMaxCycleS) latch(Fault::ControlOverrun);
  if (weight_.implausible() || in.loadAgeMs > cfg::kWeightStaleMs) latch(Fault::WeightImplausible);
  if (in.bucketUp && in.bucketDown) latch(Fault::LimitSwitch);  // curto na fiação de um dos fins de curso
  checkDrivePlausibility(in);
}

// O encoder é a única medida de velocidade: se ele mente, o PI e a guarda de colisão ficam cegos.
void Controller::checkDrivePlausibility(const SensorFrame& in) {
  const float speed = std::fabs(in.encoderSpeed);
  const bool pushing = lastOut_.motorEnable && std::fabs(lastOut_.motorDuty) > cfg::kStallDuty;
  stallTime_ = (pushing && speed < kStandstill) ? stallTime_ + in.dt : 0.0f;
  if (stallTime_ > cfg::kStallTimeS) latch(Fault::DriveStalled);

  const bool tooFast = !std::isfinite(speed) || speed > cfg::kMaxSpeedManual * cfg::kOverspeedFactor;
  overspeedTime_ = tooFast ? overspeedTime_ + in.dt : 0.0f;
  if (overspeedTime_ > cfg::kOverspeedTimeS) latch(Fault::Overspeed);
}

void Controller::latch(Fault f) {
  if (fault_ == Fault::None) fault_ = f;  // guarda a primeira causa, que é a raiz
  requestManual();
}

bool Controller::hardStop() const {
  // Desligam o motor e aplicam o freio na hora: emergência, laço atrasado e as falhas em que a medida de
  // velocidade deixou de ser confiável. As demais falhas param pela rampa de emergência.
  return fault_ == Fault::EmergencyStop || fault_ == Fault::ControlOverrun || fault_ == Fault::DriveStalled ||
         fault_ == Fault::Overspeed;
}

bool Controller::standingStill() const { return std::fabs(last_.encoderSpeed) <= kStandstill; }

MissionOutputs Controller::manualIntent(const SensorFrame& in) const {
  MissionOutputs out;
  out.steer = steer_.value();
  if (in.manual.ageS > cfg::kManualTimeoutS) return out;  // homem-morto: para e segura a caçamba
  const float t = clampf(in.manual.throttle, -1.0f, 1.0f);
  out.targetSpeed = t >= 0.0f ? t * cfg::kMaxSpeedManual : t * cfg::kMaxReverse;
  out.steer = clampf(in.manual.steer, -1.0f, 1.0f) * cfg::kMaxSteer;
  out.dump = in.manual.dump;
  return out;
}

MissionOutputs Controller::autoIntent(const SensorFrame& in) {
  MissionInputs mi;
  mi.pose = localizer_.pose();
  mi.speed = in.encoderSpeed;
  mi.weightKg = weight_.kg();
  mi.bucketDown = in.bucketDown;
  mi.bucketUp = in.bucketUp;
  MissionOutputs out = mission_.step(mi, in.dt);
  autoPaused_ = !localizer_.rtkOk();
  if (autoPaused_) out.targetSpeed = 0.0f;  // sem posição confiável não segue a rota
  return out;
}

float Controller::limitBySafety(const SensorFrame& in, float target) {
  const int8_t intent = target > kIntentDeadband ? 1 : (target < -kIntentDeadband ? -1 : 0);
  guardResult_ = guard_.update(in.encoderSpeed, steer_.value(), intent, kRangeMounts.data(), in.ranges.data(),
                               kRangeSensorCount, cfg::kRangeMax);
  if (guardResult_.state == SafetyState::Brake) return 0.0f;
  if (guardResult_.state == SafetyState::Warn) return clampf(target, -cfg::kWarnMaxSpeed, cfg::kWarnMaxSpeed);
  return target;
}

ActuatorOutputs Controller::actuate(const SensorFrame& in, const MissionOutputs& intent) {
  ActuatorOutputs out;
  const bool faulted = fault_ != Fault::None;

  float target = faulted ? 0.0f : intent.targetSpeed;
  if (!in.bucketDown) target = 0.0f;  // intertravamento: não anda com a caçamba levantada
  target = limitBySafety(in, target);

  // Homem-morto também freia forte: quem soltou o controle pode ter perdido o controle do carrinho.
  const bool deadman = mode_ == Mode::Manual && in.manual.ageS > cfg::kManualTimeoutS;
  const bool emergency = faulted || deadman || guardResult_.state == SafetyState::Brake;
  const float setpoint = ramp_.step(target, in.dt, emergency);
  out.motorDuty = pi_.update(setpoint, in.encoderSpeed, in.dt);
  out.motorEnable = !hardStop();
  if (hardStop()) {
    out.motorDuty = 0.0f;
    ramp_.reset();
    pi_.reset();
  }
  const bool standing = std::fabs(in.encoderSpeed) < kStandstill && setpoint == 0.0f;
  out.parkingBrake = hardStop() || standing;

  out.steer = steer_.step(hardStop() ? steer_.value() : intent.steer, in.encoderSpeed, in.dt);

  const DumpCommand dumpCmd = faulted ? DumpCommand::Hold : intent.dump;
  out.bucket = dump_.update({dumpCmd, in.bucketUp, in.bucketDown, in.encoderSpeed}, in.dt);
  if (dump_.fault()) latch(Fault::DumpTimeout);

  out.light = statusLight();
  out.buzzer = buzzer(setpoint);
  return out;
}

StatusLight Controller::statusLight() const {
  if (fault_ != Fault::None || guardResult_.sensorFault) return StatusLight::Fault;
  if (guardResult_.state == SafetyState::Brake) return StatusLight::Brake;
  if (guardResult_.state == SafetyState::Warn) return StatusLight::Alert;
  return mode_ == Mode::Auto ? StatusLight::Auto : StatusLight::SysOk;
}

Buzzer Controller::buzzer(float setpoint) const {
  if (fault_ != Fault::None || guardResult_.sensorFault) return Buzzer::Continuous;
  if (guardResult_.state == SafetyState::Brake) return Buzzer::Fast;
  if (guardResult_.state == SafetyState::Warn) return Buzzer::Slow;
  if (setpoint < -kIntentDeadband) return Buzzer::Slow;  // alarme de ré exigido em canteiro
  return Buzzer::Off;
}

AutoStartResult Controller::requestAuto() {
  if (last_.estopPressed) return AutoStartResult::EstopActive;
  if (fault_ != Fault::None) return AutoStartResult::Faulted;
  if (!(last_.batteryPct >= cfg::kBatteryAutoMinPct)) return AutoStartResult::LowBattery;
  if (!standingStill()) return AutoStartResult::Moving;
  if (!localizer_.originSet()) return AutoStartResult::NoOrigin;
  if (!localizer_.rtkOk()) return AutoStartResult::NoRtk;
  if (!localizer_.headingKnown()) return AutoStartResult::NoHeading;
  const Pose& p = localizer_.pose();
  if (distanceToPath(mission_.firstPath(weight_.kg()), {p.x, p.y}) > cfg::kAutoStartMaxOffset) {
    return AutoStartResult::OffRoute;
  }
  mode_ = Mode::Auto;
  autoPaused_ = false;
  mission_.start(weight_.kg());
  return AutoStartResult::Started;
}

void Controller::requestManual() {
  mode_ = Mode::Manual;
  autoPaused_ = false;
  mission_.stop();
}

bool Controller::resetFaults() {
  if (last_.estopPressed || !standingStill()) return false;
  // Com um comando manual ativo o carrinho arrancaria no mesmo instante do reset.
  if (last_.manual.ageS <= cfg::kManualTimeoutS && last_.manual.throttle != 0.0f) return false;
  if (last_.bucketUp && last_.bucketDown) return false;  // fiação do fim de curso ainda em curto
  if (fault_ == Fault::WeightImplausible && (weight_.implausible() || last_.loadAgeMs > cfg::kWeightStaleMs)) {
    return false;  // a causa ainda está lá
  }
  dump_.clearFault();
  ramp_.reset();
  pi_.reset();
  stallTime_ = overspeedTime_ = 0.0f;
  fault_ = Fault::None;
  return true;
}

bool Controller::tare() {
  if (!canReconfigure()) return false;
  weight_.tare(last_.loadRaw);
  return true;
}

bool Controller::calibrateWeight(float knownKg) {
  return canReconfigure() && weight_.calibrate(last_.loadRaw, knownKg);
}

bool Controller::setOrigin(double latDeg, double lonDeg) {
  if (!canReconfigure()) return false;
  localizer_.setOrigin(latDeg, lonDeg);
  return true;
}

bool Controller::setPose(Pose p) {
  if (!canReconfigure()) return false;
  localizer_.reset(p);
  return true;
}

Telemetry Controller::telemetry() const {
  Telemetry t;
  t.mode = mode_;
  t.phase = mission_.phase();
  t.autoPaused = autoPaused_;
  t.pose = localizer_.pose();
  t.speed = last_.encoderSpeed;
  t.steer = lastOut_.steer;
  t.motorDuty = lastOut_.motorDuty;
  t.weightKg = weight_.kg();
  t.batteryPct = last_.batteryPct;
  t.safety = guardResult_.state;
  t.freeDistance = guardResult_.freeDistance;
  t.sensorFault = guardResult_.sensorFault;
  t.fault = fault_;
  t.rtkOk = localizer_.rtkOk();
  t.light = lastOut_.light;
  return t;
}

}  // namespace axle
