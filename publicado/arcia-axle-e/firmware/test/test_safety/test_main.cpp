// Guarda de colisão, sensor de peso e intertravamentos da caçamba.
#include <unity.h>

#include <cmath>

#include "axle/collision_guard.h"
#include "axle/config.h"
#include "axle/dump_controller.h"
#include "axle/sensor_layout.h"
#include "axle/weight_sensor.h"

using namespace axle;

#define ASSERT_STATE(expected, actual) TEST_ASSERT_EQUAL_INT(static_cast<int>(expected), static_cast<int>(actual))

namespace {
constexpr float kFar = 1e8f;
constexpr float kDt = 0.02f;

std::array<RangeReading, kRangeSensorCount> clearReadings() {
  std::array<RangeReading, kRangeSensorCount> r{};
  for (auto& x : r) x = {cfg::kRangeMax, 20.0f};
  return r;
}

GuardResult guard(CollisionGuard& g, float speed, float steer, int8_t intent,
                  const std::array<RangeReading, kRangeSensorCount>& r) {
  return g.update(speed, steer, intent, kRangeMounts.data(), r.data(), kRangeSensorCount, cfg::kRangeMax);
}
}  // namespace

void setUp() {}
void tearDown() {}

// ---------------------------------------------------------------- corredor de colisão

void test_obstacle_straight_ahead_free_distance_excludes_bumper() {
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 5.0f - cfg::kFrontOffset - cfg::kObstacleRadius, freeDistanceTo(5.0f, 0.0f, 0.0f, 1));
}

void test_obstacle_beside_the_corridor_is_ignored() {
  TEST_ASSERT_TRUE(freeDistanceTo(5.0f, 2.0f, 0.0f, 1) > kFar);
}

void test_obstacle_on_the_arc_is_measured_along_the_arc() {
  // Curva à esquerda de raio 5: ponto do próprio arco a 0,6 rad do início -> 3 m de arco.
  const float r = 5.0f, theta = 0.6f;
  const float d = freeDistanceTo(r * std::sin(theta), r - r * std::cos(theta), 1.0f / r, 1);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, r * theta - cfg::kFrontOffset - cfg::kObstacleRadius, d);
}

void test_obstacle_straight_ahead_is_ignored_in_a_tight_turn() {
  TEST_ASSERT_TRUE(freeDistanceTo(6.0f, 0.0f, 0.3f, 1) > kFar);
}

void test_reverse_uses_rear_offset() {
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 5.0f - cfg::kRearOffset - cfg::kObstacleRadius, freeDistanceTo(-5.0f, 0.0f, 0.0f, -1));
}

// ---------------------------------------------------------------- guarda

void test_guard_brakes_inside_stop_distance() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kFrontCenter].meters = 1.0f;  // obstáculo 0,9 m à frente do para-choque
  const GuardResult res = guard(g, 2.0f, 0.0f, 1, r);
  ASSERT_STATE(SafetyState::Brake, res.state);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 0.9f, res.freeDistance);
}

void test_guard_warns_before_braking() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kFrontCenter].meters = 2.5f;
  ASSERT_STATE(SafetyState::Warn, guard(g, 2.0f, 0.0f, 1, r).state);
}

void test_guard_ok_when_clear() {
  CollisionGuard g;
  ASSERT_STATE(SafetyState::Ok, guard(g, 2.0f, 0.0f, 1, clearReadings()).state);
}

void test_guard_ignores_rear_sensors_when_going_forward() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kRearLeft].meters = 0.3f;
  ASSERT_STATE(SafetyState::Ok, guard(g, 1.0f, 0.0f, 1, r).state);
  ASSERT_STATE(SafetyState::Brake, guard(g, -1.0f, 0.0f, -1, r).state);
}

void test_stale_sensor_in_travel_direction_brakes_and_flags_fault() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kFrontRight].ageMs = cfg::kSensorStaleMs + 1.0f;
  const GuardResult res = guard(g, 1.0f, 0.0f, 1, r);
  ASSERT_STATE(SafetyState::Brake, res.state);
  TEST_ASSERT_TRUE(res.sensorFault);
}

void test_stale_sensor_behind_is_not_used_going_forward() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kRearRight].ageMs = 1e9f;
  ASSERT_STATE(SafetyState::Ok, guard(g, 1.0f, 0.0f, 1, r).state);
}

void test_brake_has_hysteresis() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kFrontCenter].meters = 0.6f;  // livre 0,5 m
  ASSERT_STATE(SafetyState::Brake, guard(g, 0.5f, 0.0f, 1, r).state);
  // Parada a 0,5 m/s = 0,71 m; livre 0,85 m está dentro da histerese: continua freando.
  r[kFrontCenter].meters = 0.95f;
  ASSERT_STATE(SafetyState::Brake, guard(g, 0.5f, 0.0f, 1, r).state);
  // Sem a memória do freio, 0,85 m seria só alerta.
  CollisionGuard fresh;
  ASSERT_STATE(SafetyState::Warn, guard(fresh, 0.5f, 0.0f, 1, r).state);
}

void test_stopped_without_intent_only_warns() {
  CollisionGuard g;
  auto r = clearReadings();
  r[kFrontCenter].meters = 0.3f;
  ASSERT_STATE(SafetyState::Warn, guard(g, 0.0f, 0.0f, 0, r).state);
  ASSERT_STATE(SafetyState::Brake, guard(g, 0.0f, 0.0f, 1, r).state);
}

void test_stop_distance_includes_sensor_latency() {
  CollisionGuard g;
  const GuardResult res = guard(g, 2.0f, 0.0f, 1, clearReadings());
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 4.0f / (2.0f * cfg::kEmergencyDecel) + 2.0f * cfg::kSensorLatencyS + cfg::kMinStopDistance,
                           res.stopDistance);
}

void test_corrupted_speed_or_steer_brakes() {
  CollisionGuard g;
  const GuardResult nanSteer = guard(g, 1.0f, NAN, 1, clearReadings());
  ASSERT_STATE(SafetyState::Brake, nanSteer.state);
  TEST_ASSERT_TRUE(nanSteer.sensorFault);
  CollisionGuard h;
  ASSERT_STATE(SafetyState::Brake, guard(h, INFINITY, 0.0f, 1, clearReadings()).state);
}

// ---------------------------------------------------------------- peso

void test_weight_tare_and_calibration() {
  WeightSensor w;
  w.tare(1000);
  w.calibrate(1000 + 50000, 50.0f);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1000.0f, w.calibration().countsPerKg);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 100.0f, w.update(1000 + 100000, kDt));
}

void test_weight_is_low_pass_filtered() {
  WeightSensor w({0, 1000.0f});
  w.update(0, kDt);
  const float kg = w.update(100000, kDt);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 100.0f * kDt / (cfg::kWeightFilterTau + kDt), kg);
}

void test_negative_weight_clamps_to_zero() {
  WeightSensor w({0, 1000.0f});
  TEST_ASSERT_EQUAL_FLOAT(0.0f, w.update(-5000, kDt));
}

void test_implausible_weight_keeps_last_good_value() {
  WeightSensor w({0, 1000.0f});
  w.update(50000, kDt);
  const float kg = w.update(1000 * 1000, kDt);  // 1000 kg numa caçamba de 200
  TEST_ASSERT_TRUE(w.implausible());
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 50.0f, kg);
}

void test_calibration_rejects_bad_mass() {
  WeightSensor w({0, 1000.0f});
  TEST_ASSERT_FALSE(w.calibrate(5000, 0.0f));
  TEST_ASSERT_FALSE(w.calibrate(5000, -3.0f));
  TEST_ASSERT_FALSE(w.calibrate(5000, NAN));
  TEST_ASSERT_FALSE(w.calibrate(0, 50.0f));   // nada sobre a caçamba: célula solta
  TEST_ASSERT_FALSE(w.calibrate(200, 50.0f)); // 4 contagens/kg: implausível
  TEST_ASSERT_EQUAL_FLOAT(1000.0f, w.calibration().countsPerKg);
}

void test_corrupted_tare_does_not_overflow() {
  WeightSensor w({INT32_MIN, 1000.0f});
  w.update(INT32_MAX, kDt);
  TEST_ASSERT_TRUE(w.implausible());
}

// ---------------------------------------------------------------- caçamba

void test_dump_raises_only_when_stopped() {
  DumpController d;
  TEST_ASSERT_EQUAL_INT8(0, d.update({DumpCommand::Raise, false, true, 0.5f}, kDt));
  TEST_ASSERT_EQUAL_INT8(1, d.update({DumpCommand::Raise, false, true, 0.0f}, kDt));
}

void test_dump_stops_at_limit_switches() {
  DumpController d;
  TEST_ASSERT_EQUAL_INT8(0, d.update({DumpCommand::Raise, true, false, 0.0f}, kDt));
  TEST_ASSERT_EQUAL_INT8(0, d.update({DumpCommand::Lower, false, true, 0.0f}, kDt));
  TEST_ASSERT_EQUAL_INT8(-1, d.update({DumpCommand::Lower, false, false, 0.5f}, kDt));  // descer pode andando
}

void test_dump_timeout_latches_fault_until_cleared() {
  DumpController d;
  const DumpInputs stuck{DumpCommand::Raise, false, true, 0.0f};
  for (int i = 0; i < static_cast<int>(cfg::kDumpTimeout / kDt) + 2; ++i) d.update(stuck, kDt);
  TEST_ASSERT_TRUE(d.fault());
  TEST_ASSERT_EQUAL_INT8(0, d.update(stuck, kDt));
  d.clearFault();
  TEST_ASSERT_EQUAL_INT8(1, d.update(stuck, kDt));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_obstacle_straight_ahead_free_distance_excludes_bumper);
  RUN_TEST(test_obstacle_beside_the_corridor_is_ignored);
  RUN_TEST(test_obstacle_on_the_arc_is_measured_along_the_arc);
  RUN_TEST(test_obstacle_straight_ahead_is_ignored_in_a_tight_turn);
  RUN_TEST(test_reverse_uses_rear_offset);
  RUN_TEST(test_guard_brakes_inside_stop_distance);
  RUN_TEST(test_guard_warns_before_braking);
  RUN_TEST(test_guard_ok_when_clear);
  RUN_TEST(test_guard_ignores_rear_sensors_when_going_forward);
  RUN_TEST(test_stale_sensor_in_travel_direction_brakes_and_flags_fault);
  RUN_TEST(test_stale_sensor_behind_is_not_used_going_forward);
  RUN_TEST(test_brake_has_hysteresis);
  RUN_TEST(test_stopped_without_intent_only_warns);
  RUN_TEST(test_stop_distance_includes_sensor_latency);
  RUN_TEST(test_corrupted_speed_or_steer_brakes);
  RUN_TEST(test_corrupted_tare_does_not_overflow);
  RUN_TEST(test_weight_tare_and_calibration);
  RUN_TEST(test_weight_is_low_pass_filtered);
  RUN_TEST(test_negative_weight_clamps_to_zero);
  RUN_TEST(test_implausible_weight_keeps_last_good_value);
  RUN_TEST(test_calibration_rejects_bad_mass);
  RUN_TEST(test_dump_raises_only_when_stopped);
  RUN_TEST(test_dump_stops_at_limit_switches);
  RUN_TEST(test_dump_timeout_latches_fault_until_cleared);
  return UNITY_END();
}
