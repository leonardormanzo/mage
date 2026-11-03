from __future__ import annotations

import logging
import re
import unicodedata
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.models import (
    Document,
    DocumentChunk,
    ExtractedRecord,
    Material,
    MaterialMovement,
    RagQuery,
    RagSource,
    User,
)
from app.services import ai
from app.services.inventory import material_balance
from app.services.rag.vector_store import search_chunks

logger = logging.getLogger(__name__)

TOP_K = 3
LEXICAL_LIMIT = 5
LEXICAL_MIN_WORD = 4
LEXICAL_MAX_WORDS = 8
ANSWER_PREVIEW_CHARS = 600


def normalize(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn"
    )


def answer_question(db: Session, *, user: User, project_id: str, question: str) -> dict:
    normalized = normalize(question)
    quantitative = any(word in normalized for word in ("saldo", "quanto", "quantos", "quantas"))
    if quantitative:
        result = _answer_quantitative(db, user=user, project_id=project_id, question=question)
    else:
        result = _answer_documental(db, user=user, project_id=project_id, question=question)
    query = RagQuery(
        company_id=user.company_id,
        project_id=project_id,
        user_id=user.id,
        question=question,
        answer=result["answer"],
        route=result["route"],
        confidence=Decimal(str(result["confidence"])),
    )
    db.add(query)
    db.flush()
    for source in result["sources"]:
        db.add(
            RagSource(
                rag_query_id=query.id,
                source_type=source["type"],
                source_id=source["id"],
                label=source["label"],
                source_date=source.get("date"),
            )
        )
    db.commit()
    result["query_id"] = query.id
    return result


def _movement_source(move: MaterialMovement) -> dict:
    return {
        "type": "material_movement",
        "id": move.id,
        "label": f"{move.movement_type}: {move.quantity:g} {move.unit}",
        "date": move.movement_date,
    }


def _answer_quantitative(db: Session, *, user: User, project_id: str, question: str) -> dict:
    normalized = normalize(question)
    materials = db.scalars(
        select(Material).where(
            Material.company_id == user.company_id, Material.project_id == project_id
        )
    ).all()
    material = next((item for item in materials if normalize(item.name) in normalized), None)
    if not material:
        return _not_found("structured", retrieval="structured")
    scope = (
        MaterialMovement.company_id == user.company_id,
        MaterialMovement.project_id == project_id,
        MaterialMovement.material_id == material.id,
        MaterialMovement.status == "confirmed",
    )
    if "saldo" in normalized:
        balance = material_balance(
            db, company_id=user.company_id, project_id=project_id, material_id=material.id
        )
        movements = db.scalars(select(MaterialMovement).where(*scope)).all()
        return {
            "answer": f"Saldo de {material.name}: {balance:g} {material.default_unit}.",
            "route": "structured",
            "retrieval": "structured",
            "confidence": 1.0,
            "sources": [_movement_source(move) for move in movements],
        }
    movement_type = "consumption" if "consum" in normalized else "entry"
    reversed_ids = select(MaterialMovement.reverses_movement_id).where(
        MaterialMovement.reverses_movement_id.is_not(None)
    )
    movements = db.scalars(
        select(MaterialMovement).where(
            *scope,
            MaterialMovement.movement_type == movement_type,
            MaterialMovement.id.not_in(reversed_ids),
        )
    ).all()
    total = sum((Decimal(move.quantity) for move in movements), Decimal(0))
    return {
        "answer": f"Total de {material.name}: {total:g} {material.default_unit}.",
        "route": "structured",
        "retrieval": "structured",
        "confidence": 1.0 if movements else 0.0,
        "sources": [_movement_source(move) for move in movements],
    }


def _answer_documental(db: Session, *, user: User, project_id: str, question: str) -> dict:
    return _answer_by_vector(db, user=user, project_id=project_id, question=question) or (
        _answer_lexical(db, user=user, project_id=project_id, question=question)
    )


def _answer_by_vector(db: Session, *, user: User, project_id: str, question: str) -> dict | None:
    """Busca vetorial nos documentos da obra; devolve None para cair na busca textual."""
    provider = ai.get_embedding_provider()
    try:
        question_vector = provider.embed(question, task="query")
    except Exception:
        logger.warning("Embedding da pergunta indisponível; usando busca textual", exc_info=True)
        return None
    hits = search_chunks(
        db,
        company_id=user.company_id,
        project_id=project_id,
        embedding=question_vector,
        embedder=provider.name,
        limit=TOP_K,
        min_score=provider.min_score,
    )
    if not hits:
        return None
    context = [chunk.content for _, chunk, _ in hits]
    try:
        answer = ai.get_llm_provider().answer(question, context)
    except Exception:
        logger.warning("Geração indisponível; devolvendo o trecho mais próximo", exc_info=True)
        answer = context[0][:ANSWER_PREVIEW_CHARS]
    documents: dict[str, Document] = {}
    for _, _, document in hits:
        documents.setdefault(document.id, document)
    return {
        "answer": answer,
        "route": "documental",
        "retrieval": "vector",
        "confidence": round(hits[0][0], 3),
        "sources": [_document_source(document) for document in documents.values()],
    }


def _document_source(document: Document) -> dict:
    return {
        "type": "document",
        "id": document.id,
        "label": document.name,
        "date": document.created_at.date() if document.created_at else None,
    }


def _answer_lexical(db: Session, *, user: User, project_id: str, question: str) -> dict:
    words = [
        word
        for word in re.findall(r"\w+", normalize(question))
        if len(word) >= LEXICAL_MIN_WORD
    ][:LEXICAL_MAX_WORDS]
    filters = [func.lower(DocumentChunk.content).contains(word) for word in words]
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.company_id == user.company_id,
            DocumentChunk.project_id == project_id,
        )
        .limit(LEXICAL_LIMIT)
    )
    if filters:
        stmt = stmt.where(or_(*filters))
    rows = db.execute(stmt).all()
    if rows:
        chunk, document = rows[0]
        return {
            "answer": chunk.content[:ANSWER_PREVIEW_CHARS],
            "route": "documental",
            "retrieval": "lexical",
            "confidence": 0.7,
            "sources": [_document_source(document)],
        }
    records = db.scalars(
        select(ExtractedRecord)
        .where(
            ExtractedRecord.company_id == user.company_id,
            ExtractedRecord.project_id == project_id,
            ExtractedRecord.status.in_(["included_in_rdo", "closed"]),
        )
        .order_by(ExtractedRecord.event_date.desc())
        .limit(LEXICAL_LIMIT)
    ).all()
    matched = [r for r in records if any(word in normalize(r.evidence_text) for word in words)]
    if not matched:
        return _not_found("documental")
    record = matched[0]
    return {
        "answer": record.evidence_text,
        "route": "documental",
        "retrieval": "lexical",
        "confidence": 0.75,
        "sources": [
            {
                "type": "record",
                "id": record.id,
                "label": "Registro confirmado",
                "date": record.event_date,
            }
        ],
    }


def _not_found(route: str, retrieval: str = "none") -> dict:
    return {
        "answer": "Não encontrei esse dado nos registros da obra.",
        "route": route,
        "retrieval": retrieval,
        "confidence": 0.0,
        "sources": [],
    }
