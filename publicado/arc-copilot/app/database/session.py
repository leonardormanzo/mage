from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, **kwargs)


def ensure_pgvector(bind: Engine | Connection) -> None:
    """Habilita a extensão pgvector no PostgreSQL; não faz nada em outros bancos."""
    if bind.dialect.name != "postgresql":
        return
    statement = text("CREATE EXTENSION IF NOT EXISTS vector")
    if isinstance(bind, Engine):
        with bind.begin() as connection:
            connection.execute(statement)
    else:
        bind.execute(statement)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
