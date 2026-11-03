"""Busca por similaridade de cosseno nos trechos indexados.

No PostgreSQL a ordenação é feita pelo pgvector (`<=>`, índice HNSW). No SQLite, usado em
demonstração e testes, os vetores ficam em JSON e a similaridade é calculada em Python.
Só se comparam vetores gerados pelo mesmo embedder.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk

ScoredChunk = tuple[float, DocumentChunk, Document]


def cosine_similarity(first: Sequence[float], second: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(first, second, strict=True))
    norms = math.sqrt(sum(a * a for a in first)) * math.sqrt(sum(b * b for b in second))
    return dot / norms if norms else 0.0


def _scoped(*, company_id: str, project_id: str, embedder: str) -> Select:
    return (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.company_id == company_id,
            DocumentChunk.project_id == project_id,
            DocumentChunk.embedding.is_not(None),
            DocumentChunk.metadata_json["embedder"].as_string() == embedder,
        )
    )


def build_vector_statement(
    *,
    company_id: str,
    project_id: str,
    embedding: Sequence[float],
    embedder: str,
    limit: int,
) -> Select:
    distance = DocumentChunk.embedding.cosine_distance(list(embedding)).label("distance")
    return (
        _scoped(company_id=company_id, project_id=project_id, embedder=embedder)
        .add_columns(distance)
        .order_by(distance)
        .limit(limit)
    )


def search_chunks(
    db: Session,
    *,
    company_id: str,
    project_id: str,
    embedding: Sequence[float],
    embedder: str,
    limit: int,
    min_score: float,
) -> list[ScoredChunk]:
    """Devolve até `limit` trechos da obra com similaridade >= `min_score`, do melhor ao pior."""
    if not any(embedding):
        return []
    if db.get_bind().dialect.name == "postgresql":
        statement = build_vector_statement(
            company_id=company_id,
            project_id=project_id,
            embedding=embedding,
            embedder=embedder,
            limit=limit,
        )
        scored = [
            (1.0 - float(distance), chunk, document)
            for chunk, document, distance in db.execute(statement).all()
        ]
    else:
        rows = db.execute(
            _scoped(company_id=company_id, project_id=project_id, embedder=embedder)
        ).all()
        scored = sorted(
            (
                (cosine_similarity(embedding, chunk.embedding), chunk, document)
                for chunk, document in rows
            ),
            key=lambda item: item[0],
            reverse=True,
        )
    return [item for item in scored if item[0] >= min_score][:limit]
