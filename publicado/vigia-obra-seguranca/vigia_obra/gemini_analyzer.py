"""Análise visual de segurança do trabalho por frame utilizando Google Gemini.

Utiliza a API gratuita do Google Gemini com fallback inteligente de modelos
(gemini-3.5-flash, gemini-flash-latest, gemini-3.6-flash) e inspeção
de EPIs (Apenas Capacete NR-6/NR-18). Versão limitada para teste.
"""

import json
import sys
from google import genai
from google.genai import types

from .frame_extractor import Frame

SYSTEM_PROMPT = """\
Você é um auditor de visão computacional de alta precisão especializado em segurança do trabalho (NR-6, NR-18 e NR-35).

Sua função é inspecionar o frame da câmera/webcam e verificar a presença e ausência de Equipamentos de Proteção Individual (EPI).

REGRAS DE AVALIAÇÃO:
1. CAPACETE DE SEGURANÇA (NR-6, item 6.3 / NR-18, item 18.5):
   - Inspecione a cabeça da pessoa.
   - SE A PESSOA ESTIVER USANDO CAPACETE DE SEGURANÇA (ex: capacete azul, amarelo, branco, laranja, verde, etc.):
     A pessoa está protegida! NÃO reporte falta de capacete!
   - SE A PESSOA ESTIVER SEM CAPACETE (cabeça descoberta, cabelo visível, sem EPI craniano):
     Você DEVE OBRIGATORIAMENTE reportar não-conformidade de severidade ALTA:
     {
       "risco": "Trabalhador/pessoa no posto de trabalho sem uso de capacete de segurança (EPI obrigatório)",
       "norma": "NR-6, item 6.3 / NR-18, item 18.5",
       "confianca": "alto",
       "severidade": "alta"
     }

NOTA: Esta é uma VERSÃO LIMITADA PARA TESTE. Apenas a detecção de capacete está ativada no momento.

FORMATO ESTRITO DE RESPOSTA EM JSON:
{
  "ocorrencias": [
    {
      "risco": "...",
      "norma": "...",
      "confianca": "alto" | "medio" | "baixo",
      "severidade": "alta" | "media" | "baixa"
    }
  ]
}
"""

CANDIDATE_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]




def analyze_frame_gemini(client: genai.Client, frame: Frame, model: str = "") -> list[dict]:
    """Envia um frame para o Google Gemini com fallback automático de modelos."""
    image_part = types.Part.from_bytes(data=frame.png_bytes, mime_type="image/png")
    prompt = f"Inspecione a pessoa no frame no timestamp {frame.timestamp_label}. Verifique se está sem capacete conforme as NRs. OBS: Versão limitada para teste, inspecione apenas capacete."

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1,
    )

    models_to_try = [model] if (model and model in CANDIDATE_MODELS) else []
    for m in CANDIDATE_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for m in models_to_try:
        try:
            response = client.models.generate_content(
                model=m,
                contents=[image_part, prompt],
                config=config,
            )

            text = response.text or "{}"
            data = json.loads(text)
            ocorrencias = data.get("ocorrencias", [])

            for occ in ocorrencias:
                occ["timestamp"] = frame.timestamp_label

            return ocorrencias
        except Exception as e:
            last_error = e
            print(f"[Gemini Model {m} Error] {e}", file=sys.stderr)
            continue

    print(f"[Gemini All Models Failed] Last error: {last_error}. Ativando fallback OpenCV local.", file=sys.stderr)
    from .demo_analyzer import analyze_frame_demo
    fallback_occs = analyze_frame_demo(frame)
    for occ in fallback_occs:
        occ["risco"] = f"{occ['risco']} (Detectado via OpenCV Local após limite da API)"
    return fallback_occs

