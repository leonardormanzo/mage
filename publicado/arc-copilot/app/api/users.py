from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_engineer
from app.database.models import User
from app.database.session import get_db
from app.schemas import PasswordInput, UserCreateInput, UserOut, UserUpdateInput
from app.services import users as service

router = APIRouter(prefix="/api/users", tags=["users"])


def _out(user: User, project_ids: list[str]) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        project_ids=project_ids,
        created_at=user.created_at,
    )


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[UserOut])
def list_users(actor: User = Depends(require_engineer), db: Session = Depends(get_db)):
    return [_out(user, ids) for user, ids in service.list_users(db, company_id=actor.company_id)]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateInput,
    request: Request,
    actor: User = Depends(require_engineer),
    db: Session = Depends(get_db),
):
    user, project_ids = service.create_user(
        db, actor=actor, ip_address=_ip(request), **payload.model_dump()
    )
    return _out(user, project_ids)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdateInput,
    request: Request,
    actor: User = Depends(require_engineer),
    db: Session = Depends(get_db),
):
    user = service.get_company_user(db, company_id=actor.company_id, user_id=user_id)
    user, project_ids = service.update_user(
        db,
        actor=actor,
        user=user,
        changes=payload.model_dump(exclude_unset=True),
        ip_address=_ip(request),
    )
    return _out(user, project_ids)


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: str,
    payload: PasswordInput,
    request: Request,
    actor: User = Depends(require_engineer),
    db: Session = Depends(get_db),
):
    user = service.get_company_user(db, company_id=actor.company_id, user_id=user_id)
    service.reset_password(
        db, actor=actor, user=user, password=payload.password, ip_address=_ip(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
