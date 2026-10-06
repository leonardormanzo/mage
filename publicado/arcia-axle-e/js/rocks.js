import * as THREE from 'three';

// Física simplificada das pedras: livres no mundo ou presas ao referencial da caçamba.
// Pedras paradas "dormem" (não integram) para manter o custo baixo com centenas de pedras.

export const ROCK_KG = 2;
const GRAVITY = 9.8, FRICTION = 0.5, R_RANGE = [0.085, 0.115];
const SLEEP_SPEED = 0.06, SLEEP_TIME = 0.4;
const PALETTE = [0x6f6a64, 0x857d73, 0x5d5852, 0x938773, 0x7a6e5f];

export function createRocks(scene, cart, { count = 260, zone }) {
  const { bucket, frontGate, BY, BW, BL, BH, TILT, T } = cart;
  const rocks = Array.from({ length: count }, () => ({
    p: new THREE.Vector3(), v: new THREE.Vector3(),
    r: R_RANGE[0] + Math.random() * (R_RANGE[1] - R_RANGE[0]),
    active: false, inB: false, sleep: false, still: 0, counted: false,
    q: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.random() * 6, Math.random() * 6, Math.random() * 6)),
    squash: 0.75 + Math.random() * 0.4,
  }));
  const mesh = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ roughness: 0.9, flatShading: true }), count);
  mesh.castShadow = mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  rocks.forEach((r, i) => mesh.setColorAt(i, new THREE.Color(PALETTE[i % PALETTE.length]).offsetHSL(0, 0, (Math.random() - 0.5) * 0.08)));
  scene.add(mesh);

  const out = { rocks, mesh, deliveredKg: 0, inBucket: 0, weightKg: 0 };
  const qb = new THREE.Quaternion(), qi = new THREE.Quaternion(), gL = new THREE.Vector3();
  const tv = new THREE.Vector3(), tp = new THREE.Vector3(), tm = new THREE.Matrix4(), ts = new THREE.Vector3();
  const zeroM = new THREE.Matrix4().makeScale(0, 0, 0);
  const halfWidthAt = (y, r) => Math.max(0.12, BW / 2 + (y - BY) * Math.tan(TILT) - r - 0.03);
  const inZone = p => Math.abs(p.x - zone.x) < zone.half && Math.abs(p.z - zone.z) < zone.half;

  function wakeNear(p, radius = 0.5) {
    for (const r of rocks) if (r.sleep && !r.inB && r.p.distanceToSquared(p) < radius * radius) r.sleep = false;
  }

  // Pega pedras livres; se faltar, recicla as que repousam no chão (primeiro as derramadas fora do bota-fora).
  function takeRocks(n) {
    const picked = rocks.filter(r => !r.active).slice(0, n);
    if (picked.length < n) {
      const resting = rocks.filter(r => r.active && !r.inB && r.sleep).sort((a, b) => (inZone(a.p) - inZone(b.p)) || (b.p.y - a.p.y));
      for (const r of resting.slice(0, n - picked.length)) { wakeNear(r.p); picked.push(r); }
    }
    return picked;
  }

  // Solta n pedras numa posição do mundo (caçamba da escavadeira).
  out.drop = (pos, n, spread = 0.35) => {
    for (const r of takeRocks(n)) {
      r.p.set(pos.x + (Math.random() - 0.5) * spread * 2, pos.y + Math.random() * 0.3, pos.z + (Math.random() - 0.5) * spread * 2);
      r.v.set((Math.random() - 0.5) * 0.4, -0.8, (Math.random() - 0.5) * 0.4);
      Object.assign(r, { active: true, inB: false, sleep: false, still: 0, counted: false });
    }
  };
  out.clear = () => { rocks.forEach(r => { r.active = false; r.inB = false; }); out.deliveredKg = 0; };

  function stepOne(r, dt, gateClosed, carVx, carVz) {
    if (r.inB) {
      r.v.addScaledVector(gL, dt);
      r.p.addScaledVector(r.v, dt);
      const floorY = BY + T / 2 + r.r;
      if (r.p.y < floorY) {
        r.p.y = floorY;
        if (r.v.y < 0) r.v.y = -r.v.y * 0.1;
        const N = Math.max(0, -gL.y), vt = Math.hypot(r.v.x, r.v.z);
        const k = vt > 0 ? Math.max(0, vt - FRICTION * N * dt) / vt : 0;
        r.v.x *= k; r.v.z *= k;
      }
      const hw = halfWidthAt(r.p.y, r.r);
      if (Math.abs(r.p.x) > hw) { r.p.x = Math.sign(r.p.x) * hw; if (r.v.x * r.p.x > 0) r.v.x *= -0.15; }
      if (r.p.z < -BL / 2 + r.r) { r.p.z = -BL / 2 + r.r; if (r.v.z < 0) r.v.z *= -0.15; }
      if (gateClosed && r.p.z > BL / 2 - r.r) { r.p.z = BL / 2 - r.r; if (r.v.z > 0) r.v.z *= -0.15; }
      if (!gateClosed && r.p.z > BL / 2 + 0.02) {
        tv.copy(r.v).applyQuaternion(qb);
        bucket.localToWorld(r.p);
        r.v.copy(tv); r.v.x += carVx; r.v.z += carVz;
        r.inB = false; r.still = 0;
      }
      return;
    }
    if (r.sleep) return;
    r.v.y -= GRAVITY * dt;
    r.p.addScaledVector(r.v, dt);
    if (r.p.y < r.r) {
      r.p.y = r.r;
      r.v.y = r.v.y < -0.8 ? -r.v.y * 0.25 : 0;
      const damp = Math.exp(-6 * dt);
      r.v.x *= damp; r.v.z *= damp;
    }
    r.still = r.v.lengthSq() < SLEEP_SPEED * SLEEP_SPEED ? r.still + dt : 0;
    // entregue: pousou dentro do bota-fora (no chão ou sobre a pilha)
    if (!r.counted && r.p.y < 1.2 && r.v.lengthSq() < 0.25 && inZone(r.p)) { r.counted = true; out.deliveredKg += ROCK_KG; }
    if (r.still > SLEEP_TIME) {
      r.sleep = true; r.v.set(0, 0, 0);
    }
    tp.copy(r.p); bucket.worldToLocal(tp);
    if (tp.y < BY + BH - 0.05 && tp.y > BY && Math.abs(tp.x) < halfWidthAt(tp.y, r.r) && tp.z > -BL / 2 + r.r && tp.z < BL / 2 - r.r) {
      tv.copy(r.v); tv.x -= carVx; tv.z -= carVz; tv.applyQuaternion(qi);
      r.p.copy(tp); r.v.copy(tv); r.inB = true; r.counted = false;
    }
  }

  function collidePairs() {
    for (let i = 0; i < count; i++) {
      const a = rocks[i]; if (!a.active) continue;
      for (let j = i + 1; j < count; j++) {
        const b = rocks[j]; if (!b.active || a.inB !== b.inB || (a.sleep && b.sleep)) continue;
        const dx = a.p.x - b.p.x, min = a.r + b.r; if (dx > min || dx < -min) continue;
        const dz = a.p.z - b.p.z; if (dz > min || dz < -min) continue;
        const dy = a.p.y - b.p.y, d2 = dx * dx + dy * dy + dz * dz;
        if (d2 >= min * min || d2 < 1e-8) continue;
        const d = Math.sqrt(d2), over = min - d, nx = dx / d, ny = dy / d, nz = dz / d;
        const wa = a.sleep ? 0 : b.sleep ? 1 : 0.5, wb = 1 - wa;
        a.p.x += nx * over * wa; a.p.y += ny * over * wa; a.p.z += nz * over * wa;
        b.p.x -= nx * over * wb; b.p.y -= ny * over * wb; b.p.z -= nz * over * wb;
        const rel = (a.v.x - b.v.x) * nx + (a.v.y - b.v.y) * ny + (a.v.z - b.v.z) * nz;
        if (rel < 0) {
          a.v.x -= rel * nx * wa; a.v.y -= rel * ny * wa; a.v.z -= rel * nz * wa;
          b.v.x += rel * nx * wb; b.v.y += rel * ny * wb; b.v.z += rel * nz * wb;
        }
        if (!a.sleep) a.v.multiplyScalar(0.995);
        if (!b.sleep) b.v.multiplyScalar(0.995);
      }
    }
  }

  out.step = (dt, car, substeps = 3) => {
    bucket.getWorldQuaternion(qb); qi.copy(qb).invert();
    gL.set(0, -GRAVITY, 0).applyQuaternion(qi);
    const gateClosed = frontGate.rotation.x < TILT + 0.25;
    const carVx = Math.sin(car.heading) * car.v, carVz = Math.cos(car.heading) * car.v;
    const h = dt / substeps;
    for (let k = 0; k < substeps; k++) {
      for (const r of rocks) if (r.active) stepOne(r, h, gateClosed, carVx, carVz);
      collidePairs();
    }
  };

  out.sync = () => {
    bucket.updateWorldMatrix(true, false);
    let inB = 0;
    rocks.forEach((r, i) => {
      if (!r.active) { mesh.setMatrixAt(i, zeroM); return; }
      tp.copy(r.p);
      if (r.inB) { bucket.localToWorld(tp); inB++; }
      ts.set(r.r, r.r * r.squash, r.r);
      mesh.setMatrixAt(i, tm.compose(tp, r.q, ts));
    });
    mesh.instanceMatrix.needsUpdate = true;
    out.inBucket = inB;
    // sensor de peso: célula de carga com ruído e filtro passa-baixa
    const raw = inB * ROCK_KG + (Math.random() - 0.5) * 1.2;
    out.weightKg += (Math.max(0, raw) - out.weightKg) * 0.15;
    return out;
  };
  return out;
}
