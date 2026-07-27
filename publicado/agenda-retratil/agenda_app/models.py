from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    title: str
    start: datetime | date
    end: datetime | date
    location: str | None = None
    etag: str | None = None
    html_link: str | None = None

    def public_projection(self) -> dict[str, Any]:
        return {
            "id": self.id, "title": self.title,
            "start": self.start.isoformat(), "end": self.end.isoformat(),
            "location": self.location, "etag": self.etag, "html_link": self.html_link,
            "all_day": isinstance(self.start, date) and not isinstance(self.start, datetime),
        }


@dataclass(frozen=True)
class EventDraft:
    title: str
    start: datetime
    end: datetime
    location: str | None = None
    description: str | None = None

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("O título é obrigatório.")
        if self.end <= self.start:
            raise ValueError("O término deve ser posterior ao início.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Goal:
    id: int
    label: str
    period: str
    done: bool


@dataclass(frozen=True)
class ScheduleSuggestion:
    id: int
    title: str
    starts_at: str
    ends_at: str
    status: str


@dataclass(frozen=True)
class CalendarConnection:
    connected: bool
    account: str | None = None


@dataclass(frozen=True)
class SyncState:
    last_sync: str | None
    status: str
    message: str = ""

