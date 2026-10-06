// Tração, direção, rota, localização GPS RTK, leitor UBX e protocolo do console.
#include <unity.h>

#include <cmath>
#include <cstring>
#include <string>
#include <vector>

#include "axle/config.h"
#include "axle/drive.h"
#include "axle/localizer.h"
#include "axle/protocol.h"
#include "axle/route.h"
#include "axle/ubx.h"

using namespace axle;

#define ASSERT_ENUM(expected, actual) TEST_ASSERT_EQUAL_INT(static_cast<int>(expected), static_cast<int>(actual))

namespace {
constexpr float kPi = 3.14159265f;
constexpr double kLat0 = -23.5505, kLon0 = -46.6333;
}  // namespace

void setUp() {}
void tearDown() {}

// ---------------------------------------------------------------- rampa, PI, direção, odometria

void test_ramp_limits_acceleration_and_brakes_harder_in_emergency() {
  SpeedRamp r;
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, cfg::kAccel * 0.1f, r.step(2.0f, 0.1f, false));
  r.reset(2.0f);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, 2.0f - cfg::kDecel * 0.1f, r.step(0.0f, 0.1f, false));
  r.reset(2.0f);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, 2.0f - cfg::kEmergencyDecel * 0.1f, r.step(0.0f, 0.1f, true));
}

void test_ramp_reaches_target_exactly() {
  SpeedRamp r;
  for (int i = 0; i < 200; ++i) r.step(1.0f, 0.02f, false);
  TEST_ASSERT_EQUAL_FLOAT(1.0f, r.value());
}

void test_pi_releases_motor_at_standstill() {
  SpeedController pi;
  TEST_ASSERT_EQUAL_FLOAT(0.0f, pi.update(0.0f, 0.0f, 0.02f));
}

void test_pi_output_is_saturated() {
  SpeedController pi;
  for (int i = 0; i < 500; ++i) {
    const float duty = pi.update(50.0f, 0.0f, 0.02f);
    TEST_ASSERT_TRUE(duty <= 1.0f && duty >= -1.0f);
  }
}

void test_pi_integrates_persistent_error() {
  SpeedController pi;
  const float first = pi.update(1.0f, 0.5f, 0.02f);
  float last = first;
  for (int i = 0; i < 50; ++i) last = pi.update(1.0f, 0.5f, 0.02f);
  TEST_ASSERT_TRUE(last > first);
}

void test_steering_is_rate_limited_and_narrows_with_speed() {
  SteeringLimiter s;
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, cfg::kSteerRate * 0.1f, s.step(cfg::kMaxSteer, 0.0f, 0.1f));
  for (int i = 0; i < 100; ++i) s.step(cfg::kMaxSteer, cfg::kMaxSpeedManual, 0.1f);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, cfg::kMaxSteer / (1.0f + cfg::kMaxSpeedManual * cfg::kSteerSpeedFactor), s.value());
}

void test_bicycle_model_closes_a_circle() {
  const float radius = 5.0f;
  const float steer = std::atan(cfg::kWheelbase / radius);
  Pose p;
  const int steps = 3142;  // 2·pi·5 m em passos de 1 cm
  for (int i = 0; i < steps; ++i) p = integrateBicycle(p, 2.0f * kPi * radius / steps, steer);
  TEST_ASSERT_FLOAT_WITHIN(0.02f, 0.0f, p.x);
  TEST_ASSERT_FLOAT_WITHIN(0.02f, 0.0f, p.y);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, p.heading);
}

void test_bicycle_model_does_not_modify_input() {
  const Pose p{1.0f, 2.0f, 0.5f};
  integrateBicycle(p, 3.0f, 0.2f);
  TEST_ASSERT_EQUAL_FLOAT(1.0f, p.x);
  TEST_ASSERT_EQUAL_FLOAT(0.5f, p.heading);
}

// ---------------------------------------------------------------- rota

void test_site_route_lengths() {
  SiteRoute r;
  buildSiteRoute(r);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 20.0f, r.toDump.length());
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 8.0f * kPi + 23.0f, r.toLoad.length());
  TEST_ASSERT_TRUE(r.toLoad.size() < Path::kMaxPoints);
}

void test_path_reports_overflow() {
  Path p;
  TEST_ASSERT_FALSE(p.addLine({0.0f, 0.0f}, {200.0f, 0.0f}));
  TEST_ASSERT_EQUAL_UINT32(Path::kMaxPoints, p.size());
}

void test_follower_goes_straight_on_a_straight_path() {
  Path p;
  p.addLine({0.0f, 0.0f}, {20.0f, 0.0f});
  PathFollower f;
  const FollowResult r = f.follow(p, {0.0f, 0.0f, 0.0f}, 0.0f, cfg::kMaxSpeedAuto);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 0.0f, r.steer);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 20.0f, r.distanceToEnd);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, cfg::kMaxSpeedAuto, r.targetSpeed);
}

void test_follower_steers_back_to_the_path() {
  Path p;
  p.addLine({0.0f, 0.0f}, {20.0f, 0.0f});
  PathFollower f;
  TEST_ASSERT_TRUE(f.follow(p, {5.0f, 1.0f, 0.0f}, 1.0f, cfg::kMaxSpeedAuto).steer < -0.05f);  // à esquerda: vira à direita
  PathFollower g;
  TEST_ASSERT_TRUE(g.follow(p, {5.0f, -1.0f, 0.0f}, 1.0f, cfg::kMaxSpeedAuto).steer > 0.05f);
}

void test_follower_slows_to_a_stop_at_the_end() {
  Path p;
  p.addLine({0.0f, 0.0f}, {20.0f, 0.0f});
  PathFollower f;
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 0.0f, f.follow(p, {19.97f, 0.0f, 0.0f}, 0.0f, cfg::kMaxSpeedAuto).targetSpeed);
  PathFollower g;
  TEST_ASSERT_TRUE(g.follow(p, {18.0f, 0.0f, 0.0f}, 1.0f, cfg::kMaxSpeedAuto).targetSpeed < cfg::kMaxSpeedAuto);
}

// ---------------------------------------------------------------- localização

GnssSample fixAt(const Localizer& geo, float x, float y, GnssFix fix = GnssFix::RtkFixed) {
  GnssSample g;
  geo.toGeo({x, y}, g.latDeg, g.lonDeg);
  g.fix = fix;
  g.horizontalAccuracy = 0.02f;
  return g;
}

void test_local_and_geo_conversions_round_trip() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  double lat = 0.0, lon = 0.0;
  l.toGeo({120.5f, -80.25f}, lat, lon);
  const Vec2 back = l.toLocal(lat, lon);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 120.5f, back.x);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, -80.25f, back.y);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.113f, l.toLocal(kLat0 + 1e-5, kLon0).y);  // 1e-5 grau de latitude ≈ 1,11 m
}

void test_first_rtk_fix_sets_position() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  TEST_ASSERT_FALSE(l.rtkOk());
  l.correct(fixAt(l, 30.0f, -12.0f));
  TEST_ASSERT_TRUE(l.rtkOk());
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 30.0f, l.pose().x);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, -12.0f, l.pose().y);
}

void test_non_rtk_fixes_are_ignored() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  l.correct(fixAt(l, 30.0f, -12.0f, GnssFix::Single));
  l.correct(fixAt(l, 30.0f, -12.0f, GnssFix::RtkFloat));
  GnssSample imprecise = fixAt(l, 30.0f, -12.0f);
  imprecise.horizontalAccuracy = 0.5f;
  l.correct(imprecise);
  TEST_ASSERT_FALSE(l.rtkOk());
  TEST_ASSERT_EQUAL_FLOAT(0.0f, l.pose().x);
}

void test_rtk_expires_without_new_fixes() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  l.correct(fixAt(l, 0.0f, 0.0f));
  l.tick(1.9f);
  TEST_ASSERT_TRUE(l.rtkOk());
  l.tick(0.2f);
  TEST_ASSERT_FALSE(l.rtkOk());
}

void test_gps_corrects_heading_drift_on_straights() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  l.reset({0.0f, 0.0f, 0.3f});  // odometria acha que aponta 17° para a esquerda; na verdade vai para leste
  float truthX = 0.0f;
  for (int i = 0; i < 800; ++i) {  // 40 m a 5 cm por ciclo, GPS a cada 10 cm
    truthX += 0.05f;
    l.predict(0.05f, 0.0f);
    if (i % 2 == 1) l.correct(fixAt(l, truthX, 0.0f));
  }
  TEST_ASSERT_FLOAT_WITHIN(0.03f, 0.0f, l.pose().heading);
  TEST_ASSERT_FLOAT_WITHIN(0.10f, truthX, l.pose().x);
  TEST_ASSERT_FLOAT_WITHIN(0.10f, 0.0f, l.pose().y);
}

void test_gps_heading_works_in_reverse() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  l.reset({0.0f, 0.0f, 0.2f});  // aponta para leste (com erro), andando de ré para oeste
  float truthX = 0.0f;
  for (int i = 0; i < 800; ++i) {
    truthX -= 0.05f;
    l.predict(-0.05f, 0.0f);
    if (i % 2 == 1) l.correct(fixAt(l, truthX, 0.0f));
  }
  TEST_ASSERT_FLOAT_WITHIN(0.03f, 0.0f, l.pose().heading);
}

void test_gps_fixes_a_heading_180_degrees_wrong() {
  Localizer l;
  l.setOrigin(kLat0, kLon0);
  l.reset({0.0f, 0.0f, kPi});  // operador informou oeste; o carrinho anda para leste, de frente
  float truthX = 0.0f;
  for (int i = 0; i < 1200; ++i) {
    truthX += 0.05f;
    l.predict(0.05f, 0.0f);
    if (i % 2 == 1) l.correct(fixAt(l, truthX, 0.0f));
  }
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 0.0f, l.pose().heading);
  TEST_ASSERT_TRUE(l.headingKnown());
}

void test_heading_is_unknown_until_declared_or_confirmed() {
  Localizer l;
  TEST_ASSERT_FALSE(l.originSet());
  l.setOrigin(kLat0, kLon0);
  TEST_ASSERT_TRUE(l.originSet());
  TEST_ASSERT_FALSE(l.headingKnown());
  float truthX = 0.0f;
  for (int i = 0; i < 400; ++i) {  // 20 m para leste; a odometria começou achando rumo 0, que está certo
    truthX += 0.05f;
    l.predict(0.05f, 0.0f);
    if (i % 2 == 1) l.correct(fixAt(l, truthX, 0.0f));
  }
  TEST_ASSERT_TRUE(l.headingKnown());
}

// ---------------------------------------------------------------- UBX NAV-PVT

void put32(std::vector<uint8_t>& v, std::size_t at, uint32_t x) {
  for (int i = 0; i < 4; ++i) v[at + i] = static_cast<uint8_t>(x >> (8 * i));
}

std::vector<uint8_t> navPvt(int32_t latE7, int32_t lonE7, uint8_t fixType, uint8_t flags, uint32_t hAccMm) {
  std::vector<uint8_t> payload(92, 0);
  payload[20] = fixType;
  payload[21] = flags;
  payload[23] = 21;  // satélites
  put32(payload, 24, static_cast<uint32_t>(lonE7));
  put32(payload, 28, static_cast<uint32_t>(latE7));
  put32(payload, 40, hAccMm);
  std::vector<uint8_t> f{0xB5, 0x62, 0x01, 0x07, 92, 0};
  f.insert(f.end(), payload.begin(), payload.end());
  uint8_t a = 0, b = 0;
  for (std::size_t i = 2; i < f.size(); ++i) { a += f[i]; b += a; }
  f.push_back(a);
  f.push_back(b);
  return f;
}

bool feedAll(UbxParser& p, const std::vector<uint8_t>& bytes) {
  bool got = false;
  for (uint8_t b : bytes) got |= p.feed(b);
  return got;
}

void test_ubx_parses_rtk_fixed_nav_pvt() {
  UbxParser p;
  std::vector<uint8_t> stream{0x00, 0xB5, 0x13};  // lixo antes do quadro
  const auto frame = navPvt(-235505000, -466333000, 3, 0x81, 14);
  stream.insert(stream.end(), frame.begin(), frame.end());
  TEST_ASSERT_TRUE(feedAll(p, stream));
  TEST_ASSERT_DOUBLE_WITHIN(1e-7, -23.5505, p.sample().latDeg);
  TEST_ASSERT_DOUBLE_WITHIN(1e-7, -46.6333, p.sample().lonDeg);
  ASSERT_ENUM(GnssFix::RtkFixed, p.sample().fix);
  TEST_ASSERT_FLOAT_WITHIN(1e-6f, 0.014f, p.sample().horizontalAccuracy);
  TEST_ASSERT_EQUAL_UINT8(21, p.satellites());
}

void test_ubx_maps_fix_quality() {
  UbxParser p;
  feedAll(p, navPvt(0, 0, 3, 0x41, 300));
  ASSERT_ENUM(GnssFix::RtkFloat, p.sample().fix);
  feedAll(p, navPvt(0, 0, 3, 0x01, 1500));
  ASSERT_ENUM(GnssFix::Single, p.sample().fix);
  feedAll(p, navPvt(0, 0, 3, 0x80, 1500));  // sem gnssFixOK
  ASSERT_ENUM(GnssFix::None, p.sample().fix);
}

void test_ubx_rejects_bad_checksum() {
  UbxParser p;
  auto frame = navPvt(1, 1, 3, 0x81, 10);
  frame[30] ^= 0xFF;
  TEST_ASSERT_FALSE(feedAll(p, frame));
  TEST_ASSERT_TRUE(feedAll(p, navPvt(1, 1, 3, 0x81, 10)));  // e se recupera no quadro seguinte
}

void test_ubx_skips_other_messages() {
  UbxParser p;
  std::vector<uint8_t> other{0xB5, 0x62, 0x01, 0x35, 4, 0, 1, 2, 3, 4};  // NAV-SAT curto
  uint8_t a = 0, b = 0;
  for (std::size_t i = 2; i < other.size(); ++i) { a += other[i]; b += a; }
  other.push_back(a);
  other.push_back(b);
  TEST_ASSERT_FALSE(feedAll(p, other));
}

void test_ubx_resyncs_after_absurd_length() {
  UbxParser p;
  const std::vector<uint8_t> garbage{0xB5, 0x62, 0x01, 0x07, 0xFF, 0xFF};  // diz ter 65535 bytes
  feedAll(p, garbage);
  TEST_ASSERT_TRUE(feedAll(p, navPvt(1, 1, 3, 0x81, 10)));  // o quadro seguinte é lido normalmente
}

// ---------------------------------------------------------------- console

void test_parse_simple_commands_ignoring_case_and_spaces() {
  ASSERT_ENUM(CommandType::Auto, parseCommand("  AUTO \r").type);
  ASSERT_ENUM(CommandType::Manual, parseCommand("parar").type);
  ASSERT_ENUM(CommandType::Empty, parseCommand("   ").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("auto agora").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("voar").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand(nullptr).type);
}

void test_parse_numeric_arguments_with_ranges() {
  const Command c = parseCommand("calibrar 50");
  ASSERT_ENUM(CommandType::Calibrate, c.type);
  TEST_ASSERT_EQUAL_DOUBLE(50.0, c.a);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("calibrar -1").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("calibrar 5kg").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("calibrar nan").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("origem 91 0").type);
  const Command o = parseCommand("origem -23.5505 -46.6333");
  ASSERT_ENUM(CommandType::Origin, o.type);
  TEST_ASSERT_EQUAL_DOUBLE(-46.6333, o.b);
  ASSERT_ENUM(CommandType::SetPose, parseCommand("pose 2 -6 -90").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("pose 2 -6").type);
}

void test_parse_drive_command() {
  const Command d = parseCommand("dirigir 0.5 -0.2 sobe");
  ASSERT_ENUM(CommandType::Drive, d.type);
  TEST_ASSERT_EQUAL_DOUBLE(0.5, d.a);
  TEST_ASSERT_EQUAL_DOUBLE(-0.2, d.b);
  ASSERT_ENUM(DumpCommand::Raise, d.dump);
  ASSERT_ENUM(DumpCommand::Hold, parseCommand("dirigir 0 0").dump);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("dirigir 2 0").type);
  ASSERT_ENUM(CommandType::Invalid, parseCommand("dirigir 0.5 0 voa").type);
}

void test_parse_rejects_overlong_lines() {
  const std::string longLine = "calibrar " + std::string(200, '1');
  ASSERT_ENUM(CommandType::Invalid, parseCommand(longLine.c_str()).type);
}

void test_telemetry_is_one_json_line() {
  Telemetry t;
  t.weightKg = 172.4f;
  t.fault = Fault::EmergencyStop;
  char buf[512];
  const std::size_t n = formatTelemetry(t, buf, sizeof buf);
  TEST_ASSERT_TRUE(n > 0);
  TEST_ASSERT_EQUAL_CHAR('{', buf[0]);
  TEST_ASSERT_EQUAL_CHAR('}', buf[n - 1]);
  TEST_ASSERT_NOT_NULL(std::strstr(buf, "\"modo\":\"manual\""));
  TEST_ASSERT_NOT_NULL(std::strstr(buf, "\"peso\":172.4"));
  TEST_ASSERT_NOT_NULL(std::strstr(buf, "\"falha\":\"emergencia\""));
  TEST_ASSERT_NULL(std::strchr(buf, '\n'));
  char tiny[16];
  TEST_ASSERT_EQUAL_UINT32(0, formatTelemetry(t, tiny, sizeof tiny));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_ramp_limits_acceleration_and_brakes_harder_in_emergency);
  RUN_TEST(test_ramp_reaches_target_exactly);
  RUN_TEST(test_pi_releases_motor_at_standstill);
  RUN_TEST(test_pi_output_is_saturated);
  RUN_TEST(test_pi_integrates_persistent_error);
  RUN_TEST(test_steering_is_rate_limited_and_narrows_with_speed);
  RUN_TEST(test_bicycle_model_closes_a_circle);
  RUN_TEST(test_bicycle_model_does_not_modify_input);
  RUN_TEST(test_site_route_lengths);
  RUN_TEST(test_path_reports_overflow);
  RUN_TEST(test_follower_goes_straight_on_a_straight_path);
  RUN_TEST(test_follower_steers_back_to_the_path);
  RUN_TEST(test_follower_slows_to_a_stop_at_the_end);
  RUN_TEST(test_local_and_geo_conversions_round_trip);
  RUN_TEST(test_first_rtk_fix_sets_position);
  RUN_TEST(test_non_rtk_fixes_are_ignored);
  RUN_TEST(test_rtk_expires_without_new_fixes);
  RUN_TEST(test_gps_corrects_heading_drift_on_straights);
  RUN_TEST(test_gps_heading_works_in_reverse);
  RUN_TEST(test_gps_fixes_a_heading_180_degrees_wrong);
  RUN_TEST(test_heading_is_unknown_until_declared_or_confirmed);
  RUN_TEST(test_ubx_parses_rtk_fixed_nav_pvt);
  RUN_TEST(test_ubx_maps_fix_quality);
  RUN_TEST(test_ubx_rejects_bad_checksum);
  RUN_TEST(test_ubx_skips_other_messages);
  RUN_TEST(test_ubx_resyncs_after_absurd_length);
  RUN_TEST(test_parse_simple_commands_ignoring_case_and_spaces);
  RUN_TEST(test_parse_numeric_arguments_with_ranges);
  RUN_TEST(test_parse_drive_command);
  RUN_TEST(test_parse_rejects_overlong_lines);
  RUN_TEST(test_telemetry_is_one_json_line);
  return UNITY_END();
}
