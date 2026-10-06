#pragma once
// Modelo físico simplificado do carrinho e do canteiro, só para os testes no PC.
// Fecha a malha com o supervisor: o Controller decide, a Plant reage, e a Plant gera o próximo quadro de sensores.

#include <cmath>
#include <vector>

#include "axle/config.h"
#include "axle/controller.h"
#include "axle/drive.h"
#include "axle/localizer.h"
#include "axle/route.h"
#include "axle/sensor_layout.h"

namespace sim {

constexpr float kDt = 1.0f / axle::cfg::kControlHz;
constexpr float kPi = 3.14159265f;
constexpr double kOriginLat = -23.5505;  // canteiro fictício em São Paulo
constexpr double kOriginLon = -46.6333;
constexpr float kBeamHalfAngle = 0.30f;   // rad, cone do ultrassom
constexpr float kMotorTau = 0.30f;        // s, resposta do motor+carga
constexpr float kParkingDecel = 4.0f;     // m/s² do freio de mola
constexpr float kBucketTravelS = 4.0f;    // s para subir ou descer a caçamba inteira
constexpr float kLoaderKgPerS = 40.0f;    // escavadeira enchendo
constexpr float kDumpKgPerS = 80.0f;      // material escorrendo da caçamba
constexpr float kLoadedKg = 185.0f;
constexpr float kRunawaySpeed = 6.5f;     // m/s que o motor descontrolado alcança
const axle::Vec2 kLoadSpot{10.0f, -14.0f};

struct Obstacle {
  float x, y, r;
};

class Plant {
 public:
  axle::Pose pose;
  float speed = 0.0f;
  float bucket = 0.0f;  // 0 = abaixada, 1 = no ângulo máximo
  float loadKg = 0.0f;
  bool bucketStuck = false, estop = false, gnssOn = true, loadCellOn = true, loaderOn = true;
  bool encoderDead = false;  // encoder solto: lê zero com o carrinho andando
  bool runaway = false;      // controlador do motor com defeito: acelera sozinho
  bool limitShort = false;   // fio do fim de curso superior em curto: lê "em cima" sempre
  float battery = 80.0f;
  std::vector<Obstacle> obstacles;
  axle::ManualCommand manual;  // ageS conta sozinho a partir do último sendManual()
  axle::WeightCalibration cal{50000, 1000.0f};

  Plant() { geo_.setOrigin(kOriginLat, kOriginLon); }

  void sendManual(float throttle, float steer, axle::DumpCommand dump = axle::DumpCommand::Hold) {
    manual.throttle = throttle;
    manual.steer = steer;
    manual.dump = dump;
    manual.ageS = 0.0f;
  }

  bool bucketDown() const { return bucket <= 0.0f; }
  bool bucketUp() const { return bucket >= 1.0f; }

  axle::SensorFrame frame(float dt) {
    axle::SensorFrame f;
    f.dt = dt;
    f.encoderDistance = encoderDead ? 0.0f : speed * dt;
    f.encoderSpeed = encoderDead ? 0.0f : speed;
    f.bucketUp = bucketUp() || limitShort;
    f.bucketDown = bucketDown();
    f.estopPressed = estop;
    f.batteryPct = battery;
    f.loadRaw = cal.tareOffset + static_cast<int32_t>(loadKg * cal.countsPerKg);
    f.loadAgeMs = loadCellOn ? 10.0f : 5000.0f;
    f.manual = manual;
    manual.ageS += dt;
    for (std::size_t i = 0; i < axle::kRangeSensorCount; ++i) f.ranges[i] = range(axle::kRangeMounts[i]);
    gnssTimer_ += dt;
    if (gnssOn && gnssTimer_ >= 0.1f) {
      gnssTimer_ = 0.0f;
      f.gnssNew = true;
      geo_.toGeo({pose.x, pose.y}, f.gnss.latDeg, f.gnss.lonDeg);
      f.gnss.fix = axle::GnssFix::RtkFixed;
      f.gnss.horizontalAccuracy = 0.02f;
    }
    return f;
  }

  void apply(const axle::ActuatorOutputs& out, float dt) {
    const float duty = out.motorEnable ? out.motorDuty : 0.0f;
    float accel = (duty * axle::cfg::kMaxSpeedManual - speed) / kMotorTau;
    if (runaway) accel = (kRunawaySpeed - speed) / kMotorTau;
    if (out.parkingBrake) accel = speed > 0.0f ? -kParkingDecel : (speed < 0.0f ? kParkingDecel : 0.0f);
    const float next = speed + accel * dt;
    speed = (out.parkingBrake && next * speed < 0.0f) ? 0.0f : next;  // o freio não inverte o sentido
    pose = axle::integrateBicycle(pose, speed * dt, out.steer);

    if (!bucketStuck) bucket += out.bucket * dt / kBucketTravelS;
    bucket = bucket < 0.0f ? 0.0f : (bucket > 1.0f ? 1.0f : bucket);

    const bool atLoadSpot = std::hypot(pose.x - kLoadSpot.x, pose.y - kLoadSpot.y) < 0.5f;
    if (loaderOn && atLoadSpot && std::fabs(speed) < 0.05f && bucketDown() && loadKg < kLoadedKg) {
      loadKg += kLoaderKgPerS * dt;
    }
    if (bucket > 0.8f) loadKg = loadKg > kDumpKgPerS * dt ? loadKg - kDumpKgPerS * dt : 0.0f;
  }

  // Distância do para-choque dianteiro ao obstáculo mais próximo (para conferir que parou antes).
  float frontClearance() const {
    float best = 1e9f;
    const float fx = pose.x + axle::cfg::kFrontOffset * std::cos(pose.heading);
    const float fy = pose.y + axle::cfg::kFrontOffset * std::sin(pose.heading);
    for (const Obstacle& o : obstacles) best = std::fmin(best, std::hypot(o.x - fx, o.y - fy) - o.r);
    return best;
  }

 private:
  axle::RangeReading range(const axle::RangeSensorMount& m) const {
    const float c = std::cos(pose.heading), s = std::sin(pose.heading);
    const float sx = pose.x + c * m.x - s * m.y;
    const float sy = pose.y + s * m.x + c * m.y;
    const float beam = pose.heading + m.bearing;
    axle::RangeReading r;
    r.meters = axle::cfg::kRangeMax;
    r.ageMs = 20.0f;
    for (const Obstacle& o : obstacles) {
      const float dx = o.x - sx, dy = o.y - sy;
      const float off = std::remainder(std::atan2(dy, dx) - beam, 2.0f * 3.14159265f);
      const float d = std::hypot(dx, dy) - o.r;
      if (std::fabs(off) < kBeamHalfAngle && d < r.meters) r.meters = d < 0.0f ? 0.0f : d;
    }
    return r;
  }

  axle::Localizer geo_;
  float gnssTimer_ = 1.0f;
};

// Supervisor + carrinho + rota, já posicionados no início da rota e com o GPS chegando.
struct Rig {
  axle::SiteRoute route;
  Plant plant;
  axle::Controller ctl;
  axle::ActuatorOutputs out;

  enum class Setup { Full, NoOrigin, OriginOnly };

  // Full: operador já informou origem e pose. Os outros modos testam a partida sem essas informações.
  explicit Rig(Setup setup = Setup::Full) : ctl(route, plant.cal) {
    axle::buildSiteRoute(route);
    if (setup != Setup::NoOrigin) ctl.setOrigin(kOriginLat, kOriginLon);
    if (setup == Setup::Full) ctl.setPose(route.start);
    plant.pose = route.start;
  }

  const axle::ActuatorOutputs& step() {
    const axle::SensorFrame f = plant.frame(kDt);
    out = ctl.step(f);
    plant.apply(out, kDt);
    return out;
  }

  void run(float seconds) {
    for (int i = 0; i < static_cast<int>(seconds / kDt); ++i) step();
  }

  // Roda até a condição valer ou o tempo acabar. Retorna se a condição foi atingida.
  template <typename Pred>
  bool runUntil(float seconds, Pred done) {
    for (int i = 0; i < static_cast<int>(seconds / kDt); ++i) {
      step();
      if (done()) return true;
    }
    return false;
  }
};

}  // namespace sim
