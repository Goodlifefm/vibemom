"""Add rendered_post to submission (V2 submit pipeline)."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("submission", sa.Column("rendered_post", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("submission", "rendered_post")
