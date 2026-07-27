from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
INSERT INTO schema_version SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM schema_version);
CREATE TABLE IF NOT EXISTS documents(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, path TEXT NOT NULL UNIQUE,
 pages INTEGER NOT NULL, indexed_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'indexado'
);
CREATE TABLE IF NOT EXISTS chunks(
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 page INTEGER NOT NULL, content TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(content, content='chunks', content_rowid='id',
 tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
 INSERT INTO chunks_fts(rowid, content) VALUES(new.id, new.content); END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
 INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', old.id, old.content); END;
CREATE TABLE IF NOT EXISTS occurrences(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, priority TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '', due_date TEXT, responsible TEXT, status TEXT NOT NULL DEFAULT 'aberta',
 attachment TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS occurrence_history(
 id INTEGER PRIMARY KEY, occurrence_id INTEGER NOT NULL REFERENCES occurrences(id) ON DELETE CASCADE,
 status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tasks(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, due_date TEXT, responsible TEXT,
 status TEXT NOT NULL DEFAULT 'pendente', occurrence_id INTEGER REFERENCES occurrences(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS announcements(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'rascunho',
 published_at TEXT
);
CREATE TABLE IF NOT EXISTS contacts(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, phone TEXT, email TEXT, notes TEXT
);
CREATE TABLE IF NOT EXISTS spaces(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, rules TEXT NOT NULL DEFAULT '',
 opens_at TEXT NOT NULL DEFAULT '08:00', closes_at TEXT NOT NULL DEFAULT '22:00'
);
CREATE TABLE IF NOT EXISTS reservations(
 id INTEGER PRIMARY KEY, space_id INTEGER NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
 title TEXT NOT NULL, starts_at TEXT NOT NULL, ends_at TEXT NOT NULL, notes TEXT
);
CREATE INDEX IF NOT EXISTS reservations_space_time ON reservations(space_id, starts_at, ends_at);
"""


def default_data_dir() -> Path:
    root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return root / "SindicoInteligente"


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        self.data_dir = Path(path).parent if path else default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = Path(path) if path else self.data_dir / "sindico.db"
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def migrate(self) -> None:
        with self.connect() as con:
            con.executescript(SCHEMA)

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
        tables = ("documents", "occurrences", "occurrence_history", "tasks",
                  "announcements", "contacts", "spaces", "reservations")
        payload = {table: self.rows(f"SELECT * FROM {table}") for table in tables}
        out = self.data_dir / f"exportacao-{datetime.now():%Y%m%d-%H%M%S}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(out)
