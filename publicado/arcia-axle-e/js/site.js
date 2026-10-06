import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import {
  paintTexture, concreteTexture, corrugatedTexture, brickTexture, woodTexture, roadTexture,
  latticeTexture, netTexture, stripeTexture, labelTexture, repeatTex,
} from './textures.js';
import { ROUTE, LOAD_STOP, BAY, ZONE_CENTER, ZONE_HALF } from './autopilot.js';

// Cenário de obra: vias de terra, baia de carregamento, bota-fora, prédio em construção com
// andaime, grua, betoneira, contêineres, estoques de material, barreiras, sinalização e tapume.
// Retorna colisores estáticos (círculos) usados pelo sensor e pela colisão do carrinho.

export const WORLD = 38;
export const PILE = { x: -20, z: 17.5, r: 3.0 };
export const EXCAVATOR_POS = new THREE.Vector3(-14.5, 0, 16);

export function createSite(scene) {
  const colliders = [];
  const circle = (x, z, r) => colliders.push({ x, z, r });
  // retângulo (rotacionado) aproximado por círculos no perímetro
  function rect(cx, cz, w, d, rot = 0, r = 0.5) {
    const c = Math.cos(rot), s = Math.sin(rot), pts = [];
    const edge = (x0, z0, x1, z1) => {
      const n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, z1 - z0) / (r * 1.4)));
      for (let i = 0; i <= n; i++) pts.push([x0 + (x1 - x0) * i / n, z0 + (z1 - z0) * i / n]);
    };
    const hw = w / 2 - r * 0.6, hd = d / 2 - r * 0.6;
    edge(-hw, -hd, hw, -hd); edge(hw, -hd, hw, hd); edge(hw, hd, -hw, hd); edge(-hw, hd, -hw, -hd);
    for (const [x, z] of pts) circle(cx + x * c + z * s, cz - x * s + z * c, r);
  }

  // ---------- materiais ----------
  const pbr = (set, extra = {}) => new THREE.MeshStandardMaterial({ roughness: 1, ...set, ...extra });
  const conc = concreteTexture();
  const M = {
    concrete: pbr(repeatTex(conc, 3)),
    concreteSmall: pbr(repeatTex(conc, 1)),
    brick: pbr(repeatTex(brickTexture(), 4, 2)),
    wood: pbr(repeatTex(woodTexture(), 1)),
    road: pbr(roadTexture(), { polygonOffset: true, polygonOffsetFactor: -1 }),
    container: pbr(repeatTex(corrugatedTexture(0xe9ecef, { rust: 0.2 }), 3, 1), { metalness: 0.4 }),
    containerBlue: pbr(repeatTex(corrugatedTexture(0x1f5fa8, { seed: 113 }), 1), { metalness: 0.4 }),
    fence: pbr(repeatTex(corrugatedTexture(0xdfe3e6, { seed: 117, ribs: 12, rust: 0.25 }), 1), { metalness: 0.5, side: THREE.DoubleSide }),
    yellow: pbr(repeatTex(paintTexture(0xe8a317, { size: 256, seed: 91, grime: 0.3, chips: 10 }), 2), { metalness: 0.3 }),
    white: pbr(repeatTex(paintTexture(0xeeeeee, { size: 256, seed: 93, grime: 0.35, chips: 6 }), 1), { metalness: 0.2 }),
    steel: new THREE.MeshStandardMaterial({ color: 0x8c9299, roughness: 0.4, metalness: 0.8 }),
    dark: new THREE.MeshStandardMaterial({ color: 0x222326, roughness: 0.7, metalness: 0.4 }),
    rubber: new THREE.MeshStandardMaterial({ color: 0x151515, roughness: 0.95 }),
    glass: new THREE.MeshStandardMaterial({ color: 0x2b3d4a, roughness: 0.05, metalness: 0.85 }),
    green: new THREE.MeshStandardMaterial({ color: 0x1f7a3a, roughness: 0.7 }),
    lattice: new THREE.MeshStandardMaterial({ map: latticeTexture(), transparent: true, alphaTest: 0.4, side: THREE.DoubleSide, roughness: 0.5, metalness: 0.4 }),
    net: new THREE.MeshStandardMaterial({ map: netTexture(), transparent: true, side: THREE.DoubleSide, depthWrite: false, roughness: 0.9 }),
    lamp: new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff2d0, emissiveIntensity: 1.6 }),
    beacon: new THREE.MeshStandardMaterial({ color: 0xff2a1a, emissive: 0xff1a0a, emissiveIntensity: 2 }),
    reflector: new THREE.MeshStandardMaterial({ color: 0xff7a1a, emissive: 0x501c00, roughness: 0.2 }),
    gravel: new THREE.MeshStandardMaterial({ color: 0x77716a, roughness: 1, flatShading: true }),
    sand: new THREE.MeshStandardMaterial({ color: 0xc9a46a, roughness: 1, flatShading: true }),
    dirt: new THREE.MeshStandardMaterial({ color: 0x9a7c58, roughness: 1, flatShading: true }),
    leaves: new THREE.MeshStandardMaterial({ color: 0x4f7a3a, roughness: 0.9, flatShading: true }),
    trunk: new THREE.MeshStandardMaterial({ color: 0x5a4030, roughness: 0.9 }),
  };

  const add = (m, parent = scene) => { m.castShadow = true; m.receiveShadow = true; parent.add(m); return m; };
  const box = (w, h, d, mat, x, y, z, ry = 0, parent = scene) => {
    const m = add(new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat), parent);
    m.position.set(x, y, z); m.rotation.y = ry; return m;
  };
  const rbox = (w, h, d, mat, x, y, z, r = 0.05, parent = scene) => {
    const m = add(new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 2, r), mat), parent);
    m.position.set(x, y, z); return m;
  };
  const cylY = (r, h, mat, x, y, z, parent = scene, seg = 16) => {
    const m = add(new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat), parent);
    m.position.set(x, y, z); return m;
  };
  const instanced = (geo, mat, list) => {
    const im = new THREE.InstancedMesh(geo, mat, list.length);
    const o = new THREE.Object3D();
    list.forEach((t, i) => {
      o.position.set(t[0], t[1], t[2]); o.rotation.set(t[4] || 0, t[3] || 0, t[5] || 0); o.scale.set(1, 1, 1);
      o.updateMatrix(); im.setMatrixAt(i, o.matrix);
    });
    im.castShadow = im.receiveShadow = true;
    scene.add(im); return im;
  };
  const mound = (mat, x, z, sx, sy, sz, seed = 1) => {
    const g = new THREE.IcosahedronGeometry(1, 3), p = g.attributes.position;
    let s = seed * 9301;
    const rnd = () => (s = (s * 9301 + 49297) % 233280) / 233280;
    for (let i = 0; i < p.count; i++) {
      const n = 1 + (rnd() - 0.5) * 0.2;
      p.setXYZ(i, p.getX(i) * n * sx, Math.max(p.getY(i), -0.05) * n * sy, p.getZ(i) * n * sz);
    }
    g.computeVertexNormals();
    const m = add(new THREE.Mesh(g, mat)); m.position.set(x, 0, z); return m;
  };
  const decalPlane = (tex, w, h, x, y, z, ry = 0, rx = 0) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.8, polygonOffset: true, polygonOffsetFactor: -2, depthWrite: false }));
    m.position.set(x, y, z); m.rotation.set(rx, ry, 0); m.receiveShadow = true; scene.add(m); return m;
  };

  // ---------- terreno ----------
  const grass = new THREE.Mesh(new THREE.PlaneGeometry(260, 260), new THREE.MeshStandardMaterial({ color: 0x6f8a4e, roughness: 1 }));
  grass.rotation.x = -Math.PI / 2; grass.position.y = -0.02; grass.receiveShadow = true; scene.add(grass);
  const dirtTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const g = c.getContext('2d'); g.fillStyle = '#b79f78'; g.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 2600; i++) {
      const v = 120 + Math.random() * 90;
      g.fillStyle = `rgba(${v},${v * 0.82},${v * 0.58},${0.25 + Math.random() * 0.35})`;
      g.fillRect(Math.random() * 256, Math.random() * 256, 1 + Math.random() * 3, 1 + Math.random() * 3);
    }
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(36, 36);
    t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
  })();
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(WORLD * 2, WORLD * 2), new THREE.MeshStandardMaterial({ map: dirtTex, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

  // vias (faixas de terra batida seguindo a rota)
  function ribbon(path, width, y) {
    const pos = [], uv = [], idx = [];
    path.pts.forEach(([x, z], i) => {
      const a = path.pts[Math.max(0, i - 1)], b = path.pts[Math.min(path.pts.length - 1, i + 1)];
      const tx = b[0] - a[0], tz = b[1] - a[1], l = Math.hypot(tx, tz) || 1;
      const nx = -tz / l * width / 2, nz = tx / l * width / 2;
      pos.push(x + nx, y, z + nz, x - nx, y, z - nz);
      uv.push(0, path.s[i] / 5, 1, path.s[i] / 5);
      if (i) { const k = i * 2; idx.push(k - 2, k, k - 1, k - 1, k, k + 1); }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx); g.computeVertexNormals();
    const m = new THREE.Mesh(g, M.road); m.receiveShadow = true; scene.add(m);
  }
  M.road.map.wrapS = THREE.ClampToEdgeWrapping;
  ribbon(ROUTE.toLoad, 3.4, 0.015);
  ribbon(ROUTE.toDump, 3.4, 0.02);

  // baia de carregamento
  const bayTex = labelTexture('CARREGAMENTO', 512, 360, { font: 'bold 54px Arial', bg: 'rgba(242,194,0,0.18)', fg: '#1d1a15', border: '#f2c200' });
  decalPlane(bayTex, BAY.halfX * 2, BAY.halfZ * 2, BAY.x, 0.03, BAY.z, 0, -Math.PI / 2);

  // bota-fora (zona de descarga) + leira de contenção
  const zoneTex = labelTexture('BOTA-FORA', 512, 512, { font: 'bold 64px Arial', bg: 'rgba(224,162,27,0.25)', fg: '#1d1a15', border: '#1d1a15' });
  decalPlane(zoneTex, ZONE_HALF * 2, ZONE_HALF * 2, ZONE_CENTER[0], 0.03, ZONE_CENTER[1], 0, -Math.PI / 2);
  const bermX = ZONE_CENTER[0] + ZONE_HALF + 1.6;
  mound(M.dirt, bermX, ZONE_CENTER[1], 1.6, 1.3, ZONE_HALF + 1.5, 7);
  for (let z = -ZONE_HALF - 1; z <= ZONE_HALF + 1; z += 1.3) circle(bermX, ZONE_CENTER[1] + z, 1.3);

  // pilha de cascalho (carregada pela escavadeira)
  mound(M.gravel, PILE.x, PILE.z, PILE.r, 1.6, PILE.r, 3);
  circle(PILE.x, PILE.z, PILE.r - 0.3);

  // ---------- prédio em construção ----------
  const B = { x0: 8.4, x1: 23.6, z0: -27.6, z1: -12.4 };
  const bx = (B.x0 + B.x1) / 2, bz = (B.z0 + B.z1) / 2, bw = B.x1 - B.x0, bd = B.z1 - B.z0;
  box(bw + 0.6, 0.3, bd + 0.6, M.concrete, bx, 0.15, bz);
  box(bw + 0.4, 0.25, bd + 0.4, M.concrete, bx, 3.42, bz);                      // laje 1
  box(bw + 0.4, 0.25, bd / 2, M.concrete, bx, 6.67, B.z0 + bd / 4);             // laje 2 (metade)
  const cols = [], rebar = [], forms = [];
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    const x = B.x0 + i * bw / 3, z = B.z0 + j * bd / 3;
    cols.push([x, 1.8, z], [x, 5.05, z]);
    if (z < bz) cols.push([x, 7.4, z]);                                          // pilares do 2º andar
    else for (const [dx, dz] of [[-0.12, -0.12], [0.12, -0.12], [-0.12, 0.12], [0.12, 0.12]]) rebar.push([x + dx, 7.15, z + dz]);
    if (z < bz && j === 0) forms.push([x, 8.6, z]);
  }
  instanced(new THREE.BoxGeometry(0.4, 3.0, 0.4), M.concreteSmall, cols);
  instanced(new THREE.CylinderGeometry(0.014, 0.014, 1.3, 6), new THREE.MeshStandardMaterial({ color: 0x7a4a2a, roughness: 0.6, metalness: 0.6 }), rebar);
  instanced(new THREE.BoxGeometry(0.6, 1.0, 0.6), M.wood, forms);
  // alvenaria no térreo (fachada sul com janelas, oeste parcial)
  for (const [x, w] of [[B.x0 + 1.2, 2.4], [B.x0 + 5.2, 2.6], [B.x0 + 9.4, 2.6], [B.x1 - 1.6, 3.2]]) box(w, 3.0, 0.2, M.brick, x, 1.8, B.z0 - 0.1);
  for (const x of [B.x0 + 3.2, B.x0 + 7.3, B.x0 + 11.6]) box(1.4, 1.1, 0.2, M.brick, x, 0.85, B.z0 - 0.1);
  box(0.2, 3.0, 8, M.brick, B.x0 - 0.1, 1.8, B.z0 + 4);
  rect(bx, bz, bw + 0.8, bd + 0.8, 0, 0.6);

  // andaime + tela na fachada norte
  const tubes = [], planks = [];
  for (let x = B.x0; x <= B.x1 + 0.01; x += 2) for (const z of [B.z1 + 0.6, B.z1 + 1.6]) tubes.push([x, 4.25, z]);
  instanced(new THREE.CylinderGeometry(0.024, 0.024, 8.5, 8), M.steel, tubes);
  const hTubes = [];
  for (let y = 2; y <= 8; y += 2) for (const z of [B.z1 + 0.6, B.z1 + 1.6]) hTubes.push([bx, y, z, 0, 0, Math.PI / 2]);
  instanced(new THREE.CylinderGeometry(0.022, 0.022, bw, 8), M.steel, hTubes);
  for (let y = 2; y <= 6; y += 2) for (let x = B.x0 + 1; x < B.x1; x += 2) planks.push([x, y + 0.04, B.z1 + 1.1]);
  instanced(new THREE.BoxGeometry(1.95, 0.05, 0.95), M.wood, planks);
  const net = new THREE.Mesh(new THREE.PlaneGeometry(bw, 8.4), M.net);
  M.net.map.wrapS = M.net.map.wrapT = THREE.RepeatWrapping; M.net.map.repeat.set(bw * 2, 8.4 * 2);
  net.position.set(bx, 4.2, B.z1 + 1.7); scene.add(net);
  rect(bx, B.z1 + 1.1, bw + 0.4, 1.6, 0, 0.5);

  // ---------- grua ----------
  const crane = { x: 3, z: -24 };
  box(3.2, 1.0, 3.2, M.concrete, crane.x, 0.5, crane.z);
  const mast = new THREE.Mesh(new THREE.BoxGeometry(1.2, 24, 1.2), M.lattice);
  mast.position.set(crane.x, 13, crane.z); mast.castShadow = true; scene.add(mast);
  const slew = new THREE.Group(); slew.position.set(crane.x, 25, crane.z); scene.add(slew);
  const jib = new THREE.Mesh(new THREE.BoxGeometry(22, 1.0, 1.0), M.lattice); jib.position.set(11.6, 0.5, 0); jib.castShadow = true; slew.add(jib);
  const cjib = new THREE.Mesh(new THREE.BoxGeometry(7, 0.8, 1.0), M.lattice); cjib.position.set(-4, 0.4, 0); slew.add(cjib);
  for (let i = 0; i < 3; i++) box(0.8, 1.6, 1.4, M.concrete, -5.2 - i * 0.85, -0.5, 0, 0, slew);
  const apex = new THREE.Mesh(new THREE.BoxGeometry(1.0, 4, 1.0), M.lattice); apex.position.set(0, 3, 0); slew.add(apex);
  rbox(1.6, 1.6, 1.4, M.yellow, 0.4, -0.5, 1.2, 0.08, slew);
  const tieMat = new THREE.LineBasicMaterial({ color: 0x333333 });
  slew.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-7.4, 0.8, 0), new THREE.Vector3(0, 5, 0), new THREE.Vector3(14, 1, 0)]), tieMat));
  const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.18, 12, 8), M.beacon); beacon.position.set(0, 5.1, 0); slew.add(beacon);
  const trolley = box(1.0, 0.4, 1.1, M.dark, 12, -0.2, 0, 0, slew);
  const cable = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1, 6).translate(0, -0.5, 0), M.dark); slew.add(cable);
  const hookLoad = new THREE.Group(); slew.add(hookLoad);
  box(1.2, 0.15, 1.2, M.wood, 0, 0, 0, 0, hookLoad);
  box(1.0, 0.7, 1.0, M.brick, 0, 0.42, 0, 0, hookLoad);
  rect(crane.x, crane.z, 3.4, 3.4, 0, 0.6);

  // ---------- betoneira ----------
  const mixer = new THREE.Group(); mixer.position.set(-1, 0, -15.5); mixer.rotation.y = Math.PI / 2; scene.add(mixer);
  rbox(2.3, 0.4, 7.5, M.dark, 0, 0.9, 0, 0.05, mixer);
  rbox(2.4, 1.9, 1.9, M.white, 0, 1.95, 2.9, 0.15, mixer);
  const ws = new THREE.Mesh(new THREE.PlaneGeometry(2.0, 0.8), M.glass); ws.position.set(0, 2.4, 3.86); mixer.add(ws);
  for (const z of [2.7, -1.2, -2.5]) for (const s of [-1, 1]) {
    const w = add(new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.4, 20), M.rubber), mixer);
    w.rotation.z = Math.PI / 2; w.position.set(s * 1.05, 0.5, z);
  }
  const drumGeo = new THREE.LatheGeometry([[0.2, -2.7], [1.0, -2.2], [1.35, -0.8], [1.35, 0.6], [0.9, 2.0], [0.45, 2.6]].map(([r, y]) => new THREE.Vector2(r, y)), 32);
  const drumMat = new THREE.MeshStandardMaterial({ map: stripeTexture('#e9791a', '#f1f1f1', 8, true), roughness: 0.5, metalness: 0.3 });
  const drumPivot = new THREE.Group(); drumPivot.position.set(0, 2.45, -0.8); drumPivot.rotation.x = Math.PI / 2 - 0.25; mixer.add(drumPivot);
  const drum = add(new THREE.Mesh(drumGeo, drumMat), drumPivot);
  rect(-1, -15.5, 7.6, 2.5, 0, 0.6);

  // ---------- canteiro: contêineres, banheiros ----------
  const cont = (x, y, z, ry = 0) => {
    const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; scene.add(g);
    box(6.06, 2.6, 2.44, M.container, 0, 1.3, 0, 0, g);
    box(6.1, 0.12, 2.5, M.containerBlue, 0, 2.62, 0, 0, g);
    for (const wx of [-1.6, 1.4]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.9), M.glass); w.position.set(wx, 1.55, 1.23); g.add(w); }
    const door = box(0.9, 2.0, 0.04, M.containerBlue, 0.0, 1.05, 1.23, 0, g); door.castShadow = false;
    return g;
  };
  cont(-30, 0, -21, Math.PI / 2); cont(-27.4, 0, -21, Math.PI / 2); cont(-28.7, 2.68, -21, Math.PI / 2);
  for (let i = 0; i < 6; i++) box(0.9, 0.18, 0.3, M.steel, -26.1, 0.3 + i * 0.42, -18.6 + i * 0.32);
  const office = labelTexture('ESCRITÓRIO DA OBRA', 1024, 160, { font: 'bold 76px Arial', bg: '#1f5fa8', fg: '#ffffff' });
  decalPlane(office, 4.6, 0.72, -27.4, 5.9, -21, Math.PI / 2);
  box(0.1, 0.8, 4.8, M.containerBlue, -27.45, 5.9, -21);
  rect(-28.7, -21, 5.6, 6.4, 0, 0.6);
  for (let i = 0; i < 3; i++) {
    box(1.15, 2.3, 1.15, M.containerBlue, -21 + i * 1.3, 1.15, -30);
    box(1.25, 0.12, 1.25, M.white, -21 + i * 1.3, 2.36, -30);
  }
  rect(-19.7, -30, 4.2, 1.6, 0, 0.5);

  // ---------- estoques de material ----------
  mound(M.sand, -12, -12.5, 2.3, 1.3, 2.0, 11); circle(-12, -12.5, 2.1);
  for (const x of [-7, -5.6]) {
    box(1.2, 0.14, 1.0, M.wood, x, 0.07, -13.5);
    const b = box(1.1, 0.9, 0.95, M.brick, x, 0.6, -13.5); b.material = M.brick;
    circle(x, -13.5, 0.75);
  }
  for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) rbox(0.7, 0.16, 0.45, M.white, -3.6 + j * 0.5, 0.22 + i * 0.17, -13.5, 0.06);
  box(1.2, 0.14, 1.0, M.wood, -3.35, 0.07, -13.5); circle(-3.35, -13.5, 0.7);
  const bars = [];
  for (let i = 0; i < 24; i++) bars.push([-9 + (i % 6) * 0.04 - 0.1, 0.3 + Math.floor(i / 6) * 0.04, -19, 0, 0, Math.PI / 2]);
  instanced(new THREE.CylinderGeometry(0.016, 0.016, 6, 6), new THREE.MeshStandardMaterial({ color: 0x6a4a35, roughness: 0.6, metalness: 0.6 }), bars);
  for (const x of [-11.5, -9, -6.5]) box(0.15, 0.25, 1.0, M.wood, x, 0.12, -19);
  rect(-9, -19, 6.4, 1.2, 0, 0.5);
  for (let i = 0; i < 6; i++) box(4, 0.08, 0.3, M.wood, -2.5, 0.06 + i * 0.09, -20 + (i % 2) * 0.05);
  rect(-2.5, -20, 4.2, 0.8, 0, 0.45);

  // ---------- barreiras de concreto (New Jersey) ----------
  const jersey = new THREE.Shape([[-0.3, 0], [0.3, 0], [0.12, 0.3], [0.08, 0.8], [-0.08, 0.8], [-0.12, 0.3]].map(([x, y]) => new THREE.Vector2(x, y)));
  const jerseyGeo = new THREE.ExtrudeGeometry(jersey, { depth: 1.95, bevelEnabled: false }).translate(0, 0, -0.975).rotateY(Math.PI / 2);
  for (const x of [-13, -11, -9, -7, -3, -1, 1, 3]) {
    const m = add(new THREE.Mesh(jerseyGeo, M.concreteSmall)); m.position.set(x, 0, -5);
    box(0.3, 0.08, 0.02, M.reflector, x, 0.6, -4.88);
    circle(x - 0.5, -5, 0.45); circle(x + 0.5, -5, 0.45);
  }

  // ---------- torres de iluminação ----------
  const lightTowers = [];
  for (const [x, z] of [[-24, -3], [18, 3]]) {
    rbox(1.4, 0.8, 2.4, M.yellow, x, 0.7, z, 0.08);
    cylY(0.08, 7, M.steel, x, 4, z);
    const head = new THREE.Group(); head.position.set(x, 7.6, z); scene.add(head);
    for (const [dx, dy] of [[-0.45, 0.3], [0.45, 0.3], [-0.45, -0.3], [0.45, -0.3]]) {
      box(0.75, 0.5, 0.15, M.dark, dx, dy, 0, 0, head);
      box(0.65, 0.4, 0.02, M.lamp, dx, dy, 0.08, 0, head);
    }
    lightTowers.push(head);
    circle(x, z, 1.3);
  }

  // ---------- sinalização ----------
  function sign(x, z, ry, tex, w = 1.2, h = 0.9) {
    cylY(0.04, 2.0, M.steel, x, 1.0, z);
    const g = new THREE.Group(); g.position.set(x, 2.0 + h / 2 - 0.1, z); g.rotation.y = ry; scene.add(g);
    box(w + 0.06, h + 0.06, 0.03, M.dark, 0, 0, -0.02, 0, g);
    const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6 }));
    face.position.z = 0.001; g.add(face);
    const back = face.clone(); back.rotation.y = Math.PI; back.position.z = -0.04; g.add(back);
    circle(x, z, 0.25);
  }
  const speedTex = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, 256, 256);
    g.beginPath(); g.arc(128, 128, 112, 0, Math.PI * 2); g.fillStyle = '#d4201a'; g.fill();
    g.beginPath(); g.arc(128, 128, 88, 0, Math.PI * 2); g.fillStyle = '#fff'; g.fill();
    g.fillStyle = '#111'; g.font = 'bold 92px Arial'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('10', 128, 118);
    g.font = 'bold 30px Arial'; g.fillText('km/h', 128, 182);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  sign(-10, -0.6, 0, speedTex, 0.9, 0.9);
  sign(-6, 12.4, 0, labelTexture('ÁREA DE\nCARREGAMENTO', 512, 320, { font: 'bold 56px Arial', bg: '#f2c200', fg: '#111', border: '#111' }));
  sign(9, 14.6, 0, labelTexture('BOTA-FORA\nDESCARGA', 512, 320, { font: 'bold 60px Arial', bg: '#f2c200', fg: '#111', border: '#111' }));
  sign(-24, -14, Math.PI / 2, labelTexture('USO OBRIGATÓRIO\nDE EPI', 512, 320, { font: 'bold 50px Arial', bg: '#1f5fa8', fg: '#fff' }));
  sign(-8.5, -3.8, 0, labelTexture('ATENÇÃO\nTRÂNSITO DE\nMÁQUINAS', 512, 360, { font: 'bold 50px Arial', bg: '#f2c200', fg: '#111', border: '#111' }), 1.2, 1.0);

  // ---------- tapume ----------
  const PANEL = 2.4, panels = [], bands = [];
  for (let t = -WORLD + PANEL / 2; t < WORLD; t += PANEL) {
    for (const [x, z, ry] of [[t, -WORLD, 0], [t, WORLD, 0], [-WORLD, t, Math.PI / 2], [WORLD, t, Math.PI / 2]]) {
      panels.push([x, 1.1, z, ry]); bands.push([x, 2.1, z, ry]);
    }
  }
  instanced(new THREE.BoxGeometry(PANEL, 2.2, 0.05), M.fence, panels);
  instanced(new THREE.BoxGeometry(PANEL, 0.22, 0.06), M.green, bands);
  const logo = labelTexture('TERRA-BOTICS  •  OBRA EM ANDAMENTO', 1024, 128, { font: 'bold 58px Arial', bg: null, fg: '#1f7a3a' });
  for (const t of [-24, 0, 24]) {
    decalPlane(logo, 7, 0.9, t, 1.3, -WORLD + 0.04);
    decalPlane(logo, 7, 0.9, t, 1.3, WORLD - 0.04, Math.PI);
    decalPlane(logo, 7, 0.9, -WORLD + 0.04, 1.3, t, Math.PI / 2);
  }
  for (let t = -WORLD; t <= WORLD; t += 1.2) { circle(t, -WORLD, 0.4); circle(t, WORLD, 0.4); circle(-WORLD, t, 0.4); circle(WORLD, t, 0.4); }

  // ---------- árvores fora do canteiro ----------
  const trunks = [], crowns = [];
  for (let i = 0; i < 60; i++) {
    const a = (i / 60) * Math.PI * 2 + Math.random() * 0.1, r = 44 + Math.random() * 22;
    const x = Math.cos(a) * r, z = Math.sin(a) * r;
    trunks.push([x, 1.2, z]); crowns.push([x, 3.4 + Math.random(), z, Math.random() * 6]);
  }
  instanced(new THREE.CylinderGeometry(0.18, 0.25, 2.4, 8), M.trunk, trunks);
  instanced(new THREE.IcosahedronGeometry(2.2, 1), M.leaves, crowns);

  // ---------- animações do cenário ----------
  let t = 0;
  function update(dt) {
    t += dt;
    slew.rotation.y = Math.sin(t * 0.05) * 1.2 + 0.4;
    const tr = 12 + Math.sin(t * 0.12) * 5;
    trolley.position.x = tr;
    const hookY = -12 - Math.sin(t * 0.09) * 4;
    cable.position.set(tr, -0.4, 0); cable.scale.y = -hookY - 0.4 - 0.9;
    hookLoad.position.set(tr, hookY, 0);
    drum.rotation.y += dt * 1.2;
    M.beacon.emissiveIntensity = Math.sin(t * 4) > 0 ? 2.5 : 0.2;
  }
  update(0);

  return { colliders, update };
}
