from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
INSERT INTO schema_version SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM schema_version);
CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY,label TEXT NOT NULL,period TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS suggestions(
 id INTEGER PRIMARY KEY,title TEXT NOT NULL,starts_at TEXT NOT NULL,ends_at TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pendente',location TEXT,description TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS preferences(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sync_state(id INTEGER PRIMARY KEY CHECK(id=1),last_sync TEXT,status TEXT NOT NULL,message TEXT NOT NULL DEFAULT '');
INSERT OR IGNORE INTO sync_state(id,status,message) VALUES(1,'desconectado','Conecte o Google Agenda para sincronizar.');
"""


def default_dir() -> Path:
    root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return root / "AgendaRetratil"


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        self.data_dir = Path(path).parent if path else default_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = Path(path) if path else self.data_dir / "agenda.db"
        with self.connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as con:
            return [dict(r) for r in con.execute(sql, params).fetchall()]

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self.connect() as con:
            cur = con.execute(sql, params)
            return int(cur.lastrowid)

    def backup(self) -> str:
        out = self.data_dir / f"backup-{datetime.now():%Y%m%d-%H%M%S}.db"
        target = sqlite3.connect(out)
        try:
            with self.connect() as source:
                source.backup(target)
        finally:
            target.close()
        return str(out)

    def export_json(self) -> str:
        payload = {t: self.rows(f"SELECT * FROM {t}") for t in ("goals", "suggestions", "preferences", "sync_state")}
        out = self.data_dir / f"exportacao-{datetime.now():%Y%m%d-%H%M%S}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(out)
