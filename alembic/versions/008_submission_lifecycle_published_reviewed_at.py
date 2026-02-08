"""Normalize submission lifecycle: draft/submitted/rejected/published + reviewed_at.

Revision ID: 008
Revises: 007
Create Date: 2026-02-08

Changes:
- Replace `projectstatus` enum values to match the simplified lifecycle:
  draft, submitted, rejected, published
- Add `reviewed_at` timestamp to `submission`

Notes:
- We do NOT drop legacy columns (`approved_at`, `rejected_at`, etc.) to avoid data loss.
- Enum replacement is done by renaming the old type and creating a new one (Postgres limitation).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add reviewed_at on submission ---
    op.add_column("submission", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))

    # --- Replace enum type (Postgres doesn't support removing enum values in-place) ---
    # Old: draft, submitted, approved, rejected, published_to_tg
    # New: draft, submitted, rejected, published
    op.execute("ALTER TYPE projectstatus RENAME TO projectstatus_old")
    op.execute("CREATE TYPE projectstatus AS ENUM ('draft', 'submitted', 'rejected', 'published')")

    # project.status: approved/published_to_tg -> published
    op.execute("ALTER TABLE project ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE project
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'approved' THEN 'published'
                WHEN 'published_to_tg' THEN 'published'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE project ALTER COLUMN status SET DEFAULT 'draft'")

    # submission.status: approved/published_to_tg -> published
    op.execute("ALTER TABLE submission ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE submission
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'approved' THEN 'published'
                WHEN 'published_to_tg' THEN 'published'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE submission ALTER COLUMN status SET DEFAULT 'draft'")

    op.execute("DROP TYPE projectstatus_old")

    # --- Backfill reviewed_at (best-effort) ---
    op.execute(
        """
        UPDATE submission
        SET reviewed_at = COALESCE(reviewed_at, approved_at, rejected_at, moderated_at, published_at)
        WHERE reviewed_at IS NULL
          AND (approved_at IS NOT NULL OR rejected_at IS NOT NULL OR moderated_at IS NOT NULL OR published_at IS NOT NULL)
        """
    )

    # Ensure published rows have published_at populated for storefront ordering.
    op.execute(
        """
        UPDATE submission
        SET published_at = COALESCE(published_at, reviewed_at, updated_at)
        WHERE status = 'published' AND published_at IS NULL
        """
    )


def downgrade() -> None:
    # --- Recreate old enum type ---
    op.execute("ALTER TYPE projectstatus RENAME TO projectstatus_new")
    op.execute(
        "CREATE TYPE projectstatus AS ENUM ('draft', 'submitted', 'approved', 'rejected', 'published_to_tg')"
    )

    # project.status: published -> published_to_tg
    op.execute("ALTER TABLE project ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE project
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'published' THEN 'published_to_tg'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE project ALTER COLUMN status SET DEFAULT 'draft'")

    # submission.status: published -> published_to_tg
    op.execute("ALTER TABLE submission ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE submission
        ALTER COLUMN status TYPE projectstatus
        USING (
            CASE status::text
                WHEN 'published' THEN 'published_to_tg'
                ELSE status::text
            END
        )::projectstatus
        """
    )
    op.execute("ALTER TABLE submission ALTER COLUMN status SET DEFAULT 'draft'")

    op.execute("DROP TYPE projectstatus_new")

    # --- Drop reviewed_at column from submission ---
    op.drop_column("submission", "reviewed_at")

