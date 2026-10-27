from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

UNITS = {
    "saco": "sacos",
    "sacos": "sacos",
    "kg": "kg",
    "quilo": "kg",
    "quilos": "kg",
    "m3": "m³",
    "m³": "m³",
    "metro": "m",
    "metros": "m",
    "unidade": "unidades",
    "unidades": "unidades",
    "peca": "peças",
    "pecas": "peças",
}
KNOWN_MATERIALS = ("cimento", "concreto", "areia", "argamassa", "bloco", "tijolo", "aço")


def normalize(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value.lower())
        if unicodedata.category(char) != "Mn"
    )


@dataclass
class Extraction:
    record_type: str
    quantity: Decimal | None
    unit: str | None
    material_name: str | None
    service: str | None
    location: str | None
    missing_fields: list[str]
    confidence: Decimal
    evidence: str


def extract_message(content: str) -> Extraction:
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.ai_mode:
        from app.services.ai import GeminiProvider
        provider = GeminiProvider(api_key=settings.gemini_api_key)
        prompt = f"""
Extraia os dados da mensagem da obra: "{content}"
Responda APENAS em formato JSON válido e sem blocos markdown:
{{
  "record_type": "material_consumed" ou "material_received" ou "service",
  "quantity": número ou null,
  "unit": string ou null,
  "material_name": string ou null,
  "service": string ou null,
  "location": string ou null
}}
"""
        try:
            import json
            response = provider.answer(prompt, [])
            clean_json = response.strip("`").replace("json\n", "").strip()
            data = json.loads(clean_json)
            
            missing = []
            if data.get("record_type") in ("material_consumed", "material_received"):
                if data.get("quantity") is None: missing.append("quantity")
                if data.get("unit") is None: missing.append("unit")
                if data.get("material_name") is None: missing.append("material_name")
                if data.get("service") is None: missing.append("service")
            
            return Extraction(
                data.get("record_type", "service"),
                Decimal(str(data["quantity"])) if data.get("quantity") is not None else None,
                data.get("unit"),
                data.get("material_name"),
                data.get("service"),
                data.get("location"),
                missing,
                Decimal("0.950"),
                content
            )
        except Exception:
            pass # fallback to rule-based

    text = normalize(content)
    consumption_words = ("usamos", "consumimos", "utilizamos", "gastei", "consumo")
    received_words = ("recebemos", "chegou", "entregue", "entrada")
    if any(word in text for word in consumption_words):
        record_type = "material_consumed"
    elif any(word in text for word in received_words):
        record_type = "material_received"
    else:
        return Extraction(
            "service", None, None, None, content.strip(), None, [], Decimal("0.650"), content
        )

    match = re.search(
        r"(?P<quantity>\d+(?:[.,]\d+)?)\s*(?P<unit>sacos?|kg|quilos?|m[³3]|metros?|unidades?|pecas?)?",
        text,
    )
    quantity = None
    unit = None
    if match:
        try:
            quantity = Decimal(match.group("quantity").replace(",", "."))
        except InvalidOperation:
            quantity = None
        raw_unit = match.group("unit")
        unit = UNITS.get(raw_unit) if raw_unit else None

    material = next((name for name in KNOWN_MATERIALS if name in text), None)
    service_match = re.search(r"(?:na|no|para|em)\s+(.+)$", text)
    service = service_match.group(1).strip(" .") if service_match else None
    if service and material and service == material:
        service = None

    missing = []
    if quantity is None:
        missing.append("quantity")
    if unit is None:
        missing.append("unit")
    if material is None:
        missing.append("material_name")
    if service is None:
        missing.append("service")
    completeness = Decimal(len(missing)) * Decimal("0.08")
    return Extraction(
        record_type,
        quantity,
        unit,
        material,
        service,
        None,
        missing,
        max(Decimal("0.500"), Decimal("0.920") - completeness),
        content,
    )


def next_question(field: str) -> str:
    return {
        "quantity": "Qual foi a quantidade?",
        "unit": "Qual é a unidade? Ex.: sacos, kg ou m³.",
        "material_name": "Qual é o material?",
        "service": "Em qual serviço foi usado?",
        "location": "Em qual local da obra?",
    }.get(field, "Pode completar essa informação?")


def summary_text(record) -> str:
    if record.record_type == "service":
        return f"Confirmar serviço executado: {record.service}?"
    action = "consumo" if record.record_type == "material_consumed" else "entrada"
    quantity = f"{record.quantity:g}" if record.quantity is not None else "Não informado"
    return (
        f"Confirmar {action}: {quantity} {record.unit} de {record.material_name} "
        f"no serviço {record.service}?"
    )
