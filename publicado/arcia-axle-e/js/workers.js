import * as THREE from 'three';
import { imageTexture, loadJSON } from './assets.js';

// Trabalhadores com EPI caminhando em rotas de vai-e-vem (alguns cruzam as vias).
// Cada um expõe um colisor dinâmico {x, z, r} usado pelo sensor do carrinho.
// Texturas: textures/trabalhadores (originais) e textures/prontas (recortes de tools/preparar_texturas.py).

const WALK_SPEED = 1.1, RADIUS = 0.4, LOOK_AHEAD = 0.9, KEEP_CLEAR = 0.6;
const YIELD_AFTER = 1.5, STEP_ASIDE = 2.0; // s bloqueado antes de dar passagem; s se afastando
const FACES = 4, DEFAULT_SKIN = '#b8876c';
const T_RAW = 'textures/trabalhadores/', T_READY = 'textures/prontas/';

function sharedMaterials() {
  const std = (map, extra = {}) => new THREE.MeshStandardMaterial({ map, roughness: 0.85, ...extra });
  const front = imageTexture(T_READY + 'colete_frente.jpg');
  // laterais e ombros reaproveitam uma faixa laranja da frente (entre a faixa refletiva vertical e o zíper)
  const vestSide = imageTexture(T_READY + 'colete_frente.jpg', { repeat: [0.18, 1], offset: [0.15, 0] });
  const vestTop = imageTexture(T_READY + 'colete_frente.jpg', { repeat: [0.2, 0.06], offset: [0.15, 0.9] });
  const side = std(vestSide, { roughness: 0.7 }), top = std(vestTop, { roughness: 0.7 });
  return {
    // ordem das faces da caixa: +x, -x, +y, -y, +z (frente), -z (costas)
    vest: [side, side, top, top, std(front, { roughness: 0.7 }), std(imageTexture(T_READY + 'colete_costas.jpg'), { roughness: 0.7 })],
    sleeve: std(imageTexture(T_RAW + 'manga_camisa.png', { repeat: [0.5, 1.2] })),
    pants: std(imageTexture(T_RAW + 'calca_trabalho.png', { repeat: [0.6, 1.6] })),
    boots: std(imageTexture(T_RAW + 'bota_couro.png', { repeat: [0.6, 0.4] }), { roughness: 0.6 }),
    helmetMap: imageTexture(T_RAW + 'capacete_plastico.png'),
    sticker: new THREE.MeshStandardMaterial({
      map: imageTexture(T_READY + 'capacete_adesivo.png'), transparent: true, roughness: 0.4,
      polygonOffset: true, polygonOffsetFactor: -2, depthWrite: false,
    }),
    faces: Array.from({ length: FACES }, (_, i) => new THREE.MeshStandardMaterial({
      map: imageTexture(`${T_READY}rosto_${i + 1}.png`), transparent: true, roughness: 0.75,
      polygonOffset: true, polygonOffsetFactor: -1, depthWrite: false,
    })),
  };
}

// rosto: calota esférica na frente (+z) da cabeça, um pouco maior que ela
const HEAD_R = 0.13;
const faceGeo = new THREE.SphereGeometry(HEAD_R * 1.012, 28, 20, Math.PI / 2 - 1.1, 2.2, 0.75, 1.45);

function makeWorker(M, faceIndex, helmetColor) {
  const g = new THREE.Group();
  const skin = new THREE.MeshStandardMaterial({ color: DEFAULT_SKIN, roughness: 0.75 });
  const helmet = new THREE.MeshStandardMaterial({ color: helmetColor, map: M.helmetMap, roughness: 0.3 });
  const add = (m, parent = g) => { m.castShadow = true; parent.add(m); return m; };
  const legs = [-1, 1].map(s => {
    const hip = new THREE.Group(); hip.position.set(s * 0.11, 0.9, 0); g.add(hip);
    add(new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.82, 0.17).translate(0, -0.41, 0), M.pants), hip);
    add(new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.1, 0.26).translate(0, -0.85, 0.04), M.boots), hip);
    return hip;
  });
  add(new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.6, 0.25), M.vest)).position.y = 1.2;
  const arms = [-1, 1].map(s => {
    const sh = new THREE.Group(); sh.position.set(s * 0.27, 1.45, 0); g.add(sh);
    add(new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.6, 0.12).translate(0, -0.3, 0), M.sleeve), sh);
    add(new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 6), skin), sh).position.y = -0.62;
    return sh;
  });
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.1, 12), skin)).position.y = 1.53;      // pescoço
  add(new THREE.Mesh(new THREE.SphereGeometry(HEAD_R, 24, 18), skin)).position.y = 1.65;
  const face = new THREE.Mesh(faceGeo, M.faces[faceIndex]);
  face.position.y = 1.65; g.add(face);
  const hat = add(new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), helmet));
  hat.position.y = 1.7;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.19, 0.015, 24), helmet)).position.set(0, 1.71, 0.03);
  const sticker = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.055), M.sticker);
  sticker.position.set(0, 1.79, 0.128); sticker.rotation.x = -0.55; g.add(sticker);
  return { g, legs, arms, skin };
}

export function createWorkers(scene, routes) {
  const M = sharedMaterials();
  const helmets = [0xffffff, 0xf2c200, 0x1f6fd1, 0xffffff, 0xf2c200, 0xffffff];
  const workers = routes.map((pts, i) => {
    const w = makeWorker(M, i % FACES, helmets[i % helmets.length]);
    scene.add(w.g);
    const [x, z] = pts[0];
    return { ...w, face: i % FACES, pts, i: 1, dir: 1, x, z, r: RADIUS, pause: Math.random() * 2, phase: Math.random() * 6, heading: 0, waitT: 0, asideT: 0 };
  });
  // cor da pele de cada rosto (medida pelo script de preparo)
  loadJSON(T_READY + 'pele.json', {}).then(skins => {
    for (const w of workers) { const c = skins[`rosto_${w.face + 1}`]; if (c) w.skin.color.set(c); }
  });

  // blockers: círculos {x, z, r} do carrinho — o trabalhador espera se o próximo passo o aproximar
  // demais do carrinho (afastar-se é sempre permitido, para não travar quem está no caminho)
  const blocked = (w, x, z) => update.blockers.some(b => {
    const next = Math.hypot(b.x - x, b.z - z);
    return next < b.r + RADIUS + KEEP_CLEAR && next < Math.hypot(b.x - w.x, b.z - w.z);
  });
  const nearestBlocker = w => update.blockers.reduce((a, b) => (Math.hypot(b.x - w.x, b.z - w.z) < Math.hypot(a.x - w.x, a.z - w.z) ? b : a));
  function update(dt) {
    for (const w of workers) {
      let moving = false;
      if (w.pts.length > 1) {
        if (w.pause > 0) w.pause -= dt;
        else {
          const [tx, tz] = w.pts[w.i];
          const dx = tx - w.x, dz = tz - w.z, d = Math.hypot(dx, dz), step = WALK_SPEED * dt;
          if (w.asideT > 0) {                                   // dá passagem: afasta-se do carrinho
            w.asideT -= dt;
            const b = nearestBlocker(w);
            const ax = w.x - b.x, az = w.z - b.z, al = Math.hypot(ax, az) || 1;
            w.x += ax / al * step * 0.8; w.z += az / al * step * 0.8;
            w.heading = Math.atan2(ax, az); moving = true;
          } else if (d > 1e-3 && blocked(w, w.x + dx / d * LOOK_AHEAD, w.z + dz / d * LOOK_AHEAD)) {
            w.waitT += dt;                                        // aguarda o carrinho passar
            if (w.waitT > YIELD_AFTER) { w.waitT = 0; w.asideT = STEP_ASIDE; }
          } else if (d <= step) {
            w.waitT = 0;
            w.x = tx; w.z = tz;
            if (w.i + w.dir < 0 || w.i + w.dir >= w.pts.length) { w.dir *= -1; w.pause = 1.5 + Math.random() * 2.5; }
            w.i += w.dir;
          } else {
            w.waitT = 0;
            w.x += dx / d * step; w.z += dz / d * step;
            w.heading = Math.atan2(dx, dz); moving = true;
          }
        }
      }
      w.phase += dt * (moving ? 7 : 0);
      const swing = moving ? Math.sin(w.phase) * 0.55 : 0;
      w.legs[0].rotation.x = swing; w.legs[1].rotation.x = -swing;
      w.arms[0].rotation.x = -swing * 0.8; w.arms[1].rotation.x = swing * 0.8;
      w.g.position.set(w.x, moving ? Math.abs(Math.cos(w.phase)) * 0.03 : 0, w.z);
      w.g.rotation.y += Math.atan2(Math.sin(w.heading - w.g.rotation.y), Math.cos(w.heading - w.g.rotation.y)) * Math.min(1, dt * 8);
    }
  }
  update.blockers = [];
  return { workers, colliders: workers, update };
}
