from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from .db import Database
from .services import CondominiumService, DocumentService


class Api:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()
        self.ops = CondominiumService(self.db)
        self.docs = DocumentService(self.db)

    def _result(self, fn, *args, **kwargs) -> dict[str, Any]:
        try:
            return {"ok": True, "data": fn(*args, **kwargs)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def bootstrap(self) -> dict[str, Any]:
        return {"ok": True, "data": {
            "dashboard": self.ops.dashboard(),
            "documents": self.docs.list_documents(),
            **{name: self.ops.list(name) for name in
               ("occurrences", "tasks", "announcements", "contacts", "spaces", "reservations")}
        }}

    def list_entity(self, entity: str) -> dict[str, Any]:
        return self._result(self.ops.list, entity)

    def preview(self, action: str, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "data": {"action": action, "entity": entity, "payload": data}}

    def commit(self, action: str, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        if action == "delete":
            return self._result(self.ops.delete, entity, int(data["id"]))
        if entity == "reservations":
            return self._result(self.ops.reserve, data)
        return self._result(self.ops.save, entity, data)

    def choose_pdf(self) -> dict[str, Any]:
        try:
            import webview
            paths = webview.windows[0].create_file_dialog(
                webview.FileDialog.OPEN, allow_multiple=False, file_types=("PDF (*.pdf)",)
            )
            return {"ok": True, "data": paths[0] if paths else None}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def import_pdf(self, path: str) -> dict[str, Any]:
        return self._result(self.docs.import_pdf, path)

    def delete_document(self, doc_id: int) -> dict[str, Any]:
        return self._result(self.docs.delete_document, int(doc_id))

    def ask_documents(self, question: str) -> dict[str, Any]:
        return self._result(self.docs.ask, question)

    def backup(self) -> dict[str, Any]:
        return self._result(self.db.backup)

    def export_data(self) -> dict[str, Any]:
        return self._result(self.db.export_json)


def web_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "web"
    return Path(__file__).parent / "web"
