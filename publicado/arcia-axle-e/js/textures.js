import * as THREE from 'three';

// Texturas PBR procedurais (canvas): cor + rugosidade + relevo, todas "tileable".

function hash(x, y, s) {
  let h = Math.imul(x, 374761393) ^ Math.imul(y, 668265263) ^ Math.imul(s + 1, 1442695041);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function vnoise(x, y, period, seed) {
  const x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const m = i => ((i % period) + period) % period;
  const a = hash(m(x0), m(y0), seed), b = hash(m(x0 + 1), m(y0), seed);
  const c = hash(m(x0), m(y0 + 1), seed), d = hash(m(x0 + 1), m(y0 + 1), seed);
  return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy;
}

function fbm(u, v, freq, octaves, seed) {
  let sum = 0, amp = 0.5, norm = 0, f = freq;
  for (let o = 0; o < octaves; o++) {
    sum += amp * vnoise(u * f, v * f, f, seed + o * 17);
    norm += amp; amp *= 0.5; f *= 2;
  }
  return sum / norm;
}

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

function makeCanvas(w, h = w) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  return [c, c.getContext('2d')];
}

function toTexture(canvas, srgb = false) {
  const t = new THREE.CanvasTexture(canvas);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// Preenche 3 canvases (cor, rugosidade, relevo) num único laço por pixel.
function pixelPass(size, fn) {
  const layers = [0, 1, 2].map(() => makeCanvas(size));
  const imgs = layers.map(([, g]) => g.createImageData(size, size));
  const out = { c: [0, 0, 0], r: 0, b: 0 };
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    fn(x / size, y / size, out);
    const i = (y * size + x) * 4;
    imgs[0].data.set([out.c[0], out.c[1], out.c[2], 255], i);
    imgs[1].data.set([out.r, out.r, out.r, 255], i);
    imgs[2].data.set([out.b, out.b, out.b, 255], i);
  }
  layers.forEach(([, g], k) => g.putImageData(imgs[k], 0, 0));
  return layers;
}

function rgb(hex) { return [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255]; }

// Tinta sobre metal: variação, sujeira, arranhões e lascas.
export function paintTexture(hex, { size = 512, seed = 1, grime = 0.5, scratches = 70, chips = 25, rough = [0.32, 0.55], freq = 5 } = {}) {
  const base = rgb(hex), dirt = [86, 70, 50];
  const [[cc, cg], [rc, rg], [bc, bg]] = pixelPass(size, (u, v, o) => {
    const n = fbm(u, v, freq, 4, seed);
    const g = smooth(0.52, 0.78, fbm(u, v, 3, 4, seed + 5)) * grime;
    const speck = hash((u * size) | 0, (v * size) | 0, seed + 9);
    const k = 0.9 + 0.2 * n;
    for (let i = 0; i < 3; i++) o.c[i] = Math.min(255, base[i] * k * (1 - g) + dirt[i] * g + (speck - 0.5) * 8);
    o.r = 255 * Math.min(1, rough[0] + (rough[1] - rough[0]) * n + g * 0.45);
    o.b = 128 + (n - 0.5) * 50 + (speck - 0.5) * 18 - g * 20;
  });
  const rnd = (() => { let s = seed * 9301 + 49297; return () => (s = (s * 9301 + 49297) % 233280) / 233280; })();
  for (let i = 0; i < scratches; i++) {
    const x = rnd() * size, y = rnd() * size, a = rnd() * Math.PI, len = 8 + rnd() * size * 0.12;
    const x2 = x + Math.cos(a) * len, y2 = y + Math.sin(a) * len, w = 0.6 + rnd() * 1.4;
    for (const [g, col] of [[cg, 'rgba(105,104,100,.85)'], [rg, 'rgb(80,80,80)'], [bg, 'rgb(70,70,70)']]) {
      g.strokeStyle = col; g.lineWidth = w; g.beginPath(); g.moveTo(x, y); g.lineTo(x2, y2); g.stroke();
    }
  }
  for (let i = 0; i < chips; i++) {
    const x = rnd() * size, y = rnd() * size, r = 2 + rnd() * 7;
    for (const [g, col] of [[cg, 'rgb(72,70,68)'], [rg, 'rgb(150,150,150)'], [bg, 'rgb(60,60,60)']]) {
      g.fillStyle = col; g.beginPath();
      for (let k = 0; k < 7; k++) {
        const a = k / 7 * Math.PI * 2, rr = r * (0.6 + rnd() * 0.6);
        g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
      }
      g.fill();
    }
  }
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Banda de rodagem do pneu (u = volta, v = largura) com garras em V.
export function tireTexture({ lugs = 22 } = {}) {
  const W = 1024, H = 256;
  const [cc, cg] = makeCanvas(W, H), [bc, bg] = makeCanvas(W, H), [rc, rg] = makeCanvas(W, H);
  const img = cg.createImageData(W, H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const n = fbm(x / W, y / H, 16, 3, 41), dust = smooth(0.55, 0.8, fbm(x / W, y / H, 6, 3, 43));
    const l = 24 + n * 14;
    img.data.set([l + dust * 60, l + dust * 48, l + dust * 32, 255], (y * W + x) * 4);
  }
  cg.putImageData(img, 0, 0);
  bg.fillStyle = 'rgb(70,70,70)'; bg.fillRect(0, 0, W, H);
  rg.fillStyle = 'rgb(235,235,235)'; rg.fillRect(0, 0, W, H);
  const step = W / lugs;
  for (let i = 0; i <= lugs; i++) for (const side of [-1, 1]) {
    const cx = i * step + (side > 0 ? step / 2 : 0);
    const pts = side < 0
      ? [[cx, 50], [cx + step * 0.45, 50], [cx + step * 0.75, 128], [cx + step * 0.3, 128]]
      : [[cx + step * 0.3, 128], [cx + step * 0.75, 128], [cx + step * 0.45, 206], [cx, 206]];
    for (const [g, col] of [[bg, 'rgb(220,220,220)'], [cg, 'rgba(58,56,54,.9)'], [rg, 'rgb(200,200,200)']]) {
      g.fillStyle = col; g.beginPath(); pts.forEach(([x, y]) => g.lineTo(x, y)); g.closePath(); g.fill();
    }
  }
  return { map: toTexture(cc, true), bumpMap: toTexture(bc), roughnessMap: toTexture(rc) };
}

// Inscrição em relevo na lateral do pneu (decalque circular transparente).
export function sidewallDecal(text) {
  const S = 512, [c, g] = makeCanvas(S);
  g.translate(S / 2, S / 2);
  g.font = 'bold 30px Arial'; g.fillStyle = 'rgba(150,150,150,.75)';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  const R = S * 0.42, chars = [...text], span = Math.PI * 1.7;
  chars.forEach((ch, i) => {
    g.save(); g.rotate(-span / 2 + span * i / (chars.length - 1)); g.translate(0, -R); g.fillText(ch, 0, 0); g.restore();
  });
  g.strokeStyle = 'rgba(120,120,120,.5)'; g.lineWidth = 3;
  g.beginPath(); g.arc(0, 0, S * 0.36, 0, Math.PI * 2); g.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

// Chapa xadrez (piso antiderrapante).
export function diamondPlateTexture() {
  const S = 256;
  const [[cc, cg], [rc, rg], [bc, bg]] = pixelPass(S, (u, v, o) => {
    const n = fbm(u, v, 8, 3, 61), g = smooth(0.55, 0.8, fbm(u, v, 3, 3, 67)) * 0.6;
    const l = 120 + n * 40;
    o.c[0] = l * (1 - g) + 80 * g; o.c[1] = l * (1 - g) + 66 * g; o.c[2] = (l + 6) * (1 - g) + 50 * g;
    o.r = 255 * (0.35 + n * 0.2 + g * 0.4); o.b = 100;
  });
  for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
    const cx = (x + (y % 2) * 0.5) * S / 4 + S / 8, cy = y * S / 4 + S / 8, a = (x + y) % 2 ? 0.8 : -0.8;
    for (const [g, col] of [[bg, 'rgb(230,230,230)'], [cg, 'rgba(190,190,195,.6)'], [rg, 'rgb(70,70,70)']]) {
      g.save(); g.translate(cx, cy); g.rotate(a); g.fillStyle = col;
      g.beginPath(); g.ellipse(0, 0, 22, 5, 0, 0, Math.PI * 2); g.fill(); g.restore();
    }
  }
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Plástico com nervuras verticais (caixas de bateria).
export function ribbedPlasticTexture() {
  const S = 256;
  const [[cc], [rc], [bc]] = pixelPass(S, (u, v, o) => {
    const n = fbm(u, v, 10, 3, 81), rib = 0.5 + 0.5 * Math.cos(u * Math.PI * 2 * 12);
    const dust = smooth(0.5, 0.85, fbm(u, v, 4, 3, 83)) * 0.5;
    const l = 34 + n * 12;
    o.c[0] = l + dust * 50; o.c[1] = l + dust * 42; o.c[2] = l + 4 + dust * 30;
    o.r = 255 * (0.55 + n * 0.15 + dust * 0.3); o.b = 60 + rib * 150;
  });
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Metal escovado (tampas do motor, cubos).
export function brushedMetalTexture() {
  const S = 256, [c, g] = makeCanvas(S);
  g.fillStyle = '#9ea3a8'; g.fillRect(0, 0, S, S);
  for (let i = 0; i < 900; i++) {
    const y = Math.random() * S, l = 130 + Math.random() * 90;
    g.strokeStyle = `rgba(${l},${l + 3},${l + 6},.35)`; g.lineWidth = Math.random() * 1.5;
    g.beginPath(); g.moveTo(0, y); g.lineTo(S, y + (Math.random() - 0.5) * 2); g.stroke();
  }
  return toTexture(c, true);
}

// Faixa zebrada amarelo/preto com desgaste.
export function hazardTexture() {
  const W = 512, H = 64, [c, g] = makeCanvas(W, H);
  g.fillStyle = '#e0a21b'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#16140f';
  for (let x = -H; x < W + H; x += 48) { g.beginPath(); g.moveTo(x, H); g.lineTo(x + 24, H); g.lineTo(x + 24 + H, 0); g.lineTo(x + H, 0); g.fill(); }
  for (let i = 0; i < 260; i++) {
    g.fillStyle = `rgba(110,105,95,${Math.random() * 0.6})`;
    g.fillRect(Math.random() * W, Math.random() * H, 1 + Math.random() * 4, 1 + Math.random() * 2);
  }
  return toTexture(c, true);
}

// Etiqueta/decalque de texto. lines: string com \n. icon: 'bolt' | 'warn'.
export function labelTexture(text, w, h, { font = 'bold 56px Arial', bg = '#2b2d30', fg = '#fff', border, icon, align = 'center' } = {}) {
  const [c, g] = makeCanvas(w, h);
  if (bg) { g.fillStyle = bg; g.fillRect(0, 0, w, h); }
  if (border) { g.strokeStyle = border; g.lineWidth = Math.max(3, h * 0.03); g.strokeRect(g.lineWidth, g.lineWidth, w - g.lineWidth * 2, h - g.lineWidth * 2); }
  let x0 = w / 2;
  if (icon === 'bolt') {
    const s = h * 0.32, cx = w * 0.5, cy = h * 0.24;
    g.fillStyle = '#e0a21b'; g.beginPath();
    [[0.1, -1], [-0.55, 0.15], [-0.05, 0.15], [-0.2, 1], [0.55, -0.2], [0.05, -0.2]].forEach(([x, y]) => g.lineTo(cx + x * s, cy + y * s));
    g.fill();
  }
  g.fillStyle = fg; g.font = font; g.textAlign = align; g.textBaseline = 'middle';
  if (align === 'left') x0 = h * 0.2;
  const lines = text.split('\n'), top = icon ? 0.45 : 0;
  lines.forEach((l, i) => g.fillText(l, x0, h * (top + (1 - top) * (i + 1) / (lines.length + 1))));
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

// Clona um conjunto {map, roughnessMap, bumpMap} com repetição própria.
export function repeatTex(set, rx, ry = rx) {
  const out = {};
  for (const [k, t] of Object.entries(set)) { const c = t.clone(); c.repeat.set(rx, ry); c.needsUpdate = true; out[k] = c; }
  return out;
}

// Concreto: variação, manchas e poros.
export function concreteTexture({ seed = 101, tone = 150 } = {}) {
  const S = 256;
  const [[cc], [rc], [bc]] = pixelPass(S, (u, v, o) => {
    const n = fbm(u, v, 6, 4, seed), f = hash((u * S) | 0, (v * S) | 0, seed + 1);
    const stain = smooth(0.55, 0.8, fbm(u, v, 3, 3, seed + 3)) * 0.3;
    const l = tone * (0.86 + 0.24 * n) * (1 - stain) + (f - 0.5) * 14;
    o.c[0] = l; o.c[1] = l * 0.99; o.c[2] = l * 0.95;
    o.r = 255 * (0.82 + n * 0.15); o.b = 128 + (f - 0.5) * 60 + (n - 0.5) * 40;
  });
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Chapa ondulada (contêineres, tapume).
export function corrugatedTexture(hex, { seed = 111, ribs = 16, rust = 0.15 } = {}) {
  const base = rgb(hex), rustCol = [120, 72, 40], S = 256;
  const [[cc], [rc], [bc]] = pixelPass(S, (u, v, o) => {
    const rib = 0.5 + 0.5 * Math.sin(u * Math.PI * 2 * ribs);
    const n = fbm(u, v, 5, 3, seed), r = smooth(0.62, 0.85, fbm(u, v, 4, 4, seed + 2)) * rust;
    const k = 0.84 + 0.2 * rib + (n - 0.5) * 0.1;
    for (let i = 0; i < 3; i++) o.c[i] = Math.min(255, base[i] * k * (1 - r) + rustCol[i] * r);
    o.r = 255 * (0.45 + n * 0.2 + r * 0.4); o.b = 40 + rib * 180;
  });
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Alvenaria de tijolos com argamassa.
export function brickTexture() {
  const S = 256, rows = 8, cols = 4;
  const [[cc], [rc], [bc]] = pixelPass(S, (u, v, o) => {
    const row = Math.floor(v * rows), uu = u * cols + (row % 2) * 0.5;
    const fu = uu - Math.floor(uu), fv = v * rows - row;
    const mortar = fu < 0.04 || fv < 0.08;
    const n = fbm(u, v, 12, 3, 131), tint = hash(Math.floor(uu), row, 133);
    if (mortar) { const l = 170 + n * 30; o.c[0] = l; o.c[1] = l * 0.97; o.c[2] = l * 0.9; o.r = 240; o.b = 60; return; }
    o.c[0] = 150 + tint * 50 + n * 30; o.c[1] = 62 + tint * 20 + n * 15; o.c[2] = 42 + n * 12;
    o.r = 220; o.b = 170 + n * 40;
  });
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Madeira compensada / tábuas.
export function woodTexture({ seed = 141 } = {}) {
  const S = 256;
  const [[cc], [rc], [bc]] = pixelPass(S, (u, v, o) => {
    const grain = fbm(u * 0.5, v * 4, 4, 4, seed);
    const ring = 0.5 + 0.5 * Math.sin((u * 8 + grain * 6) * Math.PI * 2);
    const l = 0.8 + 0.2 * ring;
    o.c[0] = 196 * l; o.c[1] = 150 * l; o.c[2] = 98 * l;
    o.r = 230; o.b = 110 + ring * 40;
  });
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Estrada de terra batida com marcas de pneu (u = largura, v = comprimento).
export function roadTexture() {
  const S = 256;
  const [[cc], [rc], [bc]] = pixelPass(S, (u, v, o) => {
    const n = fbm(u, v, 8, 4, 151), g = hash((u * S) | 0, (v * S) | 0, 153);
    const track = Math.max(Math.exp(-((u - 0.3) ** 2) / 0.004), Math.exp(-((u - 0.7) ** 2) / 0.004));
    const tread = track * (Math.sin(v * Math.PI * 2 * 24) > 0.3 ? 1 : 0.6);
    const edge = smooth(0.0, 0.12, Math.min(u, 1 - u));
    const l = (128 + n * 40 - tread * 30 + (g - 0.5) * 30) * (0.92 + 0.08 * edge);
    o.c[0] = l; o.c[1] = l * 0.86; o.c[2] = l * 0.68;
    o.r = 255 * (0.9 - track * 0.15); o.b = 128 + (g - 0.5) * 70 - tread * 40;
  });
  return { map: toTexture(cc, true), roughnessMap: toTexture(rc), bumpMap: toTexture(bc) };
}

// Treliça (grua) com transparência.
export function latticeTexture(color = '#e8b000') {
  const [c, g] = makeCanvas(128);
  g.strokeStyle = color; g.lineWidth = 10; g.strokeRect(5, 5, 118, 118);
  g.lineWidth = 6; g.beginPath(); g.moveTo(5, 5); g.lineTo(123, 123); g.moveTo(123, 5); g.lineTo(5, 123); g.stroke();
  return toTexture(c, true);
}

// Tela de proteção verde (andaime).
export function netTexture() {
  const [c, g] = makeCanvas(64);
  g.fillStyle = 'rgba(40,140,60,0.35)'; g.fillRect(0, 0, 64, 64);
  g.strokeStyle = 'rgba(30,110,45,0.95)'; g.lineWidth = 2;
  for (let i = 0; i <= 64; i += 8) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 64); g.moveTo(0, i); g.lineTo(64, i); g.stroke(); }
  return toTexture(c, true);
}

// Listras (betoneira, barreiras, colete).
export function stripeTexture(c1, c2, stripes = 6, vertical = false) {
  const [c, g] = makeCanvas(256);
  for (let i = 0; i < stripes; i++) {
    g.fillStyle = i % 2 ? c2 : c1;
    if (vertical) g.fillRect(i * 256 / stripes, 0, 256 / stripes + 1, 256); else g.fillRect(0, i * 256 / stripes, 256, 256 / stripes + 1);
  }
  return toTexture(c, true);
}
