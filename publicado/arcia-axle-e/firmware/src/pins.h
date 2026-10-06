#pragma once
#include <cstdint>

// Mapa de pinos para ESP32-S3-DevKitC-1 (o ESP32 clássico não tem GPIO livres suficientes).
// Evitados: 0/3/46 (boot), 19/20 (USB), 35–37 (PSRAM octal), 43/44 (console serial), 48 (LED da placa v1.0).
// Livres para expansão: 12.
// Todos os sinais de 5 V (eco do ultrassom, fins de curso de 12/24 V via optoacoplador) entram por divisor
// ou opto — o ESP32-S3 NÃO tolera 5 V.

namespace pins {

// ---- sensores de distância (JSN-SR04T): um gatilho por grupo, um eco por sensor ----
// Os três da frente disparam juntos, os dois de trás juntos; a ordem dos ecos segue axle::kRangeMounts.
inline constexpr uint8_t kTrigFront = 4;
inline constexpr uint8_t kTrigRear = 5;
inline constexpr uint8_t kEcho[5] = {6, 7, 15, 16, 17};  // FE, FC, FD, TE, TD

// ---- célula de carga (HX711, 4 células em ponte) ----
inline constexpr uint8_t kHx711Data = 18;
inline constexpr uint8_t kHx711Clock = 8;

// ---- encoder de quadratura no eixo do motor de tração (PCNT) ----
inline constexpr uint8_t kEncoderA = 9;
inline constexpr uint8_t kEncoderB = 10;

// ---- controlador do motor de tração 72 V (classe VESC 75 V, entrada PPM em "duty com ré") ----
inline constexpr uint8_t kMotorPpm = 11;     // pulso de servo: 1500 µs parado, 1000 ré total, 2000 frente total
inline constexpr uint8_t kMotorEnable = 13;  // relé da ignição (KSI) do controlador; pull-down de 10 k na placa

// ---- direção: atuador com controle de posição por pulso de servo (1000–2000 µs) ----
inline constexpr uint8_t kSteerPwm = 14;

// ---- caçamba: dois relés da bomba/válvula + fins de curso (NA, fecham no fim do curso) ----
inline constexpr uint8_t kBucketUpRelay = 21;
inline constexpr uint8_t kBucketDownRelay = 47;
inline constexpr uint8_t kLimitUp = 39;
inline constexpr uint8_t kLimitDown = 40;

// ---- freio de estacionamento por mola: relé LIGADO = freio solto ----
inline constexpr uint8_t kBrakeRelease = 41;

// ---- emergência: laço NF; aberto (pino em nível alto pelo pull-up) = emergência acionada ----
inline constexpr uint8_t kEstopSense = 2;

// ---- bateria 72 V (20S Li-ion) por divisor 300 k / 10 k (ADC1) ----
inline constexpr uint8_t kBatteryAdc = 1;

// ---- interface ----
inline constexpr uint8_t kStatusLeds = 38;  // fita WS2812 (na placa v1.1 o LED da placa espelha o 1º LED)
inline constexpr uint8_t kBuzzer = 45;      // via transistor NPN; 45 é pino de boot: nada pode puxá-lo para cima

// ---- GPS RTK u-blox ZED-F9P: só recebemos NAV-PVT (TX do receptor -> RX do ESP32) ----
inline constexpr uint8_t kGnssRx = 42;
inline constexpr uint32_t kGnssBaud = 115200;

}  // namespace pins

// Constantes elétricas que dependem da montagem (ajuste na bancada).
namespace hw {
inline constexpr float kBatteryDivider = 31.0f;      // (300 k + 10 k) / 10 k: 84 V -> 2,7 V no ADC
inline constexpr float kBatteryEmptyV = 60.0f;       // 0 %   (3,0 V por célula)
inline constexpr float kBatteryFullV = 84.0f;        // 100 % (4,2 V por célula; aproximação linear)
inline constexpr float kEncoderCountsPerMeter = 1000.0f;  // contagens x4 por metro rodado (medir: ver README)
inline constexpr uint16_t kPulseCenterUs = 1500;     // neutro do PPM do motor e centro da direção
inline constexpr uint16_t kPulseSpanUs = 500;        // ±500 µs = curso total
inline constexpr uint8_t kStatusLedCount = 12;
}  // namespace hw
