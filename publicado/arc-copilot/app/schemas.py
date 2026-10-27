from __future__ import annotations

from decimal import Decimal

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
