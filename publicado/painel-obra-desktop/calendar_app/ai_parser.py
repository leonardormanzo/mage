from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pydantic import BaseModel

LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


class AppointmentResult(BaseModel):
    understood: bool
    title: str | None
    start: str | None
    end: str | None


@dataclass(frozen=True)
class ParsedAppointment:
    title: str
    start: datetime
    end: datetime


class _ClaudeResponses:
    """Adapta a API de Messages da Anthropic à interface responses.parse()."""

    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def parse(self, **kwargs) -> SimpleNamespace:
        if not self.api_key:
            raise ValueError(
                "Defina ANTHROPIC_API_KEY no .env.local para usar o Claude."
            )
        system = ""
        user = ""
        for message in kwargs.get("input", []):
            if message["role"] == "system":
                system = message["content"]
            elif message["role"] == "user":
                user = message["content"]
        payload = {
            "model": kwargs.get("model", ANTHROPIC_MODEL),
            "max_tokens": 300,
            "system": (
                system
                + " Responda APENAS com JSON válido, sem texto extra, no formato: "
                + '{"understood": bool, "title": str|null, "start": str|null, "end": str|null}'
            ),
            "messages": [{"role": "user", "content": user}],
        }
        request = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise ValueError(
                    "Chave da Anthropic inválida ou revogada (401). "
                    "Gere uma nova em console.anthropic.com e atualize o .env.local."
                ) from error
            if error.code == 429:
                raise ValueError(
                    "Limite ou créditos da API esgotados (429)."
                ) from error
            detail = ""
            try:
                detail = error.read().decode("utf-8")
            except Exception:
                pass
            if "credit balance" in detail:
                raise ValueError(
                    "Sem créditos na API da Anthropic. Adicione créditos em "
                    "console.anthropic.com > Plans & Billing."
                ) from error
            raise ValueError(f"Erro na API do Claude ({error.code}).") from error
        except urllib.error.URLError as error:
            raise ValueError("Sem conexão com a API do Claude.") from error
        text = body["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        result = AppointmentResult.model_validate_json(text.strip())
        return SimpleNamespace(output_parsed=result)


class ClaudeClient:
    def __init__(self, api_key: str | None = None):
        self.responses = _ClaudeResponses(api_key)


def _load_env() -> None:
    """Procura o .env.local na raiz do projeto e na pasta acima dela."""
    project_root = Path(__file__).resolve().parents[1]
    for candidate in (project_root / ".env.local", project_root.parent / ".env.local"):
        if candidate.is_file():
            load_dotenv(candidate)
            return


class AppointmentParser:
    def __init__(self, client=None):
        _load_env()
        self.client = client or ClaudeClient(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    def parse(self, text: str, now: datetime | None = None) -> ParsedAppointment:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Digite um compromisso.")
        now = now or datetime.now(LOCAL_TIMEZONE)
        response = self.client.responses.parse(
            model=ANTHROPIC_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Extraia um compromisso de uma frase em português do Brasil. "
                        "Resolva datas relativas usando a data atual informada. "
                        "Use America/Sao_Paulo e retorne datetimes ISO 8601 com fuso. "
                        "Se não houver duração, use uma hora. "
                        "Se houver horário mas não houver data, assuma hoje caso o horário "
                        "ainda não tenha passado, senão amanhã. "
                        "Se houver data mas não houver horário, assuma 09:00. "
                        "O título pode ser qualquer coisa (evento, jogo, lembrete, tarefa); "
                        "não exija que pareça um compromisso formal. "
                        "Só marque understood=false se não houver nem data nem horário "
                        "reconhecíveis na frase."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Agora: {now.isoformat()}\nCompromisso: {cleaned}",
                },
            ],
        )
        result = response.output_parsed
        if not result or not result.understood or not result.title or not result.start or not result.end:
            raise ValueError("Não entendi, tente novamente.")
        start = datetime.fromisoformat(result.start)
        end = datetime.fromisoformat(result.end)
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ValueError("Não entendi, tente novamente.")
        return ParsedAppointment(result.title.strip(), start, end)
