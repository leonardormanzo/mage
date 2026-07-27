from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agenda_app.db import Database
from agenda_app.parser import parse_event
from agenda_app.service import AgendaService


class FakeCalendar:
    connected = True

    def __init__(self) -> None:
        self.events = []

    def list_events(self, start=None, end=None):
        return list(self.events)

    def create_event(self, draft, request_id):
        event = {"id": request_id, "title": draft.title, "start": draft.start.isoformat(),
                 "end": draft.end.isoformat(), "etag": "v1"}
        self.events.append(event)
        return event

    def update_event(self, event_id, draft, etag):
        if etag != "v1":
            raise RuntimeError("etag divergente")
        return {"id": event_id, "title": draft.title, "etag": "v2"}

    def delete_event(self, event_id, etag):
        if etag != "v1":
            raise RuntimeError("etag divergente")


class AgendaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "test.db")
        self.calendar = FakeCalendar()
        self.service = AgendaService(self.db, self.calendar)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_local_parser_understands_tomorrow_and_duration(self):
        now = datetime(2026, 7, 27, 10, tzinfo=timezone(timedelta(hours=-3)))
        draft = parse_event("Reunião com cliente amanhã às 14h por 2 horas", now)
        self.assertEqual("Reunião com cliente", draft.title)
        self.assertEqual((28, 14), (draft.start.day, draft.start.hour))
        self.assertEqual(2, int((draft.end - draft.start).total_seconds() / 3600))

    def test_goal_persists(self):
        goal_id = self.service.save_goal({"label": "Fechar relatório", "period": "diaria"})
        self.service.toggle_goal(goal_id)
        self.assertEqual(1, self.db.rows("SELECT done FROM goals WHERE id=?", (goal_id,))[0]["done"])

    def test_fake_calendar_create_and_etag_guard(self):
        data = {"title": "Vistoria", "start": "2026-08-01T09:00:00-03:00", "end": "2026-08-01T10:00:00-03:00"}
        created = self.service.create(data)
        self.assertEqual("Vistoria", created["title"])
        with self.assertRaisesRegex(RuntimeError, "etag"):
            self.service.update({**data, "id": created["id"], "etag": "antigo"})

    def test_suggestion_acceptance_creates_event(self):
        suggestion_id = self.service.save_suggestion({"title": "Alinhamento", "start": "2026-08-01T09:00:00-03:00", "end": "2026-08-01T10:00:00-03:00"})
        event = self.service.respond_suggestion(suggestion_id, True)
        self.assertEqual("Alinhamento", event["title"])
        self.assertEqual("aceita", self.db.rows("SELECT status FROM suggestions WHERE id=?", (suggestion_id,))[0]["status"])


if __name__ == "__main__":
    unittest.main()
