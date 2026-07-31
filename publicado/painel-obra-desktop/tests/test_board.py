import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from calendar_app.board import BoardStore
from calendar_app.models import CalendarEvent
from calendar_app.publish import render_snapshot


class BoardStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = BoardStore(Path(self.temp.name) / "board.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_open_item_add_toggle_remove(self):
        item_id = self.store.add_open_item("Liberar acesso do fornecedor")
        self.assertEqual(1, len(self.store.open_items()))
        self.store.toggle_open_item(item_id)
        self.assertTrue(self.store.open_items()[0]["done"])
        self.store.remove_open_item(item_id)
        self.assertEqual([], self.store.open_items())

    def test_goals_separated_by_period(self):
        self.store.add_goal("Concretar laje 3", "semana")
        self.store.add_goal("Zero acidentes no trimestre", "geral")
        self.assertEqual(["Concretar laje 3"], [g["label"] for g in self.store.goals("semana")])
        self.assertEqual(["Zero acidentes no trimestre"], [g["label"] for g in self.store.goals("geral")])

    def test_synced_events_snapshot_roundtrip(self):
        now = datetime(2026, 8, 1, 9, tzinfo=timezone.utc)
        events = [CalendarEvent("a", "Vistoria", now, now, location="Obra")]
        self.store.store_synced_events(events)
        rows = self.store.synced_events()
        self.assertEqual(1, len(rows))
        self.assertEqual("Vistoria", rows[0]["title"])

    def test_render_snapshot_includes_board_content(self):
        self.store.add_open_item("Liberar acesso do fornecedor")
        self.store.add_goal("Concretar laje 3", "semana")
        self.store.add_goal("Zero acidentes no trimestre", "geral")
        html = render_snapshot(self.store)
        self.assertIn("Liberar acesso do fornecedor", html)
        self.assertIn("Concretar laje 3", html)
        self.assertIn("Zero acidentes no trimestre", html)


if __name__ == "__main__":
    unittest.main()
