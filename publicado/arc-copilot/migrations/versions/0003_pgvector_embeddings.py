"""Coluna `embedding` (pgvector no PostgreSQL) no lugar de `embedding_json`.

Vetores legados só são migrados no PostgreSQL quando têm 768 posições. Eles não trazem o
nome do embedder em `metadata_json`, então a busca os ignora até o documento ser
reenviado: modelos diferentes geram espaços vetoriais incompatíveis.
"""

import sqlalchemy as sa
from alembic import op

from app.core.config import EMBEDDING_DIMENSION
from app.database.types import EMBEDDING_TYPE

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABLE = "document_chunks"
INDEX = "ix_document_chunks_embedding_hnsw"


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    columns = {column["name"] for column in sa.inspect(bind).get_columns(TABLE)}
    if "embedding" not in columns:
        op.add_column(TABLE, sa.Column("embedding", EMBEDDING_TYPE, nullable=True))
    if "embedding_json" in columns:
        if is_postgres:
            op.execute(
                f"""
                UPDATE {TABLE} SET embedding = embedding_json::text::vector
                WHERE CASE WHEN json_typeof(embedding_json::json) = 'array'
                           THEN json_array_length(embedding_json::json) ELSE 0 END
                      = {EMBEDDING_DIMENSION}
                """
            )
        else:
            op.execute(f"UPDATE {TABLE} SET embedding = embedding_json")
        with op.batch_alter_table(TABLE) as batch:
            batch.drop_column("embedding_json")
    if is_postgres:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {INDEX} ON {TABLE} "
            "USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(f"DROP INDEX IF EXISTS {INDEX}")
    op.add_column(TABLE, sa.Column("embedding_json", sa.JSON(), nullable=True))
    if bind.dialect.name == "postgresql":
        op.execute(f"UPDATE {TABLE} SET embedding_json = embedding::text::json")
    else:
        op.execute(f"UPDATE {TABLE} SET embedding_json = embedding")
    with op.batch_alter_table(TABLE) as batch:
        batch.drop_column("embedding")
