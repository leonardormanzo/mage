#pragma once
#include <array>
#include <cstddef>

#include "axle/collision_guard.h"

// Onde ficam os sensores de distância (ultrassom à prova d'água, tipo JSN-SR04T).
// A ordem aqui é a mesma dos pinos de eco em src/pins.h.
//
// Três na frente (o do meio reto, os das pontas abertos ~20°) e dois atrás, na altura dos para-choques,
// abaixo da caçamba — ela bascula por cima sem cobri-los.

namespace axle {

enum RangeSensorIndex : std::size_t { kFrontLeft, kFrontCenter, kFrontRight, kRearLeft, kRearRight, kRangeSensorCount };

inline constexpr std::array<RangeSensorMount, kRangeSensorCount> kRangeMounts{{
    {1.30f, 0.70f, 0.35f},          // frente-esquerda
    {1.30f, 0.00f, 0.00f},          // frente-centro
    {1.30f, -0.70f, -0.35f},        // frente-direita
    {-2.10f, 0.60f, 3.14159265f},   // trás-esquerda
    {-2.10f, -0.60f, 3.14159265f},  // trás-direita
}};

}  // namespace axle
