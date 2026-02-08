"""Step 3 verification: V2 repo layer (get_or_create_user, submission, log_admin_action)."""
import inspect


from src.v2.repo import (
    get_or_create_user,
    get_submission,
    get_active_submission,
    list_submissions_by_user,
    create_submission,
    update_answers_step,
    set_status,
    log_admin_action,
)


def test_repo_exports():
    """All required repo functions are exported and callable."""
    assert callable(get_or_create_user)
    assert callable(get_submission)
    assert callable(get_active_submission)
    assert callable(list_submissions_by_user)
    assert callable(create_submission)
    assert callable(update_answers_step)
    assert callable(set_status)
    assert callable(log_admin_action)


def test_get_or_create_user_signature():
    """get_or_create_user(telegram_id, username, full_name) -> User."""
    sig = inspect.signature(get_or_create_user)
    params = list(sig.parameters)
    assert params == ["telegram_id", "username", "full_name"]


def test_create_submission_signature():
    """create_submission(user_id, project_id=None) -> Submission."""
    sig = inspect.signature(create_submission)
    params = list(sig.parameters)
    assert "user_id" in params
    assert "project_id" in params


def test_update_answers_step_signature():
    """update_answers_step(submission_id, answers) -> Submission | None."""
    sig = inspect.signature(update_answers_step)
    params = list(sig.parameters)
    assert "submission_id" in params
    assert "answers" in params


def test_set_status_signature():
    """set_status(submission_id, status) -> Submission | None."""
    sig = inspect.signature(set_status)
    params = list(sig.parameters)
    assert "submission_id" in params
    assert "status" in params


def test_log_admin_action_signature():
    """log_admin_action(admin_id, action, *, target_project_id, target_submission_id, comment)."""
    sig = inspect.signature(log_admin_action)
    params = list(sig.parameters)
    assert "admin_id" in params
    assert "action" in params
    assert "target_project_id" in params
    assert "target_submission_id" in params
    assert "comment" in params
