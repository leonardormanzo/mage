from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .models import EventDraft


WEEKDAYS = {"segunda": 0, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6}


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def parse_event(text: str, now: datetime | None = None) -> EventDraft:
    if now is None:
        try:
            now = datetime.now(ZoneInfo("America/Sao_Paulo"))
        except Exception:
            now = datetime.now(timezone(timedelta(hours=-3)))
    raw = normalize(text)
    time_match = re.search(r"\b(\d{1,2})(?::|h)(\d{2})?\b", raw)
    hour = int(time_match.group(1)) if time_match else 9
    minute = int(time_match.group(2) or 0) if time_match else 0
    if hour > 23 or minute > 59:
        raise ValueError("Horário inválido.")
    date_match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b", raw)
    target = now
    if "amanha" in raw:
        target = now + timedelta(days=1)
    elif date_match:
        year = int(date_match.group(3) or now.year)
        target = now.replace(year=year, month=int(date_match.group(2)), day=int(date_match.group(1)))
    else:
        for name, weekday in WEEKDAYS.items():
            if name in raw:
                delta = (weekday - now.weekday()) % 7 or 7
                target = now + timedelta(days=delta)
                break
    start = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
    duration_match = re.search(r"(?:por|duracao de)\s*(\d+)\s*(hora|horas|min|minutos)", raw)
    if duration_match:
        number = int(duration_match.group(1))
        duration = timedelta(hours=number) if duration_match.group(2).startswith("hora") else timedelta(minutes=number)
    else:
        duration = timedelta(hours=1)
    title = text
    for pattern in (r"\bamanh[ãa]\b", r"\bhoje\b", r"\b(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)(?:-feira)?\b",
                    r"\b\d{1,2}/\d{1,2}(?:/\d{4})?\b", r"\b(?:às|as)?\s*\d{1,2}(?::|h)\d{0,2}\b",
                    r"\b(?:por|duração de|duracao de)\s*\d+\s*(?:hora|horas|min|minutos)\b"):
        title = re.sub(pattern, "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" ,-")
    draft = EventDraft(title=title.capitalize() or "Compromisso", start=start, end=start + duration)
    draft.validate()
    return draft
