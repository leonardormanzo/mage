#pragma once
#include <cstdint>

// Tipos compartilhados do núcleo. Referencial do veículo: x para frente, y para a esquerda,
// ângulos em radianos (positivo = anti-horário / para a esquerda).

namespace axle {

struct Vec2 {
  float x = 0.0f;
  float y = 0.0f;
};

struct Pose {
  float x = 0.0f;
  float y = 0.0f;
  float heading = 0.0f;  // rad, 0 = eixo x do canteiro
};

enum class SafetyState : uint8_t { Ok, Warn, Brake };

// O que a barra de LED mostra (SYS OK / AUTO / ALERTA / FREIO / FALHA).
enum class StatusLight : uint8_t { SysOk, Auto, Alert, Brake, Fault };

enum class DumpCommand : int8_t { Lower = -1, Hold = 0, Raise = 1 };

enum class Mode : uint8_t { Manual, Auto };

enum class Fault : uint8_t {
  None = 0,
  EmergencyStop,     // botão de emergência acionado
  SensorStale,       // sensor de distância sem leitura recente
  DumpTimeout,       // atuador da caçamba não chegou ao fim de curso
  WeightImplausible, // célula de carga com leitura impossível
  ControlOverrun,    // laço de controle atrasou (watchdog de software)
  DriveStalled,      // motor com potência e encoder parado (encoder solto ou roda travada)
  Overspeed,         // acima da velocidade máxima (encoder ou controlador do motor com defeito)
  LimitSwitch,       // os dois fins de curso da caçamba fechados ao mesmo tempo (curto na fiação)
};

const char* toString(SafetyState s);
const char* toString(StatusLight s);
const char* toString(Fault f);

}  // namespace axle
