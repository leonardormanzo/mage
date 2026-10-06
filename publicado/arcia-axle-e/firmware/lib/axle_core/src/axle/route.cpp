#include "axle/route.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

namespace {
constexpr float kPi = 3.14159265358979f;
float minf(float a, float b) { return a < b ? a : b; }
float maxf(float a, float b) { return a > b ? a : b; }
}  // namespace

bool Path::push(Vec2 p) {
  if (count_ >= kMaxPoints) return false;
  const float ds = count_ ? std::hypot(p.x - pts_[count_ - 1].x, p.y - pts_[count_ - 1].y) : 0.0f;
  if (count_ && ds < 1e-4f) return true;  // ponto repetido na emenda de segmentos
  s_[count_] = count_ ? s_[count_ - 1] + ds : 0.0f;
  pts_[count_++] = p;
  return true;
}

bool Path::addLine(Vec2 a, Vec2 b, float step) {
  const int n = maxf(1.0f, std::ceil(std::hypot(b.x - a.x, b.y - a.y) / step));
  for (int i = 0; i <= n; ++i) {
    const float t = static_cast<float>(i) / n;
    if (!push({a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t})) return false;
  }
  return true;
}

bool Path::addArc(Vec2 c, float r, float a0, float a1, float step) {
  const int n = maxf(2.0f, std::ceil(std::fabs(a1 - a0) * r / step));
  for (int i = 0; i <= n; ++i) {
    const float a = a0 + (a1 - a0) * static_cast<float>(i) / n;
    if (!push({c.x + r * std::cos(a), c.y + r * std::sin(a)})) return false;
  }
  return true;
}

FollowResult PathFollower::follow(const Path& path, const Pose& pose, float speed, float maxSpeed) {
  FollowResult out;
  const long n = static_cast<long>(path.size());
  if (n < 2) return out;

  // Ponto mais próximo: busca global na primeira vez, depois só numa janela à frente.
  const long from = index_ < 0 ? 0 : (index_ > 4 ? index_ - 4 : 0);
  const long to = index_ < 0 ? n : (index_ + 40 < n ? index_ + 40 : n);
  float best = 1e18f;
  const float ch = std::cos(pose.heading), sh = std::sin(pose.heading);
  for (long i = from; i < to; ++i) {
    const Vec2& p = path.point(i);
    float score = (p.x - pose.x) * (p.x - pose.x) + (p.y - pose.y) * (p.y - pose.y);
    if (index_ < 0 && i < n - 1) {  // na busca global, evita pegar o trecho no sentido contrário
      const Vec2& q = path.point(i + 1);
      if ((q.x - p.x) * ch + (q.y - p.y) * sh < 0.0f) score += 64.0f;
    }
    if (score < best) { best = score; index_ = i; }
  }

  const float s0 = path.s(index_);
  const float remaining = path.length() - s0;
  const float lookahead = maxf(cfg::kLookaheadMin, 1.5f + cfg::kLookaheadGain * std::fabs(speed));
  const Vec2& end = path.point(n - 1);
  const Vec2& prev = path.point(n - 2);
  const float eLen = std::hypot(end.x - prev.x, end.y - prev.y);
  const float ex = (end.x - prev.x) / eLen, ey = (end.y - prev.y) / eLen;

  Vec2 target;
  if (remaining < lookahead) {  // além do fim: prolonga a última direção para chegar alinhado
    target = {end.x + ex * (lookahead - remaining), end.y + ey * (lookahead - remaining)};
  } else {
    long ti = index_;
    while (ti < n - 1 && path.s(ti) < s0 + lookahead) ++ti;
    target = path.point(ti);
  }
  const float dx = target.x - pose.x, dy = target.y - pose.y;
  const float left = -sh * dx + ch * dy;
  const float curvature = 2.0f * left / maxf(dx * dx + dy * dy, 0.01f);
  out.steer = std::atan(curvature * cfg::kWheelbase);
  out.distanceToEnd = remaining < 3.0f ? (end.x - pose.x) * ex + (end.y - pose.y) * ey : remaining;

  const float vCurve = std::sqrt(cfg::kLatAccel / maxf(std::fabs(curvature), 1e-3f));
  const float vStop = std::sqrt(2.0f * cfg::kStopDecel * maxf(0.0f, out.distanceToEnd - 0.05f));
  out.targetSpeed = minf(maxSpeed, minf(vCurve, vStop));
  return out;
}

void buildSiteRoute(SiteRoute& r) {
  // Pontos (x_fw, y_fw) = (z_sim, x_sim) da simulação.
  const Vec2 loadStop{10.0f, -14.0f};
  const Vec2 dumpStop{10.0f, 6.0f};
  r.toDump.clear();
  r.toDump.addLine(loadStop, dumpStop);

  r.toLoad.clear();
  // Retorno leste: arco de raio 4 em torno de (6, 1), de (10, 1) até (2, 1) passando por (6, 5).
  r.toLoad.addArc({6.0f, 1.0f}, 4.0f, 0.0f, kPi);
  r.toLoad.addLine({2.0f, 1.0f}, {2.0f, -18.0f});
  // Retorno oeste: arco de raio 4 em torno de (6, -18), de (2, -18) até (10, -18).
  r.toLoad.addArc({6.0f, -18.0f}, 4.0f, kPi, 2.0f * kPi);
  r.toLoad.addLine({10.0f, -18.0f}, loadStop);

  r.start = {2.0f, -6.0f, -kPi / 2.0f};
}

float distanceToPath(const Path& path, Vec2 p) {
  float best = 1e9f;
  for (std::size_t i = 0; i < path.size(); ++i) {
    best = minf(best, std::hypot(path.point(i).x - p.x, path.point(i).y - p.y));
  }
  return best;
}

}  // namespace axle
