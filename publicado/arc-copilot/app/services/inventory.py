from __future__ import annotations

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database.models import Material, MaterialMovement


def material_balance(db: Session, *, company_id: str, project_id: str, material_id: str) -> Decimal:
    signed = case(
        (
            MaterialMovement.movement_type.in_(["entry", "adjustment_positive"]),
            MaterialMovement.quantity,
        ),
        (
            MaterialMovement.movement_type.in_(["consumption", "adjustment_negative"]),
            -MaterialMovement.quantity,
        ),
        (MaterialMovement.movement_type == "reversal", MaterialMovement.quantity),
        else_=0,
    )
    value = db.scalar(
        select(func.coalesce(func.sum(signed), 0)).where(
            MaterialMovement.company_id == company_id,
            MaterialMovement.project_id == project_id,
            MaterialMovement.material_id == material_id,
            MaterialMovement.status == "confirmed",
        )
    )
    return Decimal(value or 0)


def find_or_create_material(
    db: Session, *, company_id: str, project_id: str, name: str, unit: str
) -> Material:
    material = db.scalar(
        select(Material).where(
            Material.company_id == company_id,
            Material.project_id == project_id,
            func.lower(Material.name) == name.lower(),
        )
    )
    if not material:
        material = Material(
            company_id=company_id,
            project_id=project_id,
            name=name.capitalize(),
            default_unit=unit,
        )
        db.add(material)
        db.flush()
    return material
