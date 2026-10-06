"""Analisador em modo demonstração/teste local usando OpenCV.

Permite testar o pipeline e a interface do Vigia Obra com a câmera do computador
ou vídeos de teste, sem custos e sem depender de chave de API da Anthropic.
Detecta a presença de pessoas/faces no enquadramento e gera ocorrências
realistas de não-conformidade conforme as NRs brasileiras (NR-6, NR-18, NR-35).
"""

import cv2
import numpy as np

from .frame_extractor import Frame

# Carrega o classificador pré-treinado do OpenCV
_FACE_CASCADE = None


def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
    return _FACE_CASCADE


# Catálogo de ocorrências simuladas com base técnica nas Normas Regulamentadoras
DEMO_RISK_CATALOG = [
    {
        "risco": "Trabalhador em atividade sem uso de capacete de segurança classe B com jugular",
        "norma": "NR-6, item 6.3 / NR-18, item 18.5",
        "confianca": "alto",
        "severidade": "alta",
    },
    {
        "risco": "Ausência de óculos de segurança contra impactos e partículas volantes",
        "norma": "NR-6, item 6.5.1",
        "confianca": "medio",
        "severidade": "media",
    },
    {
        "risco": "Trabalhador sem colete ou vestimenta com faixas retrorrefletivas de alta visibilidade",
        "norma": "NR-18, item 18.4.1",
        "confianca": "medio",
        "severidade": "baixa",
    },
    {
        "risco": "Operação em área de movimentação sem isolamento perimetral ou sinalização de advertência",
        "norma": "NR-18, item 18.14",
        "confianca": "alto",
        "severidade": "media",
    },
    {
        "risco": "Postura de risco próximo a desnível sem ponto de ancoragem ou retenção de queda",
        "norma": "NR-35, item 35.5.2",
        "confianca": "baixo",
        "severidade": "alta",
    },
]


def analyze_frame_demo(frame: Frame, frame_index: int = 0) -> list[dict]:
    """Analisa um frame localmente no modo demonstração.
    
    Verifica se há presença de pessoas na imagem através do OpenCV.
    Se detectada pessoa/face, reporta não-conformidades de segurança do trabalho
    com o respectivo timestamp.
    """
    try:
        # Decodifica os bytes PNG para imagem numpy
        np_arr = np.frombuffer(frame.png_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = _get_face_cascade()
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(30, 30),
        )

        ocorrencias = []
        has_person = len(faces) > 0
        img_mean = float(np.mean(img))
        img_std = float(np.std(img))
        is_camera_covered = img_mean < 12.0 or img_std < 8.0

        if is_camera_covered:
            return [
                {
                    "timestamp": frame.timestamp_label,
                    "risco": "Sensor de imagem obstruído ou com iluminação insuficiente no posto",
                    "norma": "NR-18",
                    "confianca": "baixo",
                    "severidade": "baixa",
                }
            ]

        # Inspeciona a presença real de capacete de segurança na cabeça da pessoa:
        has_helmet = False
        if has_person:
            # Pega a primeira face detectada para analisar a região craniana
            fx, fy, fw, fh = faces[0]
            hy1 = max(0, int(fy - 0.95 * fh))
            hy2 = int(fy + 0.05 * fh)
            hx1 = max(0, int(fx - 0.25 * fw))
            hx2 = min(img.shape[1], int(fx + 1.25 * fw))
            head_roi = img[hy1:hy2, hx1:hx2]

            if head_roi.size > 0:
                hsv = cv2.cvtColor(head_roi, cv2.COLOR_BGR2HSV)
                # Capacete azul vibrante (como o capacete de obra azul do operador)
                blue_mask = (hsv[:, :, 0] >= 90) & (hsv[:, :, 0] <= 135) & (hsv[:, :, 1] >= 70) & (hsv[:, :, 2] >= 50)
                # Capacete amarelo vibrante de obra
                yellow_mask = (hsv[:, :, 0] >= 18) & (hsv[:, :, 0] <= 35) & (hsv[:, :, 1] >= 90) & (hsv[:, :, 2] >= 80)
                # Capacete laranja / vermelho de obra
                red_mask = ((hsv[:, :, 0] <= 15) | (hsv[:, :, 0] >= 165)) & (hsv[:, :, 1] >= 110) & (hsv[:, :, 2] >= 80)
                # Capacete verde vibrante
                green_mask = (hsv[:, :, 0] >= 38) & (hsv[:, :, 0] <= 85) & (hsv[:, :, 1] >= 90) & (hsv[:, :, 2] >= 70)

                area = float(head_roi.shape[0] * head_roi.shape[1])
                b_ratio = np.sum(blue_mask) / area if area > 0 else 0
                y_ratio = np.sum(yellow_mask) / area if area > 0 else 0
                r_ratio = np.sum(red_mask) / area if area > 0 else 0
                g_ratio = np.sum(green_mask) / area if area > 0 else 0

                # Se mais de 10% da região craniana contiver a cor característica do capacete:
                if b_ratio > 0.10 or y_ratio > 0.10 or r_ratio > 0.10 or g_ratio > 0.10:
                    has_helmet = True

        confianca = "alto" if has_person else "medio"

        # Se NÃO estiver com capacete identificado, reporta severidade ALTA:
        if not has_helmet:
            occ_capacete = {
                "timestamp": frame.timestamp_label,
                "risco": "Trabalhador/pessoa no posto de trabalho sem uso de capacete de segurança (EPI obrigatório)",
                "norma": "NR-6, item 6.3 / NR-18, item 18.5",
                "confianca": confianca,
                "severidade": "alta",
            }
            ocorrencias.append(occ_capacete)



        return ocorrencias
    except Exception as e:
        # Fallback gracioso se a análise OpenCV falhar
        return [
            {
                "timestamp": frame.timestamp_label,
                "risco": "Trabalhador no enquadramento sem identificação de capacete de segurança (NR-6/NR-18)",
                "norma": "NR-6, item 6.3 / NR-18, item 18.5",
                "confianca": "medio",
                "severidade": "alta",
            }
        ]

