from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON

from app.core.config import EMBEDDING_DIMENSION

# vector(768) no PostgreSQL (pgvector); JSON no SQLite, onde a busca é feita em Python.
EMBEDDING_TYPE = Vector(EMBEDDING_DIMENSION).with_variant(JSON(), "sqlite")
