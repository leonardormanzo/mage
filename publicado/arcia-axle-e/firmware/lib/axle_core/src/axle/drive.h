#pragma once
#include "axle/types.h"

// Tração e direção: rampa de velocidade, PI de velocidade do motor, limitador de esterço e odometria.

namespace axle {

// Limita a variação da velocidade-alvo: acelera suave, freia mais forte, e mais forte ainda em emergência.
class SpeedRamp {
 public:
  float step(float target, float dt, bool emergency);
  float value() const { return value_; }
  void reset(float v = 0.0f) { value_ = v; }

 private:
  float value_ = 0.0f;
};

struct PiGains {
  float feedForward = 1.0f / 4.5f;  // duty por m/s (motor sem carga a 100% ≈ 4,5 m/s)
  float kp = 0.25f;
  float ki = 0.40f;
};

// PI de velocidade com feed-forward e anti-windup. Saída: duty de -1 (ré) a +1 (frente).
class SpeedController {
 public:
  explicit SpeedController(PiGains g = {}) : g_(g) {}
  float update(float setpoint, float measured, float dt);
  void reset() { integral_ = 0.0f; }

 private:
  PiGains g_;
  float integral_ = 0.0f;
};

// Esterço máximo cai com a velocidade e o servo tem velocidade de giro limitada.
class SteeringLimiter {
 public:
  float step(float target, float speed, float dt);
  float value() const { return value_; }

 private:
  float value_ = 0.0f;
};

// Odometria pelo modelo de bicicleta: avança a pose pela distância do encoder da transmissão e pelo
// ângulo de esterço. Devolve a pose nova; não altera a recebida.
Pose integrateBicycle(const Pose& pose, float distance, float steer);

}  // namespace axle
