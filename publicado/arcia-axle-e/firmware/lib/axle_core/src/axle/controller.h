#pragma once
#include <array>
#include <cstdint>

#include "axle/collision_guard.h"
#include "axle/drive.h"
#include "axle/dump_controller.h"
#include "axle/localizer.h"
#include "axle/mission.h"
#include "axle/route.h"
#include "axle/sensor_layout.h"
#include "axle/weight_sensor.h"

// Supervisor do Axle-E: recebe um quadro com todas as leituras do ciclo e devolve o que cada
// atuador deve fazer. Não toca em hardware — por isso roda igual no ESP32 e nos testes do PC.
//
// Ordem de prioridade dentro de um ciclo:
//  1. falhas travadas (emergência, laço atrasado, célula de carga, caçamba) mandam parar;
//  2. intertravamento: não anda com a caçamba fora do fim de curso inferior;
//  3. guarda de colisão: alerta limita a velocidade, freio zera o alvo com desaceleração de emergência;
//  4. só então o comando do operador (manual, com homem-morto) ou do ciclo autônomo.

namespace axle {

struct ManualCommand {
  float throttle = 0.0f;  // -1 ré … +1 frente
  float steer = 0.0f;     // -1 direita … +1 esquerda
  DumpCommand dump = DumpCommand::Hold;
  float ageS = 1e9f;      // idade do último comando recebido do controle
};

struct SensorFrame {
  float dt = 1.0f / 50.0f;                              // s desde o ciclo anterior (medido)
  std::array<RangeReading, kRangeSensorCount> ranges{};
  int32_t loadRaw = 0;                                  // última contagem do HX711
  float loadAgeMs = 0.0f;
  float encoderDistance = 0.0f;                         // m andados desde o ciclo anterior (com sinal)
  float encoderSpeed = 0.0f;                            // m/s (com sinal)
  bool bucketUp = false;                                // fim de curso superior
  bool bucketDown = true;                               // fim de curso inferior
  bool estopPressed = false;                            // laço NF da emergência aberto
  float batteryPct = 100.0f;
  ManualCommand manual;
  bool gnssNew = false;                                 // chegou amostra nova do GPS neste ciclo
  GnssSample gnss;
};

enum class Buzzer : uint8_t { Off, Slow, Fast, Continuous };

struct ActuatorOutputs {
  float motorDuty = 0.0f;     // -1 ré … +1 frente
  bool motorEnable = false;   // liga a ignição do controlador do motor
  bool parkingBrake = true;   // true = freio de estacionamento aplicado
  float steer = 0.0f;         // rad
  int8_t bucket = 0;          // +1 sobe, -1 desce, 0 parado
  StatusLight light = StatusLight::SysOk;
  Buzzer buzzer = Buzzer::Off;
};

enum class AutoStartResult : uint8_t {
  Started, Faulted, EstopActive, LowBattery, NoRtk, NoOrigin, NoHeading, OffRoute, Moving
};
const char* toString(AutoStartResult r);

struct Telemetry {
  Mode mode = Mode::Manual;
  MissionPhase phase = MissionPhase::Idle;
  bool autoPaused = false;  // autônomo esperando o RTK voltar
  Pose pose;
  float speed = 0.0f;
  float steer = 0.0f;
  float motorDuty = 0.0f;
  float weightKg = 0.0f;
  float batteryPct = 0.0f;
  SafetyState safety = SafetyState::Ok;
  float freeDistance = 0.0f;
  bool sensorFault = false;
  Fault fault = Fault::None;
  bool rtkOk = false;
  StatusLight light = StatusLight::SysOk;
};

class Controller {
 public:
  explicit Controller(const SiteRoute& route, WeightCalibration cal = {});

  ActuatorOutputs step(const SensorFrame& in);

  // Comandos do operador (console serial / painel). Valem a partir do próximo ciclo.
  // Os que mudam referência ou calibração só são aceitos no manual e com o carrinho parado.
  AutoStartResult requestAuto();
  void requestManual();
  bool resetFaults();  // emergência solta, parado, sem comando manual ativo, causa resolvida
  bool tare();         // caçamba vazia
  bool calibrateWeight(float knownKg);
  bool setOrigin(double latDeg, double lonDeg);
  bool setPose(Pose p);

  Telemetry telemetry() const;
  Fault fault() const { return fault_; }
  Mode mode() const { return mode_; }
  const WeightCalibration& weightCalibration() const { return weight_.calibration(); }
  const Localizer& localizer() const { return localizer_; }

 private:
  void updateFaults(const SensorFrame& in);
  void checkDrivePlausibility(const SensorFrame& in);
  void latch(Fault f);
  bool hardStop() const;
  bool standingStill() const;
  bool canReconfigure() const { return mode_ == Mode::Manual && standingStill(); }
  MissionOutputs manualIntent(const SensorFrame& in) const;
  MissionOutputs autoIntent(const SensorFrame& in);
  float limitBySafety(const SensorFrame& in, float target);
  ActuatorOutputs actuate(const SensorFrame& in, const MissionOutputs& intent);
  StatusLight statusLight() const;
  Buzzer buzzer(float setpoint) const;

  Mission mission_;
  WeightSensor weight_;
  Localizer localizer_;
  CollisionGuard guard_;
  DumpController dump_;
  SpeedRamp ramp_;
  SpeedController pi_;
  SteeringLimiter steer_;

  Mode mode_ = Mode::Manual;
  Fault fault_ = Fault::None;
  bool autoPaused_ = false;
  float stallTime_ = 0.0f;
  float overspeedTime_ = 0.0f;
  GuardResult guardResult_;
  SensorFrame last_;
  ActuatorOutputs lastOut_;
};

}  // namespace axle
