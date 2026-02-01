"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.VARCHAR(255), nullable=True),
        sa.Column("full_name", sa.VARCHAR(255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_telegram_id"), "user", ["telegram_id"], unique=True)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projectstatus') THEN
                CREATE TYPE projectstatus AS ENUM ('draft', 'pending', 'needs_fix', 'approved', 'rejected');
            END IF;
        END
        $$;
    """)
    project_status = postgresql.ENUM("draft", "pending", "needs_fix", "approved", "rejected", name="projectstatus", create_type=False)

    op.create_table(
        "project",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.VARCHAR(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("stack", sa.VARCHAR(500), nullable=False),
        sa.Column("link", sa.VARCHAR(1000), nullable=False),
        sa.Column("price", sa.VARCHAR(200), nullable=False),
        sa.Column("contact", sa.VARCHAR(200), nullable=False),
        sa.Column("status", project_status, nullable=False, server_default="pending"),
        sa.Column("moderation_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["seller_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "buyer_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("what", sa.Text(), nullable=False),
        sa.Column("budget", sa.VARCHAR(200), nullable=False),
        sa.Column("contact", sa.VARCHAR(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["buyer_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leadtype') THEN
                CREATE TYPE leadtype AS ENUM ('PROJECT_INTEREST', 'REQUEST_OFFER');
            END IF;
        END
        $$;
    """)
    lead_type = postgresql.ENUM("PROJECT_INTEREST", "REQUEST_OFFER", name="leadtype", create_type=False)

    op.create_table(
        "lead",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_type", lead_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["buyer_request_id"], ["buyer_request.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("lead")
    op.drop_table("buyer_request")
    op.drop_table("project")
    op.drop_index(op.f("ix_user_telegram_id"), table_name="user")
    op.drop_table("user")
    op.execute("DROP TYPE IF EXISTS leadtype")
    op.execute("DROP TYPE IF EXISTS projectstatus")
