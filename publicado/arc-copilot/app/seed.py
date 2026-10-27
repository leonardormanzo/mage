from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models import (
    Company,
    Document,
    DocumentChunk,
    Material,
    MaterialMovement,
    Project,
    ProjectPhoneNumber,
    ProjectUser,
    User,
)

DEMO_PASSWORD = "ArcDemo123!"


def seed_demo(db: Session) -> dict:
    existing = db.scalar(select(Company).where(Company.name == "Construtora Horizonte Demo"))
    if existing:
        engineer = db.scalar(select(User).where(User.email == "engenheiro@arc.local"))
        project = db.scalar(select(Project).where(Project.company_id == existing.id))
        return {"company": existing, "engineer": engineer, "project": project, "created": False}

    company = Company(name="Construtora Horizonte Demo")
    db.add(company)
    db.flush()
    users = [
        User(
            company_id=company.id,
            name="Marina Costa",
            email="engenheiro@arc.local",
            password_hash=hash_password(DEMO_PASSWORD),
            role="engineer",
        ),
        User(
            company_id=company.id,
            name="Carlos Mendes",
            email="mestre@arc.local",
            password_hash=hash_password(DEMO_PASSWORD),
            role="master",
        ),
        User(
            company_id=company.id,
            name="João Silva",
            email="trabalhador@arc.local",
            password_hash=hash_password(DEMO_PASSWORD),
            role="worker",
        ),
    ]
    db.add_all(users)
    project = Project(
        company_id=company.id,
        name="Residencial Aurora",
        code="RA-001",
        address="Rua das Palmeiras, 100 — São Paulo/SP",
    )
    restricted_project = Project(
        company_id=company.id,
        name="Obra Restrita",
        code="OR-002",
        address="Endereço demonstrativo",
    )
    db.add_all([project, restricted_project])
    db.flush()
    db.add_all(
        [
            ProjectUser(company_id=company.id, project_id=project.id, user_id=user.id)
            for user in users
        ]
        + [
            ProjectUser(
                company_id=company.id, project_id=restricted_project.id, user_id=users[0].id
            )
        ]
    )
    db.add(
        ProjectPhoneNumber(
            company_id=company.id,
            project_id=project.id,
            phone_number="+5511999990001",
        )
    )
    materials = [
        Material(
            company_id=company.id,
            project_id=project.id,
            name="Cimento",
            default_unit="sacos",
            category="Argamassas",
            low_stock_threshold=20,
        ),
        Material(
            company_id=company.id,
            project_id=project.id,
            name="Areia",
            default_unit="m³",
            category="Agregados",
            low_stock_threshold=5,
        ),
        Material(
            company_id=company.id,
            project_id=project.id,
            name="Bloco",
            default_unit="unidades",
            category="Alvenaria",
            low_stock_threshold=300,
        ),
    ]
    db.add_all(materials)
    db.flush()
    db.add_all(
        [
            MaterialMovement(
                company_id=company.id,
                project_id=project.id,
                material_id=materials[0].id,
                movement_type="entry",
                quantity=Decimal("100"),
                unit="sacos",
                supplier="Depósito Central",
                movement_date=date.today() - timedelta(days=2),
                user_id=users[0].id,
                status="confirmed",
            ),
            MaterialMovement(
                company_id=company.id,
                project_id=project.id,
                material_id=materials[1].id,
                movement_type="entry",
                quantity=Decimal("12"),
                unit="m³",
                supplier="Areial Demo",
                movement_date=date.today() - timedelta(days=1),
                user_id=users[0].id,
                status="confirmed",
            ),
        ]
    )
    document = Document(
        company_id=company.id,
        project_id=project.id,
        name="Procedimento de concretagem.txt",
        document_type="txt",
        stored_name="demo/procedimento-concretagem.txt",
        status="indexed",
    )
    db.add(document)
    db.flush()
    db.add(
        DocumentChunk(
            company_id=company.id,
            project_id=project.id,
            document_id=document.id,
            content="Antes da concretagem, conferir formas, armaduras, espaçadores e liberação do engenheiro responsável.",
            page=1,
            metadata_json={"source_name": document.name, "confirmation_status": "confirmed"},
        )
    )
    db.commit()
    return {"company": company, "engineer": users[0], "project": project, "created": True}
