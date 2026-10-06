#include "axle/drive.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

namespace {
float clampf(float v, float lo, float hi) {
  if (!std::isfinite(v)) return 0.0f;  // NaN nunca entra no estado (ficaria preso para sempre)
  return v < lo ? lo : (v > hi ? hi : v);
}
}  // namespace

float SpeedRamp::step(float target, float dt, bool emergency) {
  const float diff = target - value_;
  const bool gainingSpeed = (value_ >= 0.0f && diff > 0.0f) || (value_ <= 0.0f && diff < 0.0f);
  const float rate = gainingSpeed ? cfg::kAccel : (emergency ? cfg::kEmergencyDecel : cfg::kDecel);
  const float maxStep = rate * dt;
  value_ += clampf(diff, -maxStep, maxStep);
  return value_;
}

float SpeedController::update(float setpoint, float measured, float dt) {
  if (setpoint == 0.0f && std::fabs(measured) < 0.05f) {  // parado: solta o motor e zera o integrador
    integral_ = 0.0f;
    return 0.0f;
  }
  const float error = setpoint - measured;
  const float unsat = g_.feedForward * setpoint + g_.kp * error + g_.ki * integral_;
  // Anti-windup: só integra se não estiver saturado, ou se o erro ajuda a sair da saturação.
  if (std::fabs(unsat) < 1.0f || (unsat > 0.0f) != (error > 0.0f)) integral_ += error * dt;
  return clampf(g_.feedForward * setpoint + g_.kp * error + g_.ki * integral_, -1.0f, 1.0f);
}

float SteeringLimiter::step(float target, float speed, float dt) {
  const float maxSteer = cfg::kMaxSteer / (1.0f + std::fabs(speed) * cfg::kSteerSpeedFactor);
  const float goal = clampf(target, -maxSteer, maxSteer);
  const float maxStep = cfg::kSteerRate * dt;
  value_ += clampf(goal - value_, -maxStep, maxStep);
  return value_;
}

Pose integrateBicycle(const Pose& pose, float distance, float steer) {
  const float dHeading = distance / cfg::kWheelbase * std::tan(steer);
  const float mid = pose.heading + dHeading * 0.5f;
  return {pose.x + distance * std::cos(mid), pose.y + distance * std::sin(mid),
          std::remainder(pose.heading + dHeading, 2.0f * 3.14159265358979f)};
}

}  // namespace axle
