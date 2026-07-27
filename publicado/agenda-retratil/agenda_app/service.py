from __future__ import annotations

from datetime import datetime
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
                self.db.execute("UPDATE sync_state SET last_sync=?,status='sincronizado',message='' WHERE id=1",
                                (datetime.now().isoformat(timespec="seconds"),))
                sync = self.db.rows("SELECT * FROM sync_state WHERE id=1")[0]
            except Exception as exc:
                sync = {**sync, "status": "erro", "message": str(exc)}
        return {"connected": connected, "sync": sync, "events": events,
                "goals": self.db.rows("SELECT * FROM goals ORDER BY period,id"),
                "suggestions": self.db.rows("SELECT * FROM suggestions ORDER BY starts_at")}

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

