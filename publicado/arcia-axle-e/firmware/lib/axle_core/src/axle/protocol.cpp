#include "axle/protocol.h"

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "axle/config.h"

namespace axle {

namespace {
constexpr std::size_t kMaxLine = 96;
constexpr std::size_t kMaxTokens = 5;
constexpr double kRadToDeg = 57.29577951308232;
constexpr double kMaxPoseMeters = 10000.0;

struct Tokens {
  char buf[kMaxLine + 1];
  const char* tok[kMaxTokens];
  std::size_t count = 0;
};

// Copia a linha em minúsculas e separa por espaços. Linha comprida demais = inválida.
bool tokenize(const char* line, Tokens& t) {
  const std::size_t len = std::strlen(line);
  if (len > kMaxLine) return false;
  for (std::size_t i = 0; i <= len; ++i) t.buf[i] = static_cast<char>(std::tolower(static_cast<unsigned char>(line[i])));
  char* p = t.buf;
  while (*p) {
    while (*p && std::isspace(static_cast<unsigned char>(*p))) *p++ = '\0';
    if (!*p) break;
    if (t.count == kMaxTokens) return false;
    t.tok[t.count++] = p;
    while (*p && !std::isspace(static_cast<unsigned char>(*p))) ++p;
  }
  return true;
}

bool toNumber(const char* s, double lo, double hi, double& out) {
  char* end = nullptr;
  const double v = std::strtod(s, &end);
  if (end == s || *end != '\0' || !std::isfinite(v) || v < lo || v > hi) return false;
  out = v;
  return true;
}

bool is(const Tokens& t, const char* word) { return t.count > 0 && std::strcmp(t.tok[0], word) == 0; }

Command invalid() { Command c; c.type = CommandType::Invalid; return c; }

Command simple(const Tokens& t, CommandType type) {
  if (t.count != 1) return invalid();
  Command c;
  c.type = type;
  return c;
}

Command withNumbers(const Tokens& t, CommandType type, const double (*range)[2], std::size_t n) {
  if (t.count != n + 1) return invalid();
  Command c;
  c.type = type;
  double* dst[3] = {&c.a, &c.b, &c.c};
  for (std::size_t i = 0; i < n; ++i) {
    if (!toNumber(t.tok[i + 1], range[i][0], range[i][1], *dst[i])) return invalid();
  }
  return c;
}

Command drive(const Tokens& t) {
  if (t.count != 3 && t.count != 4) return invalid();
  static const double kRange[2][2] = {{-1.0, 1.0}, {-1.0, 1.0}};
  Tokens head = t;
  head.count = 3;
  Command c = withNumbers(head, CommandType::Drive, kRange, 2);
  if (c.type == CommandType::Invalid || t.count == 3) return c;
  const char* d = t.tok[3];
  if (std::strcmp(d, "sobe") == 0) c.dump = DumpCommand::Raise;
  else if (std::strcmp(d, "desce") == 0) c.dump = DumpCommand::Lower;
  else if (std::strcmp(d, "segura") != 0) return invalid();
  return c;
}
}  // namespace

const char* const kHelpText =
    "comandos: auto | manual | parar | reset | tara | calibrar <kg> | origem <lat> <lon> | "
    "pose <x> <y> <graus> | dirigir <acel> <dir> [sobe|desce|segura] | status | ajuda";

Command parseCommand(const char* line) {
  if (line == nullptr) return invalid();
  Tokens t;
  if (!tokenize(line, t)) return invalid();
  if (t.count == 0) return Command{};

  if (is(t, "auto")) return simple(t, CommandType::Auto);
  if (is(t, "manual") || is(t, "parar")) return simple(t, CommandType::Manual);
  if (is(t, "reset")) return simple(t, CommandType::Reset);
  if (is(t, "tara")) return simple(t, CommandType::Tare);
  if (is(t, "status")) return simple(t, CommandType::Status);
  if (is(t, "ajuda")) return simple(t, CommandType::Help);
  if (is(t, "calibrar")) {
    static const double kRange[1][2] = {{0.1, 2.0 * cfg::kCapacityKg}};
    return withNumbers(t, CommandType::Calibrate, kRange, 1);
  }
  if (is(t, "origem")) {
    static const double kRange[2][2] = {{-90.0, 90.0}, {-180.0, 180.0}};
    return withNumbers(t, CommandType::Origin, kRange, 2);
  }
  if (is(t, "pose")) {
    static const double kRange[3][2] = {{-kMaxPoseMeters, kMaxPoseMeters}, {-kMaxPoseMeters, kMaxPoseMeters}, {-360.0, 360.0}};
    return withNumbers(t, CommandType::SetPose, kRange, 3);
  }
  if (is(t, "dirigir")) return drive(t);
  return invalid();
}

const char* toString(Mode m) { return m == Mode::Auto ? "auto" : "manual"; }

std::size_t formatTelemetry(const Telemetry& t, char* out, std::size_t size) {
  const float freeDist = t.freeDistance > 99.9f ? 99.9f : t.freeDistance;
  const int n = std::snprintf(
      out, size,
      "{\"modo\":\"%s\",\"fase\":\"%s\",\"pausado\":%s,\"x\":%.2f,\"y\":%.2f,\"rumo\":%.1f,"
      "\"v\":%.2f,\"esterco\":%.1f,\"duty\":%.2f,\"peso\":%.1f,\"bateria\":%.0f,\"seguranca\":\"%s\","
      "\"livre\":%.2f,\"sensor_falha\":%s,\"falha\":\"%s\",\"rtk\":%s,\"luz\":\"%s\"}",
      toString(t.mode), toString(t.phase), t.autoPaused ? "true" : "false", t.pose.x, t.pose.y,
      t.pose.heading * kRadToDeg, t.speed, t.steer * kRadToDeg, t.motorDuty, t.weightKg, t.batteryPct,
      toString(t.safety), freeDist, t.sensorFault ? "true" : "false", toString(t.fault), t.rtkOk ? "true" : "false",
      toString(t.light));
  if (n < 0 || static_cast<std::size_t>(n) >= size) return 0;
  return static_cast<std::size_t>(n);
}

}  // namespace axle
