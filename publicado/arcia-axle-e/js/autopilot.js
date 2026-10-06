// Rota da obra + piloto automático (pure pursuit) com máquina de estados:
// ir ao carregamento → aguardar sensor de peso → ir à descarga → bascular → recolher → ré → repetir.

export const AUTO_VMAX = 2.7;           // m/s (~10 km/h, limite da obra)
export const LOAD_TARGET_KG = 170;      // peso que libera a saída do carregamento
export const CAPACITY_KG = 200;
const LOOKAHEAD_MIN = 2.2, LOOKAHEAD_GAIN = 0.6;
const LAT_ACCEL = 1.0, STOP_DECEL = 1.2;
const DUMP_EMPTY_KG = 4, LOAD_STABLE_S = 1.5, EMPTY_STABLE_S = 1.2, DUMP_TIMEOUT_S = 14;
const REVERSE_DIST = 5, REVERSE_SPEED = 1.0;
const ARRIVE_DIST = 0.15, ARRIVE_SPEED = 0.1;

// ---------- geometria da rota (x, z) ----------
function line(out, a, b, step = 0.25) {
  const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
  for (let i = out.length ? 1 : 0; i <= n; i++) out.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]);
  return out;
}
function arc(out, c, r, t0, t1, step = 0.25) {
  const n = Math.max(2, Math.ceil(Math.abs(t1 - t0) * r / step));
  for (let i = out.length ? 1 : 0; i <= n; i++) { const t = t0 + (t1 - t0) * i / n; out.push([c[0] + r * Math.cos(t), c[1] + r * Math.sin(t)]); }
  return out;
}
function makePath(pts) {
  const s = [0];
  for (let i = 1; i < pts.length; i++) s.push(s[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return { pts, s, length: s[s.length - 1] };
}

export const LOAD_STOP = [-14, 10];
export const DUMP_STOP = [6, 10];
export const REVERSE_END = [DUMP_STOP[0] - REVERSE_DIST, DUMP_STOP[1]];
export const ZONE_HALF = 3.5;
export const ZONE_CENTER = [DUMP_STOP[0] + 0.8 + ZONE_HALF, DUMP_STOP[1]];
export const BAY = { x: LOAD_STOP[0], z: LOAD_STOP[1], halfX: 2.6, halfZ: 1.8 };
export const START = { x: -6, z: 2, heading: -Math.PI / 2 };   // estrada sul, sentido oeste

const toDump = makePath(line([], LOAD_STOP, DUMP_STOP));
const toLoad = makePath((() => {
  const p = [];
  arc(p, [1, 6], 4, Math.PI / 2, -Math.PI / 2);          // retorno leste
  line(p, [1, 2], [-18, 2]);                              // estrada sul
  arc(p, [-18, 6], 4, -Math.PI / 2, -Math.PI * 1.5);      // retorno oeste
  line(p, [-18, 10], LOAD_STOP);
  return p;
})());
export const ROUTE = { toDump, toLoad };

export const PHASE_LABEL = {
  IDLE: 'Desligado',
  TO_LOAD: 'Indo ao carregamento',
  WAIT_LOAD: 'Aguardando carga (sensor de peso)',
  TO_DUMP: 'Levando carga à descarga',
  DUMP: 'Descarregando',
  LOWER: 'Recolhendo caçamba',
  REVERSE: 'Manobra de ré',
};

export function inBay(x, z) { return Math.abs(x - BAY.x) < BAY.halfX && Math.abs(z - BAY.z) < BAY.halfZ; }

// ---------- seguidor de trajetória ----------
function nearestIndex(path, car, from, to, preferAligned) {
  let best = 0, bestScore = Infinity;
  const sh = Math.sin(car.heading), ch = Math.cos(car.heading);
  for (let i = Math.max(0, from); i < Math.min(to, path.pts.length); i++) {
    const [x, z] = path.pts[i];
    let score = (x - car.x) ** 2 + (z - car.z) ** 2;
    if (preferAligned && i < path.pts.length - 1) {
      const dx = path.pts[i + 1][0] - x, dz = path.pts[i + 1][1] - z;
      if (dx * sh + dz * ch < 0) score += 64;
    }
    if (score < bestScore) { bestScore = score; best = i; }
  }
  return best;
}

function follow(ap, path, car, wheelbase) {
  ap.idx = ap.idx < 0
    ? nearestIndex(path, car, 0, path.pts.length, true)
    : nearestIndex(path, car, ap.idx - 4, ap.idx + 40, false);
  const s0 = path.s[ap.idx], remaining = path.length - s0;
  const Ld = Math.max(LOOKAHEAD_MIN, 1.5 + LOOKAHEAD_GAIN * Math.abs(car.v));
  const n = path.pts.length, end = path.pts[n - 1], prev = path.pts[n - 2];
  const eLen = Math.hypot(end[0] - prev[0], end[1] - prev[1]);
  const ex = (end[0] - prev[0]) / eLen, ez = (end[1] - prev[1]) / eLen;

  let tx, tz;
  if (remaining < Ld) { tx = end[0] + ex * (Ld - remaining); tz = end[1] + ez * (Ld - remaining); }
  else {
    let ti = ap.idx;
    while (ti < n - 1 && path.s[ti] < s0 + Ld) ti++;
    [tx, tz] = path.pts[ti];
  }
  const sh = Math.sin(car.heading), ch = Math.cos(car.heading);
  const dx = tx - car.x, dz = tz - car.z;
  const left = dx * ch - dz * sh;
  const kappa = 2 * left / Math.max(dx * dx + dz * dz, 0.01);
  const dEnd = remaining < 3 ? (end[0] - car.x) * ex + (end[1] - car.z) * ez : remaining;

  const vCurve = Math.sqrt(LAT_ACCEL / Math.max(Math.abs(kappa), 1e-3));
  const vStop = Math.sqrt(2 * STOP_DECEL * Math.max(0, dEnd - 0.05));
  return { targetV: Math.min(AUTO_VMAX, vCurve, vStop), steer: Math.atan(kappa * wheelbase), dEnd };
}

// ---------- máquina de estados ----------
export function createAutopilot({ wheelbase, dumpMax }) {
  const ap = { active: false, phase: 'IDLE', idx: -1, timer: 0, stable: 0, revFrom: null };

  function setPhase(p) { ap.phase = p; ap.timer = 0; ap.stable = 0; ap.idx = -1; }

  ap.start = weightKg => { ap.active = true; setPhase(weightKg >= LOAD_TARGET_KG * 0.8 ? 'TO_DUMP' : 'TO_LOAD'); };
  ap.stop = () => { ap.active = false; setPhase('IDLE'); };

  // Retorna { targetV, steer, dumpCmd } para o controlador do carrinho.
  ap.control = (dt, car, weightKg) => {
    ap.timer += dt;
    const arrived = r => r.dEnd < ARRIVE_DIST && Math.abs(car.v) < ARRIVE_SPEED;
    switch (ap.phase) {
      case 'TO_LOAD': {
        const r = follow(ap, toLoad, car, wheelbase);
        if (arrived(r)) setPhase('WAIT_LOAD');
        return { targetV: r.targetV, steer: r.steer, dumpCmd: -1 };
      }
      case 'WAIT_LOAD':
        ap.stable = weightKg >= LOAD_TARGET_KG ? ap.stable + dt : 0;
        if (ap.stable >= LOAD_STABLE_S) setPhase('TO_DUMP');
        return { targetV: 0, steer: 0, dumpCmd: -1 };
      case 'TO_DUMP': {
        const r = follow(ap, toDump, car, wheelbase);
        if (arrived(r)) setPhase('DUMP');
        return { targetV: r.targetV, steer: r.steer, dumpCmd: -1 };
      }
      case 'DUMP':
        ap.stable = car.dump >= dumpMax - 0.01 && weightKg < DUMP_EMPTY_KG ? ap.stable + dt : 0;
        if (ap.stable >= EMPTY_STABLE_S || ap.timer > DUMP_TIMEOUT_S) setPhase('LOWER');
        return { targetV: 0, steer: 0, dumpCmd: 1 };
      case 'LOWER':
        if (car.dump <= 0.001) { setPhase('REVERSE'); ap.revFrom = { x: car.x, z: car.z }; }
        return { targetV: 0, steer: 0, dumpCmd: -1 };
      case 'REVERSE': {
        const left = REVERSE_DIST - Math.hypot(car.x - ap.revFrom.x, car.z - ap.revFrom.z);
        if (left < 0.1 && Math.abs(car.v) < ARRIVE_SPEED) setPhase('TO_LOAD');
        return { targetV: -Math.min(REVERSE_SPEED, Math.sqrt(2 * STOP_DECEL * Math.max(0, left - 0.05))), steer: 0, dumpCmd: -1 };
      }
      default:
        return { targetV: 0, steer: 0, dumpCmd: 0 };
    }
  };
  return ap;
}
