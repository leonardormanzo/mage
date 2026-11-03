"""Extração de texto, divisão em trechos e indexação vetorial de documentos da obra."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk
from app.services import ai

logger = logging.getLogger(__name__)

CHUNK_SIZE = 900
CHUNK_OVERLAP = 100


@dataclass(frozen=True)
class IndexResult:
    chunks: int
    embedded: int
    embedder: str


def extract_text(path: Path, extension: str) -> str:
    try:
        if extension == ".txt":
            return path.read_text(encoding="utf-8", errors="replace")
        if extension == ".pdf":
            from pypdf import PdfReader

            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        if extension == ".docx":
            from docx import Document as DocxDocument

            return "\n".join(paragraph.text for paragraph in DocxDocument(path).paragraphs)
    except Exception:
        logger.warning("Falha ao extrair texto de %s", path.name, exc_info=True)
    return ""


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide em trechos de até `size` caracteres, cortando em espaço e repetindo `overlap`."""
    cleaned = text.strip()
    pieces: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + size, len(cleaned))
        if end < len(cleaned):
            cut = cleaned.rfind(" ", start + size // 2, end)
            end = cut if cut != -1 else end
        piece = cleaned[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return pieces


def index_document(db: Session, *, document: Document, text: str) -> IndexResult:
    """Cria os trechos do documento, com embedding quando o provedor responde.

    Se o provedor falhar, o restante do documento é indexado sem vetor e continua
    encontrável pela busca textual.
    """
    provider = ai.get_embedding_provider()
    embedding_available = True
    pieces = chunk_text(text)
    embedded = 0
    for position, piece in enumerate(pieces, start=1):
        vector = None
        if embedding_available:
            try:
                vector = provider.embed(piece, task="document")
                embedded += 1
            except Exception:
                logger.warning(
                    "Embedding indisponível; %s indexado sem vetores a partir do trecho %d",
                    document.name,
                    position,
                    exc_info=True,
                )
                embedding_available = False
        db.add(
            DocumentChunk(
                company_id=document.company_id,
                project_id=document.project_id,
                document_id=document.id,
                content=piece,
                embedding=vector,
                metadata_json={
                    "source_name": document.name,
                    "confirmation_status": "confirmed",
                    "embedder": provider.name if vector is not None else None,
                },
            )
        )
    return IndexResult(chunks=len(pieces), embedded=embedded, embedder=provider.name)
