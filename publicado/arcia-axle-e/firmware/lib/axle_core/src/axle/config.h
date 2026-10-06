#pragma once
// Parâmetros físicos e de controle do Axle-E (unidades SI: m, s, rad, kg).
// Os valores de rota/peso/segurança espelham a simulação web (js/autopilot.js e js/safety.js);
// os de dinâmica foram reduzidos para o que um carrinho real de ~450 kg carregado consegue fazer.

namespace axle::cfg {

// ---- geometria ----
inline constexpr float kWheelbase = 1.90f;       // entre-eixos
inline constexpr float kTrack = 1.88f;           // bitola
inline constexpr float kWheelRadius = 0.406f;    // pneu 25x10-12
inline constexpr float kBodyHalfWidth = 0.95f;   // meia largura para o corredor de colisão
inline constexpr float kFrontOffset = 1.30f;     // centro -> para-choque dianteiro
inline constexpr float kRearOffset = 2.15f;      // centro -> fim das alças traseiras

// ---- direção ----
inline constexpr float kMaxSteer = 0.60f;        // rad
inline constexpr float kSteerRate = 0.80f;       // rad/s (velocidade do servo de direção)
inline constexpr float kSteerSpeedFactor = 0.12f;// reduz o esterço máximo com a velocidade

// ---- velocidade ----
inline constexpr float kMaxSpeedManual = 4.5f;   // m/s (16 km/h)
inline constexpr float kMaxSpeedAuto = 2.7f;     // m/s (~10 km/h, limite da obra)
inline constexpr float kMaxReverse = 2.5f;
inline constexpr float kAccel = 1.2f;            // m/s² aceleração normal
inline constexpr float kDecel = 2.0f;            // m/s² desaceleração de serviço
inline constexpr float kEmergencyDecel = 3.5f;   // m/s² freio automático (a simulação usa 7)

// ---- segurança (sensor de colisão) ----
inline constexpr float kSafetyMargin = 0.25f;    // folga lateral do corredor
inline constexpr float kObstacleRadius = 0.10f;  // um eco vira um obstáculo deste raio
inline constexpr float kMinStopDistance = 0.60f; // folga mínima mesmo parado
inline constexpr float kWarnExtra = 2.2f;        // zona de aviso além da distância de parada
inline constexpr float kWarnTimeGap = 0.9f;      // s de antecipação extra no aviso
inline constexpr float kBrakeHysteresis = 0.35f; // evita liga/desliga do freio
inline constexpr float kSensorStaleMs = 300.0f;  // leitura mais velha que isso = falha (freia)
inline constexpr float kWarnMaxSpeed = 1.0f;     // m/s: teto de velocidade na zona de alerta
inline constexpr float kRangeMax = 4.5f;         // m: alcance útil do ultrassom (sem eco além disso)
inline constexpr float kSensorLatencyS = 0.15f;  // s: idade típica da leitura (100 ms por grupo) + ciclo + rampa

// ---- plausibilidade da tração ----
inline constexpr float kStallDuty = 0.30f;       // potência acima disso com o encoder parado...
inline constexpr float kStallTimeS = 1.0f;       // ...por este tempo = encoder solto ou roda travada
inline constexpr float kOverspeedFactor = 1.25f; // acima de 1,25 x a velocidade máxima...
inline constexpr float kOverspeedTimeS = 0.5f;   // ...por este tempo = sobrevelocidade

// ---- partida do autônomo ----
inline constexpr float kAutoStartMaxOffset = 3.0f;  // m: longe disso da rota, recusa iniciar

// ---- caçamba ----
inline constexpr float kDumpTimeout = 12.0f;     // s: atuador sem chegar ao fim de curso = falha
inline constexpr float kDumpMaxSpeed = 0.05f;    // m/s: só bascula parado

// ---- sensor de peso ----
inline constexpr float kCapacityKg = 200.0f;
inline constexpr float kLoadTargetKg = 170.0f;   // libera a saída do carregamento
inline constexpr float kEmptyKg = 4.0f;          // considera a caçamba vazia
inline constexpr float kLoadStableS = 1.5f;
inline constexpr float kEmptyStableS = 1.2f;
inline constexpr float kWeightFilterTau = 0.4f;  // s: constante do filtro passa-baixa
inline constexpr float kWeightImplausibleKg = 400.0f;
inline constexpr float kWeightStaleMs = 1000.0f;  // HX711 sem amostra nova = falha de cabo

// ---- autopiloto ----
inline constexpr float kLookaheadMin = 2.2f;
inline constexpr float kLookaheadGain = 0.6f;
inline constexpr float kLatAccel = 1.0f;         // m/s² lateral máximo em curva
inline constexpr float kStopDecel = 1.2f;        // m/s² para parar no fim da rota
inline constexpr float kArriveDistance = 0.15f;
inline constexpr float kArriveSpeed = 0.10f;
inline constexpr float kReverseDistance = 5.0f;
inline constexpr float kReverseSpeed = 1.0f;

// ---- energia ----
inline constexpr float kBatteryAutoMinPct = 15.0f;  // abaixo disso o autônomo não inicia

// ---- laço de controle ----
inline constexpr float kControlHz = 50.0f;
inline constexpr float kManualTimeoutS = 0.5f;   // homem-morto: sem comando manual => para
inline constexpr float kMaxCycleS = 3.0f / kControlHz;  // ciclo mais longo que isso = laço atrasado

}  // namespace axle::cfg
