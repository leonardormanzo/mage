from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import CalendarEvent, EventDraft


class CalendarConflictError(RuntimeError):
    pass


class CalendarAdapter(ABC):
    @abstractmethod
    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        raise NotImplementedError

    @abstractmethod
    def get_event(self, event_id: str) -> CalendarEvent:
        raise NotImplementedError

    @abstractmethod
    def create_event(self, draft: EventDraft, request_id: str) -> CalendarEvent:
        raise NotImplementedError

    @abstractmethod
    def update_event(self, event_id: str, draft: EventDraft, etag: str) -> CalendarEvent:
        raise NotImplementedError

    @abstractmethod
    def delete_event(self, event_id: str, etag: str) -> None:
        raise NotImplementedError

