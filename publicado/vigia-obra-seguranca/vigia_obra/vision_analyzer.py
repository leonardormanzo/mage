"""Chamada à API Claude (visão) para análise de segurança do trabalho por frame."""

import base64
import json

import anthropic

from .frame_extractor import Frame

SYSTEM_PROMPT = """\
Persona:
Você é um agente de visão computacional especializado em segurança do trabalho em canteiros de obra, atuando como apoio a um SESMT (Serviço de Segurança do Trabalho). Você não substitui inspeção humana — sinaliza riscos para revisão de um técnico.

Contexto:
Você recebe um frame extraído de um vídeo de canteiro de obra. O objetivo é detectar não-conformidades de segurança visíveis e associá-las às normas regulamentadoras brasileiras aplicáveis (NR-18: condições de construção civil; NR-6: EPI; NR-35: trabalho em altura).

Objetivo:
Verificar a presença/ausência dos seguintes itens quando aplicável à cena:
- Capacete de segurança
- Cinto de segurança / trava-quedas (quando houver trabalho em altura ou próximo a bordas)
- Sinalização de área de risco (cones, fitas, placas)
- Guarda-corpo / proteção lateral em andaimes ou aberturas

Só reporte uma não-conformidade quando a confiança da detecção for razoável. Quando a cena for ambígua (ex: capacete parcialmente oculto, ângulo ruim), classifique como "incerto" em vez de afirmar ausência.

Como trabalhar:
1. Se houver pessoas ou estrutura de risco visível no frame, identifique os itens de segurança esperados na cena.
2. Compare com o que está de fato visível.
3. Para cada não-conformidade ou caso incerto, registre: descrição do risco, norma e item correspondente, nível de confiança (alto/médio/baixo), severidade estimada (baixa/média/alta).
4. Se o frame não tiver pessoas nem elementos de risco relevantes, retorne uma lista vazia.
5. Não gere um veredito geral de "aprovado/reprovado" — apenas liste as ocorrências encontradas neste frame.

Regras de interação:
- Nunca afirme certeza absoluta sobre um risco não visível com clareza — use "incerto" no campo de confiança quando aplicável.
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ocorrencias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risco": {"type": "string", "description": "Descrição curta do risco"},
                    "norma": {"type": "string", "description": "Ex: 'NR-18, item 18.15'"},
                    "confianca": {"type": "string", "enum": ["alto", "medio", "baixo"]},
                    "severidade": {"type": "string", "enum": ["baixa", "media", "alta"]},
                },
                "required": ["risco", "norma", "confianca", "severidade"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ocorrencias"],
    "additionalProperties": False,
}


def analyze_frame(client: anthropic.Anthropic, frame: Frame, model: str, effort: str) -> list[dict]:
    """Envia um frame para o Claude e retorna a lista de ocorrências detectadas."""
    image_b64 = base64.standard_b64encode(frame.png_bytes).decode("utf-8")

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        output_config={
            "effort": effort,
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Frame do vídeo no timestamp {frame.timestamp_label}. Analise conforme as instruções.",
                    },
                ],
            }
        ],
    )

    if response.stop_reason == "refusal":
        return []

    text = next((block.text for block in response.content if block.type == "text"), "{}")
    data = json.loads(text)
    ocorrencias = data.get("ocorrencias", [])

    for ocorrencia in ocorrencias:
        ocorrencia["timestamp"] = frame.timestamp_label

    return ocorrencias
