#pragma once
#include <cstddef>

#include "axle/controller.h"

// Console serial: comandos de texto, uma linha por comando, e telemetria em JSON (uma linha por amostra).
//
//   auto                         inicia o ciclo autônomo
//   manual | parar               volta ao manual (o carrinho para pela rampa)
//   reset                        limpa falhas travadas (emergência solta, causa resolvida)
//   tara                         zera o peso com a caçamba vazia
//   calibrar <kg>                ajusta a escala com uma massa conhecida na caçamba
//   origem <lat> <lon>           ponto de referência do canteiro (graus decimais)
//   pose <x> <y> <graus>         posição inicial no canteiro (m, m, rumo)
//   dirigir <acel> <dir> [sobe|desce|segura]
//                                comando manual de bancada, -1…1; repetir a cada <0,5 s (homem-morto)
//   status                       imprime uma linha de telemetria
//   ajuda                        lista os comandos

namespace axle {

enum class CommandType : uint8_t {
  Empty, Invalid, Auto, Manual, Reset, Tare, Calibrate, Origin, SetPose, Drive, Status, Help
};

struct Command {
  CommandType type = CommandType::Empty;
  double a = 0.0, b = 0.0, c = 0.0;     // argumentos numéricos, na ordem da linha
  DumpCommand dump = DumpCommand::Hold;  // só em "dirigir"
};

// Interpreta uma linha. Argumentos fora da faixa ou sobrando/faltando viram CommandType::Invalid.
Command parseCommand(const char* line);

// Escreve a telemetria como JSON numa linha (sem '\n'). Retorna o número de caracteres, ou 0 se não coube.
std::size_t formatTelemetry(const Telemetry& t, char* out, std::size_t size);

const char* toString(Mode m);
extern const char* const kHelpText;

}  // namespace axle
