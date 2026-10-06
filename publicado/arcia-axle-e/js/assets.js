import * as THREE from 'three';

// Carregamento das texturas em imagem (textures/). Gere os recortes com tools/preparar_texturas.py.

const loader = new THREE.TextureLoader();
const cache = new Map();

export function imageTexture(path, { repeat = [1, 1], offset = [0, 0], srgb = true } = {}) {
  const key = `${path}|${repeat}|${offset}|${srgb}`;
  if (cache.has(key)) return cache.get(key);
  const t = loader.load(path, undefined, undefined, () => console.warn(`Textura não encontrada: ${path}`));
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.offset.set(offset[0], offset[1]);
  t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  cache.set(key, t);
  return t;
}

export async function loadJSON(path, fallback) {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(res.status);
    return await res.json();
  } catch {
    console.warn(`Arquivo não encontrado: ${path}`);
    return fallback;
  }
}
