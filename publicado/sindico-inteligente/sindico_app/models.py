from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Document:
    id: int
    name: str
    path: str
    pages: int
    indexed_at: str
    status: str = "indexado"


@dataclass(frozen=True)
class SourceChunk:
    id: int
    document_id: int
    page: int
    content: str


@dataclass(frozen=True)
class Occurrence:
    id: int
    title: str
    category: str
    priority: str
    description: str
    due_date: str | None
    responsible: str | None
    status: str
    attachment: str | None = None


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    due_date: str | None
    responsible: str | None
    status: str
    occurrence_id: int | None = None


@dataclass(frozen=True)
class Announcement:
    id: int
    title: str
    body: str
    status: str
    published_at: str | None = None


@dataclass(frozen=True)
class Contact:
    id: int
    name: str
    kind: str
    phone: str | None
    email: str | None
    notes: str | None


@dataclass(frozen=True)
class Space:
    id: int
    name: str
    rules: str
    opens_at: str
    closes_at: str


@dataclass(frozen=True)
class Reservation:
    id: int
    space_id: int
    title: str
    starts_at: str
    ends_at: str
    notes: str | None


def as_dict(value: Any) -> dict[str, Any]:
    return asdict(value)

