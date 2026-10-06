import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import {
  paintTexture, tireTexture, sidewallDecal, diamondPlateTexture, ribbedPlasticTexture,
  brushedMetalTexture, hazardTexture, labelTexture, repeatTex,
} from './textures.js';

// Modelo procedural detalhado do Terra-Botics Axle-E (referência: prancha + vídeo).
// Retorno usado por index.html e game.html — manter os campos ao trocar por um GLB.

// ---------- dimensões (m) ----------
const CX = 0.7, CZ = 1.0, DECK_Y = 0.78, SKID_Y = 0.36;
const WHEEL_X = 0.94, WHEEL_Z = 0.95, WHEEL_R = 0.42, TIRE_HW = 0.17;
const BY = 0.96, BW = 0.8, BL = 1.9, BH = 0.62, TILT = 0.3, T = 0.04;
// Frente: tudo abaixo do arco varrido pela tampa basculante aberta (~0,72 m).
const BAR_Y = 0.66, SENSOR_Y = 0.46, BUMPER_Y = 0.29;
const FLARE = BH * Math.sin(TILT), BTOP = BY + BH * Math.cos(TILT), TW = BW / 2 + FLARE;

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);

function makeMaterials() {
  const yellow = paintTexture(0xe0a21b, { seed: 3, grime: 0.22, scratches: 70, chips: 8 });
  const steel = paintTexture(0x3a3d41, { seed: 11, grime: 0.35, scratches: 60, chips: 12, rough: [0.4, 0.62], freq: 7 });
  const orange = paintTexture(0xe9791a, { seed: 21, grime: 0.25, scratches: 40, chips: 10 });
  const tire = tireTexture();
  const plate = diamondPlateTexture();
  const ribbed = ribbedPlasticTexture();
  const brushed = brushedMetalTexture();
  const pbr = (t, extra) => new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, bumpScale: 1.2, ...t, ...extra });
  return {
    yellow: pbr(repeatTex(yellow, 1.4), { metalness: 0.2, side: THREE.DoubleSide, bumpScale: 0.5 }),
    steel: pbr(repeatTex(steel, 1, 2), { metalness: 0.45 }),
    steelBox: pbr(repeatTex(steel, 2, 1), { metalness: 0.45 }),
    orange: pbr(repeatTex(orange, 1, 2), { metalness: 0.25 }),
    orangePlate: pbr(repeatTex(orange, 3), { metalness: 0.25 }),
    tire: new THREE.MeshStandardMaterial({ ...tire, roughness: 1, bumpScale: 3, side: THREE.DoubleSide }),
    lug: new THREE.MeshStandardMaterial({ color: 0x232323, roughness: 0.92, bumpMap: tire.bumpMap, bumpScale: 1 }),
    plate: pbr(repeatTex(plate, 6, 8), { metalness: 0.5, color: 0x55585c, envMapIntensity: 0.6 }),
    ribbed: pbr(repeatTex(ribbed, 1), { metalness: 0.05 }),
    brushed: new THREE.MeshStandardMaterial({ map: brushed, roughness: 0.32, metalness: 0.95 }),
    rim: pbr(repeatTex(steel, 2), { metalness: 0.55, color: 0x777777 }),
    dark: new THREE.MeshStandardMaterial({ color: 0x18191b, roughness: 0.55, metalness: 0.35 }),
    hose: new THREE.MeshStandardMaterial({ color: 0x0d0d0e, roughness: 0.65 }),
    hv: new THREE.MeshStandardMaterial({ color: 0xff6a10, roughness: 0.5 }),
    red: new THREE.MeshStandardMaterial({ color: 0xb3201b, roughness: 0.45 }),
    chrome: new THREE.MeshStandardMaterial({ color: 0xdfe3e6, roughness: 0.12, metalness: 1 }),
    glass: new THREE.MeshStandardMaterial({ color: 0x06090c, roughness: 0.05, metalness: 0.9 }),
    lens: new THREE.MeshStandardMaterial({ color: 0x0b1a2a, roughness: 0.02, metalness: 1, emissive: 0x0a2a44, emissiveIntensity: 0.4 }),
    ledWhite: new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff4e0, emissiveIntensity: 2.2 }),
    ledRed: new THREE.MeshStandardMaterial({ color: 0xff2a1a, emissive: 0xff1a0a, emissiveIntensity: 1.6 }),
    ledGreen: new THREE.MeshStandardMaterial({ color: 0x2bff6b, emissive: 0x2bff6b, emissiveIntensity: 2 }),
    hazard: new THREE.MeshStandardMaterial({ map: hazardTexture(), roughness: 0.6, metalness: 0.2 }),
  };
}

const decal = (map, extra = {}) => new THREE.MeshStandardMaterial({
  map, transparent: true, roughness: 0.6, metalness: 0.1, polygonOffset: true, polygonOffsetFactor: -2, depthWrite: false, ...extra,
});

export function buildCart() {
  const M = makeMaterials();
  const root = new THREE.Group();
  const wheels = [];

  // ---------- helpers ----------
  function add(mesh, parent = root) {
    mesh.castShadow = true; mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }
  function tube(a, b, r, mat = M.steel, parent = root, seg = 16) {
    const dir = b.clone().sub(a), len = dir.length();
    const m = add(new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), mat), parent);
    m.position.copy(a).add(b).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(UP, dir.normalize());
    return m;
  }
  function tubePath(pts, r, mat = M.steel, { closed = false, parent = root } = {}) {
    const n = pts.length;
    for (let i = 0; i < (closed ? n : n - 1); i++) tube(pts[i], pts[(i + 1) % n], r, mat, parent);
    pts.forEach(p => add(new THREE.Mesh(new THREE.SphereGeometry(r * 1.06, 16, 12), mat), parent).position.copy(p));
  }
  function box(w, h, d, mat, x, y, z, parent = root, radius = 0) {
    const geo = radius ? new RoundedBoxGeometry(w, h, d, 3, radius) : new THREE.BoxGeometry(w, h, d);
    const m = add(new THREE.Mesh(geo, mat), parent);
    m.position.set(x, y, z);
    return m;
  }
  function cyl(r, len, mat, pos, axis = 'x', parent = root, seg = 24) {
    const m = add(new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), mat), parent);
    if (axis === 'x') m.rotation.z = Math.PI / 2;
    if (axis === 'z') m.rotation.x = Math.PI / 2;
    m.position.copy(pos);
    return m;
  }
  function plane(w, h, mat, pos, rotY = 0, parent = root) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
    m.position.copy(pos); m.rotation.y = rotY;
    parent.add(m);
    return m;
  }
  // Superfície feita de quadriláteros com UV planar em metros (caçamba).
  function quadGeometry(quads, uvScale = 1) {
    const pos = [], uv = [];
    for (const q of quads) {
      const e1 = q[1].clone().sub(q[0]).normalize();
      const n = q[3].clone().sub(q[0]).cross(e1).normalize();
      const e2 = e1.clone().cross(n);
      const uvOf = p => { const d = p.clone().sub(q[0]); return [d.dot(e1) * uvScale, d.dot(e2) * uvScale]; };
      for (const i of [0, 1, 2, 0, 2, 3]) { pos.push(q[i].x, q[i].y, q[i].z); uv.push(...uvOf(q[i])); }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.computeVertexNormals();
    return g;
  }
  // Mola helicoidal ao longo de +Y, de 0 a len.
  function springGeometry(radius, len, turns, wire) {
    class Helix extends THREE.Curve {
      getPoint(t, target = new THREE.Vector3()) {
        const a = t * turns * Math.PI * 2;
        return target.set(Math.cos(a) * radius, t * len, Math.sin(a) * radius);
      }
    }
    return new THREE.TubeGeometry(new Helix(), turns * 24, wire, 8, false);
  }
  function orientedMesh(geo, mat, a, b, parent = root) {
    const m = add(new THREE.Mesh(geo, mat), parent);
    m.position.copy(a);
    m.quaternion.setFromUnitVectors(UP, b.clone().sub(a).normalize());
    return m;
  }

  // ---------- rodas ----------
  const tireDecal = decal(sidewallDecal('TERRA-GRIP  AT 25x10-12  •  OFF-ROAD 4X4  •  TUBELESS'));
  function makeWheel(sx) {
    const g = new THREE.Group();
    const HW = TIRE_HW, RO = 0.40, RI = 0.255;
    const prof = [
      [RI, -HW + 0.02], [RI + 0.02, -HW], [0.31, -HW - 0.006], [0.355, -HW], [0.385, -HW + 0.025],
      [RO, -HW + 0.065], [RO + 0.005, -0.04], [RO + 0.006, 0], [RO + 0.005, 0.04], [RO, HW - 0.065],
      [0.385, HW - 0.025], [0.355, HW], [0.31, HW + 0.006], [RI + 0.02, HW], [RI, HW - 0.02],
    ].map(([r, y]) => new THREE.Vector2(r, y));
    const tireGeo = new THREE.LatheGeometry(prof, 72);
    tireGeo.rotateZ(-Math.PI / 2);
    add(new THREE.Mesh(tireGeo, M.tire), g);

    // garras em V (silhueta off-road)
    const LUGS = 20;
    for (let i = 0; i < LUGS; i++) {
      const pivot = new THREE.Group();
      pivot.rotation.x = (i / LUGS) * Math.PI * 2;
      for (const s of [-1, 1]) {
        const lug = add(new THREE.Mesh(new RoundedBoxGeometry(0.15, 0.045, 0.09, 2, 0.012), M.lug), pivot);
        lug.position.set(s * 0.08, 0.41, s * 0.02);
        lug.rotation.y = s * 0.5;
      }
      g.add(pivot);
    }
    // inscrição na lateral
    for (const side of [-1, 1]) {
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.262, 0.395, 72), tireDecal);
      ring.rotation.y = side * Math.PI / 2;
      ring.position.x = side * (HW + 0.009);
      g.add(ring);
    }
    // aro: tambor + disco com furos + cubo
    const barrel = add(new THREE.Mesh(new THREE.CylinderGeometry(0.256, 0.256, 0.3, 40, 1, true), M.rim), g);
    barrel.rotation.z = Math.PI / 2; barrel.material.side = THREE.DoubleSide;
    cyl(0.25, 0.022, M.rim, V(sx * 0.06, 0, 0), 'x', g, 40);
    cyl(0.236, 0.02, M.dark, V(sx * 0.11, 0, 0), 'x', g, 40).scale.set(1, 0.2, 1);
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const hole = cyl(0.038, 0.026, M.hose, V(sx * 0.062, Math.cos(a) * 0.165, Math.sin(a) * 0.165), 'x', g, 20);
      hole.castShadow = false;
    }
    cyl(0.1, 0.07, M.rim, V(sx * 0.085, 0, 0), 'x', g, 32);
    cyl(0.07, 0.09, M.brushed, V(sx * 0.1, 0, 0), 'x', g, 32);
    cyl(0.032, 0.1, M.chrome, V(sx * 0.12, 0, 0), 'x', g, 20);
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2;
      cyl(0.011, 0.11, M.chrome, V(sx * 0.1, Math.cos(a) * 0.052, Math.sin(a) * 0.052), 'x', g, 6);
    }
    return g;
  }

  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const w = makeWheel(sx);
    const pivot = new THREE.Group();
    pivot.position.set(sx * WHEEL_X, WHEEL_R, sz * WHEEL_Z);
    pivot.add(w);
    root.add(pivot);
    wheels.push({ pivot, spin: w, sz });
  }

  // ---------- suspensão e transmissão ----------
  const springGeo = springGeometry(0.045, 0.3, 7, 0.009);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const z = sz * WHEEL_Z, hubX = sx * (WHEEL_X - TIRE_HW - 0.06);
    box(0.06, 0.3, 0.09, M.steelBox, hubX, WHEEL_R, z, root, 0.015);                 // manga de eixo
    for (const dz of [-0.16, 0.16]) {
      tube(V(sx * 0.44, 0.33, z + dz), V(hubX, 0.31, z), 0.022, M.steel);            // braço inferior
      tube(V(sx * 0.48, 0.6, z + dz * 0.8), V(hubX, 0.54, z), 0.019, M.steel);       // braço superior
    }
    const lo = V(hubX - sx * 0.02, 0.36, z - sz * 0.09), hi = V(sx * 0.58, 0.95, z - sz * 0.12);
    const len = lo.distanceTo(hi);
    orientedMesh(new THREE.CylinderGeometry(0.03, 0.03, len * 0.55, 16).translate(0, len * 0.275, 0), M.dark, hi, lo);
    orientedMesh(new THREE.CylinderGeometry(0.012, 0.012, len, 10).translate(0, len / 2, 0), M.chrome, lo, hi);
    orientedMesh(springGeo, M.orange, lo.clone().lerp(hi, 0.18), hi);
    box(0.08, 0.05, 0.08, M.steelBox, hi.x, hi.y + 0.02, hi.z);
    // semieixo com coifas
    tube(V(sx * 0.16, WHEEL_R, z), V(hubX, WHEEL_R, z), 0.024, M.dark);
    for (const t of [0.2, 0.85]) {
      const p = V(sx * 0.16, WHEEL_R, z).lerp(V(hubX, WHEEL_R, z), t);
      for (let k = 0; k < 4; k++) cyl(0.04 - k * 0.005, 0.02, M.hose, V(p.x + sx * k * 0.018, p.y, p.z), 'x');
    }
  }
  for (const sz of [-1, 1]) {
    box(0.3, 0.2, 0.22, M.steelBox, 0, WHEEL_R, sz * WHEEL_Z, root, 0.05);              // diferencial
    cyl(0.085, 0.06, M.brushed, V(0, WHEEL_R, sz * (WHEEL_Z - 0.13)), 'z');
  }

  // ---------- chassi ----------
  for (const sx of [-1, 1]) box(0.07, 0.13, 2 * CZ + 0.14, M.steelBox, sx * CX, DECK_Y, 0, root, 0.012);
  for (const sz of [-1, 1]) box(2 * CX + 0.07, 0.13, 0.07, M.steelBox, 0, DECK_Y, sz * CZ, root, 0.012);
  for (const z of [-0.5, 0, 0.5]) box(2 * CX, 0.05, 0.05, M.steelBox, 0, DECK_Y - 0.02, z);
  tubePath([V(-0.5, SKID_Y, -0.9), V(0.5, SKID_Y, -0.9), V(0.5, SKID_Y, 0.9), V(-0.5, SKID_Y, 0.9)], 0.035, M.steel, { closed: true });
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    tube(V(sx * 0.5, SKID_Y, sz * 0.9), V(sx * CX, DECK_Y - 0.06, sz * CZ), 0.03, M.steel);
    tube(V(sx * 0.5, SKID_Y, sz * 0.3), V(sx * CX, DECK_Y - 0.06, sz * 0.3), 0.026, M.steel);
  }
  box(1.0, 0.025, 1.8, M.plate, 0, SKID_Y - 0.03, 0);                                    // proteção inferior
  box(2 * CX - 0.05, 0.02, 2 * CZ - 0.05, M.plate, 0, DECK_Y + 0.07, 0);                // piso xadrez

  // placas TERRA-BOTICS AXLE-E nas longarinas
  const beamLabel = decal(labelTexture('TERRA-BOTICS            AXLE-E            CHASSI 4X4', 2048, 96, { font: 'bold 54px Arial', bg: null, fg: '#d9d4c8' }));
  for (const sx of [-1, 1]) plane(1.9, 0.09, beamLabel, V(sx * (CX + 0.037), DECK_Y, 0), sx * Math.PI / 2);
  // lanternas traseiras
  for (const sx of [-1, 1]) box(0.12, 0.05, 0.02, M.ledRed, sx * 0.5, DECK_Y, -CZ - 0.045, root, 0.008);

  // ---------- acessórios (sem roll cage: caçamba livre) ----------
  // placa TERRA-BOTICS laranja na longarina traseira
  box(0.5, 0.09, 0.02, M.orangePlate, 0, DECK_Y, -CZ - 0.045, root, 0.008);
  plane(0.46, 0.07, decal(labelTexture('TERRA-BOTICS', 512, 80, { font: 'bold 52px Arial', bg: null, fg: '#1a1a1a' })), V(0, DECK_Y, -CZ - 0.056), Math.PI);
  // faróis de trabalho nas pontas da barra SYS OK
  for (const s of [-1, 1]) {
    box(0.14, 0.08, 0.07, M.dark, s * 0.64, BAR_Y, CZ + 0.1, root, 0.015);
    box(0.11, 0.05, 0.01, M.ledWhite, s * 0.64, BAR_Y, CZ + 0.136);
  }
  // LiDAR giratório no canto dianteiro do chassi (fora da largura da tampa)
  const lidar = new THREE.Group();
  lidar.position.set(0.6, DECK_Y + 0.085, CZ - 0.02);
  root.add(lidar);
  cyl(0.075, 0.035, M.dark, V(0, 0, 0), 'y', lidar, 32);
  cyl(0.068, 0.06, M.glass, V(0, 0.047, 0), 'y', lidar, 32);
  cyl(0.072, 0.02, M.dark, V(0, 0.087, 0), 'y', lidar, 32);
  box(0.02, 0.03, 0.01, M.ledGreen, 0, 0.047, 0.068, lidar);
  // antena + GPS no canto traseiro do chassi
  box(0.08, 0.04, 0.08, M.steelBox, 0.6, DECK_Y + 0.085, -CZ + 0.06, root, 0.01);
  tube(V(0.6, DECK_Y + 0.1, -CZ + 0.06), V(0.6, DECK_Y + 0.75, -CZ + 0.06), 0.006, M.dark);
  add(new THREE.Mesh(new THREE.SphereGeometry(0.014, 10, 8), M.dark)).position.set(0.6, DECK_Y + 0.75, -CZ + 0.06);
  cyl(0.05, 0.025, M.dark, V(-0.6, DECK_Y + 0.08, -CZ + 0.06), 'y', root, 24);

  // ---------- caçamba ----------
  const bucket = new THREE.Group();
  root.add(bucket);
  const bl = BL / 2;
  const shell = quadGeometry([
    [V(-BW / 2, BY, bl), V(BW / 2, BY, bl), V(BW / 2, BY, -bl), V(-BW / 2, BY, -bl)],                          // fundo
    [V(BW / 2, BY, bl), V(TW, BTOP, bl + FLARE), V(TW, BTOP, -bl - FLARE), V(BW / 2, BY, -bl)],                 // lateral +x
    [V(-BW / 2, BY, -bl), V(-TW, BTOP, -bl - FLARE), V(-TW, BTOP, bl + FLARE), V(-BW / 2, BY, bl)],             // lateral -x
    [V(BW / 2, BY, -bl), V(TW, BTOP, -bl - FLARE), V(-TW, BTOP, -bl - FLARE), V(-BW / 2, BY, -bl)],             // traseira
  ], 0.9);
  add(new THREE.Mesh(shell, M.yellow), bucket);
  // borda enrolada (3 lados; o 4º fica na tampa)
  tubePath([V(TW, BTOP, bl + FLARE), V(TW, BTOP, -bl - FLARE), V(-TW, BTOP, -bl - FLARE), V(-TW, BTOP, bl + FLARE)], 0.026, M.yellow, { parent: bucket });
  // nervuras externas nas laterais
  for (const s of [-1, 1]) {
    const side = new THREE.Group();
    side.position.set(s * BW / 2, BY, 0); side.rotation.z = -s * TILT;
    bucket.add(side);
    for (const h of [0.22, 0.44]) box(0.025, 0.035, BL + 2 * h * Math.tan(TILT) - 0.04, M.yellow, s * 0.014, h, 0, side, 0.01);
    for (const z of [-0.6, 0, 0.6]) box(0.022, BH - 0.06, 0.04, M.yellow, s * 0.012, BH / 2, z, side, 0.008);
  }
  // logo na traseira da caçamba
  const back = new THREE.Group();
  back.position.set(0, BY, -bl); back.rotation.x = -TILT;
  bucket.add(back);
  plane(0.62, 0.12, decal(labelTexture('TERRA-BOTICS', 768, 140, { font: 'bold 88px Arial', bg: null, fg: '#1d1a15' })), V(0, BH * 0.55, -0.004), Math.PI, back);
  // subchassi da caçamba
  for (const s of [-1, 1]) box(0.05, 0.06, BL, M.steelBox, s * 0.25, BY - 0.035, 0, bucket, 0.01);
  for (const z of [-0.7, 0, 0.7]) box(0.6, 0.04, 0.05, M.steelBox, 0, BY - 0.03, z, bucket);
  // tampa frontal basculante (dobradiça na base)
  const frontGate = new THREE.Group();
  frontGate.position.set(0, BY, bl); frontGate.rotation.x = TILT;
  bucket.add(frontGate);
  add(new THREE.Mesh(quadGeometry([[V(-BW / 2, 0, 0), V(BW / 2, 0, 0), V(TW, BH, 0), V(-TW, BH, 0)]], 0.9), M.yellow), frontGate);
  tube(V(-TW, BH, 0), V(TW, BH, 0), 0.026, M.yellow, frontGate);
  box(TW * 2 - 0.1, 0.035, 0.025, M.yellow, 0, BH * 0.45, 0.013, frontGate, 0.01);
  for (const s of [-1, 1]) cyl(0.02, 0.08, M.steel, V(s * 0.3, 0, 0), 'x', frontGate, 12);
  // dobradiças e cilindro hidráulico
  for (const s of [-1, 1]) box(0.05, 0.1, 0.08, M.steelBox, s * 0.3, BY - 0.07, bl, root, 0.01);
  const ramA = V(0, DECK_Y + 0.12, -0.05), ramB = V(0, BY - 0.07, -0.6);
  const ramBarrel = add(new THREE.Mesh(new THREE.CylinderGeometry(0.042, 0.042, 0.34, 20).translate(0, 0.17, 0), M.steel));
  const ramRod = add(new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1, 14).translate(0, 0.5, 0), M.chrome));
  box(0.09, 0.05, 0.06, M.steelBox, ramA.x, ramA.y - 0.02, ramA.z);
  const tmpB = new THREE.Vector3(), tmpD = new THREE.Vector3();
  function updateRam() {
    root.updateMatrixWorld(true);
    tmpB.copy(ramB); bucket.localToWorld(tmpB); root.worldToLocal(tmpB);
    tmpD.copy(tmpB).sub(ramA);
    const len = tmpD.length(); tmpD.normalize();
    ramBarrel.position.copy(ramA); ramBarrel.quaternion.setFromUnitVectors(UP, tmpD);
    ramRod.position.copy(ramA).addScaledVector(tmpD, 0.3); ramRod.quaternion.copy(ramBarrel.quaternion);
    ramRod.scale.y = Math.max(0.05, len - 0.3);
  }

  // ---------- baterias POWER PACK 70V ----------
  const batLabel = decal(labelTexture('Power Pack\n70V', 256, 256, { font: 'bold 44px Arial', bg: '#d9d4c6', fg: '#141414', border: '#141414', icon: 'bolt' }), { transparent: false, depthWrite: true });
  for (const s of [-1, 1]) for (const z of [-0.2, -0.68]) {
    box(0.3, 0.46, 0.42, M.ribbed, s * 0.5, 0.57, z, root, 0.025);
    plane(0.27, 0.27, batLabel, V(s * 0.652, 0.6, z), s * Math.PI / 2);
    box(0.32, 0.03, 0.04, M.steelBox, s * 0.5, 0.81, z, root, 0.008);                  // cinta
    cyl(0.02, 0.04, M.red, V(s * 0.5 - 0.07, 0.82, z + 0.12), 'y', root, 12);
    cyl(0.02, 0.04, M.dark, V(s * 0.5 + 0.07, 0.82, z + 0.12), 'y', root, 12);
  }
  for (const s of [-1, 1]) box(0.36, 0.03, 1.0, M.steelBox, s * 0.5, 0.335, -0.44);      // bandeja

  // ---------- inversor + motor elétrico ----------
  box(0.32, 0.14, 0.36, M.steelBox, 0, 0.6, -0.45, root, 0.02);
  for (let i = 0; i < 8; i++) box(0.3, 0.04, 0.008, M.brushed, 0, 0.69, -0.6 + i * 0.043);
  const motor = new THREE.Group();
  motor.position.set(0, 0.56, 0.32);
  root.add(motor);
  cyl(0.16, 0.42, M.steel, V(0, 0, 0), 'z', motor, 32);
  for (let i = 0; i < 11; i++) cyl(0.178, 0.012, M.steel, V(0, 0, -0.19 + i * 0.038), 'z', motor, 32);
  cyl(0.17, 0.05, M.brushed, V(0, 0, 0.235), 'z', motor, 32);
  cyl(0.17, 0.05, M.brushed, V(0, 0, -0.235), 'z', motor, 32);
  box(0.26, 0.24, 0.16, M.steelBox, 0, -0.02, 0.36, motor, 0.03);                          // redutor
  box(0.14, 0.09, 0.12, M.dark, 0.12, 0.14, -0.05, motor, 0.015);                          // caixa de ligação
  tube(V(0, WHEEL_R, 0.8), V(0, 0.54, 0.76), 0.03, M.dark);                                 // cardã dianteiro
  tube(V(0, 0.52, 0.06), V(0, WHEEL_R, -0.82), 0.03, M.dark);                              // cardã traseiro
  // cabos de alta tensão (laranja) e mangueiras
  for (const s of [-1, 1]) {
    tubePath([V(s * 0.43, 0.84, -0.08), V(s * 0.3, 0.8, -0.2), V(s * 0.16, 0.66, -0.3)], 0.014, M.hv);
    tubePath([V(s * 0.08, 0.66, -0.27), V(s * 0.1, 0.72, 0), V(s * 0.12, 0.72, 0.27)], 0.016, M.hv);
    tubePath([V(s * 0.2, 0.62, 0.55), V(s * 0.38, 0.55, 0.7), V(s * 0.45, 0.45, 0.88)], 0.02, M.hose);
  }

  // ---------- frente: para-choque, sensor e barra SYS OK ----------
  box(1.5, 0.1, 0.08, M.hazard, 0, BUMPER_Y, CZ + 0.14, root, 0.015);
  for (const s of [-1, 1]) tube(V(s * 0.6, BUMPER_Y, CZ + 0.1), V(s * 0.6, DECK_Y - 0.04, CZ), 0.025);
  const sensor = new THREE.Group();
  sensor.position.set(0, SENSOR_Y, 1.15);
  root.add(sensor);
  box(0.54, 0.22, 0.14, M.dark, 0, 0, 0, sensor, 0.035);
  box(0.46, 0.13, 0.01, M.glass, 0, 0.005, 0.071, sensor, 0.004);
  for (const x of [-0.15, 0.11]) {
    cyl(0.046, 0.02, M.lens, V(x, 0.005, 0.078), 'z', sensor, 28);
    add(new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.007, 8, 28), M.brushed), sensor).position.set(x, 0.005, 0.083);
  }
  cyl(0.018, 0.02, M.lens, V(-0.02, 0.005, 0.078), 'z', sensor, 16);
  cyl(0.012, 0.02, M.ledGreen, V(0.21, 0.04, 0.078), 'z', sensor, 12);
  box(0.58, 0.03, 0.17, M.steelBox, 0, 0.125, 0, sensor, 0.008);
  plane(0.12, 0.07, decal(labelTexture('AXLE-E\nAUTONOMY', 256, 150, { font: 'bold 40px Arial', bg: '#e0a21b', fg: '#141414' }), { transparent: false, depthWrite: true }), V(0.2, -0.065, 0.072), 0, sensor);

  box(1.08, 0.12, 0.06, M.dark, 0, BAR_Y, CZ + 0.1, root, 0.02);
  const sysTex = labelTexture('SYS OK', 1024, 96, { font: 'bold 60px Arial', bg: '#18c24f', fg: '#ffffff' });
  const STATUS = { ok: ['SYS OK', '#18c24f'], auto: ['AUTO', '#1f8fff'], warn: ['ALERTA', '#f2a900'], brake: ['FREIO', '#e0281b'] };
  let statusNow = 'ok';
  function setStatus(kind) {
    if (kind === statusNow || !STATUS[kind]) return;
    statusNow = kind;
    const [text, color] = STATUS[kind], c = sysTex.image, g = c.getContext('2d');
    g.fillStyle = color; g.fillRect(0, 0, c.width, c.height);
    g.fillStyle = '#ffffff'; g.font = 'bold 60px Arial'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(text, c.width / 2, c.height / 2);
    sysTex.needsUpdate = true;
  }
  plane(0.82, 0.07, new THREE.MeshStandardMaterial({ map: sysTex, emissive: 0xffffff, emissiveMap: sysTex, emissiveIntensity: 0.55 }), V(0, BAR_Y, CZ + 0.131));
  const sideTag = new THREE.MeshStandardMaterial({ map: labelTexture('TERRA-BOTICS\nAUTONOMY 4X4', 256, 110, { font: 'bold 34px Arial', bg: '#e0a21b', fg: '#141414' }), roughness: 0.6 });
  for (const s of [-1, 1]) plane(0.1, 0.055, sideTag, V(s * 0.47, BAR_Y, CZ + 0.132));

  // ---------- alças traseiras ----------
  const hexBracket = (() => {
    const shape = new THREE.Shape([[-0.97, 0.85], [-0.99, 1.0], [-1.33, 1.2], [-1.44, 1.13], [-1.26, 0.85]].map(([z, y]) => new THREE.Vector2(z, y)));
    for (const [cz, cy] of [[-1.08, 0.93], [-1.2, 0.95], [-1.28, 1.08]]) {
      const hole = new THREE.Path();
      for (let k = 0; k < 6; k++) {
        const a = k / 6 * Math.PI * 2, px = cz + Math.cos(a) * 0.045, py = cy + Math.sin(a) * 0.045;
        if (k === 0) hole.moveTo(px, py); else hole.lineTo(px, py);
      }
      shape.holes.push(hole);
    }
    const g = new THREE.ExtrudeGeometry(shape, { depth: 0.016, bevelEnabled: true, bevelSize: 0.004, bevelThickness: 0.004, bevelSegments: 2 });
    g.rotateY(-Math.PI / 2);
    return g;
  })();
  for (const s of [-1, 1]) {
    const x = s * 0.52;
    tubePath([V(x, 0.84, -CZ), V(x, 1.18, -1.4), V(x, 1.3, -1.78)], 0.035);
    tube(V(x, 1.3, -1.78), V(x, 1.335, -2.06), 0.048, M.orange);
    for (let k = 0; k < 6; k++) {
      const p = V(x, 1.3, -1.78).lerp(V(x, 1.335, -2.06), (k + 0.5) / 6);
      add(new THREE.Mesh(new THREE.TorusGeometry(0.048, 0.006, 6, 20), M.orange)).position.copy(p).setZ(p.z);
    }
    add(new THREE.Mesh(new THREE.SphereGeometry(0.05, 14, 10), M.dark)).position.set(x, 1.336, -2.065);
    const br = add(new THREE.Mesh(hexBracket, M.orangePlate));
    br.position.x = x + s * 0.03 + 0.008;
  }
  tube(V(-0.52, 1.18, -1.4), V(0.52, 1.18, -1.4), 0.03);

  // ---------- painel do operador (display + emergência) ----------
  const [dispCanvas, dispCtx] = (() => { const c = document.createElement('canvas'); c.width = 320; c.height = 192; return [c, c.getContext('2d')]; })();
  const dispTex = new THREE.CanvasTexture(dispCanvas);
  dispTex.colorSpace = THREE.SRGBColorSpace;
  function setDisplay({ speed = 0, load = 0, dump = 0, battery = 87, mode = 'AUTO' } = {}) {
    const g = dispCtx;
    g.fillStyle = '#071a0f'; g.fillRect(0, 0, 320, 192);
    g.fillStyle = '#2bff6b'; g.font = 'bold 26px Consolas, monospace'; g.textBaseline = 'top';
    g.fillText(`AXLE-E   ${mode}`, 14, 10);
    g.font = 'bold 22px Consolas, monospace';
    g.fillText(`VEL  ${String(Math.round(speed)).padStart(3)} km/h`, 14, 52);
    g.fillText(`PESO ${String(Math.round(load)).padStart(4)} kg`, 14, 84);
    g.fillText(`BASC ${String(Math.round(dump)).padStart(3)}°`, 14, 116);
    g.strokeStyle = '#2bff6b'; g.lineWidth = 3; g.strokeRect(14, 152, 200, 26);
    g.fillStyle = battery > 20 ? '#2bff6b' : '#ff5a3a'; g.fillRect(18, 156, 192 * battery / 100, 18);
    g.fillRect(216, 159, 6, 12);
    g.fillStyle = '#2bff6b'; g.fillText(`${Math.round(battery)}%`, 234, 154);
    dispTex.needsUpdate = true;
  }
  setDisplay();
  const console_ = new THREE.Group();
  console_.position.set(0, 1.27, -1.43);
  console_.rotation.set(0.6, Math.PI, 0);
  root.add(console_);
  box(0.4, 0.24, 0.06, M.dark, 0, 0, 0, console_, 0.02);
  box(0.25, 0.15, 0.008, M.glass, -0.055, 0.01, 0.031, console_, 0.003);
  plane(0.23, 0.138, new THREE.MeshStandardMaterial({ map: dispTex, emissive: 0xffffff, emissiveMap: dispTex, emissiveIntensity: 0.9, roughness: 0.3 }), V(-0.055, 0.01, 0.036), 0, console_);
  cyl(0.04, 0.012, new THREE.MeshStandardMaterial({ color: 0xf2c200, roughness: 0.5 }), V(0.135, 0.035, 0.036), 'z', console_, 24);
  cyl(0.026, 0.03, M.red, V(0.135, 0.035, 0.055), 'z', console_, 24);
  cyl(0.032, 0.014, M.red, V(0.135, 0.035, 0.075), 'z', console_, 24);
  cyl(0.014, 0.02, M.chrome, V(0.135, -0.07, 0.04), 'z', console_, 16);
  box(0.05, 0.12, 0.05, M.steelBox, 0, 1.2, -1.41);                                         // suporte do painel

  // ---------- engates, recarga, refletores, parafusos ----------
  box(0.1, 0.16, 0.06, M.steelBox, 0, DECK_Y - 0.12, -CZ - 0.04, root, 0.01);
  box(0.07, 0.07, 0.22, M.steelBox, 0, DECK_Y - 0.2, -CZ - 0.12, root, 0.008);             // receptor do engate
  cyl(0.012, 0.12, M.chrome, V(0, DECK_Y - 0.2, -CZ - 0.18), 'x', root, 12);
  for (const s of [-1, 1]) {
    const hook = add(new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.011, 8, 20, Math.PI * 1.3), M.hv));
    hook.position.set(s * 0.45, BUMPER_Y - 0.08, CZ + 0.2); hook.rotation.set(0, Math.PI / 2, -Math.PI * 0.15);
    box(0.04, 0.05, 0.05, M.steelBox, s * 0.45, BUMPER_Y - 0.05, CZ + 0.17);
  }
  box(0.12, 0.08, 0.03, M.dark, -0.3, DECK_Y, -CZ - 0.05, root, 0.01);                      // tomada de recarga
  cyl(0.025, 0.02, M.hv, V(-0.3, DECK_Y, -CZ - 0.07), 'z', root, 16);
  const reflector = new THREE.MeshStandardMaterial({ color: 0xff8a1a, roughness: 0.15, metalness: 0.2, emissive: 0x401800 });
  for (const s of [-1, 1]) for (const z of [-0.9, 0.9]) box(0.008, 0.05, 0.08, reflector, s * (CX + 0.04), DECK_Y, z, root);
  // mangueiras do cilindro hidráulico
  for (const dx of [-0.05, 0.05]) {
    tubePath([V(dx, DECK_Y + 0.12, -0.02), V(dx * 2, DECK_Y + 0.1, 0.12), V(dx * 3, 0.74, 0.22), V(0.12 + dx, 0.7, 0.27)], 0.011, M.hose);
  }
  // parafusos sextavados nas longarinas (instanciados)
  const boltGeo = new THREE.CylinderGeometry(0.011, 0.011, 0.012, 6).rotateZ(Math.PI / 2);
  const boltPos = [];
  for (const s of [-1, 1]) for (let z = -0.95; z <= 0.951; z += 0.19) for (const dy of [-0.045, 0.045]) boltPos.push([s * (CX + 0.037), DECK_Y + dy, z]);
  const bolts = new THREE.InstancedMesh(boltGeo, M.chrome, boltPos.length);
  boltPos.forEach(([x, y, z], i) => bolts.setMatrixAt(i, new THREE.Matrix4().makeTranslation(x, y, z)));
  bolts.castShadow = true;
  root.add(bolts);

  // ---------- faróis (luz real) ----------
  const headlights = [];
  for (const s of [-1, 1]) {
    const spot = new THREE.SpotLight(0xfff1dc, 14, 26, 0.5, 0.6, 1.4);
    spot.position.set(s * 0.64, BAR_Y, CZ + 0.15);
    spot.target.position.set(s * 0.9, 0, CZ + 7);
    root.add(spot, spot.target);
    headlights.push(spot);
  }
  function setLights(on) {
    headlights.forEach(l => { l.visible = on; });
    M.ledWhite.emissiveIntensity = on ? 2.2 : 0.05;
  }

  updateRam();
  function update(dt = 0) {
    lidar.rotation.y += dt * 9;
    updateRam();
  }

  return { root, bucket, wheels, frontGate, lidar, update, setDisplay, setLights, setStatus, BY, BW, BL, BH, TILT, T, WHEEL_R };
}
