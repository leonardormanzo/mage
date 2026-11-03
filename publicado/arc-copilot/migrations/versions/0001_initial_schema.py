"""Initial Arc Copilot schema."""

from alembic import op

from app.database.models import *  # noqa: F403
from app.database.session import Base, ensure_pgvector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ensure_pgvector(bind)  # a coluna vector(768) exige a extensão antes do create_all
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
