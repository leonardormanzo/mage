import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { paintTexture, repeatTex, labelTexture } from './textures.js';
import { imageTexture } from './assets.js';

// Escavadeira que carrega o carrinho: cava na pilha, gira, posiciona sobre a caçamba e solta as pedras.
// Braço com IK de dois segmentos no plano vertical da cabine.

const L1 = 3.4, L2 = 2.6;                    // lança e braço
const PIVOT = new THREE.Vector3(0.35, 1.95, 1.0); // pivô da lança no referencial da cabine
const YAW_RATE = 1.5, TIP_SPEED = 4.2, ROCKS_PER_SCOOP = 30;

export function createExcavator(scene, { position, pile }) {
  const dark = paintTexture(0x2c2e31, { size: 256, seed: 78, grime: 0.3, scratches: 30, chips: 5, rough: [0.5, 0.7] });
  const M = {
    yellow: (() => {             // textures/escavadeira/pintura_amarela.png (gerada no Gemini)
      const map = imageTexture('textures/escavadeira/pintura_amarela.png', { repeat: [1.2, 1.2] });
      return new THREE.MeshStandardMaterial({ map, bumpMap: map, bumpScale: 0.6, roughness: 0.55, metalness: 0.25 });
    })(),
    dark: new THREE.MeshStandardMaterial({ ...repeatTex(dark, 1.5), roughness: 1, metalness: 0.4 }),
    track: new THREE.MeshStandardMaterial({ color: 0x1b1b1c, roughness: 0.9, metalness: 0.3 }),
    glass: new THREE.MeshStandardMaterial({ color: 0x23323d, roughness: 0.05, metalness: 0.8, transparent: true, opacity: 0.75 }),
    chrome: new THREE.MeshStandardMaterial({ color: 0xdfe3e6, roughness: 0.15, metalness: 1 }),
    gravel: new THREE.MeshStandardMaterial({ color: 0x77716a, roughness: 1, flatShading: true }),
  };
  const add = (m, parent) => { m.castShadow = m.receiveShadow = true; parent.add(m); return m; };
  const rbox = (w, h, d, mat, x, y, z, parent, r = 0.05) => {
    const m = add(new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 2, r), mat), parent);
    m.position.set(x, y, z); return m;
  };

  const root = new THREE.Group();
  root.position.copy(position);
  scene.add(root);

  // esteiras
  for (const s of [-1, 1]) {
    rbox(0.7, 0.75, 4.2, M.track, s * 1.25, 0.38, 0, root, 0.3);
    for (let i = 0; i < 5; i++) {
      const roller = add(new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.74, 16), M.dark), root);
      roller.rotation.z = Math.PI / 2; roller.position.set(s * 1.25, 0.3, -1.4 + i * 0.7);
    }
  }
  rbox(1.9, 0.35, 2.6, M.dark, 0, 0.75, 0, root);

  // cabine giratória
  const house = new THREE.Group();
  house.position.y = 0.95;
  root.add(house);
  rbox(2.5, 1.0, 3.0, M.yellow, 0, 0.55, -0.2, house, 0.1);
  rbox(2.4, 0.9, 0.7, M.dark, 0, 0.6, -1.85, house, 0.15);                  // contrapeso
  rbox(0.95, 1.5, 1.15, M.yellow, -0.7, 1.75, 0.5, house, 0.06);            // cabine do operador
  for (const [w, h, x, y, z, ry] of [[0.8, 1.1, -0.7, 1.85, 1.08, 0], [1.0, 1.0, -1.18, 1.85, 0.5, -Math.PI / 2]]) {
    const g = new THREE.Mesh(new THREE.PlaneGeometry(w, h), M.glass);
    g.position.set(x, y, z); g.rotation.y = ry; house.add(g);
  }
  const exhaust = add(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.6, 12), M.dark), house);
  exhaust.position.set(0.8, 1.35, -1.2);
  const decal = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.3), new THREE.MeshStandardMaterial({ map: labelTexture('TERRA-BOTICS', 512, 110, { font: 'bold 70px Arial', bg: null, fg: '#1d1a15' }), transparent: true }));
  decal.position.set(1.26, 0.6, -0.4); decal.rotation.y = Math.PI / 2; house.add(decal);

  // lança, braço e caçamba (geometria ao longo de +z)
  const boom = add(new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.5, L1).translate(0, 0, L1 / 2), M.yellow), house);
  const stick = add(new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.38, L2).translate(0, 0, L2 / 2), M.yellow), house);
  const bucketG = new THREE.Group();
  house.add(bucketG);
  rbox(0.9, 0.55, 0.6, M.dark, 0, -0.2, 0.15, bucketG, 0.08);
  for (let i = 0; i < 4; i++) {
    const tooth = add(new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.16, 8), M.chrome), bucketG);
    tooth.position.set(-0.3 + i * 0.2, -0.5, 0.35); tooth.rotation.x = Math.PI;
  }
  const load = add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.38, 1), M.gravel), bucketG);
  load.position.set(0, 0.05, 0.15); load.scale.y = 0.55; load.visible = false;
  const cylinder = add(new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 1, 12).translate(0, 0.5, 0), M.chrome), house);

  // ---------- IK ----------
  const elbow = new THREE.Vector3(), tipLocal = new THREE.Vector3(), tmp = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  function solveArm(tipWorld, bucketPitch) {
    const dx = tipWorld.x - root.position.x, dz = tipWorld.z - root.position.z;
    const r = Math.hypot(dx, dz) - PIVOT.z;
    const h = tipWorld.y - (house.position.y + PIVOT.y);
    const d = THREE.MathUtils.clamp(Math.hypot(r, h), Math.abs(L1 - L2) + 0.2, L1 + L2 - 0.05);
    const a = Math.atan2(h, r);
    const b = Math.acos(THREE.MathUtils.clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
    const t1 = a + b;
    boom.position.copy(PIVOT); boom.rotation.set(-t1, 0, 0);
    elbow.set(PIVOT.x, PIVOT.y + Math.sin(t1) * L1, PIVOT.z + Math.cos(t1) * L1);
    tipLocal.set(PIVOT.x, PIVOT.y + Math.sin(a) * d, PIVOT.z + Math.cos(a) * d);
    const t2 = Math.atan2(tipLocal.y - elbow.y, tipLocal.z - elbow.z);
    stick.position.copy(elbow); stick.rotation.set(-t2, 0, 0);
    bucketG.position.copy(tipLocal); bucketG.rotation.set(bucketPitch, 0, 0);
    // cilindro hidráulico da lança
    const base = tmp.set(PIVOT.x, 0.75, PIVOT.z - 0.2);
    const mid = elbow.clone().lerp(PIVOT, 0.55);
    cylinder.position.copy(base);
    cylinder.quaternion.setFromUnitVectors(up, mid.clone().sub(base).normalize());
    cylinder.scale.y = mid.distanceTo(base);
  }

  // ---------- animação / estados ----------
  const pileDir = Math.atan2(pile.x - position.x, pile.z - position.z);
  const pileEdge = new THREE.Vector3(position.x + Math.sin(pileDir) * 4.6, 0, position.z + Math.cos(pileDir) * 4.6);
  const ex = { state: 'idle', yaw: pileDir, tip: new THREE.Vector3(pileEdge.x, 3, pileEdge.z), pitch: 0, timer: 0, loaded: false };
  const restTip = ex.tip.clone();
  const target = new THREE.Vector3();
  const colliders = [
    { x: position.x, z: position.z - 1, r: 1.7 }, { x: position.x, z: position.z + 1, r: 1.7 },
  ];

  function moveTip(goal, dt) {
    const d = goal.clone().sub(ex.tip), len = d.length(), stepLen = TIP_SPEED * dt;
    if (len <= stepLen) { ex.tip.copy(goal); return true; }
    ex.tip.addScaledVector(d, stepLen / len);
    return false;
  }
  function turnTo(yaw, dt) {
    let diff = Math.atan2(Math.sin(yaw - ex.yaw), Math.cos(yaw - ex.yaw));
    const stepYaw = YAW_RATE * dt;
    if (Math.abs(diff) <= stepYaw) { ex.yaw = yaw; return true; }
    ex.yaw += Math.sign(diff) * stepYaw;
    return false;
  }
  const approach = (cur, goal, rate, dt) => cur + (goal - cur) * Math.min(1, rate * dt);

  // ctx: { wantLoad, cartTarget (Vector3: centro da caçamba do carrinho), drop(pos, n) }
  function update(dt, ctx) {
    ex.timer += dt;
    const toCartYaw = Math.atan2(ctx.cartTarget.x - position.x, ctx.cartTarget.z - position.z);
    switch (ex.state) {
      case 'idle':
        turnTo(pileDir, dt); moveTip(restTip, dt); ex.pitch = approach(ex.pitch, 0, 3, dt);
        if (ctx.wantLoad) ex.state = ex.loaded ? 'lift' : 'reach';
        break;
      case 'reach':      // posiciona sobre a pilha
        target.set(pileEdge.x, 2.2, pileEdge.z);
        if (turnTo(pileDir, dt) & moveTip(target, dt)) ex.state = 'dig';
        ex.pitch = approach(ex.pitch, -0.6, 3, dt);
        break;
      case 'dig':        // afunda e recolhe a caçamba
        target.set(pileEdge.x, 0.5, pileEdge.z);
        if (moveTip(target, dt)) { ex.pitch = approach(ex.pitch, 0.9, 7, dt); if (ex.pitch > 0.85) { ex.loaded = true; ex.state = 'lift'; } }
        break;
      case 'lift':
        target.set(ex.tip.x, 3.4, ex.tip.z);
        if (moveTip(target, dt)) ex.state = ctx.wantLoad ? 'swing' : 'idle';
        break;
      case 'swing': {    // gira até o carrinho e posiciona sobre a caçamba
        if (!ctx.wantLoad) { ex.state = 'lift'; break; }
        const dist = Math.hypot(ctx.cartTarget.x - position.x, ctx.cartTarget.z - position.z);
        target.set(position.x + Math.sin(ex.yaw) * dist, ctx.cartTarget.y + 1.3, position.z + Math.cos(ex.yaw) * dist);
        if (turnTo(toCartYaw, dt) & moveTip(target, dt)) { ex.state = 'dump'; ex.timer = 0; }
        break;
      }
      case 'dump':
        ex.pitch = approach(ex.pitch, -1.4, 6, dt);
        if (ex.loaded && ex.pitch < -1.0) {
          bucketG.getWorldPosition(target);
          if (ctx.wantLoad && Math.hypot(target.x - ctx.cartTarget.x, target.z - ctx.cartTarget.z) < 0.9) ctx.drop(target.clone().setY(target.y - 0.45), ROCKS_PER_SCOOP, 0.3);
          ex.loaded = false;
        }
        if (ex.timer > 0.8) ex.state = ctx.wantLoad ? 'reach' : 'idle';
        break;
    }
    load.visible = ex.loaded;
    house.rotation.y = ex.yaw;
    root.updateMatrixWorld(true);
    solveArm(ex.tip, ex.pitch);
  }
  solveArm(ex.tip, 0);
  return { root, colliders, update, state: () => ex.state };
}
