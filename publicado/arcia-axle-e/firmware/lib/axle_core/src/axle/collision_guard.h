#pragma once
#include <cstddef>
#include <cstdint>

#include "axle/types.h"

// Alerta de colisão + freio automático.
//
// Cada sensor de distância (ultrassom/ToF) tem posição e direção no referencial do veículo.
// Um eco vira um obstáculo pontual. O guarda calcula a distância livre AO LONGO do caminho que o
// carrinho vai percorrer — reta, ou arco em torno do centro instantâneo de rotação definido pelo
// esterço — e compara com a distância de parada. Mesmo algoritmo de js/safety.js.
//
// Falha segura: um sensor que aponta para onde o carrinho vai e está sem leitura recente conta como
// obstáculo encostado (freia).

namespace axle {

struct RangeSensorMount {
  float x = 0.0f;        // m, para frente a partir do centro do veículo
  float y = 0.0f;        // m, para a esquerda
  float bearing = 0.0f;  // rad, direção do feixe (0 = para frente, pi = para trás)
};

struct RangeReading {
  float meters = 0.0f;    // distância medida; >= maxRange quando não há eco
  float ageMs = 0.0f;     // idade da leitura
};

struct GuardResult {
  SafetyState state = SafetyState::Ok;
  float freeDistance = 1e9f;  // m livres ao longo do caminho (após o para-choque)
  int8_t direction = 1;       // +1 frente, -1 ré
  bool sensorFault = false;
  float stopDistance = 0.0f;
  float warnDistance = 0.0f;
};

// Distância livre ao longo do caminho até um obstáculo pontual em (px, py) do referencial do veículo.
// Retorna um valor muito grande se o obstáculo está fora do corredor ou atrás do sentido de marcha.
float freeDistanceTo(float px, float py, float curvature, int8_t direction);

class CollisionGuard {
 public:
  // speed: m/s (com sinal) · steer: rad · intent: -1/0/+1 sentido pedido pelo condutor/autopiloto
  GuardResult update(float speed, float steer, int8_t intent, const RangeSensorMount* mounts,
                     const RangeReading* readings, std::size_t count, float maxRange);

  void reset() { braking_ = false; lastDirection_ = 1; }

 private:
  bool braking_ = false;
  int8_t lastDirection_ = 1;
};

}  // namespace axle
