#include "axle/dump_controller.h"

#include <cmath>

#include "axle/config.h"

namespace axle {

int8_t DumpController::update(const DumpInputs& in, float dt) {
  if (fault_) return 0;

  int8_t out = 0;
  if (in.command == DumpCommand::Raise && !in.upperLimit && std::fabs(in.speed) < cfg::kDumpMaxSpeed) out = 1;
  if (in.command == DumpCommand::Lower && !in.lowerLimit) out = -1;

  // Cronômetro por movimento contínuo no mesmo sentido.
  runTime_ = (out != 0 && out == lastOutput_) ? runTime_ + dt : (out != 0 ? dt : 0.0f);
  lastOutput_ = out;
  if (runTime_ > cfg::kDumpTimeout) {
    fault_ = true;
    lastOutput_ = 0;
    return 0;
  }
  return out;
}

}  // namespace axle
