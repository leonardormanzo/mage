from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import Database


ALLOWED_ENTITIES = {
    "occurrences": {"title", "category", "priority", "description", "due_date", "responsible", "status", "attachment"},
    "tasks": {"title", "due_date", "responsible", "status", "occurrence_id"},
    "announcements": {"title", "body", "status", "published_at"},
    "contacts": {"name", "kind", "phone", "email", "notes"},
    "spaces": {"name", "rules", "opens_at", "closes_at"},
}


class CondominiumService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def dashboard(self) -> dict[str, Any]:
        now = datetime.now().isoformat(timespec="minutes")
        def count(table: str, where: str = "1=1", args: tuple[Any, ...] = ()) -> int:
            return int(self.db.rows(f"SELECT COUNT(*) n FROM {table} WHERE {where}", args)[0]["n"])
        return {
            "open_occurrences": count("occurrences", "status NOT IN ('resolvida','cancelada')"),
            "overdue_tasks": count("tasks", "status!='concluida' AND due_date IS NOT NULL AND due_date < ?", (now[:10],)),
            "upcoming_reservations": count("reservations", "starts_at >= ?", (now,)),
            "documents": count("documents"),
            "recent_documents": self.db.rows("SELECT * FROM documents ORDER BY indexed_at DESC LIMIT 4"),
            "recent_occurrences": self.db.rows("SELECT * FROM occurrences ORDER BY id DESC LIMIT 5"),
        }

    def list(self, entity: str) -> list[dict[str, Any]]:
        if entity not in ALLOWED_ENTITIES and entity != "reservations":
            raise ValueError("Entidade inválida.")
        order = "starts_at" if entity == "reservations" else "id DESC"
        if entity == "reservations":
            return self.db.rows("""SELECT r.*, s.name space_name FROM reservations r
                JOIN spaces s ON s.id=r.space_id ORDER BY r.starts_at""")
        return self.db.rows(f"SELECT * FROM {entity} ORDER BY {order}")

    def save(self, entity: str, data: dict[str, Any]) -> int:
        allowed = ALLOWED_ENTITIES.get(entity)
        if not allowed:
            raise ValueError("Entidade inválida.")
        clean = {k: v for k, v in data.items() if k in allowed}
        if not clean:
            raise ValueError("Nenhum campo válido.")
        row_id = clean.pop("id", None)
        if row_id:
            fields = ", ".join(f"{k}=?" for k in clean)
            self.db.execute(f"UPDATE {entity} SET {fields} WHERE id=?", (*clean.values(), row_id))
            return int(row_id)
        cols = ", ".join(clean)
        marks = ", ".join("?" for _ in clean)
        result = self.db.execute(f"INSERT INTO {entity}({cols}) VALUES({marks})", tuple(clean.values()))
        if entity == "occurrences":
            self.db.execute("INSERT INTO occurrence_history(occurrence_id,status,note) VALUES(?,?,?)",
                            (result, clean.get("status", "aberta"), "Ocorrência criada"))
        return result

    def delete(self, entity: str, row_id: int) -> None:
        if entity not in ALLOWED_ENTITIES and entity != "reservations":
            raise ValueError("Entidade inválida.")
        self.db.execute(f"DELETE FROM {entity} WHERE id=?", (row_id,))

    def reserve(self, data: dict[str, Any]) -> int:
        start, end = data["starts_at"], data["ends_at"]
        if end <= start:
            raise ValueError("O término deve ser posterior ao início.")
        space = self.db.rows("SELECT * FROM spaces WHERE id=?", (int(data["space_id"]),))
        if not space:
            raise ValueError("Espaço não encontrado.")
        start_time, end_time = start[11:16], end[11:16]
        if start_time < space[0]["opens_at"] or end_time > space[0]["closes_at"]:
            raise ValueError("Horário fora do funcionamento do espaço.")
        conflict = self.db.rows("""SELECT id FROM reservations
            WHERE space_id=? AND starts_at < ? AND ends_at > ?""",
            (int(data["space_id"]), end, start))
        if conflict:
            raise ValueError("Este espaço já está reservado nesse intervalo.")
        return self.db.execute("""INSERT INTO reservations(space_id,title,starts_at,ends_at,notes)
            VALUES(?,?,?,?,?)""", (int(data["space_id"]), data["title"], start, end, data.get("notes")))


class DocumentService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def import_pdf(self, path: str) -> dict[str, Any]:
        from pypdf import PdfReader
        source = Path(path)
        if source.suffix.lower() != ".pdf" or not source.is_file():
            raise ValueError("Selecione um arquivo PDF válido.")
        reader = PdfReader(str(source))
        indexed_at = datetime.now().isoformat(timespec="seconds")
        existing = self.db.rows("SELECT id FROM documents WHERE path=?", (str(source),))
        if existing:
            doc_id = existing[0]["id"]
            self.db.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
            self.db.execute("UPDATE documents SET name=?,pages=?,indexed_at=?,status='indexado' WHERE id=?",
                            (source.name, len(reader.pages), indexed_at, doc_id))
        else:
            doc_id = self.db.execute("INSERT INTO documents(name,path,pages,indexed_at) VALUES(?,?,?,?)",
                                     (source.name, str(source), len(reader.pages), indexed_at))
        chunks = 0
        for page_number, page in enumerate(reader.pages, 1):
            text = re.sub(r"\s+", " ", page.extract_text() or "").strip()
            for index in range(0, len(text), 1200):
                content = text[index:index + 1400].strip()
                if content:
                    self.db.execute("INSERT INTO chunks(document_id,page,content) VALUES(?,?,?)",
                                    (doc_id, page_number, content))
                    chunks += 1
        return {"id": doc_id, "name": source.name, "pages": len(reader.pages), "chunks": chunks}

    def list_documents(self) -> list[dict[str, Any]]:
        return self.db.rows("SELECT * FROM documents ORDER BY indexed_at DESC")

    def delete_document(self, doc_id: int) -> None:
        self.db.execute("DELETE FROM documents WHERE id=?", (doc_id,))

    def ask(self, question: str) -> dict[str, Any]:
        terms = re.findall(r"[\wÀ-ÿ]{3,}", question.lower())
        query = " OR ".join(f'"{term}"' for term in terms[:12])
        if not query:
            return {"answer": "Escreva uma pergunta mais específica.", "confidence": "baixa", "sources": []}
        try:
            rows = self.db.rows("""SELECT c.id,c.page,c.content,d.name,
                bm25(chunks_fts) score FROM chunks_fts
                JOIN chunks c ON c.id=chunks_fts.rowid JOIN documents d ON d.id=c.document_id
                WHERE chunks_fts MATCH ? ORDER BY score LIMIT 4""", (query,))
        except Exception:
            rows = []
        if not rows:
            return {
                "answer": "Não encontrei evidência suficiente nos documentos indexados. Refine a pergunta ou importe outro documento.",
                "confidence": "insuficiente", "sources": []
            }
        excerpts = []
        for row in rows:
            content = row["content"]
            best = min((content.lower().find(t) for t in terms if t in content.lower()), default=0)
            start = max(0, best - 120)
            excerpts.append({**row, "excerpt": content[start:start + 520]})
        return {
            "answer": excerpts[0]["excerpt"],
            "confidence": "alta" if len(excerpts) >= 2 else "média",
            "sources": [{"document": e["name"], "page": e["page"], "excerpt": e["excerpt"]} for e in excerpts],
            "mode": "Busca local FTS5"
        }

