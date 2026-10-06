#pragma once
#include <cstdint>

#include "axle/types.h"

// Controle do basculamento da caçamba (bomba hidráulica/atuador com dois fins de curso).
//
// Intertravamentos:
//  - só levanta com o carrinho parado (|v| < cfg::kDumpMaxSpeed);
//  - para no fim de curso de cima/baixo;
//  - se o atuador ficar ligado mais que cfg::kDumpTimeout sem chegar ao fim de curso, desliga e
//    sinaliza falha (cano rompido, atuador travado, fim de curso com defeito).

namespace axle {

struct DumpInputs {
  DumpCommand command = DumpCommand::Hold;
  bool upperLimit = false;  // caçamba no ângulo máximo
  bool lowerLimit = false;  // caçamba abaixada (apoiada no chassi)
  float speed = 0.0f;       // m/s do carrinho
};

class DumpController {
 public:
  // Retorna o comando do atuador: +1 subir, -1 descer, 0 parado.
  int8_t update(const DumpInputs& in, float dt);

  bool fault() const { return fault_; }
  void clearFault() { fault_ = false; runTime_ = 0.0f; }

 private:
  bool fault_ = false;
  float runTime_ = 0.0f;
  int8_t lastOutput_ = 0;
};

}  // namespace axle
