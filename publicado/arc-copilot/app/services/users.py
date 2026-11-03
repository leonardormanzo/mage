"""Administração de usuários da empresa: criação, edição, desativação e troca de senha."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.models import Project, ProjectUser, User
from app.services.audit import audit

DEMO_ACCOUNT_SUFFIX = "@arc.local"


def project_ids_by_user(db: Session, *, company_id: str) -> dict[str, list[str]]:
    rows = db.execute(
        select(ProjectUser.user_id, ProjectUser.project_id).where(
            ProjectUser.company_id == company_id
        )
    ).all()
    grouped: dict[str, list[str]] = {}
    for user_id, project_id in rows:
        grouped.setdefault(user_id, []).append(project_id)
    return {user_id: sorted(ids) for user_id, ids in grouped.items()}


def list_users(db: Session, *, company_id: str) -> list[tuple[User, list[str]]]:
    users = db.scalars(select(User).where(User.company_id == company_id).order_by(User.name)).all()
    assigned = project_ids_by_user(db, company_id=company_id)
    return [(user, assigned.get(user.id, [])) for user in users]


def get_company_user(db: Session, *, company_id: str, user_id: str) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.company_id == company_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


def create_user(
    db: Session,
    *,
    actor: User,
    name: str,
    email: str,
    password: str,
    role: str,
    project_ids: list[str],
    ip_address: str | None = None,
) -> tuple[User, list[str]]:
    normalized = email.strip().lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == normalized)):
        raise HTTPException(status_code=409, detail="Já existe um usuário com esse e-mail")
    projects = _company_projects(db, company_id=actor.company_id, project_ids=project_ids)
    user = User(
        company_id=actor.company_id,
        name=name.strip(),
        email=normalized,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    _assign_projects(db, user=user, project_ids=projects)
    audit(
        db,
        company_id=actor.company_id,
        project_id=None,
        user_id=actor.id,
        entity_type="user",
        entity_id=user.id,
        operation="user_created",
        new_value={"email": normalized, "role": role, "project_ids": projects},
        ip_address=ip_address,
    )
    db.commit()
    return user, projects


def update_user(
    db: Session,
    *,
    actor: User,
    user: User,
    changes: dict,
    ip_address: str | None = None,
) -> tuple[User, list[str]]:
    """Aplica `changes` (name, role, active, project_ids); campos ausentes ficam como estão."""
    changes = {key: value for key, value in changes.items() if value is not None}
    _guard_demo_account(user, changes.keys() - {"name"})
    if user.id == actor.id:
        if changes.get("active") is False:
            raise HTTPException(status_code=409, detail="Você não pode desativar a própria conta")
        if "role" in changes and changes["role"] != "engineer":
            raise HTTPException(
                status_code=409, detail="Você não pode remover o próprio perfil de engenheiro"
            )
    before = {
        "name": user.name,
        "role": user.role,
        "active": user.active,
        "project_ids": project_ids_by_user(db, company_id=user.company_id).get(user.id, []),
    }
    if "project_ids" in changes:
        changes["project_ids"] = _company_projects(
            db, company_id=actor.company_id, project_ids=changes["project_ids"]
        )
        _assign_projects(db, user=user, project_ids=changes["project_ids"])
    for field in ("name", "role", "active"):
        if field in changes:
            setattr(user, field, changes[field].strip() if field == "name" else changes[field])
    after = {
        **before,
        **{key: value for key, value in changes.items() if key in before},
    }
    audit(
        db,
        company_id=actor.company_id,
        project_id=None,
        user_id=actor.id,
        entity_type="user",
        entity_id=user.id,
        operation="user_updated",
        old_value={key: before[key] for key in changes if key in before},
        new_value={key: after[key] for key in changes if key in after},
        ip_address=ip_address,
    )
    db.commit()
    return user, after["project_ids"]


def reset_password(
    db: Session, *, actor: User, user: User, password: str, ip_address: str | None = None
) -> None:
    _guard_demo_account(user, {"password"})
    user.password_hash = hash_password(password)
    audit(
        db,
        company_id=actor.company_id,
        project_id=None,
        user_id=actor.id,
        entity_type="user",
        entity_id=user.id,
        operation="password_reset",
        ip_address=ip_address,
    )
    db.commit()


def _guard_demo_account(user: User, touched: set[str] | frozenset[str]) -> None:
    """Na demonstração pública as contas fixas não podem ser trancadas por visitantes."""
    if touched and get_settings().demo_mode and user.email.endswith(DEMO_ACCOUNT_SUFFIX):
        raise HTTPException(
            status_code=403, detail="Conta fixa da demonstração: só o nome pode ser alterado"
        )


def _company_projects(db: Session, *, company_id: str, project_ids: list[str]) -> list[str]:
    wanted = set(project_ids)
    found = set(
        db.scalars(
            select(Project.id).where(Project.company_id == company_id, Project.id.in_(wanted))
        ).all()
    )
    if found != wanted:
        raise HTTPException(status_code=422, detail="Obra inexistente para esta empresa")
    return sorted(found)


def _assign_projects(db: Session, *, user: User, project_ids: list[str]) -> None:
    current = {
        row.project_id: row
        for row in db.scalars(
            select(ProjectUser).where(
                ProjectUser.company_id == user.company_id, ProjectUser.user_id == user.id
            )
        ).all()
    }
    for project_id, row in current.items():
        if project_id not in project_ids:
            db.delete(row)
    for project_id in project_ids:
        if project_id not in current:
            db.add(ProjectUser(company_id=user.company_id, project_id=project_id, user_id=user.id))
