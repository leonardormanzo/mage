# Firmware do Axle-E — ESP32-S3

Programa embarcado do carrinho: dirigir no manual, fazer o ciclo autônomo do canteiro (carregar →
aguardar o peso → levar → bascular → voltar), frear sozinho diante de obstáculos e se localizar por
GPS RTK. É o mesmo comportamento da simulação web, reescrito para rodar num microcontrolador.

**C++17 · Arduino + FreeRTOS · PlatformIO.** Sem alocação dinâmica no núcleo: rotas e buffers têm
tamanho fixo.

> ⚠️ **Segurança.** Este firmware **não é certificado** para segurança de máquinas. A parada de
> emergência precisa ser **elétrica**: botão NF em série com a bobina do contator principal, cortando a
> potência do motor sem depender do ESP32. O firmware só *lê* o botão para registrar a falha e travar o
> sistema. Para operar perto de pessoas, o projeto precisa de análise de risco (ISO 12100, ISO 13849,
> ISO 3691-4 para veículos autônomos) e de um scanner de segurança certificado no lugar dos ultrassons.

## Arquitetura

```
firmware/
├── platformio.ini            ambientes esp32s3 (placa) e native (testes no PC)
├── lib/axle_core/src/axle/   NÚCLEO: só lógica, nenhum acesso a pino — roda igual no ESP32 e no PC
│   ├── config.h              parâmetros (geometria, velocidades, limites de segurança, peso, rota)
│   ├── controller.*          supervisor: quadro de sensores -> saídas dos atuadores, falhas e modos
│   ├── collision_guard.*     corredor da trajetória (reta ou arco) x distância de parada
│   ├── sensor_layout.h       posição e direção de cada sensor de distância
│   ├── mission.*             máquina de estados do ciclo autônomo
│   ├── route.*               rotas do canteiro e seguidor pure pursuit
│   ├── localizer.*           odometria + GPS RTK (filtro complementar)
│   ├── drive.*               rampa de velocidade, PI do motor, limitador de esterço, odometria
│   ├── weight_sensor.*       tara, calibração e filtro do peso da caçamba
│   ├── dump_controller.*     basculamento com intertravamentos e tempo-limite
│   ├── ubx.*                 leitor da mensagem NAV-PVT do GPS u-blox
│   └── protocol.*            comandos de texto e telemetria JSON do console
├── src/                      CASCA: hardware do ESP32-S3
│   ├── pins.h                mapa de pinos e constantes elétricas
│   ├── hal.*                 drivers (ultrassom por interrupção, HX711, encoder PCNT, PPM, relés, LEDs, GPS)
│   └── main.cpp              tarefas FreeRTOS, watchdog, console, NVS
└── test/                     testes Unity no PC (74 casos)
    ├── test_safety/          colisão, peso, caçamba
    ├── test_motion/          tração, rota, localização, UBX, console
    ├── test_mission/         supervisor em malha fechada com um modelo físico do carrinho
    └── support/plant.h       modelo físico usado pelos testes de integração
```

**Núcleo funcional, casca imperativa.** Toda decisão — frear, bascular, trocar de fase, travar falha —
está em `lib/axle_core`, que não conhece o hardware. Por isso o comportamento inteiro é testado no PC,
em malha fechada com um modelo do carrinho, sem placa nenhuma.

**Tarefas:**

| Tarefa | Núcleo | Período | Faz |
|---|---|---|---|
| `controle` | 1 | 20 ms (50 Hz) | aplica comandos, monta o quadro de sensores, roda o supervisor, escreve os atuadores |
| `sensores` | 0 | 5 ms | dispara os ultrassons (frente/trás alternados a cada 50 ms), lê HX711, GPS e bateria, vigia o laço de controle |
| `console` | 0 | 10 ms | comandos pela serial, telemetria JSON a 5 Hz, LEDs e buzzer a 20 Hz |

**Camadas de proteção, da mais rápida para a mais lenta:**

1. Contator cortado pelo botão de emergência (hardware, independe do firmware).
2. Guarda de colisão a cada ciclo: alerta limita a 1 m/s; freio zera o alvo a 3,5 m/s². A distância de
   parada soma a frenagem, 0,15 s de atraso da leitura e 0,6 m de folga.
3. Intertravamentos: não anda com a caçamba fora do fim de curso inferior; só levanta a caçamba parado.
4. Falhas travadas:
   - **cortam o motor e aplicam o freio na hora:** emergência, laço atrasado (>60 ms), encoder parado com o
     motor empurrando (>30 % por 1 s) e sobrevelocidade (>1,25 × a máxima por 0,5 s) — nos dois últimos a
     medida de velocidade deixou de ser confiável;
   - **param pela rampa de emergência:** célula de carga sem leitura ou absurda, caçamba que não chega ao
     fim de curso em 12 s, os dois fins de curso fechados ao mesmo tempo.

   Só saem com `reset`, que exige emergência solta, carrinho parado, nenhum acelerador manual ativo e, para
   o peso e os fins de curso, a causa resolvida. O autônomo nunca volta sozinho depois de uma falha.
5. Sensor de distância sem leitura nova há 300 ms, no sentido da marcha, conta como obstáculo encostado.
   Bordas de eco perdidas ou ruidosas são descartadas sem renovar a leitura, então também caem aqui.
6. Homem-morto: sem comando manual há 0,5 s, o carrinho freia a 3,5 m/s².
7. O autônomo só parte com: emergência solta, sem falha, bateria ≥ 15 %, parado, origem gravada, RTK
   fixo, rumo confirmado (pelo comando `pose` ou pelo GPS numa reta) e a até 3 m da rota.
8. Vigia no núcleo 0: laço de controle parado há 100 ms → desliga motor e aplica freio.
9. Watchdog de hardware (1 s): reinicia o chip; resistores de pull-down mantêm motor desligado e freio aplicado.

**Prioridade da barra de LEDs:** FALHA (vermelho piscando) > FREIO (vermelho) > ALERTA (âmbar) > AUTO (azul) > SYS OK (verde).
Buzzer: contínuo na falha, rápido no freio, lento no alerta e na ré.

## Localização: por que GPS RTK

A baia de carga tem ~3,6 m de largura e o carrinho precisa parar a ~15 cm do ponto certo. GPS comum
erra 2–5 m: não serve. As opções:

| Solução | Precisão | Prós | Contras |
|---|---|---|---|
| **GPS RTK + odometria** (escolhida) | ~2 cm | sem infraestrutura no canteiro além da base (ou NTRIP); o canteiro muda e a rota acompanha | perde precisão encostado no prédio, sob a grua ou cobertura |
| Beacons UWB | 10–30 cm | funciona sob cobertura e perto de estrutura metálica | instalar e recalibrar âncoras toda vez que o canteiro muda |
| Marcadores visuais (ArUco/AprilTag) | ~1–5 cm no encaixe | atracação muito precisa na baia | precisa de câmera e processamento (não cabe num ESP32 sozinho); poeira e lama |
| GPS comum | 2–5 m | barato | impreciso demais para atracar |

Implementado: u-blox ZED-F9P com correção RTK de uma base fixa no canteiro (rádio) ou de uma rede NTRIP.
Cada fixo RTK com precisão ≤ 5 cm puxa a posição da odometria; o rumo é corrigido pelo deslocamento
medido em trechos retos. **Sem RTK por 2 s, o modo autônomo pausa no lugar** e retoma quando o sinal volta.
Uma evolução natural é somar marcadores visuais nas baias para a atracação final.

## Lista de materiais (sugestão)

| Item | Função |
|---|---|
| ESP32-S3-DevKitC-1 (N8R2 ou N16R8) | controlador |
| u-blox ZED-F9P + antena multibanda | GPS RTK (+ segundo F9P como base, ou conta NTRIP) |
| 5× JSN-SR04T (ultrassom à prova d'água) | 3 na frente, 2 atrás |
| 4 células de carga 50–100 kg + HX711 | peso da caçamba |
| Encoder de quadratura no eixo do motor | odometria e velocidade |
| Controlador de motor 72 V com entrada PPM (classe VESC 75 V) | tração |
| Atuador de direção com controle de posição por pulso de servo | direção |
| 2 relés (subir/descer) + bomba hidráulica/atuador da caçamba + 2 fins de curso NA | basculamento |
| Freio de estacionamento por mola + relé | segura o carrinho parado e em falha |
| Botão de emergência NF + contator principal | parada de emergência por hardware |
| Fita WS2812 (12 LEDs) + buzzer 12 V com transistor | sinalização |
| Divisor 300 k / 10 k + conversor DC-DC 72 V → 5 V | bateria e alimentação da eletrônica |

As ligações estão em [`src/pins.h`](src/pins.h). O ESP32-S3 **não tolera 5 V**: os ecos dos ultrassons
entram por divisor resistivo e os fins de curso/emergência por optoacoplador quando a fiação for longa.

**Fins de curso NA (fecham no fim do curso):** um cabo rompido lê "fora do fim de curso", o que bloqueia a
tração e dispara o tempo-limite da caçamba. Com chave NF, um cabo rompido diria "caçamba abaixada" e
liberaria a tração com a caçamba levantada.

## Compilar, gravar e testar

Requer [PlatformIO](https://platformio.org/) (`pip install platformio`). Os testes no PC precisam de um
compilador C++ (`g++`) no PATH — no Windows, MinGW-w64 (WinLibs ou MSYS2).

```bash
pio test -e native            # testes do núcleo no PC
pio run -e esp32s3            # compila para a placa
pio run -e esp32s3 -t upload  # grava
pio device monitor            # console serial, 115200
```

**Windows com espaço no nome do usuário** (ex.: `C:\Users\Nome Sobrenome`): o linker do MinGW falha com
`cannot find C:/Users/Nome`. Contorno: crie uma junção sem espaço para a pasta `mingw64` e aponte o GCC
para ela antes de `pio test`:

```powershell
New-Item -ItemType Junction -Path C:\Users\Public\mingw64 -Target "<pasta do mingw64>"
$env:GCC_EXEC_PREFIX = "C:/Users/Public/mingw64/lib/gcc/"
$env:Path = "C:\Users\Public\mingw64\bin;$env:Path"
```

Use esse ajuste **só** para `pio test -e native`: com `GCC_EXEC_PREFIX` definido, o compilador do ESP32 não
se encontra e `pio run -e esp32s3` falha. Rode a compilação da placa em outro terminal.

## Console serial

Uma linha por comando; a telemetria sai em JSON a 5 Hz.

| Comando | Efeito |
|---|---|
| `auto` | inicia o ciclo autônomo; se recusar, a resposta diz o motivo (`sem_origem`, `sem_rtk`, `rumo_nao_confirmado`, `longe_da_rota`, `bateria_baixa`, `em_movimento`, `falha_ativa`, `emergencia_acionada`) |
| `manual` ou `parar` | volta ao manual; sem comando manual chegando, o homem-morto freia o carrinho |
| `reset` | limpa falhas travadas (ver as condições acima) |
| `tara` | zera o peso com a caçamba vazia; fica gravado na memória |
| `calibrar <kg>` | ajusta a escala com uma massa conhecida na caçamba; recusa leitura implausível; fica gravado |
| `origem <lat> <lon>` | ponto de referência do canteiro (graus decimais); fica gravado |
| `pose <x> <y> <graus>` | posição e rumo atuais no canteiro (o próximo fixo RTK corrige a posição) |

`tara`, `calibrar`, `origem` e `pose` só são aceitos no manual e com o carrinho parado.
| `dirigir <acel> <dir> [sobe\|desce\|segura]` | comando manual de bancada, valores de -1 a 1, repetir a cada < 0,5 s |
| `status` · `ajuda` | uma linha de telemetria · lista os comandos |

Exemplo de telemetria:

```json
{"modo":"auto","fase":"indo_descarregar","pausado":false,"x":10.02,"y":-3.41,"rumo":90.2,"v":2.65,"esterco":0.4,"duty":0.61,"peso":176.3,"bateria":82,"seguranca":"OK","livre":99.90,"sensor_falha":false,"falha":"nenhuma","rtk":true,"luz":"AUTO"}
```

## Colocar em campo

1. **Base RTK.** Instale a base em ponto fixo (ou configure NTRIP no F9P) e, no u-center, configure o
   F9P do carrinho para emitir **UBX NAV-PVT a 10 Hz** no UART ligado ao ESP32.
2. **Origem.** Meça um ponto do canteiro com o RTK e envie `origem <lat> <lon>`. As coordenadas da rota
   são metros a partir desse ponto: x para leste, y para norte. Sem origem gravada o autônomo não parte.
   A cada ligada, o rumo precisa ser informado (`pose`) ou confirmado andando ~10 m em linha reta no manual.
3. **Rota.** Troque os pontos de `buildSiteRoute()` em `route.cpp` pelos pontos medidos da baia de carga,
   do bota-fora e do caminho entre eles. Hoje ela reproduz a rota da simulação.
4. **Encoder.** Empurre o carrinho 10 m em linha reta, leia as contagens e ajuste
   `hw::kEncoderCountsPerMeter` em `pins.h`.
5. **Peso.** Com a caçamba vazia, `tara`; coloque uma massa conhecida (ex.: 50 kg) e `calibrar 50`.
6. **Direção e motor.** Confira o neutro (1500 µs) e o sentido da direção e do motor com as rodas
   suspensas antes de pôr no chão.
7. **Sensores.** Com o carrinho parado, passe uma pessoa na frente de cada sensor e confira `livre` e
   `seguranca` na telemetria.

## Validação

- **Testes no PC (Unity, 74 casos, todos passando):** corredor de colisão em reta, arco e ré; histerese e
  atraso de leitura no freio; sensor sem leitura; velocidade ou esterço corrompidos (NaN); filtro, tara e
  calibração do peso; intertravamentos e tempo-limite da caçamba; rampa, PI e limitador de esterço;
  seguidor de rota; conversão lat/lon; correção de rumo em frente, em ré e com rumo 180° errado; leitor
  UBX com checksum e comprimento absurdo; comandos e telemetria.
- **Integração em malha fechada** com um modelo físico do carrinho: ciclo autônomo completo repetido
  por 7 minutos simulados, frenagem diante de um obstáculo na rota e retomada, emergência, homem-morto,
  caçamba levantada, perda de RTK, célula de carga solta, laço atrasado, caçamba travada, encoder solto,
  motor disparado, fim de curso em curto, e todas as recusas de partida do autônomo.
  Resultado medido: **7 descargas em 7 min**, parada na baia de carga a no máximo **16 cm** do ponto, e
  frenagem com o para-choque a **0,76 m** de um obstáculo no meio da rota.
- **Revisão de código independente** (segurança, concorrência, numérica): os 3 achados graves, os 7 médios
  e os 4 leves foram corrigidos e ganharam teste quando a lógica é do núcleo.
- **Build para a placa:** `pio run -e esp32s3` compila sem avisos (RAM 9 %, flash 10 %).
- A camada de hardware (`src/`) **não foi testada numa placa real**. O modelo físico dos testes é
  simplificado (motor de 1ª ordem, sem patinagem, GPS sem ruído).

## Limites

- Não foi testado em hardware: pinos, sentido do encoder, polaridade dos relés e tempos do ultrassom
  precisam ser conferidos na bancada.
- Ultrassons enxergam mal objetos finos e superfícies inclinadas, e um sensor com eco cruzado mede
  *menos* (para do lado seguro). Não substituem um scanner de segurança.
- O comando manual pela serial é só para bancada. Em campo falta o rádio-controle (ex.: ESP-NOW com
  homem-morto no próprio controle).
- A rota é fixa no código; falta gravá-la pela serial ou a partir de pontos medidos.
- O PI de velocidade e o filtro do RTK usam ganhos de projeto, não ajustados num carrinho real.
- A porcentagem da bateria é linear pela tensão, sem compensar a queda sob carga.
- A 4,5 m/s (manual) a distância de parada calculada é ~4,2 m, quase o alcance de 4,5 m do ultrassom: na
  prática o freio automático só cobre bem até ~3 m/s. Um sensor de maior alcance (LiDAR) resolve.
- Gravar na memória (`tara`, `calibrar`, `origem`) pausa a flash por alguns ms; se passar de 60 ms, o
  laço acusa `controle_atrasado` (com o carrinho parado, basta `reset`).
- Os limites de detecção do encoder parado (30 % de potência por 1 s) e de sobrevelocidade são de projeto:
  um carrinho carregado numa rampa forte pode precisar de ajuste.
