from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sindico_app.db import Database
from sindico_app.services import CondominiumService


class CondominiumServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "test.db")
        self.service = CondominiumService(self.db)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_migrations_create_all_operational_tables(self) -> None:
        names = {row["name"] for row in self.db.rows("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"documents", "occurrences", "tasks", "announcements", "contacts", "spaces", "reservations"} <= names)

    def test_reservation_conflict_is_rejected(self) -> None:
        space_id = self.service.save("spaces", {"name": "Salão", "rules": "", "opens_at": "08:00", "closes_at": "22:00"})
        self.service.reserve({"space_id": space_id, "title": "Festa A", "starts_at": "2026-08-01T18:00", "ends_at": "2026-08-01T20:00"})
        with self.assertRaisesRegex(ValueError, "já está reservado"):
            self.service.reserve({"space_id": space_id, "title": "Festa B", "starts_at": "2026-08-01T19:00", "ends_at": "2026-08-01T21:00"})

    def test_occurrence_creates_history(self) -> None:
        row_id = self.service.save("occurrences", {"title": "Vazamento", "category": "manutenção", "priority": "alta", "description": ""})
        history = self.db.rows("SELECT * FROM occurrence_history WHERE occurrence_id=?", (row_id,))
        self.assertEqual("aberta", history[0]["status"])

    def test_backup_and_export_exist(self) -> None:
        self.assertTrue(Path(self.db.backup()).is_file())
        self.assertTrue(Path(self.db.export_json()).is_file())


if __name__ == "__main__":
    unittest.main()

