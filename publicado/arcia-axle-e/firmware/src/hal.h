#pragma once
#include <array>
#include <cstdint>

#include "axle/controller.h"
#include "axle/ubx.h"

// Camada de hardware do ESP32-S3: tudo o que lê ou escreve pino fica aqui.
// O núcleo (lib/axle_core) não conhece nada disto.

namespace hal {

void begin();

// Estado seguro: ignição do controlador do motor desligada, freio de mola aplicado, relés da caçamba desligados.
// Pode ser chamado de qualquer núcleo (é o que o vigia do laço de controle usa).
void safeState();

// ---- sensores de distância ----
void fireRangeGroup(bool front);  // pulso de gatilho de 10 µs no grupo da frente ou de trás
void readRanges(std::array<axle::RangeReading, axle::kRangeSensorCount>& out, int64_t nowUs);

// ---- célula de carga ----
bool hx711Read(int32_t& raw);  // não bloqueia: false se o HX711 ainda não tem amostra

// ---- encoder ----
int32_t encoderTake();  // contagens desde a chamada anterior (com sinal)

// ---- entradas digitais/analógicas ----
bool limitUp();
bool limitDown();
bool estopPressed();
float batteryPercent();  // filtrado

// ---- saídas ----
void writeMotor(float duty, bool enable);
void writeBrake(bool applied);
void writeSteer(float rad);
void writeBucket(int8_t direction);
void writeStatus(axle::StatusLight light, axle::Buzzer buzzer, uint32_t nowMs);

// ---- GPS ----
bool gnssPoll(axle::UbxParser& parser);  // consome o UART; true se chegou NAV-PVT nova

}  // namespace hal
