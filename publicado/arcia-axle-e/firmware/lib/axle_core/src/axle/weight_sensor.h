#pragma once
#include <cstdint>

// Sensor de peso da caçamba: 4 células de carga ligadas a um HX711.
// Converte a contagem bruta em kg (tara + escala), filtra com passa-baixa de 1ª ordem e marca
// leituras impossíveis (falha de cabo/célula) para o supervisor parar o ciclo.

namespace axle {

struct WeightCalibration {
  int32_t tareOffset = 0;      // contagem bruta com a caçamba vazia
  float countsPerKg = 1000.0f; // obtido pesando uma massa conhecida (ver README)
};

// O HX711 com 4 células de 50–100 kg dá milhares de contagens por kg; menos que isto é célula solta.
inline constexpr float kMinCountsPerKg = 10.0f;
bool isPlausibleScale(float countsPerKg);

class WeightSensor {
 public:
  explicit WeightSensor(WeightCalibration cal = {}) : cal_(cal) {}

  // raw: contagem do HX711 · dt: s desde a última amostra. Retorna o peso filtrado em kg.
  float update(int32_t raw, float dt);

  // Zera a tara com a leitura bruta atual (caçamba vazia, carrinho parado).
  void tare(int32_t raw) { cal_.tareOffset = raw; filtered_ = 0.0f; primed_ = false; }
  // Calibra a escala com uma massa conhecida sobre a caçamba. false = leitura não plausível, nada muda.
  bool calibrate(int32_t raw, float knownKg);

  float kg() const { return filtered_; }
  bool implausible() const { return implausible_; }
  const WeightCalibration& calibration() const { return cal_; }

 private:
  WeightCalibration cal_;
  float filtered_ = 0.0f;
  bool primed_ = false;
  bool implausible_ = false;
};

}  // namespace axle
