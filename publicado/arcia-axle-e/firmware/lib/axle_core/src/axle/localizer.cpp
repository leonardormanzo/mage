#include "axle/localizer.h"

#include <cmath>

#include "axle/drive.h"

namespace axle {

namespace {
constexpr double kEarthRadius = 6378137.0;
constexpr double kDegToRad = 3.14159265358979323846 / 180.0;
constexpr float kTwoPi = 2.0f * 3.14159265358979f;
constexpr float kPositionGain = 0.35f;      // quanto cada fixo RTK puxa a pose
constexpr float kHeadingGain = 0.30f;
constexpr float kHeadingBaseline = 1.0f;    // m em linha reta para estimar o rumo pelo GPS
constexpr float kStraightSteer = 0.05f;     // rad: abaixo disso o trecho conta como reto
constexpr float kMaxRtkAccuracy = 0.05f;    // m
constexpr float kRtkTimeoutS = 2.0f;
constexpr float kHeadingConfirmed = 0.15f;  // rad: GPS e odometria concordam no rumo
}  // namespace

void Localizer::setOrigin(double latDeg, double lonDeg) {
  originLat_ = latDeg;
  originLon_ = lonDeg;
  cosLat_ = std::cos(latDeg * kDegToRad);
  originSet_ = true;
  everFixed_ = false;  // posição antiga estava em outro referencial
}

Vec2 Localizer::toLocal(double latDeg, double lonDeg) const {
  // x para leste, y para norte (metros).
  const double x = (lonDeg - originLon_) * kDegToRad * kEarthRadius * cosLat_;
  const double y = (latDeg - originLat_) * kDegToRad * kEarthRadius;
  return {static_cast<float>(x), static_cast<float>(y)};
}

void Localizer::toGeo(Vec2 p, double& latDeg, double& lonDeg) const {
  latDeg = originLat_ + p.y / kEarthRadius / kDegToRad;
  lonDeg = originLon_ + p.x / (kEarthRadius * cosLat_) / kDegToRad;
}

void Localizer::reset(Pose p) {
  pose_ = p;
  haveLastFix_ = false;
  everFixed_ = false;   // o próximo fixo RTK manda na posição; o rumo informado fica
  headingKnown_ = true; // rumo declarado pelo operador
}

void Localizer::predict(float distance, float steer) {
  pose_ = integrateBicycle(pose_, distance, steer);
  if (distance != 0.0f) reversing_ = distance < 0.0f;
  // Rumo pelo GPS só vale em trecho reto: uma curva invalida a linha de base.
  if (std::fabs(steer) >= kStraightSteer) haveLastFix_ = false;
}

void Localizer::correct(const GnssSample& g) {
  if (g.fix != GnssFix::RtkFixed || g.horizontalAccuracy > kMaxRtkAccuracy) return;
  const Vec2 m = toLocal(g.latDeg, g.lonDeg);
  sinceRtk_ = 0.0f;
  if (!everFixed_) {  // primeiro fixo: a odometria ainda não sabe onde está, assume a posição medida
    pose_.x = m.x;
    pose_.y = m.y;
    everFixed_ = true;
  } else {
    pose_.x += kPositionGain * (m.x - pose_.x);
    pose_.y += kPositionGain * (m.y - pose_.y);
  }
  correctHeading(m);
}

void Localizer::correctHeading(Vec2 m) {
  if (!haveLastFix_) {
    lastFix_ = m;
    haveLastFix_ = true;
    return;
  }
  const float dx = m.x - lastFix_.x, dy = m.y - lastFix_.y;
  if (std::hypot(dx, dy) < kHeadingBaseline) return;
  // Em ré (sentido dado pelo encoder) o deslocamento aponta para trás: o rumo do veículo é o oposto.
  // Decidir pelo encoder, e não pelo tamanho do erro, deixa corrigir até um rumo 180° errado.
  float measured = std::atan2(dy, dx);
  if (reversing_) measured += kTwoPi / 2.0f;
  const float err = std::remainder(measured - pose_.heading, kTwoPi);
  pose_.heading = std::remainder(pose_.heading + kHeadingGain * err, kTwoPi);
  headingKnown_ = std::fabs(err) < kHeadingConfirmed;
  lastFix_ = m;
}

bool Localizer::rtkOk() const { return sinceRtk_ < kRtkTimeoutS; }

}  // namespace axle
