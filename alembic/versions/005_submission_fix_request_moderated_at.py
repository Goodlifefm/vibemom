"""Add fix_request and moderated_at to submission (V2 moderation)."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("submission", sa.Column("fix_request", sa.Text(), nullable=True))
    op.add_column("submission", sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("submission", "moderated_at")
    op.drop_column("submission", "fix_request")
