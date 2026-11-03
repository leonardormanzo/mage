from __future__ import annotations

import logging
import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import ProjectContext, current_user, project_context, require_roles
from app.core.config import get_settings
from app.core.security import create_session_token, verify_password
from app.core.throttle import login_throttle
from app.database.models import (
    AuditLog,
    Company,
    DailyReport,
    DailyReportItem,
    Document,
    ExtractedRecord,
    Material,
    MaterialMovement,
    Message,
    Project,
    ProjectPhoneNumber,
    ProjectUser,
    User,
    now_utc,
)
from app.database.session import get_db
from app.schemas import (
    CorrectionInput,
    LoginInput,
    MessageInput,
    MovementInput,
    QueryInput,
    ReasonInput,
    RecordAnswerInput,
    ReopenInput,
)
from app.services.audit import audit
from app.services.documents import extract_text, index_document
from app.services.inventory import material_balance
from app.services.messaging import MetaWhatsAppProvider, MockWhatsAppProvider
from app.services.rag import answer_question
from app.services.reports import build_report_pdf
from app.services.workflow import (
    answer_record,
    cancel_record,
    confirm_record,
    correct_record,
    receive_message,
    reverse_record,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
ACTIVE_RDO_STATUSES = ("included_in_rdo", "closed")
ALLOWED_UPLOADS = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "video/mp4": ".mp4",
}


@router.post("/auth/login")
def login(payload: LoginInput, request: Request, db: Session = Depends(get_db)):
    key = f"{_client_ip(request)}|{payload.email.strip().lower()}"
    if login_throttle.is_blocked(key):
        raise HTTPException(
            status_code=429, detail="Muitas tentativas. Aguarde alguns minutos e tente de novo."
        )
    user = db.scalar(
        select(User).where(
            func.lower(User.email) == payload.email.strip().lower(), User.active.is_(True)
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        login_throttle.record_failure(key)
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    login_throttle.clear(key)
    token = create_session_token(user.id, get_settings().secret_key)
    response = Response(
        content='{"ok":true}',
        media_type="application/json",
    )
    response.set_cookie(
        "arc_session",
        token,
        httponly=True,
        samesite="lax",
        secure=get_settings().environment == "production",
        max_age=28_800,
    )
    return response


@router.post("/auth/logout")
def logout():
    response = Response(content='{"ok":true}', media_type="application/json")
    response.delete_cookie("arc_session")
    return response


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    projects = db.scalars(
        select(Project)
        .join(ProjectUser, ProjectUser.project_id == Project.id)
        .where(
            Project.company_id == user.company_id,
            ProjectUser.company_id == user.company_id,
            ProjectUser.user_id == user.id,
        )
    ).all()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "projects": [{"id": item.id, "name": item.name, "code": item.code} for item in projects],
    }


@router.get("/projects/{project_id}/dashboard")
def dashboard(context: ProjectContext = Depends(project_context), db: Session = Depends(get_db)):
    report = db.scalar(
        select(DailyReport).where(
            DailyReport.company_id == context.user.company_id,
            DailyReport.project_id == context.project.id,
            DailyReport.report_date == date.today(),
        )
    )
    pending = db.scalar(
        select(func.count())
        .select_from(ExtractedRecord)
        .where(
            ExtractedRecord.company_id == context.user.company_id,
            ExtractedRecord.project_id == context.project.id,
            ExtractedRecord.status.in_(["incomplete", "awaiting_confirmation"]),
        )
    )
    messages = db.scalars(
        select(Message)
        .where(
            Message.company_id == context.user.company_id,
            Message.project_id == context.project.id,
        )
        .order_by(Message.created_at.desc())
        .limit(8)
    ).all()
    return {
        "project": {
            "id": context.project.id,
            "name": context.project.name,
            "code": context.project.code,
        },
        "report": {"id": report.id, "status": report.status} if report else None,
        "pending": pending,
        "recent_messages": [
            {
                "id": item.id,
                "content": item.content,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in messages
        ],
    }


@router.post("/projects/{project_id}/messages")
def create_message(
    payload: MessageInput,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    message, record, bot_text, duplicate = receive_message(
        db,
        user=context.user,
        project_id=context.project.id,
        content=payload.content,
        external_id=payload.external_id,
        message_type=payload.message_type,
    )
    return {
        "message_id": message.id,
        "record_id": record.id,
        "record_status": record.status,
        "bot": bot_text,
        "missing_fields": record.missing_fields,
        "duplicate": duplicate,
    }


@router.post("/projects/{project_id}/records/{record_id}/answer")
def answer_missing_field(
    record_id: str,
    payload: RecordAnswerInput,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    record = _scoped_record(db, context, record_id)
    bot_text = answer_record(db, record=record, user=context.user, answer=payload.answer)
    return {
        "record_id": record.id,
        "record_status": record.status,
        "bot": bot_text,
        "missing_fields": record.missing_fields,
    }


@router.post("/projects/{project_id}/records/{record_id}/confirm")
def confirm(
    record_id: str,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    record = _scoped_record(db, context, record_id, lock=True)
    bot_text, balance = confirm_record(db, record=record, user=context.user)
    return {
        "record_id": record.id,
        "record_status": record.status,
        "bot": bot_text,
        "balance": balance,
    }


@router.post("/projects/{project_id}/records/{record_id}/cancel")
def cancel(
    record_id: str,
    request: Request,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    record = _scoped_record(db, context, record_id, lock=True)
    cancel_record(db, record=record, user=context.user, ip_address=_client_ip(request))
    return {"record_id": record.id, "record_status": record.status, "bot": "Registro cancelado."}


@router.post("/projects/{project_id}/records/{record_id}/reverse")
def reverse(
    record_id: str,
    payload: ReasonInput,
    request: Request,
    context: ProjectContext = Depends(require_roles("master", "engineer")),
    db: Session = Depends(get_db),
):
    record = _scoped_record(db, context, record_id, lock=True)
    balance = reverse_record(
        db,
        record=record,
        user=context.user,
        reason=payload.reason,
        ip_address=_client_ip(request),
    )
    return {"record_id": record.id, "record_status": record.status, "balance": balance}


@router.post("/projects/{project_id}/records/{record_id}/correct")
def correct(
    record_id: str,
    payload: CorrectionInput,
    request: Request,
    context: ProjectContext = Depends(require_roles("master", "engineer")),
    db: Session = Depends(get_db),
):
    record = _scoped_record(db, context, record_id, lock=True)
    corrected, balance = correct_record(
        db,
        record=record,
        user=context.user,
        reason=payload.reason,
        changes=payload.model_dump(exclude={"reason"}),
        ip_address=_client_ip(request),
    )
    return {
        "record_id": corrected.id,
        "replaces_record_id": record.id,
        "record_status": corrected.status,
        "balance": balance,
    }


@router.get("/projects/{project_id}/materials")
def list_materials(
    context: ProjectContext = Depends(project_context), db: Session = Depends(get_db)
):
    materials = db.scalars(
        select(Material)
        .where(
            Material.company_id == context.user.company_id,
            Material.project_id == context.project.id,
        )
        .order_by(Material.name)
    ).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "unit": item.default_unit,
            "balance": material_balance(
                db,
                company_id=context.user.company_id,
                project_id=context.project.id,
                material_id=item.id,
            ),
        }
        for item in materials
    ]


@router.post("/projects/{project_id}/movements")
def create_movement(
    payload: MovementInput,
    request: Request,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    material = db.scalar(
        select(Material).where(
            Material.id == payload.material_id,
            Material.company_id == context.user.company_id,
            Material.project_id == context.project.id,
        )
    )
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    if payload.movement_type.startswith("adjustment") and context.user.role != "engineer":
        raise HTTPException(status_code=403, detail="Ajuste exige aprovação de engenheiro")
    if payload.movement_type not in {
        "entry",
        "consumption",
        "adjustment_positive",
        "adjustment_negative",
    }:
        raise HTTPException(status_code=422, detail="Tipo de movimentação inválido")
    movement = MaterialMovement(
        company_id=context.user.company_id,
        project_id=context.project.id,
        material_id=material.id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        unit=payload.unit,
        service=payload.service,
        user_id=context.user.id,
        status="confirmed",
    )
    db.add(movement)
    db.flush()
    audit(
        db,
        company_id=context.user.company_id,
        project_id=context.project.id,
        user_id=context.user.id,
        entity_type="material_movement",
        entity_id=movement.id,
        operation="created",
        new_value={"type": payload.movement_type, "quantity": str(payload.quantity)},
        reason=payload.reason,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return {
        "id": movement.id,
        "balance": material_balance(
            db,
            company_id=context.user.company_id,
            project_id=context.project.id,
            material_id=material.id,
        ),
    }


@router.get("/projects/{project_id}/reports/today")
def today_report(context: ProjectContext = Depends(project_context), db: Session = Depends(get_db)):
    report = _report_for_date(db, context, date.today())
    if not report:
        return {"report": None, "items": [], "pending": ["RDO ainda não criado"]}
    records = _report_records(db, context, report.id)
    return {
        "report": {"id": report.id, "date": report.report_date, "status": report.status},
        "items": [_record_dict(record) for record in records],
        "pending": _report_pending(report),
    }


@router.post("/projects/{project_id}/reports/{report_id}/close")
def close_report(
    report_id: str,
    allow_incomplete: bool = False,
    context: ProjectContext = Depends(require_roles("master", "engineer")),
    db: Session = Depends(get_db),
):
    report = _scoped_report(db, context, report_id)
    if report.status != "open":
        raise HTTPException(status_code=409, detail="RDO não está aberto")
    pending = _report_pending(report)
    if pending and not allow_incomplete:
        raise HTTPException(
            status_code=409, detail={"message": "Existem pendências", "pending": pending}
        )
    report.status = "closed"
    report.closed_by_id = context.user.id
    report.closed_at = now_utc()
    for record in _report_records(db, context, report.id):
        if record.status == "included_in_rdo":
            record.status = "closed"
    audit(
        db,
        company_id=context.user.company_id,
        project_id=context.project.id,
        user_id=context.user.id,
        entity_type="daily_report",
        entity_id=report.id,
        operation="closed",
        old_value={"status": "open"},
        new_value={"status": "closed", "incomplete": bool(pending)},
    )
    db.commit()
    return {"id": report.id, "status": report.status, "pending_marked_not_informed": pending}


@router.post("/projects/{project_id}/reports/{report_id}/reopen")
def reopen_report(
    report_id: str,
    payload: ReopenInput,
    context: ProjectContext = Depends(require_roles("engineer")),
    db: Session = Depends(get_db),
):
    report = _scoped_report(db, context, report_id)
    if report.status != "closed":
        raise HTTPException(status_code=409, detail="RDO não está fechado")
    report.status = "open"
    report.reopened_reason = payload.reason
    for record in _report_records(db, context, report.id):
        if record.status == "closed":
            record.status = "included_in_rdo"
    audit(
        db,
        company_id=context.user.company_id,
        project_id=context.project.id,
        user_id=context.user.id,
        entity_type="daily_report",
        entity_id=report.id,
        operation="reopened",
        old_value={"status": "closed"},
        new_value={"status": "open"},
        reason=payload.reason,
    )
    db.commit()
    return {"id": report.id, "status": report.status}


@router.get("/projects/{project_id}/reports/{report_id}.pdf")
def report_pdf(
    report_id: str,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    report = _scoped_report(db, context, report_id)
    company = db.get(Company, context.user.company_id)
    content = build_report_pdf(
        company_name=company.name,
        project_name=context.project.name,
        report=report,
        records=_report_records(db, context, report.id),
    )
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="RDO-{report.report_date}.pdf"'},
    )


@router.post("/projects/{project_id}/query")
def query(
    payload: QueryInput,
    context: ProjectContext = Depends(project_context),
    db: Session = Depends(get_db),
):
    return answer_question(
        db, user=context.user, project_id=context.project.id, question=payload.question
    )


@router.post("/projects/{project_id}/documents")
async def upload_document(
    file: UploadFile = File(...),
    context: ProjectContext = Depends(require_roles("engineer")),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    content_type = (file.content_type or "").split(";")[0]
    extension = ALLOWED_UPLOADS.get(content_type)
    if extension not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=415, detail="Envie PDF, DOCX ou TXT")
    limit_bytes = settings.upload_limit_mb * 1024 * 1024
    content = await file.read(limit_bytes + 1)
    if len(content) > limit_bytes:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite")
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]", "-", Path(file.filename or "documento").stem)[:80]
    stored_name = (
        f"{context.user.company_id}/{context.project.id}/{uuid.uuid4()}-{safe_stem}{extension}"
    )
    destination = settings.storage_dir / stored_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    document = Document(
        company_id=context.user.company_id,
        project_id=context.project.id,
        name=file.filename or destination.name,
        document_type=extension.lstrip("."),
        stored_name=stored_name,
        status="indexed",
    )
    db.add(document)
    db.flush()
    text = extract_text(destination, extension)
    indexed = index_document(db, document=document, text=text)
    db.commit()
    return {
        "id": document.id,
        "name": document.name,
        "status": document.status,
        "characters": len(text),
        "chunks": indexed.chunks,
        "embedded_chunks": indexed.embedded,
        "embedder": indexed.embedder,
    }


@router.get("/projects/{project_id}/audit")
def list_audit(
    context: ProjectContext = Depends(require_roles("master", "engineer")),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.company_id == context.user.company_id,
            AuditLog.project_id == context.project.id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": row.id,
            "operation": row.operation,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "user_id": row.user_id,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/webhooks/whatsapp")
def verify_whatsapp_webhook(request: Request):
    settings = get_settings()
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.webhook_verify_token:
            return Response(content=challenge, media_type="text/plain")
        raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Bad Request")

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    raw_body = await request.body()
    if not settings.webhook_app_secret:
        raise HTTPException(status_code=503, detail="Webhook não configurado")
    import hashlib
    import hmac
    import json

    expected = "sha256=" + hmac.new(
        settings.webhook_app_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(request.headers.get("X-Hub-Signature-256", ""), expected):
        raise HTTPException(status_code=403, detail="Assinatura inválida")
    payload = json.loads(raw_body)

    # Meta sends a simple object payload
    if payload.get("object") != "whatsapp_business_account":
        raise HTTPException(status_code=400, detail="Invalid payload")
        
    provider = MetaWhatsAppProvider(
        access_token=settings.whatsapp_access_token,
        phone_id=settings.whatsapp_phone_id
    )
    
    try:
        incoming = provider.parse_webhook(payload)
    except ValueError as e:
        # Not all webhooks contain messages (e.g. read receipts)
        return {"status": "ignored", "reason": str(e)}

    phone = db.scalar(
        select(ProjectPhoneNumber).where(
            ProjectPhoneNumber.phone_number == incoming.destination_phone,
            ProjectPhoneNumber.active.is_(True),
        )
    )
    if not phone:
        # Ignoring message to unregistered phone
        return {"status": "ignored", "reason": "Phone not registered"}
        
    # In a real environment, you identify the user by origin_phone, not email.
    user = db.scalar(
        select(User)
        .join(ProjectUser, ProjectUser.user_id == User.id)
        .where(
            User.company_id == phone.company_id,
            ProjectUser.project_id == phone.project_id,
            # Ideally we match by a phone number field on User, but here we assume anyone
            # sending to the project's whatsapp is either an external worker or we need to look them up.
            # As a fallback for MVP if we don't have user phones mapped, we assign to a 'system/guest' user
            # or the first admin. Let's find the project admin for now:
        ).limit(1)
    )
    if not user:
        return {"status": "ignored", "reason": "No users in project"}

    message, record, bot_text, duplicate = receive_message(
        db,
        user=user,
        project_id=phone.project_id,
        content=incoming.content,
        external_id=incoming.external_id,
        message_type=incoming.message_type,
        origin_phone=incoming.origin_phone,
        destination_phone=incoming.destination_phone,
    )
    
    if bot_text:
        try:
            provider.send_text(incoming.origin_phone, bot_text)
        except Exception:
            logger.warning("Falha ao responder no WhatsApp", exc_info=True)

    return {"status": "success"}

@router.post("/webhooks/whatsapp/mock")
async def mock_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    incoming = MockWhatsAppProvider().parse_webhook(payload)
    phone = db.scalar(
        select(ProjectPhoneNumber).where(
            ProjectPhoneNumber.phone_number == incoming.destination_phone,
            ProjectPhoneNumber.active.is_(True),
        )
    )
    if not phone:
        raise HTTPException(status_code=404, detail="Número não associado a uma obra")
    user = db.scalar(
        select(User)
        .join(ProjectUser, ProjectUser.user_id == User.id)
        .where(
            User.company_id == phone.company_id,
            ProjectUser.company_id == phone.company_id,
            ProjectUser.project_id == phone.project_id,
            User.email == payload.get("sender_email"),
        )
    )
    if not user:
        raise HTTPException(status_code=403, detail="Remetente não autorizado para a obra")
    message, record, bot_text, duplicate = receive_message(
        db,
        user=user,
        project_id=phone.project_id,
        content=incoming.content,
        external_id=incoming.external_id,
        message_type=incoming.message_type,
        origin_phone=incoming.origin_phone,
        destination_phone=incoming.destination_phone,
    )
    return {
        "message_id": message.id,
        "record_id": record.id,
        "bot": bot_text,
        "duplicate": duplicate,
    }


def _scoped_record(
    db: Session, context: ProjectContext, record_id: str, *, lock: bool = False
) -> ExtractedRecord:
    """Busca o registro da obra; `lock` trava a linha no PostgreSQL contra operações simultâneas."""
    statement = select(ExtractedRecord).where(
        ExtractedRecord.id == record_id,
        ExtractedRecord.company_id == context.user.company_id,
        ExtractedRecord.project_id == context.project.id,
    )
    record = db.scalar(statement.with_for_update() if lock else statement)
    if not record:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return record


def _scoped_report(db: Session, context: ProjectContext, report_id: str) -> DailyReport:
    report = db.scalar(
        select(DailyReport).where(
            DailyReport.id == report_id,
            DailyReport.company_id == context.user.company_id,
            DailyReport.project_id == context.project.id,
        )
    )
    if not report:
        raise HTTPException(status_code=404, detail="RDO não encontrado")
    return report


def _report_for_date(db: Session, context: ProjectContext, report_date: date):
    return db.scalar(
        select(DailyReport).where(
            DailyReport.company_id == context.user.company_id,
            DailyReport.project_id == context.project.id,
            DailyReport.report_date == report_date,
        )
    )


def _report_records(db: Session, context: ProjectContext, report_id: str):
    return db.scalars(
        select(ExtractedRecord)
        .join(DailyReportItem, DailyReportItem.record_id == ExtractedRecord.id)
        .where(
            DailyReportItem.company_id == context.user.company_id,
            DailyReportItem.project_id == context.project.id,
            DailyReportItem.daily_report_id == report_id,
            ExtractedRecord.company_id == context.user.company_id,
            ExtractedRecord.project_id == context.project.id,
            ExtractedRecord.status.in_(ACTIVE_RDO_STATUSES),
        )
    ).all()


def _record_dict(record: ExtractedRecord):
    return {
        "id": record.id,
        "type": record.record_type,
        "status": record.status,
        "quantity": record.quantity,
        "unit": record.unit,
        "material": record.material_name,
        "service": record.service,
        "location": record.location,
        "date": record.event_date,
    }


def _report_pending(report: DailyReport) -> list[str]:
    pending = []
    if not report.weather:
        pending.append("Clima")
    if report.workforce is None:
        pending.append("Efetivo")
    return pending


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
