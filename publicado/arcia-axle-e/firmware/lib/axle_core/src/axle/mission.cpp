#include "axle/mission.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

const char* toString(MissionPhase p) {
  switch (p) {
    case MissionPhase::Idle: return "parado";
    case MissionPhase::ToLoad: return "indo_carregar";
    case MissionPhase::WaitLoad: return "aguardando_carga";
    case MissionPhase::ToDump: return "indo_descarregar";
    case MissionPhase::Dump: return "basculando";
    case MissionPhase::Lower: return "recolhendo";
    case MissionPhase::Reverse: return "re";
  }
  return "?";
}

void Mission::setPhase(MissionPhase p) {
  phase_ = p;
  timer_ = 0.0f;
  stable_ = 0.0f;
  follower_.restart();
}

namespace {
bool startsLoaded(float weightKg) { return weightKg >= cfg::kLoadTargetKg * 0.8f; }
}  // namespace

void Mission::start(float weightKg) {
  setPhase(startsLoaded(weightKg) ? MissionPhase::ToDump : MissionPhase::ToLoad);
}

const Path& Mission::firstPath(float weightKg) const {
  return startsLoaded(weightKg) ? route_.toDump : route_.toLoad;
}

void Mission::stop() { setPhase(MissionPhase::Idle); }

MissionOutputs Mission::step(const MissionInputs& in, float dt) {
  MissionOutputs out;
  timer_ += dt;
  const auto arrived = [&](const FollowResult& r) {
    return r.distanceToEnd < cfg::kArriveDistance && std::fabs(in.speed) < cfg::kArriveSpeed;
  };

  switch (phase_) {
    case MissionPhase::Idle:
      break;

    case MissionPhase::ToLoad: {
      const FollowResult r = follower_.follow(route_.toLoad, in.pose, in.speed, cfg::kMaxSpeedAuto);
      out.targetSpeed = r.targetSpeed;
      out.steer = r.steer;
      out.dump = DumpCommand::Lower;
      if (arrived(r)) setPhase(MissionPhase::WaitLoad);
      break;
    }

    case MissionPhase::WaitLoad:
      out.dump = DumpCommand::Lower;
      stable_ = in.weightKg >= cfg::kLoadTargetKg ? stable_ + dt : 0.0f;
      if (stable_ >= cfg::kLoadStableS) setPhase(MissionPhase::ToDump);
      break;

    case MissionPhase::ToDump: {
      const FollowResult r = follower_.follow(route_.toDump, in.pose, in.speed, cfg::kMaxSpeedAuto);
      out.targetSpeed = r.targetSpeed;
      out.steer = r.steer;
      out.dump = DumpCommand::Lower;
      if (arrived(r)) setPhase(MissionPhase::Dump);
      break;
    }

    case MissionPhase::Dump:
      out.dump = DumpCommand::Raise;
      stable_ = (in.bucketUp && in.weightKg < cfg::kEmptyKg) ? stable_ + dt : 0.0f;
      // Esvaziou (ou o tempo acabou com a caçamba em cima): recolhe.
      if (stable_ >= cfg::kEmptyStableS || (in.bucketUp && timer_ > cfg::kDumpTimeout)) setPhase(MissionPhase::Lower);
      break;

    case MissionPhase::Lower:
      out.dump = DumpCommand::Lower;
      if (in.bucketDown) {
        setPhase(MissionPhase::Reverse);
        reverseFrom_ = {in.pose.x, in.pose.y};
      }
      break;

    case MissionPhase::Reverse: {
      out.dump = DumpCommand::Lower;
      const float done = std::hypot(in.pose.x - reverseFrom_.x, in.pose.y - reverseFrom_.y);
      const float left = cfg::kReverseDistance - done;
      const float v = std::sqrt(2.0f * cfg::kStopDecel * (left > 0.05f ? left - 0.05f : 0.0f));
      out.targetSpeed = -(v < cfg::kReverseSpeed ? v : cfg::kReverseSpeed);
      if (left < 0.1f && std::fabs(in.speed) < cfg::kArriveSpeed) setPhase(MissionPhase::ToLoad);
      break;
    }
  }
  return out;
}

}  // namespace axle
