from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import read_session_token
from app.database.models import Project, ProjectUser, User
from app.database.session import get_db


@dataclass
class ProjectContext:
    user: User
    project: Project


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    token = header.removeprefix("Bearer ").strip() if header.startswith("Bearer ") else None
    token = token or request.cookies.get("arc_session")
    user_id = read_session_token(token or "", get_settings().secret_key)
    user = db.get(User, user_id) if user_id else None
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária"
        )
    return user


def project_context(
    project_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ProjectContext:
    membership = db.scalar(
        select(ProjectUser).where(
            ProjectUser.company_id == user.company_id,
            ProjectUser.project_id == project_id,
            ProjectUser.user_id == user.id,
        )
    )
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.company_id == user.company_id)
    )
    if not membership or not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra não encontrada")
    return ProjectContext(user=user, project=project)


def require_roles(*roles: str):
    def dependency(context: ProjectContext = Depends(project_context)) -> ProjectContext:
        if context.user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")
        return context

    return dependency
