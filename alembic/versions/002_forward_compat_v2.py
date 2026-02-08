"""Forward-compatible V2 schema: submission, admin_action (Step 2).

Adds tables and enum for V2; V1 tables unchanged. No renames/drops.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum for admin moderation actions (V2 audit log)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adminactiontype') THEN
                CREATE TYPE adminactiontype AS ENUM ('approve', 'needs_fix', 'reject');
            END IF;
        END
        $$;
    """)
    admin_action_type = postgresql.ENUM(
        "approve", "needs_fix", "reject",
        name="adminactiontype",
        create_type=False,
    )

    # V2 submission: lifecycle (draft → pending → needs_fix/approved/rejected)
    op.create_table(
        "submission",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM("draft", "pending", "needs_fix", "approved", "rejected", name="projectstatus", create_type=False), nullable=False, server_default="draft"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answers", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # V2 admin_action: audit log of moderation actions
    op.create_table(
        "admin_action",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("target_project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_submission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", admin_action_type, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["admin_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["target_project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["target_submission_id"], ["submission.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("admin_action")
    op.drop_table("submission")
    op.execute("DROP TYPE IF EXISTS adminactiontype")
