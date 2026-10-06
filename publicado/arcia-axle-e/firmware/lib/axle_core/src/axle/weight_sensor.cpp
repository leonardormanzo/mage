#include "axle/weight_sensor.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

float WeightSensor::update(int32_t raw, float dt) {
  // Em double: tara corrompida na memória não pode estourar a subtração de int32.
  const float kg = static_cast<float>((static_cast<double>(raw) - cal_.tareOffset) / cal_.countsPerKg);
  implausible_ = !std::isfinite(kg) || std::fabs(kg) > cfg::kWeightImplausibleKg;
  if (implausible_) return filtered_;  // mantém o último valor bom; o supervisor trata a falha

  const float clamped = kg < 0.0f ? 0.0f : kg;
  if (!primed_) {
    filtered_ = clamped;
    primed_ = true;
  } else {
    const float alpha = dt / (cfg::kWeightFilterTau + dt);
    filtered_ += alpha * (clamped - filtered_);
  }
  return filtered_;
}

bool isPlausibleScale(float countsPerKg) {
  return std::isfinite(countsPerKg) && std::fabs(countsPerKg) >= kMinCountsPerKg;
}

bool WeightSensor::calibrate(int32_t raw, float knownKg) {
  if (!(knownKg > 0.0f)) return false;
  const double counts = static_cast<double>(raw) - cal_.tareOffset;
  const float scale = static_cast<float>(counts / knownKg);
  if (!isPlausibleScale(scale)) return false;  // massa não registrou: célula solta ou caçamba vazia
  cal_.countsPerKg = scale;
  primed_ = false;
  return true;
}

}  // namespace axle
