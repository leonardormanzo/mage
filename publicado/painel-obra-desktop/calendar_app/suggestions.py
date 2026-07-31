from __future__ import annotations

import json
import os
from pathlib import Path


class SuggestionStore:
    """Local mirror of change requests waiting for desktop approval."""

    def __init__(self, path: Path | None = None):
        base = Path(os.environ.get("LOCALAPPDATA", ".")) / "SiteDiary" / "Calendar"
        self.path = path or base / "pending_suggestions.json"

    def pending_count(self) -> int:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return 0
        items = payload if isinstance(payload, list) else payload.get("suggestions", [])
        return sum(
            1 for item in items
            if isinstance(item, dict) and item.get("status", "pending") in {"pending", "approved_waiting"}
        )
