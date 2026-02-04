"""Tests for project submission schema (SPEC 03)."""


from src.bot.project_submission_schema import (
    STEPS,
    first_step,
    get_step,
    step_index,
    VALIDATORS,
)


def test_schema_has_23_steps():
    assert len(STEPS) == 23


def test_first_step_is_welcome():
    step = first_step()
    assert step["state_id"] == "welcome"
    assert step["copy_id"] == "SUBMIT_START"
    assert step["next_id"] == "title"
    assert step["back_id"] is None


def test_get_step_returns_step_by_state_id():
    assert get_step("welcome") is not None
    assert get_step("title")["state_id"] == "title"
    assert get_step("confirm")["state_id"] == "confirm"
    assert get_step("__submit__") is None
    assert get_step("nonexistent") is None


def test_integrity_next_id_exists():
    state_ids = {s["state_id"] for s in STEPS}
    for step in STEPS:
        n = step.get("next_id")
        if n and n != "__submit__":
            assert n in state_ids, f"next_id={n} missing for {step['state_id']}"


def test_integrity_back_id_exists():
    state_ids = {s["state_id"] for s in STEPS}
    for step in STEPS:
        b = step.get("back_id")
        if b:
            assert b in state_ids, f"back_id={b} missing for {step['state_id']}"


def test_integrity_skip_id_exists():
    state_ids = {s["state_id"] for s in STEPS}
    for step in STEPS:
        sref = step.get("skip_id")
        if sref:
            assert sref in state_ids, f"skip_id={sref} missing for {step['state_id']}"


def test_step_index():
    assert step_index("welcome") == 0
    assert step_index("title") == 1
    assert step_index("confirm") == 22
    assert step_index("nonexistent") == -1


def test_confirm_step_has_yes_no():
    step = get_step("confirm")
    assert step["input_type"] == "yes_no"
    assert step["next_id"] == "__submit__"
    assert step["back_id"] == "preview"


def test_validators_registered():
    assert "non_empty_200" in VALIDATORS
    assert "url_1000" in VALIDATORS
    assert "yes_no" in VALIDATORS


def test_every_step_copy_id_exists_in_messages():
    """Every step copy_id must be resolvable (audit_copy sanity)."""
    from src.bot.messages import get_copy
    for step in STEPS:
        copy_id = step.get("copy_id")
        if not copy_id:
            continue
        text = get_copy(copy_id)
        assert text is not None and len(text.strip()) > 0, f"copy_id {copy_id!r} missing or empty in messages"


def test_get_project_submission_schema_v1():
    """get_project_submission_schema(False) returns V1 schema with 23 steps."""
    from src.bot.project_submission_schema import get_project_submission_schema
    schema = get_project_submission_schema(False)
    assert len(schema.STEPS) == 23
    assert schema.first_step()["state_id"] == "welcome"
    assert schema.get_step("title") is not None
    assert schema.get_step("confirm")["next_id"] == "__submit__"


def test_get_project_submission_schema_v2():
    """get_project_submission_schema(True) returns V2 schema with 25+ steps."""
    from src.bot.project_submission_schema import get_project_submission_schema
    schema = get_project_submission_schema(True)
    assert len(schema.STEPS) >= 25
    assert schema.first_step()["state_id"] == "welcome"
    assert schema.get_step("author_name") is not None
    assert schema.get_step("preview") is not None
    assert schema.get_step("confirm")["next_id"] == "__submit__"
