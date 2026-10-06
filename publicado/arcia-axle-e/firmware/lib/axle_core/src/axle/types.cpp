#include "axle/types.h"

namespace axle {

const char* toString(SafetyState s) {
  switch (s) {
    case SafetyState::Ok: return "OK";
    case SafetyState::Warn: return "ALERTA";
    case SafetyState::Brake: return "FREIO";
  }
  return "?";
}

const char* toString(StatusLight s) {
  switch (s) {
    case StatusLight::SysOk: return "SYS OK";
    case StatusLight::Auto: return "AUTO";
    case StatusLight::Alert: return "ALERTA";
    case StatusLight::Brake: return "FREIO";
    case StatusLight::Fault: return "FALHA";
  }
  return "?";
}

const char* toString(Fault f) {
  switch (f) {
    case Fault::None: return "nenhuma";
    case Fault::EmergencyStop: return "emergencia";
    case Fault::SensorStale: return "sensor_sem_leitura";
    case Fault::DumpTimeout: return "cacamba_timeout";
    case Fault::WeightImplausible: return "peso_implausivel";
    case Fault::ControlOverrun: return "controle_atrasado";
    case Fault::DriveStalled: return "tracao_sem_movimento";
    case Fault::Overspeed: return "sobrevelocidade";
    case Fault::LimitSwitch: return "fim_de_curso_incoerente";
  }
  return "?";
}

}  // namespace axle
