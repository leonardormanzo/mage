"""Página de entrada de campo: link secreto por obra, sem login.

Substitui temporariamente o WhatsApp. O link equivale a uma credencial: quem o possui
registra mensagens naquela obra como o usuário "Campo" associado ao link. O nome digitado
na página é autodeclarado (não verificado) e fica em Message.origin_phone.
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import BASE_DIR
from app.database.models import ExtractedRecord, FieldLink, Project, User
from app.database.session import get_db
from app.services.audit import audit
from app.services.workflow import answer_record, confirm_record, receive_message, transition

router = APIRouter(prefix="/e")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

RATE_LIMIT = 40  # requisições por janela, por link (memória do processo; 1 worker)
RATE_WINDOW = 60.0
_hits: dict[str, deque[float]] = defaultdict(deque)
SECURE_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Robots-Tag": "noindex, nofollow",
}


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SendInput(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    sender: str = Field(min_length=2, max_length=40)
    external_id: str | None = Field(default=None, max_length=64)


class AnswerInput(BaseModel):
    record_id: str
    answer: str = Field(min_length=1, max_length=500)


class RecordInput(BaseModel):
    record_id: str


def resolve_link(token: str, db: Session = Depends(get_db)) -> FieldLink:
    link = db.scalar(
        select(FieldLink).where(
            FieldLink.token_hash == hash_token(token), FieldLink.active.is_(True)
        )
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link inválido ou desativado")
    now = time.monotonic()
    hits = _hits[link.id]
    while hits and now - hits[0] > RATE_WINDOW:
        hits.popleft()
    if len(hits) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Muitas mensagens. Aguarde um minuto.")
    hits.append(now)
    return link


def _record(db: Session, link: FieldLink, record_id: str) -> ExtractedRecord:
    record = db.scalar(
        select(ExtractedRecord).where(
            ExtractedRecord.id == record_id,
            ExtractedRecord.company_id == link.company_id,
            ExtractedRecord.project_id == link.project_id,
            ExtractedRecord.created_by_id == link.user_id,
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return record


@router.get("/{token}", response_class=HTMLResponse)
def field_page(token: str, request: Request, db: Session = Depends(get_db)):
    link = resolve_link(token, db)
    project = db.get(Project, link.project_id)
    return templates.TemplateResponse(
        request,
        "field.html",
        {"project": project, "title": project.name},
        headers=SECURE_HEADERS,
    )


@router.post("/{token}/send")
def field_send(payload: SendInput, link: FieldLink = Depends(resolve_link), db: Session = Depends(get_db)):
    user = db.get(User, link.user_id)
    message, record, bot, duplicate = receive_message(
        db,
        user=user,
        project_id=link.project_id,
        content=payload.content,
        external_id=f"link-{link.id}-{payload.external_id}" if payload.external_id else None,
        origin_phone=f"link:{payload.sender.strip()}"[:32],
        destination_phone="link",
    )
    return {"record_id": record.id, "record_status": record.status, "bot": bot, "duplicate": duplicate}


@router.post("/{token}/answer")
def field_answer(payload: AnswerInput, link: FieldLink = Depends(resolve_link), db: Session = Depends(get_db)):
    record = _record(db, link, payload.record_id)
    bot = answer_record(db, record=record, user=db.get(User, link.user_id), answer=payload.answer)
    return {"record_id": record.id, "record_status": record.status, "bot": bot}


@router.post("/{token}/confirm")
def field_confirm(payload: RecordInput, link: FieldLink = Depends(resolve_link), db: Session = Depends(get_db)):
    record = _record(db, link, payload.record_id)
    bot, _ = confirm_record(db, record=record, user=db.get(User, link.user_id))
    return {"record_id": record.id, "record_status": record.status, "bot": bot}


@router.post("/{token}/cancel")
def field_cancel(payload: RecordInput, link: FieldLink = Depends(resolve_link), db: Session = Depends(get_db)):
    record = _record(db, link, payload.record_id)
    transition(record, "cancelled")
    audit(
        db,
        company_id=link.company_id,
        project_id=link.project_id,
        user_id=link.user_id,
        entity_type="record",
        entity_id=record.id,
        operation="cancelled",
        new_value={"status": "cancelled"},
    )
    db.commit()
    return {"record_id": record.id, "record_status": record.status, "bot": "Registro cancelado."}
