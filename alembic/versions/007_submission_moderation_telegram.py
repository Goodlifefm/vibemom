"""Submission moderation + Telegram publishing fields.

Revision ID: 007
Revises: 006
Create Date: 2026-02-08

Changes:
- Replace `projectstatus` enum values to match the new lifecycle:
  draft, submitted, approved, rejected, published_to_tg
- Add moderation timestamps + rejection reason to `submission`
- Add Telegram post metadata fields to `submission`
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- New moderation + Telegram fields on submission ---
    op.add_column("submission", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("submission", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("submission", sa.Column("rejected_reason", sa.Text(), nullable=True))
    op.add_column("submission", sa.Column("tg_chat_id", sa.BigInteger(), nullable=True))
    op.add_column("submission", sa.Column("tg_message_id", sa.Integer(), nullable=True))
    op.add_column("submission", sa.Column("tg_post_url", sa.VARCHAR(length=1000), nullable=True))

    # --- Replace enum type (Postgres doesn't support dropping enum values in-place) ---
    # Old: draft, pending, needs_fix, approved, rejected
    # New: draft, submitted, approved, rejected, published_to_tg
    op.execute("ALTER TYPE projectstatus RENAME TO projectstatus_old")
    op.execute(
        "CREATE TYPE projectstatus AS ENUM ('draft', 'submitted', 'approved', 'rejected', 'published_to_tg')"
    )

    # project.status: pending -> submitted; needs_fix -> rejected
    op.execute("ALTER TABLE project ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE project
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'pending' THEN 'submitted'
                WHEN 'needs_fix' THEN 'rejected'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE project ALTER COLUMN status SET DEFAULT 'draft'")

    # submission.status: pending -> submitted; needs_fix -> rejected
    op.execute("ALTER TABLE submission ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE submission
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'pending' THEN 'submitted'
                WHEN 'needs_fix' THEN 'rejected'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE submission ALTER COLUMN status SET DEFAULT 'draft'")

    op.execute("DROP TYPE projectstatus_old")

    # --- Backfill new timestamps from legacy fields (best-effort) ---
    op.execute(
        """
        UPDATE submission
        SET submitted_at = COALESCE(submitted_at, updated_at)
        WHERE status = 'submitted' AND submitted_at IS NULL
        """
    )
    op.execute(
        """
        UPDATE submission
        SET approved_at = COALESCE(approved_at, moderated_at)
        WHERE status = 'approved' AND approved_at IS NULL AND moderated_at IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE submission
        SET rejected_at = COALESCE(rejected_at, moderated_at)
        WHERE status = 'rejected' AND rejected_at IS NULL AND moderated_at IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE submission
        SET rejected_reason = COALESCE(rejected_reason, fix_request)
        WHERE rejected_reason IS NULL AND fix_request IS NOT NULL
        """
    )


def downgrade() -> None:
    # --- Recreate old enum type ---
    op.execute("ALTER TYPE projectstatus RENAME TO projectstatus_new")
    op.execute(
        "CREATE TYPE projectstatus AS ENUM ('draft', 'pending', 'needs_fix', 'approved', 'rejected')"
    )

    # project.status: submitted -> pending; published_to_tg -> approved
    op.execute("ALTER TABLE project ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE project
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'submitted' THEN 'pending'
                WHEN 'published_to_tg' THEN 'approved'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE project ALTER COLUMN status SET DEFAULT 'pending'")

    # submission.status: submitted -> pending; published_to_tg -> approved
    op.execute("ALTER TABLE submission ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE submission
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'submitted' THEN 'pending'
                WHEN 'published_to_tg' THEN 'approved'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE submission ALTER COLUMN status SET DEFAULT 'draft'")

    op.execute("DROP TYPE projectstatus_new")

    # --- Drop new columns from submission ---
    op.drop_column("submission", "tg_post_url")
    op.drop_column("submission", "tg_message_id")
    op.drop_column("submission", "tg_chat_id")
    op.drop_column("submission", "rejected_reason")
    op.drop_column("submission", "rejected_at")
    op.drop_column("submission", "approved_at")

