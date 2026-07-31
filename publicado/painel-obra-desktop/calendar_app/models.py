from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    title: str
    start: datetime | date
    end: datetime | date
    location: str | None = None
    html_link: str | None = None
    etag: str | None = None
    recurring_event_id: str | None = None

    @property
    def all_day(self) -> bool:
        return isinstance(self.start, date) and not isinstance(self.start, datetime)

    def public_projection(self) -> dict[str, Any]:
        """Return only fields explicitly approved for public sharing."""
        return {
            "source_id": self.id,
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "all_day": self.all_day,
            "location": self.location,
        }


@dataclass(frozen=True)
class EventDraft:
    title: str
    start: datetime | date
    end: datetime | date
    location: str | None = None
    description: str | None = None

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("O título é obrigatório.")
        if type(self.start) is not type(self.end):
            raise ValueError("Início e término devem usar o mesmo tipo.")
        if self.end <= self.start:
            raise ValueError("O término deve ser posterior ao início.")

