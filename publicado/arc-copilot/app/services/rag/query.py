from __future__ import annotations

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
from app.services.inventory import material_balance


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


def _answer_quantitative(db: Session, *, user: User, project_id: str, question: str) -> dict:
    normalized = normalize(question)
    materials = db.scalars(
        select(Material).where(
            Material.company_id == user.company_id, Material.project_id == project_id
        )
    ).all()
    material = next((item for item in materials if normalize(item.name) in normalized), None)
    if not material:
        return _not_found("structured")
    if "saldo" in normalized:
        balance = material_balance(
            db, company_id=user.company_id, project_id=project_id, material_id=material.id
        )
        movements = db.scalars(
            select(MaterialMovement).where(
                MaterialMovement.company_id == user.company_id,
                MaterialMovement.project_id == project_id,
                MaterialMovement.material_id == material.id,
                MaterialMovement.status == "confirmed",
            )
        ).all()
        return {
            "answer": f"Saldo de {material.name}: {balance:g} {material.default_unit}.",
            "route": "structured",
            "confidence": 1.0,
            "sources": [
                {
                    "type": "material_movement",
                    "id": move.id,
                    "label": f"{move.movement_type}: {move.quantity:g} {move.unit}",
                    "date": move.movement_date,
                }
                for move in movements
            ],
        }
    movement_type = "consumption" if "consum" in normalized else "entry"
    movements = db.scalars(
        select(MaterialMovement).where(
            MaterialMovement.company_id == user.company_id,
            MaterialMovement.project_id == project_id,
            MaterialMovement.material_id == material.id,
            MaterialMovement.movement_type == movement_type,
            MaterialMovement.status == "confirmed",
        )
    ).all()
    total = sum((Decimal(move.quantity) for move in movements), Decimal(0))
    return {
        "answer": f"Total de {material.name}: {total:g} {material.default_unit}.",
        "route": "structured",
        "confidence": 1.0 if movements else 0.0,
        "sources": [
            {
                "type": "material_movement",
                "id": move.id,
                "label": f"{move.movement_type}: {move.quantity:g} {move.unit}",
                "date": move.movement_date,
            }
            for move in movements
        ],
    }


import math
from app.core.config import get_settings

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2:
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def _answer_documental(db: Session, *, user: User, project_id: str, question: str) -> dict:
    settings = get_settings()
    
    # Try Semantic RAG
    if settings.ai_mode and settings.gemini_api_key:
        from app.services.ai.providers import GeminiProvider
        provider = GeminiProvider(api_key=settings.gemini_api_key)
        try:
            question_embedding = provider.embed(question)
            
            stmt = (
                select(DocumentChunk, Document)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(
                    DocumentChunk.company_id == user.company_id,
                    DocumentChunk.project_id == project_id,
                    DocumentChunk.embedding_json.is_not(None)
                )
            )
            rows = db.execute(stmt).all()
            
            scored_rows = []
            for chunk, doc in rows:
                score = cosine_similarity(question_embedding, chunk.embedding_json)
                scored_rows.append((score, chunk, doc))
            
            scored_rows.sort(key=lambda x: x[0], reverse=True)
            top_rows = [x for x in scored_rows if x[0] > 0.4][:3]
            
            if top_rows:
                context_texts = [x[1].content for x in top_rows]
                answer = provider.answer(question, context_texts)
                return {
                    "answer": answer,
                    "route": "documental",
                    "confidence": float(top_rows[0][0]),
                    "sources": [
                        {
                            "type": "document",
                            "id": x[2].id,
                            "label": x[2].name,
                            "date": x[2].created_at.date() if x[2].created_at else None,
                        } for x in top_rows
                    ]
                }
        except Exception:
            pass # fallback to lexical
            
    # Lexical Fallback
    words = [word for word in re.findall(r"\w+", normalize(question)) if len(word) > 3][:8]
    filters = [func.lower(DocumentChunk.content).contains(word) for word in words]
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.company_id == user.company_id,
            DocumentChunk.project_id == project_id,
        )
        .limit(5)
    )
    if filters:
        stmt = stmt.where(or_(*filters))
    rows = db.execute(stmt).all()
    if not rows:
        records = db.scalars(
            select(ExtractedRecord)
            .where(
                ExtractedRecord.company_id == user.company_id,
                ExtractedRecord.project_id == project_id,
                ExtractedRecord.status.in_(["included_in_rdo", "closed"]),
            )
            .order_by(ExtractedRecord.event_date.desc())
            .limit(5)
        ).all()
        matched = [r for r in records if any(word in normalize(r.evidence_text) for word in words)]
        if not matched:
            return _not_found("documental")
        record = matched[0]
        return {
            "answer": record.evidence_text,
            "route": "documental",
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
    chunk, document = rows[0]
    return {
        "answer": chunk.content[:600],
        "route": "documental",
        "confidence": 0.7,
        "sources": [
            {
                "type": "document",
                "id": document.id,
                "label": document.name,
                "date": document.created_at.date() if document.created_at else None,
            }
        ],
    }


def _not_found(route: str) -> dict:
    return {
        "answer": "Não encontrei esse dado nos registros da obra.",
        "route": route,
        "confidence": 0.0,
        "sources": [],
    }
