from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS open_items(id INTEGER PRIMARY KEY,label TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY,label TEXT NOT NULL,period TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS synced_events(id TEXT PRIMARY KEY,title TEXT NOT NULL,start TEXT NOT NULL,"end" TEXT NOT NULL,location TEXT,all_day INTEGER NOT NULL DEFAULT 0);
"""


def default_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", ".")) / "SiteDiary" / "Calendar"
    base.mkdir(parents=True, exist_ok=True)
    return base / "board.db"


class BoardStore:
    """Persistência local do painel público: itens em aberto, metas e o
    último retrato da agenda sincronizada (para publicar mesmo offline)."""

    def __init__(self, path: Path | None = None):
        self.path = path or default_path()
        with self._connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connect() as con:
            return [dict(r) for r in con.execute(sql, params).fetchall()]

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._connect() as con:
            return int(con.execute(sql, params).lastrowid)

    # Itens em aberto
    def open_items(self) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM open_items ORDER BY created_at")

    def add_open_item(self, label: str) -> int:
        label = label.strip()
        if not label:
            raise ValueError("Descreva o item em aberto.")
        return self._execute("INSERT INTO open_items(label) VALUES(?)", (label,))

    def toggle_open_item(self, item_id: int) -> None:
        self._execute("UPDATE open_items SET done=CASE done WHEN 0 THEN 1 ELSE 0 END WHERE id=?", (item_id,))

    def remove_open_item(self, item_id: int) -> None:
        self._execute("DELETE FROM open_items WHERE id=?", (item_id,))

    # Metas (period: "semana" ou "geral")
    def goals(self, period: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM goals WHERE period=? ORDER BY id", (period,))

    def add_goal(self, label: str, period: str) -> int:
        label = label.strip()
        if not label:
            raise ValueError("Descreva a meta.")
        return self._execute("INSERT INTO goals(label,period) VALUES(?,?)", (label, period))

    def remove_goal(self, goal_id: int) -> None:
        self._execute("DELETE FROM goals WHERE id=?", (goal_id,))

    # Retrato da agenda sincronizada
    def store_synced_events(self, events) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM synced_events")
            con.executemany(
                'INSERT INTO synced_events(id,title,start,"end",location,all_day) VALUES(?,?,?,?,?,?)',
                [(e.id, e.title, e.start.isoformat(), e.end.isoformat(), e.location, int(e.all_day)) for e in events],
            )

    def synced_events(self) -> list[dict[str, Any]]:
        return self._rows('SELECT * FROM synced_events ORDER BY start')
