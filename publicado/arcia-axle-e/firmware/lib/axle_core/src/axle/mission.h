#pragma once
#include "axle/route.h"
#include "axle/types.h"

// Ciclo autônomo: ir ao carregamento -> aguardar o sensor de peso -> levar ao bota-fora ->
// bascular até esvaziar -> recolher a caçamba -> ré -> repetir. Porte de js/autopilot.js.

namespace axle {

enum class MissionPhase : uint8_t { Idle, ToLoad, WaitLoad, ToDump, Dump, Lower, Reverse };
const char* toString(MissionPhase p);

struct MissionInputs {
  Pose pose;
  float speed = 0.0f;
  float weightKg = 0.0f;
  bool bucketDown = true;  // fim de curso inferior
  bool bucketUp = false;   // fim de curso superior
};

struct MissionOutputs {
  float targetSpeed = 0.0f;
  float steer = 0.0f;
  DumpCommand dump = DumpCommand::Hold;
};

class Mission {
 public:
  explicit Mission(const SiteRoute& route) : route_(route) {}

  void start(float weightKg);  // decide por onde começar pelo peso atual
  const Path& firstPath(float weightKg) const;  // o caminho que start() vai seguir
  void stop();
  bool active() const { return phase_ != MissionPhase::Idle; }
  MissionPhase phase() const { return phase_; }

  MissionOutputs step(const MissionInputs& in, float dt);

 private:
  void setPhase(MissionPhase p);

  const SiteRoute& route_;
  PathFollower follower_;
  MissionPhase phase_ = MissionPhase::Idle;
  float timer_ = 0.0f;
  float stable_ = 0.0f;
  Vec2 reverseFrom_;
};

}  // namespace axle
