#pragma once
#include "axle/types.h"

// Localização: odometria das rodas corrigida por GPS RTK (ex.: u-blox ZED-F9P com base fixa ou NTRIP).
//
// - lat/lon viram metros num plano local com origem num ponto medido do canteiro (aprox. equirretangular,
//   erro desprezível para canteiros de algumas centenas de metros);
// - cada fixo RTK puxa a pose da odometria em direção à posição medida (filtro complementar);
// - o rumo é corrigido pelo deslocamento medido pelo GPS quando o carrinho anda em linha reta;
// - sem RTK "fixed" recente, rtkOk() fica falso e o supervisor pausa o modo autônomo.

namespace axle {

enum class GnssFix : uint8_t { None, Single, RtkFloat, RtkFixed };

struct GnssSample {
  double latDeg = 0.0;
  double lonDeg = 0.0;
  GnssFix fix = GnssFix::None;
  float horizontalAccuracy = 99.0f;  // m (hAcc do receptor)
};

class Localizer {
 public:
  void setOrigin(double latDeg, double lonDeg);
  Vec2 toLocal(double latDeg, double lonDeg) const;
  void toGeo(Vec2 p, double& latDeg, double& lonDeg) const;

  // Avança a pose pela odometria (distância percorrida + esterço) — chamar a cada ciclo de controle.
  void predict(float distance, float steer);
  // Corrige com uma amostra do GPS — chamar quando chegar uma nova (tipicamente 5–10 Hz).
  void correct(const GnssSample& g);
  // Conta o tempo sem correção RTK válida.
  void tick(float dt) { sinceRtk_ += dt; }

  // Posição e rumo declarados pelo operador; o próximo fixo RTK assume a posição.
  void reset(Pose p);
  const Pose& pose() const { return pose_; }
  bool rtkOk() const;
  bool originSet() const { return originSet_; }
  // Rumo declarado pelo operador ou confirmado pelo GPS numa reta; falso enquanto GPS e odometria discordam.
  bool headingKnown() const { return headingKnown_; }

 private:
  void correctHeading(Vec2 measured);

  double originLat_ = 0.0, originLon_ = 0.0, cosLat_ = 1.0;
  Pose pose_;
  float sinceRtk_ = 1e9f;
  bool everFixed_ = false;
  bool originSet_ = false;
  bool headingKnown_ = false;
  bool reversing_ = false;
  Vec2 lastFix_;
  bool haveLastFix_ = false;
};

}  // namespace axle
