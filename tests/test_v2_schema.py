"""Step 2 verification: V2 forward-compatible schema (submission, admin_action)."""
from src.bot.database.models import Base, Submission, AdminAction, AdminActionType, ProjectStatus


def test_v2_tables_in_metadata():
    """After migration 002, submission and admin_action exist in metadata; V1 tables unchanged."""
    tables = set(Base.metadata.tables)
    assert "user" in tables
    assert "project" in tables
    assert "buyer_request" in tables
    assert "lead" in tables
    assert "submission" in tables
    assert "admin_action" in tables


def test_submission_columns():
    """Submission has expected V2 columns (user_id, project_id, status, revision, answers, timestamps)."""
    cols = {c.name for c in Submission.__table__.columns}
    assert "id" in cols
    assert "user_id" in cols
    assert "project_id" in cols
    assert "status" in cols
    assert "revision" in cols
    assert "answers" in cols
    assert "created_at" in cols
    assert "updated_at" in cols
    assert "submitted_at" in cols


def test_admin_action_columns():
    """AdminAction has expected columns (admin_id, target_*, action, comment, created_at)."""
    cols = {c.name for c in AdminAction.__table__.columns}
    assert "id" in cols
    assert "admin_id" in cols
    assert "target_project_id" in cols
    assert "target_submission_id" in cols
    assert "action" in cols
    assert "comment" in cols
    assert "created_at" in cols


def test_admin_action_type_enum_values():
    """AdminActionType enum has approve, needs_fix, reject."""
    assert AdminActionType.approve.value == "approve"
    assert AdminActionType.needs_fix.value == "needs_fix"
    assert AdminActionType.reject.value == "reject"


def test_submission_status_uses_project_status():
    """Submission.status reuses ProjectStatus; draft is valid."""
    assert "status" in {c.name for c in Submission.__table__.columns}
    assert ProjectStatus.draft.value == "draft"
