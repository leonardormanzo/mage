import * as THREE from 'three';

// Sensor de colisão (LiDAR/câmera) com alerta sonoro/visual e freio automático.
// Obstáculos são círculos {x, z, r}. Analisa o corredor à frente (ou atrás, em ré),
// curvado conforme o esterço, e compara a distância livre com a distância de parada.

const BODY_HALF_W = 0.95, FRONT_OFF = 1.3, REAR_OFF = 2.15;
export const AUTO_BRAKE_DECEL = 7;
const MARGIN = 0.25, MIN_STOP = 0.45, RANGE = 20;
const COLORS = { ok: 0x2bd46b, warn: 0xffb000, brake: 0xff2a1a };

// ---------- áudio (bipe de sensor de estacionamento) ----------
const audio = { ctx: null, muted: false, clock: 0 };
export function ensureAudio() {
  try {
    if (!audio.ctx) audio.ctx = new (window.AudioContext || window.webkitAudioContext)();
    else if (audio.ctx.state === 'suspended') audio.ctx.resume();
  } catch { audio.ctx = null; }
}
export function toggleMute() { audio.muted = !audio.muted; return audio.muted; }
function beep(freq, dur) {
  const c = audio.ctx;
  if (!c || audio.muted || c.state !== 'running') return;
  const o = c.createOscillator(), g = c.createGain();
  o.type = 'square'; o.frequency.value = freq;
  g.gain.setValueAtTime(0.0001, c.currentTime);
  g.gain.exponentialRampToValueAtTime(0.08, c.currentTime + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur);
  o.connect(g).connect(c.destination);
  o.start(); o.stop(c.currentTime + dur + 0.02);
}

function fanTexture() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, 'rgba(255,255,255,0.75)'); grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad; g.fillRect(0, 0, 64, 256);
  g.fillStyle = 'rgba(255,255,255,0.9)'; g.fillRect(0, 0, 4, 256); g.fillRect(60, 0, 4, 256);
  return new THREE.CanvasTexture(c);
}

export function createSafety(cartRoot, wheelbase) {
  const fanMat = new THREE.MeshBasicMaterial({ color: COLORS.ok, map: fanTexture(), transparent: true, opacity: 0.55, depthWrite: false });
  const fan = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2).translate(0, 0, 0.5), fanMat);
  fan.renderOrder = 2;
  const fanPivot = new THREE.Group();
  fanPivot.position.y = 0.04;
  fanPivot.add(fan);
  cartRoot.add(fanPivot);

  const s = { state: 'ok', free: Infinity, dir: 1, braking: false, fan: fanPivot };

  // colliderSets: listas de obstáculos; intent: -1/0/1 = direção desejada pelo condutor/autopiloto
  s.update = (dt, car, colliderSets, intent) => {
    const moving = Math.abs(car.v) > 0.05;
    const dir = moving ? Math.sign(car.v) : (intent || s.dir);
    const sh = Math.sin(car.heading), ch = Math.cos(car.heading);
    const kappa = (dir > 0 ? 1 : -1) * Math.tan(car.steer) / wheelbase;
    const off = dir > 0 ? FRONT_OFF : REAR_OFF;
    let free = Infinity;
    for (const set of colliderSets) for (const c of set) {
      const dx = c.x - car.x, dz = c.z - car.z;
      if (dx * dx + dz * dz > RANGE * RANGE) continue;
      let f = dx * sh + dz * ch, l = dx * ch - dz * sh;
      if (dir < 0) { f = -f; l = -l; }
      if (f < off * 0.5) continue;
      const corridor = BODY_HALF_W + c.r + MARGIN;
      let along;
      if (Math.abs(kappa) < 0.02) {                       // reta
        if (Math.abs(l) > corridor) continue;
        along = f;
      } else {                                            // arco em torno do centro instantâneo de rotação
        const R = 1 / kappa, rl = l - R, dist = Math.hypot(rl, f);
        if (Math.abs(dist - Math.abs(R)) > corridor) continue;
        const a0 = Math.atan2(0, -R), a1 = Math.atan2(f, rl);
        let swept = R > 0 ? a0 - a1 : a1 - a0;
        swept = ((swept % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
        if (swept > Math.PI) continue;
        along = swept * Math.abs(R);
      }
      free = Math.min(free, along - off - c.r);
    }
    const speed = Math.abs(car.v);
    const stopDist = speed * speed / (2 * AUTO_BRAKE_DECEL) + MIN_STOP;
    const warnDist = stopDist + 2.2 + speed * 0.9;
    let state = 'ok';
    if (free < stopDist || (s.braking && free < stopDist + 0.35)) state = 'brake';
    else if (free < warnDist) state = 'warn';
    if (!moving && !intent && state === 'brake') state = 'warn';

    s.braking = state === 'brake';
    Object.assign(s, { state, free, dir });

    // leque do sensor no chão
    fanPivot.position.z = dir > 0 ? FRONT_OFF : -REAR_OFF;
    fanPivot.rotation.y = dir > 0 ? 0 : Math.PI;
    fan.scale.set(BODY_HALF_W * 2, 1, THREE.MathUtils.clamp(warnDist, 2.5, 9));
    fanMat.color.setHex(COLORS[state]);
    fanMat.opacity = state === 'ok' ? 0.28 : 0.6;

    // bipe: mais rápido quanto mais perto
    audio.clock -= dt;
    if (state !== 'ok' && audio.clock <= 0) {
      if (state === 'brake') { beep(1250, 0.07); audio.clock = 0.12; }
      else { beep(880, 0.06); audio.clock = THREE.MathUtils.clamp(free / warnDist, 0.25, 1) * 0.6; }
    }
    return s;
  };
  return s;
}
