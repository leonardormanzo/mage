from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any

from .db import Database
from .service import AgendaService

ANIM_STEPS = 24
ANIM_DURATION = 0.32  # segundos, mesma sensação do cubic-bezier(.2,.8,.2,1) do modelo


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


class Api:
    def __init__(self, db: Database | None = None, service: AgendaService | None = None) -> None:
        self.db = db or Database()
        self.service = service or AgendaService(self.db)
        self._window = None
        self._expanded: dict[str, int] = {}
        self._collapsed: dict[str, int] = {}

    def bind_window(self, window, expanded: dict[str, int], collapsed: dict[str, int]) -> None:
        self._window, self._expanded, self._collapsed = window, expanded, collapsed

    def collapse_window(self): return self._call(self._animate_to, self._collapsed)
    def expand_window(self): return self._call(self._animate_to, self._expanded)
    def close_window(self):
        if self._window is not None:
            self._window.destroy()

    def _animate_to(self, target: dict[str, int]) -> None:
        if self._window is None or not target:
            return
        window = self._window
        start = {"width": window.width, "height": window.height, "x": window.x, "y": window.y}
        delay = ANIM_DURATION / ANIM_STEPS
        for step in range(1, ANIM_STEPS + 1):
            t = _ease_out(step / ANIM_STEPS)
            window.resize(
                round(start["width"] + (target["width"] - start["width"]) * t),
                round(start["height"] + (target["height"] - start["height"]) * t),
            )
            window.move(
                round(start["x"] + (target["x"] - start["x"]) * t),
                round(start["y"] + (target["y"] - start["y"]) * t),
            )
            time.sleep(delay)

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
    def save_open_item(self, data: dict[str, Any]): return self._call(self.service.save_open_item, data)
    def toggle_open_item(self, item_id: int): return self._call(self.service.toggle_open_item, int(item_id))
    def delete_open_item(self, item_id: int): return self._call(self.service.delete_open_item, int(item_id))
    def publish(self): return self._call(self.service.publish_snapshot)
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
