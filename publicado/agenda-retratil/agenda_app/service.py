from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .db import Database
from .google_calendar import GoogleCalendar
from .models import EventDraft
from .parser import parse_event


class AgendaService:
    def __init__(self, db: Database, calendar: GoogleCalendar | None = None) -> None:
        self.db, self.calendar = db, calendar or GoogleCalendar()

    def bootstrap(self) -> dict[str, Any]:
        sync = self.db.rows("SELECT * FROM sync_state WHERE id=1")[0]
        events: list[dict[str, Any]] = []
        connected = self.calendar.connected
        if connected:
            try:
                events = self.calendar.list_events()
                self._store_synced_events(events)
                self.db.execute("UPDATE sync_state SET last_sync=?,status='sincronizado',message='' WHERE id=1",
                                (datetime.now().isoformat(timespec="seconds"),))
                sync = self.db.rows("SELECT * FROM sync_state WHERE id=1")[0]
            except Exception as exc:
                sync = {**sync, "status": "erro", "message": str(exc)}
        return {"connected": connected, "sync": sync, "events": events,
                "goals": self.db.rows("SELECT * FROM goals ORDER BY period,id"),
                "open_items": self.db.rows("SELECT * FROM open_items ORDER BY created_at"),
                "suggestions": self.db.rows("SELECT * FROM suggestions ORDER BY starts_at")}

    def _store_synced_events(self, events: list[dict[str, Any]]) -> None:
        with self.db.connect() as con:
            con.execute("DELETE FROM synced_events")
            con.executemany(
                "INSERT INTO synced_events(id,title,start,end,location,html_link) VALUES(?,?,?,?,?,?)",
                [(e["id"], e["title"], e["start"], e["end"], e.get("location"), e.get("html_link")) for e in events],
            )

    def parse(self, text: str) -> dict[str, Any]:
        draft = parse_event(text)
        return {"title": draft.title, "start": draft.start.isoformat(),
                "end": draft.end.isoformat(), "location": draft.location, "description": draft.description,
                "request_id": str(uuid4())}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        draft = self._draft(data)
        return self.calendar.create_event(draft, data.get("request_id") or str(uuid4()))

    def update(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.calendar.update_event(data["id"], self._draft(data), data.get("etag"))

    def delete(self, data: dict[str, Any]) -> None:
        self.calendar.delete_event(data["id"], data.get("etag"))

    def save_goal(self, data: dict[str, Any]) -> int:
        if data.get("id"):
            self.db.execute("UPDATE goals SET label=?,period=?,done=? WHERE id=?",
                            (data["label"], data["period"], int(bool(data.get("done"))), data["id"]))
            return int(data["id"])
        return self.db.execute("INSERT INTO goals(label,period,done) VALUES(?,?,?)",
                               (data["label"], data.get("period", "diaria"), int(bool(data.get("done")))))

    def toggle_goal(self, goal_id: int) -> None:
        self.db.execute("UPDATE goals SET done=CASE done WHEN 0 THEN 1 ELSE 0 END WHERE id=?", (goal_id,))

    def save_open_item(self, data: dict[str, Any]) -> int:
        label = data["label"].strip()
        if not label:
            raise ValueError("Descreva o item em aberto.")
        return self.db.execute("INSERT INTO open_items(label) VALUES(?)", (label,))

    def toggle_open_item(self, item_id: int) -> None:
        self.db.execute("UPDATE open_items SET done=CASE done WHEN 0 THEN 1 ELSE 0 END WHERE id=?", (item_id,))

    def delete_open_item(self, item_id: int) -> None:
        self.db.execute("DELETE FROM open_items WHERE id=?", (item_id,))

    def publish_snapshot(self, output_dir: str | None = None) -> str:
        from .publish import render_snapshot

        payload = {
            "open_items": self.db.rows("SELECT * FROM open_items WHERE done=0 ORDER BY created_at"),
            "weekly_goals": self.db.rows("SELECT * FROM goals WHERE period='semana' ORDER BY id"),
            "general_goals": self.db.rows("SELECT * FROM goals WHERE period='geral' ORDER BY id"),
            "events": self.db.rows("SELECT * FROM synced_events ORDER BY start"),
            "sync": self.db.rows("SELECT * FROM sync_state WHERE id=1")[0],
        }
        target = Path(output_dir) if output_dir else self._default_publish_dir()
        target.mkdir(parents=True, exist_ok=True)
        out_file = target / "index.html"
        out_file.write_text(render_snapshot(payload), encoding="utf-8")
        return str(out_file)

    def _default_publish_dir(self) -> Path:
        import sys

        if getattr(sys, "frozen", False):
            return self.db.data_dir / "painel-obra"
        # agenda_app/ -> agenda-retratil/ -> publicado/ -> irmão "painel-obra"
        return Path(__file__).resolve().parents[2] / "painel-obra"

    def save_suggestion(self, data: dict[str, Any]) -> int:
        return self.db.execute("""INSERT INTO suggestions(title,starts_at,ends_at,status,location,description)
            VALUES(?,?,?,'pendente',?,?)""",
            (data["title"], data["start"], data["end"], data.get("location"), data.get("description")))

    def respond_suggestion(self, suggestion_id: int, accepted: bool) -> dict[str, Any] | None:
        rows = self.db.rows("SELECT * FROM suggestions WHERE id=?", (suggestion_id,))
        if not rows:
            raise ValueError("Sugestão não encontrada.")
        row = rows[0]
        event = self.create({"title": row["title"], "start": row["starts_at"], "end": row["ends_at"],
                             "location": row["location"], "description": row["description"]}) if accepted else None
        self.db.execute("UPDATE suggestions SET status=? WHERE id=?", ("aceita" if accepted else "recusada", suggestion_id))
        return event

    @staticmethod
    def _draft(data: dict[str, Any]) -> EventDraft:
        start = datetime.fromisoformat(data["start"])
        end = datetime.fromisoformat(data["end"])
        draft = EventDraft(data["title"], start, end, data.get("location"), data.get("description"))
        draft.validate()
        return draft

