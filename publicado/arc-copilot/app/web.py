from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import ProjectContext, current_user, project_context
from app.core.config import BASE_DIR
from app.database.models import Project, ProjectUser, User
from app.database.session import get_db

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
MONTHS_PT = ("JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ")


@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"title": "Entrar"})


@router.get("/app", response_class=HTMLResponse)
def application_home(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    projects = db.scalars(
        select(Project)
        .join(ProjectUser, ProjectUser.project_id == Project.id)
        .where(
            Project.company_id == user.company_id,
            ProjectUser.company_id == user.company_id,
            ProjectUser.user_id == user.id,
        )
        .order_by(Project.name)
    ).all()
    return templates.TemplateResponse(
        request,
        "projects.html",
        {"title": "Selecionar obra", "user": user, "projects": projects},
    )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_page(
    request: Request,
    context: ProjectContext = Depends(project_context),
):
    today = date.today()
    return templates.TemplateResponse(
        request,
        "project.html",
        {
            "title": context.project.name,
            "project": context.project,
            "user": context.user,
            "today_label": f"{today.day:02d} {MONTHS_PT[today.month - 1]} {today.year}",
        },
    )
