from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    Confirmation,
    Conversation,
    DailyReport,
    DailyReportItem,
    ExtractedRecord,
    MaterialMovement,
    Message,
    User,
    now_utc,
)
from app.services.audit import audit
from app.services.extraction import extract_message, next_question, summary_text
from app.services.inventory import find_or_create_material, material_balance

ALLOWED_TRANSITIONS = {
    "received": {"processing"},
    "processing": {"incomplete", "awaiting_confirmation", "cancelled"},
    "incomplete": {"awaiting_confirmation", "cancelled"},
    "awaiting_confirmation": {"confirmed", "corrected", "cancelled"},
    "confirmed": {"included_in_rdo", "corrected"},
    "included_in_rdo": {"closed", "corrected"},
    "corrected": set(),
    "cancelled": set(),
    "closed": set(),
}


def transition(record: ExtractedRecord, target: str) -> None:
    if target not in ALLOWED_TRANSITIONS.get(record.status, set()):
        raise HTTPException(
            status_code=409, detail=f"Transição inválida: {record.status} → {target}"
        )
    record.status = target


def get_or_create_conversation(db: Session, *, company_id: str, project_id: str, user_id: str):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.company_id == company_id,
            Conversation.project_id == project_id,
            Conversation.user_id == user_id,
        )
    )
    if not conversation:
        conversation = Conversation(company_id=company_id, project_id=project_id, user_id=user_id)
        db.add(conversation)
        db.flush()
    return conversation


def receive_message(
    db: Session,
    *,
    user: User,
    project_id: str,
    content: str,
    external_id: str | None = None,
    message_type: str = "text",
    origin_phone: str = "web",
    destination_phone: str = "web",
) -> tuple[Message, ExtractedRecord, str, bool]:
    external_id = external_id or f"web-{uuid.uuid4()}"
    existing = db.scalar(
        select(Message).where(
            Message.company_id == user.company_id, Message.external_id == external_id
        )
    )
    if existing:
        record = db.scalar(select(ExtractedRecord).where(ExtractedRecord.message_id == existing.id))
        return existing, record, "Mensagem já processada.", True

    conversation = get_or_create_conversation(
        db, company_id=user.company_id, project_id=project_id, user_id=user.id
    )
    message = Message(
        company_id=user.company_id,
        project_id=project_id,
        conversation_id=conversation.id,
        sender_user_id=user.id,
        message_type=message_type,
        content=content,
        external_id=external_id,
        origin_phone=origin_phone,
        destination_phone=destination_phone,
        status="processing",
    )
    db.add(message)
    db.flush()
    extracted = extract_message(content)
    record = ExtractedRecord(
        company_id=user.company_id,
        project_id=project_id,
        message_id=message.id,
        created_by_id=user.id,
        record_type=extracted.record_type,
        status="processing",
        quantity=extracted.quantity,
        unit=extracted.unit,
        material_name=extracted.material_name,
        service=extracted.service,
        location=extracted.location,
        missing_fields=extracted.missing_fields,
        confidence=extracted.confidence,
        evidence_text=extracted.evidence,
    )
    db.add(record)
    db.flush()
    if record.missing_fields:
        transition(record, "incomplete")
        bot_text = next_question(record.missing_fields[0])
    else:
        transition(record, "awaiting_confirmation")
        bot_text = summary_text(record)
    message.status = "processed"
    audit(
        db,
        company_id=user.company_id,
        project_id=project_id,
        user_id=user.id,
        entity_type="record",
        entity_id=record.id,
        operation="created",
        new_value={"type": record.record_type, "status": record.status},
    )
    db.commit()
    return message, record, bot_text, False


def answer_record(db: Session, *, record: ExtractedRecord, user: User, answer: str) -> str:
    if record.status != "incomplete" or not record.missing_fields:
        raise HTTPException(status_code=409, detail="Registro não está aguardando complemento")
    if record.created_by_id != user.id and user.role == "worker":
        raise HTTPException(status_code=403, detail="Sem permissão")
    field = record.missing_fields[0]
    clean = answer.strip()
    if clean.lower() in {"não sei", "nao sei", "informar depois"}:
        record.missing_fields = record.missing_fields[1:] + [field]
        db.commit()
        return next_question(record.missing_fields[0])
    if field == "quantity":
        try:
            record.quantity = Decimal(clean.replace(",", "."))
        except InvalidOperation as exc:
            raise HTTPException(status_code=422, detail="Informe uma quantidade numérica") from exc
    elif field == "unit":
        record.unit = clean
    elif field == "material_name":
        record.material_name = clean
    elif field == "service":
        record.service = clean
    elif field == "location":
        record.location = clean
    record.missing_fields = record.missing_fields[1:]
    if record.missing_fields:
        response = next_question(record.missing_fields[0])
    else:
        transition(record, "awaiting_confirmation")
        response = summary_text(record)
    db.commit()
    return response


def confirm_record(
    db: Session, *, record: ExtractedRecord, user: User
) -> tuple[str, Decimal | None]:
    if record.status != "awaiting_confirmation":
        raise HTTPException(status_code=409, detail="Registro não está aguardando confirmação")
    if record.created_by_id != user.id and user.role == "worker":
        raise HTTPException(status_code=403, detail="Trabalhador só confirma os próprios registros")
    transition(record, "confirmed")
    record.confirmed_by_id = user.id
    record.confirmed_at = now_utc()
    db.add(
        Confirmation(
            company_id=record.company_id,
            project_id=record.project_id,
            record_id=record.id,
            user_id=user.id,
            action="confirmed",
        )
    )
    balance = None
    if record.record_type in {"material_consumed", "material_received"}:
        material = find_or_create_material(
            db,
            company_id=record.company_id,
            project_id=record.project_id,
            name=record.material_name or "Não informado",
            unit=record.unit or "un",
        )
        movement_type = "consumption" if record.record_type == "material_consumed" else "entry"
        movement = MaterialMovement(
            company_id=record.company_id,
            project_id=record.project_id,
            material_id=material.id,
            movement_type=movement_type,
            quantity=record.quantity or 0,
            unit=record.unit or material.default_unit,
            service=record.service,
            location=record.location,
            movement_date=record.event_date,
            user_id=user.id,
            source_message_id=record.message_id,
            source_record_id=record.id,
            status="confirmed",
        )
        db.add(movement)
        db.flush()
        balance = material_balance(
            db, company_id=record.company_id, project_id=record.project_id, material_id=material.id
        )

    report = db.scalar(
        select(DailyReport).where(
            DailyReport.company_id == record.company_id,
            DailyReport.project_id == record.project_id,
            DailyReport.report_date == record.event_date,
        )
    )
    if not report:
        report = DailyReport(
            company_id=record.company_id,
            project_id=record.project_id,
            report_date=record.event_date,
        )
        db.add(report)
        db.flush()
    db.add(
        DailyReportItem(
            company_id=record.company_id,
            project_id=record.project_id,
            daily_report_id=report.id,
            record_id=record.id,
        )
    )
    transition(record, "included_in_rdo")
    audit(
        db,
        company_id=record.company_id,
        project_id=record.project_id,
        user_id=user.id,
        entity_type="record",
        entity_id=record.id,
        operation="confirmed",
        old_value={"status": "awaiting_confirmation"},
        new_value={"status": record.status},
    )
    db.commit()
    return "Registrado no RDO de hoje ✅", balance
