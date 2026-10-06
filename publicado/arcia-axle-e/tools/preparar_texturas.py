"""Prepara as texturas geradas no Gemini para os modelos 3D.

- Coletes: recorta só o corpo do colete (sem fundo) na proporção do tronco.
- Rostos: detecta o rosto, enquadra da testa ao queixo e mede a cor média da pele.
- Adesivo do capacete: remove o fundo verde (#00FF00) e recorta o adesivo.

Os originais em textures/ ficam intactos; os resultados vão para textures/prontas/.
Uso: python tools/preparar_texturas.py
"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent / "textures"
SRC = ROOT / "trabalhadores"
OUT = ROOT / "prontas"
TORSO_ASPECT = 0.42 / 0.6          # largura / altura da caixa do tronco
VEST_BODY_FROM = 0.30              # fração da altura do colete onde começa o corpo (abaixo das cavas)
FACE_PAD = dict(left=0.0, right=0.0, top=0.16, bottom=0.12)
FACE_FEATHER = 0.16              # largura da borda suave da máscara oval (fração do raio)


def read(path):
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return img


def vest_crop(name):
    img = read(SRC / f"{name}.png")
    b, g, r = [img[..., i].astype(int) for i in range(3)]
    mask = (r > 170) & (g > 50) & (g < 175) & (b < 100) & (r - b > 110)
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError(f"colete não encontrado em {name}")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    top = int(y0 + (y1 - y0) * VEST_BODY_FROM)
    h = y1 - top
    w = int(h * TORSO_ASPECT)
    cx = (x0 + x1) // 2
    crop = img[top:y1, cx - w // 2: cx + w // 2]
    out = cv2.resize(crop, (512, int(512 / TORSO_ASPECT)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(OUT / f"{name}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return out.shape


def face_crop(name, detector):
    img = read(SRC / f"{name}.png")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(200, 200))
    if len(faces) == 0:
        raise ValueError(f"rosto não detectado em {name}")
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    x0 = max(0, int(x - w * FACE_PAD["left"]))
    x1 = min(img.shape[1], int(x + w * (1 + FACE_PAD["right"])))
    y0 = max(0, int(y - h * FACE_PAD["top"]))
    y1 = min(img.shape[0], int(y + h * (1 + FACE_PAD["bottom"])))
    crop = cv2.resize(img[y0:y1, x0:x1], (512, 512), interpolation=cv2.INTER_AREA)
    # máscara oval com borda suave: o rosto se funde à cor de pele da cabeça
    yy, xx = np.mgrid[0:512, 0:512]
    d = np.sqrt(((xx - 256) / 250) ** 2 + ((yy - 262) / 252) ** 2)
    alpha = np.clip((1 - d) / FACE_FEATHER, 0, 1) * 255
    cv2.imwrite(str(OUT / f"{name}.png"), np.dstack([crop, alpha.astype(np.uint8)]))
    # cor da pele: média das bochechas (abaixo dos olhos, ao lado do nariz)
    cheeks = np.concatenate([crop[260:330, 110:180].reshape(-1, 3), crop[260:330, 332:402].reshape(-1, 3)])
    b_, g_, r_ = np.median(cheeks, axis=0).astype(int)
    return f"#{r_:02x}{g_:02x}{b_:02x}"


def sticker_alpha(name):
    img = read(SRC / f"{name}.png")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (40, 120, 80), (85, 255, 255))
    alpha = cv2.GaussianBlur(255 - green, (3, 3), 0)
    ys, xs = np.nonzero(alpha > 128)
    rgba = np.dstack([img, alpha])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    cv2.imwrite(str(OUT / f"{name}.png"), rgba)
    return rgba.shape


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("colete_frente", vest_crop("colete_frente"))
    print("colete_costas", vest_crop("colete_costas"))
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    skins = {}
    for i in range(1, 5):
        skins[f"rosto_{i}"] = face_crop(f"rosto_{i}", detector)
        print(f"rosto_{i}", skins[f"rosto_{i}"])
    (OUT / "pele.json").write_text(json.dumps(skins, indent=2), encoding="utf-8")
    print("capacete_adesivo", sticker_alpha("capacete_adesivo"))


if __name__ == "__main__":
    main()
