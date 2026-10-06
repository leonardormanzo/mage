// Testes de integração: supervisor completo em malha fechada com o modelo físico (test/support/plant.h).
#include <unity.h>

#include <cmath>
#include <cstdio>

#include "../support/plant.h"
#include "axle/controller.h"

using namespace axle;
using sim::Rig;

#define ASSERT_ENUM(expected, actual) TEST_ASSERT_EQUAL_INT(static_cast<int>(expected), static_cast<int>(actual))

namespace {
// Repete o comando manual a cada 0,1 s (como o controle remoto faria) durante `seconds`.
void holdManual(Rig& rig, float seconds, float throttle, float steer, DumpCommand dump = DumpCommand::Hold) {
  const int steps = static_cast<int>(seconds / sim::kDt);
  for (int i = 0; i < steps; ++i) {
    if (i % 5 == 0) rig.plant.sendManual(throttle, steer, dump);
    rig.step();
  }
}

bool phaseIs(Rig& rig, MissionPhase p) { return rig.ctl.telemetry().phase == p; }
}  // namespace

void setUp() {}
void tearDown() {}

void test_autonomous_cycle_delivers_loads_repeatedly() {
  Rig rig;
  rig.run(1.0f);  // chega o primeiro fixo RTK
  ASSERT_ENUM(AutoStartResult::Started, rig.ctl.requestAuto());

  int deliveries = 0;
  float worstDocking = 0.0f;
  MissionPhase prev = rig.ctl.telemetry().phase;
  for (int i = 0; i < static_cast<int>(420.0f / sim::kDt); ++i) {
    rig.step();
    const MissionPhase now = rig.ctl.telemetry().phase;
    if (prev == MissionPhase::Dump && now == MissionPhase::Lower) ++deliveries;
    if (prev == MissionPhase::ToLoad && now == MissionPhase::WaitLoad) {
      const float err = std::hypot(rig.plant.pose.x - sim::kLoadSpot.x, rig.plant.pose.y - sim::kLoadSpot.y);
      worstDocking = std::fmax(worstDocking, err);
    }
    // Invariante de segurança: nunca anda com a caçamba fora do fim de curso inferior.
    if (!rig.plant.bucketDown()) TEST_ASSERT_TRUE(std::fabs(rig.plant.speed) < 0.1f);
    prev = now;
  }
  std::printf("ciclo: %d descargas em 420 s, pior parada na baia a %.3f m\n", deliveries, worstDocking);
  ASSERT_ENUM(Fault::None, rig.ctl.fault());
  TEST_ASSERT_TRUE_MESSAGE(deliveries >= 3, "menos de 3 descargas em 7 minutos");
  TEST_ASSERT_TRUE_MESSAGE(worstDocking < 0.30f, "parou longe demais da baia de carga");
}

void test_brakes_for_obstacle_on_route_and_resumes_when_clear() {
  Rig rig;
  rig.plant.obstacles.push_back({2.0f, -12.0f, 0.3f});  // pessoa/material no meio da estrada
  rig.run(1.0f);
  rig.ctl.requestAuto();

  float closest = 1e9f;
  for (int i = 0; i < static_cast<int>(25.0f / sim::kDt); ++i) {
    rig.step();
    closest = std::fmin(closest, rig.plant.frontClearance());
  }
  std::printf("obstaculo: parou com o para-choque a %.2f m\n", closest);
  TEST_ASSERT_TRUE_MESSAGE(closest > 0.25f, "chegou perto demais do obstaculo");
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 0.0f, rig.plant.speed);
  ASSERT_ENUM(StatusLight::Brake, rig.out.light);
  ASSERT_ENUM(Buzzer::Fast, rig.out.buzzer);

  rig.plant.obstacles.clear();
  TEST_ASSERT_TRUE(rig.runUntil(60.0f, [&] { return phaseIs(rig, MissionPhase::WaitLoad); }));
}

void test_emergency_stop_cuts_drive_and_needs_release_to_reset() {
  Rig rig;
  rig.run(1.0f);
  rig.ctl.requestAuto();
  rig.run(5.0f);
  TEST_ASSERT_TRUE(rig.plant.speed > 0.5f);

  rig.plant.estop = true;
  const ActuatorOutputs& out = rig.step();
  TEST_ASSERT_FALSE(out.motorEnable);
  TEST_ASSERT_TRUE(out.parkingBrake);
  ASSERT_ENUM(Fault::EmergencyStop, rig.ctl.fault());
  ASSERT_ENUM(Mode::Manual, rig.ctl.mode());
  ASSERT_ENUM(StatusLight::Fault, out.light);
  TEST_ASSERT_FALSE(rig.ctl.resetFaults());

  rig.plant.estop = false;
  rig.step();
  ASSERT_ENUM(Fault::EmergencyStop, rig.ctl.fault());  // soltar o botão não basta: precisa do reset
  TEST_ASSERT_FALSE(rig.ctl.resetFaults());            // e ainda está rolando até parar
  rig.run(3.0f);
  TEST_ASSERT_TRUE(rig.ctl.resetFaults());
  ASSERT_ENUM(Fault::None, rig.ctl.fault());
  ASSERT_ENUM(Mode::Manual, rig.ctl.mode());  // o autônomo não volta sozinho
}

void test_deadman_stops_manual_driving() {
  Rig rig;
  rig.run(1.0f);
  holdManual(rig, 3.0f, 0.5f, 0.0f);
  TEST_ASSERT_TRUE(rig.plant.speed > 1.0f);
  rig.run(4.0f);  // controle remoto parou de mandar comandos
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 0.0f, rig.plant.speed);
  TEST_ASSERT_TRUE(rig.out.parkingBrake);
}

void test_raised_bucket_blocks_driving() {
  Rig rig;
  rig.plant.bucket = 0.5f;
  rig.run(1.0f);
  holdManual(rig, 2.0f, 1.0f, 0.0f);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, rig.plant.speed);
}

void test_auto_start_preconditions() {
  Rig noGps;
  noGps.plant.gnssOn = false;
  noGps.run(1.0f);
  ASSERT_ENUM(AutoStartResult::NoRtk, noGps.ctl.requestAuto());

  Rig lowBattery;
  lowBattery.plant.battery = 10.0f;
  lowBattery.run(1.0f);
  ASSERT_ENUM(AutoStartResult::LowBattery, lowBattery.ctl.requestAuto());

  Rig estop;
  estop.plant.estop = true;
  estop.run(1.0f);
  ASSERT_ENUM(AutoStartResult::EstopActive, estop.ctl.requestAuto());

  Rig faulted;
  faulted.plant.estop = true;
  faulted.step();
  faulted.plant.estop = false;
  faulted.run(1.0f);
  ASSERT_ENUM(AutoStartResult::Faulted, faulted.ctl.requestAuto());
}

void test_rtk_loss_pauses_auto_and_resumes() {
  Rig rig;
  rig.run(1.0f);
  rig.ctl.requestAuto();
  rig.run(4.0f);
  rig.plant.gnssOn = false;
  rig.run(5.0f);
  TEST_ASSERT_TRUE(rig.ctl.telemetry().autoPaused);
  ASSERT_ENUM(Mode::Auto, rig.ctl.mode());
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 0.0f, rig.plant.speed);

  rig.plant.gnssOn = true;
  TEST_ASSERT_TRUE(rig.runUntil(60.0f, [&] { return phaseIs(rig, MissionPhase::WaitLoad); }));
}

void test_load_cell_failure_latches_fault() {
  Rig rig;
  rig.run(1.0f);
  rig.ctl.requestAuto();
  rig.run(3.0f);
  rig.plant.loadCellOn = false;
  rig.step();
  ASSERT_ENUM(Fault::WeightImplausible, rig.ctl.fault());
  ASSERT_ENUM(Mode::Manual, rig.ctl.mode());
  TEST_ASSERT_FALSE(rig.ctl.resetFaults());  // cabo ainda solto
  rig.plant.loadCellOn = true;
  rig.run(3.0f);  // parou pela rampa de emergência
  TEST_ASSERT_TRUE(rig.ctl.resetFaults());
}

void test_late_control_cycle_cuts_the_motor() {
  Rig rig;
  rig.run(1.0f);
  const SensorFrame late = rig.plant.frame(0.1f);  // 100 ms num laço de 20 ms
  const ActuatorOutputs out = rig.ctl.step(late);
  ASSERT_ENUM(Fault::ControlOverrun, rig.ctl.fault());
  TEST_ASSERT_FALSE(out.motorEnable);
}

void test_stuck_bucket_trips_dump_timeout() {
  Rig rig;
  rig.plant.bucketStuck = true;
  rig.run(1.0f);
  holdManual(rig, axle::cfg::kDumpTimeout + 1.0f, 0.0f, 0.0f, DumpCommand::Raise);
  ASSERT_ENUM(Fault::DumpTimeout, rig.ctl.fault());
  TEST_ASSERT_EQUAL_INT8(0, rig.out.bucket);
}

void test_status_light_priority() {
  Rig rig;
  rig.plant.obstacles.push_back({2.0f, -8.0f, 0.3f});  // 0,4 m à frente do para-choque
  rig.run(1.0f);
  ASSERT_ENUM(StatusLight::Alert, rig.out.light);  // parado, ninguém pedindo para andar: só alerta
  holdManual(rig, 0.5f, 0.5f, 0.0f);
  ASSERT_ENUM(StatusLight::Brake, rig.out.light);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, rig.plant.speed);
  rig.plant.estop = true;
  rig.step();
  ASSERT_ENUM(StatusLight::Fault, rig.out.light);
}

void test_reverse_sounds_the_backup_alarm() {
  Rig rig;
  rig.run(1.0f);
  holdManual(rig, 1.0f, -0.4f, 0.0f);
  TEST_ASSERT_TRUE(rig.plant.speed < -0.2f);
  ASSERT_ENUM(Buzzer::Slow, rig.out.buzzer);
}

void test_auto_needs_origin_and_a_confirmed_heading() {
  Rig noOrigin(Rig::Setup::NoOrigin);
  noOrigin.run(1.0f);
  ASSERT_ENUM(AutoStartResult::NoOrigin, noOrigin.ctl.requestAuto());

  // Origem sim, rumo não: o carrinho aponta para o sul e a odometria acha que aponta para leste.
  Rig rig(Rig::Setup::OriginOnly);
  rig.run(1.0f);
  ASSERT_ENUM(AutoStartResult::NoHeading, rig.ctl.requestAuto());
  holdManual(rig, 6.0f, 0.4f, 0.0f);  // ~10 m em linha reta: o GPS confirma o rumo
  rig.run(3.0f);                     // homem-morto para o carrinho
  TEST_ASSERT_FLOAT_WITHIN(0.15f, -sim::kPi / 2.0f, rig.ctl.localizer().pose().heading);
  ASSERT_ENUM(AutoStartResult::Started, rig.ctl.requestAuto());
}

void test_auto_refused_off_route_or_moving() {
  Rig far;
  far.plant.pose = {30.0f, 30.0f, 0.0f};
  far.ctl.setPose(far.plant.pose);
  far.run(1.0f);
  ASSERT_ENUM(AutoStartResult::OffRoute, far.ctl.requestAuto());

  Rig moving;
  moving.run(1.0f);
  holdManual(moving, 2.0f, 0.5f, 0.0f);
  ASSERT_ENUM(AutoStartResult::Moving, moving.ctl.requestAuto());
}

void test_reconfiguration_is_refused_in_auto() {
  Rig rig;
  rig.run(1.0f);
  rig.ctl.requestAuto();
  rig.run(2.0f);
  TEST_ASSERT_FALSE(rig.ctl.tare());
  TEST_ASSERT_FALSE(rig.ctl.calibrateWeight(50.0f));
  TEST_ASSERT_FALSE(rig.ctl.setPose({0.0f, 0.0f, 0.0f}));
  TEST_ASSERT_FALSE(rig.ctl.setOrigin(0.0, 0.0));
  ASSERT_ENUM(Mode::Auto, rig.ctl.mode());
}

void test_reset_refused_with_active_throttle() {
  Rig rig;
  rig.plant.estop = true;
  rig.step();
  rig.plant.estop = false;
  rig.plant.sendManual(0.8f, 0.0f);  // operador ainda segurando o acelerador
  rig.step();
  TEST_ASSERT_FALSE(rig.ctl.resetFaults());
  rig.run(1.0f);                      // soltou
  TEST_ASSERT_TRUE(rig.ctl.resetFaults());
}

void test_dead_encoder_trips_drive_stalled() {
  Rig rig;
  rig.run(1.0f);
  rig.plant.encoderDead = true;
  holdManual(rig, 3.0f, 0.6f, 0.0f);
  ASSERT_ENUM(Fault::DriveStalled, rig.ctl.fault());
  TEST_ASSERT_FALSE(rig.out.motorEnable);
  TEST_ASSERT_TRUE(rig.out.parkingBrake);
}

void test_runaway_motor_trips_overspeed() {
  Rig rig;
  rig.run(1.0f);
  holdManual(rig, 2.0f, 0.5f, 0.0f);
  rig.plant.runaway = true;
  holdManual(rig, 3.0f, 0.5f, 0.0f);
  ASSERT_ENUM(Fault::Overspeed, rig.ctl.fault());
  TEST_ASSERT_FALSE(rig.out.motorEnable);
}

void test_both_limit_switches_closed_is_a_fault() {
  Rig rig;
  rig.plant.limitShort = true;
  rig.step();
  ASSERT_ENUM(Fault::LimitSwitch, rig.ctl.fault());
  rig.run(1.0f);
  TEST_ASSERT_FALSE(rig.ctl.resetFaults());  // curto continua
  rig.plant.limitShort = false;
  rig.step();
  TEST_ASSERT_TRUE(rig.ctl.resetFaults());
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_autonomous_cycle_delivers_loads_repeatedly);
  RUN_TEST(test_brakes_for_obstacle_on_route_and_resumes_when_clear);
  RUN_TEST(test_emergency_stop_cuts_drive_and_needs_release_to_reset);
  RUN_TEST(test_deadman_stops_manual_driving);
  RUN_TEST(test_raised_bucket_blocks_driving);
  RUN_TEST(test_auto_start_preconditions);
  RUN_TEST(test_rtk_loss_pauses_auto_and_resumes);
  RUN_TEST(test_load_cell_failure_latches_fault);
  RUN_TEST(test_late_control_cycle_cuts_the_motor);
  RUN_TEST(test_stuck_bucket_trips_dump_timeout);
  RUN_TEST(test_status_light_priority);
  RUN_TEST(test_reverse_sounds_the_backup_alarm);
  RUN_TEST(test_auto_needs_origin_and_a_confirmed_heading);
  RUN_TEST(test_auto_refused_off_route_or_moving);
  RUN_TEST(test_reconfiguration_is_refused_in_auto);
  RUN_TEST(test_reset_refused_with_active_throttle);
  RUN_TEST(test_dead_encoder_trips_drive_stalled);
  RUN_TEST(test_runaway_motor_trips_overspeed);
  RUN_TEST(test_both_limit_switches_closed_is_a_fault);
  return UNITY_END();
}
