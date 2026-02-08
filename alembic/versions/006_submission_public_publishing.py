"""Add public publishing fields to submission (Mini App MVP)."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "submission",
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "submission",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "submission",
        sa.Column("public_slug", sa.VARCHAR(length=255), nullable=True),
    )
    op.add_column(
        "submission",
        sa.Column("show_contacts", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_submission_public_slug", "submission", ["public_slug"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_submission_public_slug", table_name="submission")
    op.drop_column("submission", "show_contacts")
    op.drop_column("submission", "public_slug")
    op.drop_column("submission", "published_at")
    op.drop_column("submission", "published")

