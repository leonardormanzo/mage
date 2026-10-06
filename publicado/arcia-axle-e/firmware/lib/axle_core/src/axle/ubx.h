#pragma once
#include <array>
#include <cstdint>

#include "axle/localizer.h"

// Leitor do protocolo binário UBX da u-blox, só a mensagem NAV-PVT (posição, tipo de fixo, precisão).
// Recebe byte a byte do UART, confere o checksum Fletcher-8 e descarta o resto.
// O ZED-F9P deve ser configurado (u-center, uma vez) para emitir NAV-PVT a 5–10 Hz no UART ligado ao ESP32
// e receber as correções RTCM da base pelo outro UART (rádio) ou por NTRIP.

namespace axle {

class UbxParser {
 public:
  // Retorna true quando uma NAV-PVT íntegra terminou de chegar; a amostra fica em sample().
  bool feed(uint8_t byte);
  const GnssSample& sample() const { return sample_; }
  uint8_t satellites() const { return satellites_; }

 private:
  enum class State : uint8_t { Sync1, Sync2, Class, Id, Len1, Len2, Payload, CkA, CkB };
  static constexpr uint16_t kNavPvtLength = 92;
  static constexpr uint16_t kMaxLength = 1024;  // maiores mensagens UBX de navegação ficam bem abaixo disto

  void restart() { state_ = State::Sync1; }
  void checksum(uint8_t b) { ckA_ += b; ckB_ += ckA_; }
  bool decodeNavPvt();

  State state_ = State::Sync1;
  uint8_t cls_ = 0, id_ = 0, ckA_ = 0, ckB_ = 0;
  uint16_t length_ = 0, index_ = 0;
  std::array<uint8_t, kNavPvtLength> payload_{};
  GnssSample sample_;
  uint8_t satellites_ = 0;
};

}  // namespace axle
