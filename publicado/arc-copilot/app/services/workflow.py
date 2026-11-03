from __future__ import annotations

import uuid
from datetime import date
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
    "confirmed": {"included_in_rdo", "corrected", "reversed"},
    "included_in_rdo": {"closed", "corrected", "reversed"},
    "corrected": set(),
    "reversed": set(),
    "cancelled": set(),
    "closed": set(),
}
CORRECTABLE_FIELDS = ("quantity", "unit", "material_name", "service", "location")
MATERIAL_ONLY_FIELDS = {"quantity", "unit", "material_name"}


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
    balance = _apply_confirmation(db, record=record, user=user)
    db.commit()
    return "Registrado no RDO de hoje ✅", balance


def _apply_confirmation(db: Session, *, record: ExtractedRecord, user: User) -> Decimal | None:
    """Confirma o registro e gera o movimento de estoque e o item do RDO, sem commit."""
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
    return balance


def cancel_record(
    db: Session, *, record: ExtractedRecord, user: User, ip_address: str | None = None
) -> None:
    """Cancela um registro que ainda não foi confirmado."""
    if record.created_by_id != user.id and user.role == "worker":
        raise HTTPException(status_code=403, detail="Trabalhador só cancela os próprios registros")
    previous = record.status
    transition(record, "cancelled")
    audit(
        db,
        company_id=record.company_id,
        project_id=record.project_id,
        user_id=user.id,
        entity_type="record",
        entity_id=record.id,
        operation="cancelled",
        old_value={"status": previous},
        new_value={"status": "cancelled"},
        ip_address=ip_address,
    )
    db.commit()


def reverse_record(
    db: Session,
    *,
    record: ExtractedRecord,
    user: User,
    reason: str,
    ip_address: str | None = None,
) -> Decimal | None:
    """Estorna um registro confirmado; o estoque é compensado por movimentos de estorno."""
    _require_open_report(db, record)
    previous = record.status
    transition(record, "reversed")  # recusa estados inválidos antes de qualquer efeito
    balance = _reverse_movements(db, record=record, user=user)
    audit(
        db,
        company_id=record.company_id,
        project_id=record.project_id,
        user_id=user.id,
        entity_type="record",
        entity_id=record.id,
        operation="reversed",
        old_value={"status": previous},
        new_value={"status": "reversed"},
        reason=reason,
        ip_address=ip_address,
    )
    db.commit()
    return balance


def correct_record(
    db: Session,
    *,
    record: ExtractedRecord,
    user: User,
    reason: str,
    changes: dict,
    ip_address: str | None = None,
) -> tuple[ExtractedRecord, Decimal | None]:
    """Substitui um registro confirmado por uma versão corrigida, preservando o histórico.

    O registro antigo passa a `corrected`, seus movimentos são estornados e o novo registro
    nasce já confirmado e ligado ao antigo por `corrected_from_id`.
    """
    effective = {
        field: value
        for field, value in changes.items()
        if field in CORRECTABLE_FIELDS
        and value is not None
        and getattr(record, field) != value
    }
    if not effective:
        raise HTTPException(status_code=422, detail="Informe ao menos um campo diferente do atual")
    if record.record_type == "service" and MATERIAL_ONLY_FIELDS & effective.keys():
        raise HTTPException(
            status_code=422, detail="Registro de serviço não tem quantidade, unidade ou material"
        )
    _require_open_report(db, record)
    previous = {field: _plain(getattr(record, field)) for field in effective}
    transition(record, "corrected")  # recusa estados inválidos antes de qualquer efeito
    _reverse_movements(db, record=record, user=user)
    db.add(
        Confirmation(
            company_id=record.company_id,
            project_id=record.project_id,
            record_id=record.id,
            user_id=user.id,
            action="corrected",
        )
    )
    corrected = ExtractedRecord(
        company_id=record.company_id,
        project_id=record.project_id,
        message_id=record.message_id,
        created_by_id=record.created_by_id,
        record_type=record.record_type,
        status="awaiting_confirmation",
        event_date=record.event_date,
        quantity=record.quantity,
        unit=record.unit,
        material_name=record.material_name,
        service=record.service,
        location=record.location,
        missing_fields=[],
        confidence=record.confidence,
        evidence_text=record.evidence_text,
        corrected_from_id=record.id,
    )
    for field, value in effective.items():
        setattr(corrected, field, value)
    db.add(corrected)
    db.flush()
    balance = _apply_confirmation(db, record=corrected, user=user)
    audit(
        db,
        company_id=record.company_id,
        project_id=record.project_id,
        user_id=user.id,
        entity_type="record",
        entity_id=record.id,
        operation="corrected",
        old_value=previous,
        new_value={field: _plain(value) for field, value in effective.items()}
        | {"corrected_record_id": corrected.id},
        reason=reason,
        ip_address=ip_address,
    )
    db.commit()
    return corrected, balance


def _plain(value):
    return str(value) if isinstance(value, Decimal) else value


def _require_open_report(db: Session, record: ExtractedRecord) -> None:
    if record.status not in {"confirmed", "included_in_rdo", "closed"}:
        return  # a máquina de estados recusa a operação com a mensagem de transição inválida
    report = db.scalar(
        select(DailyReport)
        .join(DailyReportItem, DailyReportItem.daily_report_id == DailyReport.id)
        .where(DailyReportItem.record_id == record.id)
    )
    if report and report.status != "open":
        raise HTTPException(
            status_code=409,
            detail="RDO fechado: reabra o RDO do dia antes de estornar ou corrigir",
        )


def _reverse_movements(db: Session, *, record: ExtractedRecord, user: User) -> Decimal | None:
    """Cria o movimento de estorno de cada movimento confirmado do registro."""
    originals = db.scalars(
        select(MaterialMovement).where(
            MaterialMovement.company_id == record.company_id,
            MaterialMovement.project_id == record.project_id,
            MaterialMovement.source_record_id == record.id,
            MaterialMovement.status == "confirmed",
            MaterialMovement.movement_type.in_(["entry", "consumption"]),
        )
    ).all()
    balance = None
    for original in originals:
        sign = -1 if original.movement_type == "entry" else 1
        db.add(
            MaterialMovement(
                company_id=original.company_id,
                project_id=original.project_id,
                material_id=original.material_id,
                movement_type="reversal",
                quantity=sign * original.quantity,
                unit=original.unit,
                service=original.service,
                location=original.location,
                movement_date=date.today(),
                user_id=user.id,
                source_message_id=original.source_message_id,
                source_record_id=record.id,
                status="confirmed",
                reverses_movement_id=original.id,
            )
        )
        db.flush()
        balance = material_balance(
            db,
            company_id=record.company_id,
            project_id=record.project_id,
            material_id=original.material_id,
        )
    return balance
