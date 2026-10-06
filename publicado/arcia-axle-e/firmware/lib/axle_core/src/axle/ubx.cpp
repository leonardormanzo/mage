#include "axle/ubx.h"

namespace axle {

namespace {
constexpr uint8_t kSync1 = 0xB5, kSync2 = 0x62;
constexpr uint8_t kClassNav = 0x01, kIdPvt = 0x07;

// Deslocamentos dentro do payload da NAV-PVT (u-blox F9 HPG, interface description).
constexpr uint16_t kOffFixType = 20, kOffFlags = 21, kOffNumSv = 23, kOffLon = 24, kOffLat = 28, kOffHAcc = 40;
constexpr uint8_t kFlagGnssFixOk = 0x01;
constexpr uint8_t kCarrSolnShift = 6;  // bits 6–7: 0 sem RTK, 1 float, 2 fixed
constexpr uint8_t kFix2D = 2;

uint32_t u32(const uint8_t* p) {
  return static_cast<uint32_t>(p[0]) | static_cast<uint32_t>(p[1]) << 8 | static_cast<uint32_t>(p[2]) << 16 |
         static_cast<uint32_t>(p[3]) << 24;
}
int32_t i32(const uint8_t* p) { return static_cast<int32_t>(u32(p)); }
}  // namespace

bool UbxParser::feed(uint8_t b) {
  switch (state_) {
    case State::Sync1:
      if (b == kSync1) state_ = State::Sync2;
      return false;
    case State::Sync2:
      state_ = b == kSync2 ? State::Class : (b == kSync1 ? State::Sync2 : State::Sync1);
      return false;
    case State::Class:
      ckA_ = ckB_ = 0;
      checksum(b);
      cls_ = b;
      state_ = State::Id;
      return false;
    case State::Id:
      checksum(b);
      id_ = b;
      state_ = State::Len1;
      return false;
    case State::Len1:
      checksum(b);
      length_ = b;
      state_ = State::Len2;
      return false;
    case State::Len2:
      checksum(b);
      length_ |= static_cast<uint16_t>(b) << 8;
      index_ = 0;
      // Comprimento corrompido faria o leitor engolir até 64 kB antes de ressincronizar.
      state_ = length_ > kMaxLength ? State::Sync1 : (length_ ? State::Payload : State::CkA);
      return false;
    case State::Payload:
      checksum(b);
      if (index_ < payload_.size()) payload_[index_] = b;  // outras mensagens: só consome
      if (++index_ >= length_) state_ = State::CkA;
      return false;
    case State::CkA:
      state_ = b == ckA_ ? State::CkB : State::Sync1;
      return false;
    case State::CkB:
      restart();
      if (b != ckB_) return false;
      return cls_ == kClassNav && id_ == kIdPvt && length_ == kNavPvtLength && decodeNavPvt();
  }
  restart();
  return false;
}

bool UbxParser::decodeNavPvt() {
  const uint8_t* p = payload_.data();
  const uint8_t flags = p[kOffFlags];
  const uint8_t carrier = (flags >> kCarrSolnShift) & 0x03;

  GnssSample s;
  s.lonDeg = i32(p + kOffLon) * 1e-7;
  s.latDeg = i32(p + kOffLat) * 1e-7;
  s.horizontalAccuracy = static_cast<float>(u32(p + kOffHAcc)) * 1e-3f;  // mm -> m
  if (!(flags & kFlagGnssFixOk) || p[kOffFixType] < kFix2D) {
    s.fix = GnssFix::None;
  } else if (carrier == 2) {
    s.fix = GnssFix::RtkFixed;
  } else if (carrier == 1) {
    s.fix = GnssFix::RtkFloat;
  } else {
    s.fix = GnssFix::Single;
  }
  sample_ = s;
  satellites_ = p[kOffNumSv];
  return true;
}

}  // namespace axle
