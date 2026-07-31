from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable
from .adapter import CalendarAdapter
from .models import CalendarEvent, EventDraft


class CalendarService:
    def __init__(self, adapter: CalendarAdapter, state_dir: Path | None = None):
        self.adapter = adapter
        base = state_dir or Path(os.environ.get("LOCALAPPDATA", ".")) / "SiteDiary" / "Calendar"
        base.mkdir(parents=True, exist_ok=True)
        self.state_file = base / "state.json"

    def next_seven_days(self, now: datetime | None = None) -> list[CalendarEvent]:
        now = now or datetime.now().astimezone()
        return self.adapter.list_events(now, now + timedelta(days=7))

    def create(self, draft: EventDraft, request_id: str | None = None) -> CalendarEvent:
        event = self.adapter.create_event(draft, request_id or str(uuid.uuid4()))
        self._remember(event)
        return event

    def update(self, event_id: str, draft: EventDraft, expected_etag: str) -> CalendarEvent:
        current = self.adapter.get_event(event_id)
        if current.etag != expected_etag:
            raise RuntimeError("Conflito: revise a versão atual antes de confirmar.")
        event = self.adapter.update_event(event_id, draft, expected_etag)
        self._remember(event)
        return event

    def delete(self, event_id: str, expected_etag: str) -> None:
        current = self.adapter.get_event(event_id)
        if current.etag != expected_etag:
            raise RuntimeError("Conflito: revise a versão atual antes de excluir.")
        self.adapter.delete_event(event_id, expected_etag)

    def _remember(self, event: CalendarEvent) -> None:
        state = {}
        if self.state_file.exists():
            try:
                state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                state = {}
        state[event.id] = {"etag": event.etag, "html_link": event.html_link}
        self.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def run_async(action: Callable, on_success: Callable, on_error: Callable) -> None:
    def worker():
        try:
            result = action()
        except Exception as exc:
            on_error(exc)
        else:
            on_success(result)
    threading.Thread(target=worker, daemon=True).start()
