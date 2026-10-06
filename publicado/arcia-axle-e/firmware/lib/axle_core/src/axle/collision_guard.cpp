#include "axle/collision_guard.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

namespace {
constexpr float kPi = 3.14159265358979f;
constexpr float kFar = 1e9f;
constexpr float kStraightCurvature = 0.02f;  // abaixo disso o caminho é tratado como reta
}  // namespace

float freeDistanceTo(float px, float py, float curvature, int8_t direction) {
  // No referencial "de marcha": f para onde o carrinho vai, l para a esquerda desse sentido.
  float f = direction > 0 ? px : -px;
  float l = direction > 0 ? py : -py;
  const float bumper = direction > 0 ? cfg::kFrontOffset : cfg::kRearOffset;
  if (f < bumper * 0.5f) return kFar;  // ao lado/atrás do para-choque: não está no caminho

  const float corridor = cfg::kBodyHalfWidth + cfg::kObstacleRadius + cfg::kSafetyMargin;
  // Em ré, o centro de rotação fica do mesmo lado físico, que no referencial de marcha é o oposto.
  const float k = direction > 0 ? curvature : -curvature;

  float along;
  if (std::fabs(k) < kStraightCurvature) {
    if (std::fabs(l) > corridor) return kFar;
    along = f;
  } else {
    const float r = 1.0f / k;  // centro de rotação em (f=0, l=r)
    const float rl = l - r;
    const float dist = std::hypot(rl, f);
    if (std::fabs(dist - std::fabs(r)) > corridor) return kFar;
    const float a0 = std::atan2(0.0f, -r);
    const float a1 = std::atan2(f, rl);
    float swept = r > 0 ? a0 - a1 : a1 - a0;
    swept = std::fmod(std::fmod(swept, 2 * kPi) + 2 * kPi, 2 * kPi);
    if (swept > kPi) return kFar;
    along = swept * std::fabs(r);
  }
  return along - bumper - cfg::kObstacleRadius;
}

GuardResult CollisionGuard::update(float speed, float steer, int8_t intent, const RangeSensorMount* mounts,
                                   const RangeReading* readings, std::size_t count, float maxRange) {
  GuardResult out;
  const bool moving = std::fabs(speed) > 0.05f;
  const int8_t dir = moving ? (speed > 0 ? 1 : -1) : (intent != 0 ? intent : lastDirection_);
  const float curvature = std::tan(steer) / cfg::kWheelbase;

  float freeDist = kFar;
  if (!std::isfinite(speed) || !std::isfinite(curvature)) {  // entrada corrompida: não dá para saber o caminho
    out.sensorFault = true;
    freeDist = 0.0f;
  }
  for (std::size_t i = 0; i < count; ++i) {
    const RangeSensorMount& m = mounts[i];
    const bool pointsForward = std::cos(m.bearing) > 0.0f;
    if (pointsForward != (dir > 0)) continue;  // só os sensores que olham para onde vamos

    const RangeReading& rd = readings[i];
    if (rd.ageMs > cfg::kSensorStaleMs || !std::isfinite(rd.meters)) {
      out.sensorFault = true;
      freeDist = 0.0f;
      continue;
    }
    if (rd.meters >= maxRange) continue;  // sem eco: nada no alcance desse sensor
    const float px = m.x + rd.meters * std::cos(m.bearing);
    const float py = m.y + rd.meters * std::sin(m.bearing);
    const float d = freeDistanceTo(px, py, curvature, dir);
    if (!(d >= freeDist)) freeDist = std::isfinite(d) ? d : 0.0f;  // NaN conta como encostado
  }

  const float v = std::isfinite(speed) ? std::fabs(speed) : 0.0f;
  // Distância de parada = frenagem + o que se anda enquanto a leitura envelhece + folga mínima.
  const float stopDist = v * v / (2.0f * cfg::kEmergencyDecel) + v * cfg::kSensorLatencyS + cfg::kMinStopDistance;
  const float warnDist = stopDist + cfg::kWarnExtra + v * cfg::kWarnTimeGap;

  SafetyState state = SafetyState::Ok;
  if (freeDist < stopDist || (braking_ && freeDist < stopDist + cfg::kBrakeHysteresis)) {
    state = SafetyState::Brake;
  } else if (freeDist < warnDist) {
    state = SafetyState::Warn;
  }
  // Parado e sem ninguém pedindo para andar: não há o que frear, só avisar.
  if (!moving && intent == 0 && state == SafetyState::Brake && !out.sensorFault) state = SafetyState::Warn;

  braking_ = state == SafetyState::Brake;
  lastDirection_ = dir;
  out.state = state;
  out.freeDistance = freeDist;
  out.direction = dir;
  out.stopDistance = stopDist;
  out.warnDistance = warnDist;
  return out;
}

}  // namespace axle
