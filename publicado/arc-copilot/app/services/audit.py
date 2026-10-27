from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import AuditLog


def audit(
    db: Session,
    *,
    company_id: str,
    project_id: str | None,
    user_id: str | None,
    entity_type: str,
    entity_id: str,
    operation: str,
    old_value: dict | None = None,
    new_value: dict | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        company_id=company_id,
        project_id=project_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        operation=operation,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        ip_address=ip_address,
    )
    db.add(entry)
    return entry
