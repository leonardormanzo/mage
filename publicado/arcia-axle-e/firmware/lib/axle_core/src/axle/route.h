#pragma once
#include <array>
#include <cstddef>

#include "axle/types.h"

// Trajetórias do canteiro e seguidor "pure pursuit".
// Memória fixa (sem new/malloc): cada caminho guarda até kMaxPoints pontos com a distância acumulada.

namespace axle {

class Path {
 public:
  static constexpr std::size_t kMaxPoints = 400;

  // Segmento de reta e arco (centro, raio, ângulos inicial/final em rad), amostrados a cada `step` m.
  bool addLine(Vec2 a, Vec2 b, float step = 0.25f);
  bool addArc(Vec2 center, float radius, float a0, float a1, float step = 0.25f);

  std::size_t size() const { return count_; }
  const Vec2& point(std::size_t i) const { return pts_[i]; }
  float s(std::size_t i) const { return s_[i]; }
  float length() const { return count_ ? s_[count_ - 1] : 0.0f; }
  void clear() { count_ = 0; }

 private:
  bool push(Vec2 p);
  std::array<Vec2, kMaxPoints> pts_{};
  std::array<float, kMaxPoints> s_{};
  std::size_t count_ = 0;
};

struct FollowResult {
  float targetSpeed = 0.0f;  // m/s
  float steer = 0.0f;        // rad
  float distanceToEnd = 0.0f;
};

class PathFollower {
 public:
  void restart() { index_ = -1; }
  FollowResult follow(const Path& path, const Pose& pose, float speed, float maxSpeed);

 private:
  long index_ = -1;
};

// Rota da simulação (js/autopilot.js), convertida para o referencial do firmware (x_fw = z_sim,
// y_fw = x_sim). Em campo, troque por pontos medidos no canteiro (GNSS RTK ou marcos).
struct SiteRoute {
  Path toDump;  // baia de carregamento -> bota-fora
  Path toLoad;  // fim da ré -> retorno -> baia de carregamento
  Pose start;   // onde o carrinho começa (estrada sul, sentido oeste)
};
void buildSiteRoute(SiteRoute& route);

// Distância da posição ao ponto mais próximo do caminho (m). Caminho vazio = muito longe.
float distanceToPath(const Path& path, Vec2 p);

}  // namespace axle
