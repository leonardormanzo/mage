from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class LoginInput(BaseModel):
    email: str
    password: str


class MessageInput(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    external_id: str | None = None
    message_type: str = "text"


class RecordAnswerInput(BaseModel):
    answer: str = Field(min_length=1, max_length=500)


class QueryInput(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class MovementInput(BaseModel):
    material_id: str
    movement_type: str
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=32)
    service: str | None = None
    reason: str | None = None


class ReopenInput(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class ReasonInput(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class CorrectionInput(ReasonInput):
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    material_name: str | None = Field(default=None, min_length=1, max_length=120)
    service: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=255)


Role = Literal["engineer", "master", "worker"]
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
MIN_PASSWORD_LENGTH = 10


class UserCreateInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
    role: Role
    project_ids: list[str] = Field(default_factory=list, max_length=100)


class UserUpdateInput(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Role | None = None
    active: bool | None = None
    project_ids: list[str] | None = Field(default=None, max_length=100)


class PasswordInput(BaseModel):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    active: bool
    project_ids: list[str]
    created_at: datetime
