from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from .db import Database
from .service import AgendaService


class Api:
    def __init__(self, db: Database | None = None, service: AgendaService | None = None) -> None:
        self.db = db or Database()
        self.service = service or AgendaService(self.db)

    def _call(self, fn, *args) -> dict[str, Any]:
        try:
            return {"ok": True, "data": fn(*args)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def bootstrap(self): return self._call(self.service.bootstrap)
    def parse_event(self, text: str): return self._call(self.service.parse, text)
    def commit_event(self, action: str, data: dict[str, Any]):
        return self._call({"create": self.service.create, "update": self.service.update, "delete": self.service.delete}[action], data)
    def save_goal(self, data: dict[str, Any]): return self._call(self.service.save_goal, data)
    def toggle_goal(self, goal_id: int): return self._call(self.service.toggle_goal, int(goal_id))
    def save_suggestion(self, data: dict[str, Any]): return self._call(self.service.save_suggestion, data)
    def respond_suggestion(self, suggestion_id: int, accepted: bool):
        return self._call(self.service.respond_suggestion, int(suggestion_id), accepted)
    def backup(self): return self._call(self.db.backup)
    def export_data(self): return self._call(self.db.export_json)

    def choose_google_credentials(self):
        try:
            import webview
            paths = webview.windows[0].create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False,
                file_types=("Credencial Google (*.json)",))
            return {"ok": True, "data": paths[0] if paths else None}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def connect_google(self, path: str): return self._call(self.service.calendar.connect, path)
    def disconnect_google(self): return self._call(self.service.calendar.disconnect)


def web_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "web"
    return Path(__file__).parent / "web"
