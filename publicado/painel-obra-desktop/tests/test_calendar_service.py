from datetime import date, datetime, timedelta, timezone
import tempfile
import unittest
from pathlib import Path
import json

from calendar_app.adapter import CalendarAdapter
from calendar_app.models import CalendarEvent, EventDraft
from calendar_app.service import CalendarService
from calendar_app.suggestions import SuggestionStore


class FakeCalendar(CalendarAdapter):
    def __init__(self):
        self.items = {}
        self.created = 0

    def list_events(self, start, end):
        return sorted(self.items.values(), key=lambda item: item.start)

    def get_event(self, event_id):
        return self.items[event_id]

    def create_event(self, draft, request_id):
        for event in self.items.values():
            if event.id == request_id:
                return event
        self.created += 1
        event = CalendarEvent(request_id, draft.title, draft.start, draft.end, draft.location, etag='"1"')
        self.items[event.id] = event
        return event

    def update_event(self, event_id, draft, etag):
        event = CalendarEvent(event_id, draft.title, draft.start, draft.end, draft.location, etag='"2"')
        self.items[event_id] = event
        return event

    def delete_event(self, event_id, etag):
        del self.items[event_id]


class CalendarServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_next_seven_days_uses_bounded_window(self):
        fake = FakeCalendar()
        now = datetime(2026, 7, 24, 10, tzinfo=timezone.utc)
        fake.items["a"] = CalendarEvent("a", "Reunião", now, now + timedelta(hours=1))
        service = CalendarService(fake, self.state_dir)
        self.assertEqual([item.title for item in service.next_seven_days(now)], ["Reunião"])

    def test_all_day_event(self):
        fake = FakeCalendar()
        fake.items["a"] = CalendarEvent("a", "Feriado", date(2026, 7, 25), date(2026, 7, 26))
        self.assertTrue(CalendarService(fake, self.state_dir).next_seven_days()[0].all_day)

    def test_create_is_idempotent(self):
        fake = FakeCalendar()
        service = CalendarService(fake, self.state_dir)
        draft = EventDraft("Inspeção", date(2026, 8, 1), date(2026, 8, 2))
        service.create(draft, "request-1")
        service.create(draft, "request-1")
        self.assertEqual(fake.created, 1)

    def test_rejects_stale_etag(self):
        fake = FakeCalendar()
        fake.items["a"] = CalendarEvent("a", "Original", date(2026, 8, 1), date(2026, 8, 2), etag='"new"')
        service = CalendarService(fake, self.state_dir)
        with self.assertRaisesRegex(RuntimeError, "Conflito"):
            service.update("a", EventDraft("Novo", date(2026, 8, 1), date(2026, 8, 2)), '"old"')

    def test_public_projection_excludes_private_fields(self):
        event = CalendarEvent("a", "Reunião", date(2026, 8, 1), date(2026, 8, 2), location="Obra")
        self.assertEqual(
            set(event.public_projection()),
            {"source_id", "title", "start", "end", "all_day", "location"},
        )

    def test_notification_count_only_includes_pending_requests(self):
        path = self.state_dir / "pending_suggestions.json"
        path.write_text(json.dumps([
            {"status": "pending"},
            {"status": "approved_waiting"},
            {"status": "applied"},
            {"status": "rejected"},
        ]), encoding="utf-8")
        self.assertEqual(SuggestionStore(path).pending_count(), 2)


if __name__ == "__main__":
    unittest.main()
