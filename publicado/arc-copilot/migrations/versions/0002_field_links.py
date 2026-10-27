"""Link secreto de campo por obra."""

from alembic import op

from app.database.models import FieldLink

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    FieldLink.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    FieldLink.__table__.drop(bind=op.get_bind(), checkfirst=True)
