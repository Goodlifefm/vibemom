"""Tests for submission engine (transitions, set_answer, resume)."""

import pytest

from src.bot.project_submission_schema import get_step
from src.bot.submission_engine import (
    get_current_step_id,
    get_current_step,
    set_answer,
    set_step_id,
    transition,
    META_KEY,
    STATE_KEY,
)


def test_get_current_step_id():
    assert get_current_step_id({}) is None
    assert get_current_step_id({META_KEY: {}}) is None
    assert get_current_step_id({META_KEY: {STATE_KEY: "title"}}) == "title"


def test_get_current_step():
    assert get_current_step({}) is None
    data = {META_KEY: {STATE_KEY: "title"}}
    step = get_current_step(data)
    assert step is not None
    assert step["state_id"] == "title"


def test_set_answer():
    data = {}
    data = set_answer(data, "title", "My Project")
    assert data["title"] == "My Project"
    assert META_KEY not in data or STATE_KEY not in (data.get(META_KEY) or {})


def test_set_step_id():
    data = {}
    data = set_step_id(data, "welcome")
    assert (data.get(META_KEY) or {}).get(STATE_KEY) == "welcome"
    data = set_step_id(data, "title")
    assert (data.get(META_KEY) or {}).get(STATE_KEY) == "title"


def test_transition_next():
    step = get_step("welcome")
    assert transition(step, "next") == "title"
    step = get_step("title")
    assert transition(step, "next") == "title_subtitle"
    step = get_step("confirm")
    assert transition(step, "next") == "__submit__"


def test_transition_back():
    step = get_step("title")
    assert transition(step, "back") == "welcome"
    step = get_step("title_subtitle")
    assert transition(step, "back") == "title"
    step = get_step("welcome")
    assert transition(step, "back") is None


def test_transition_skip():
    step = get_step("title_subtitle")
    assert transition(step, "skip") == "description_intro"
    step = get_step("description_features")
    assert transition(step, "skip") == "stack"
    step = get_step("title")  # not skippable, no skip_id
    assert transition(step, "skip") == "title_subtitle"  # falls back to next_id


def test_resume_from_saved_state():
    data = {META_KEY: {STATE_KEY: "price"}}
    step = get_current_step(data)
    assert step["state_id"] == "price"
    data = set_step_id(data, "contact")
    step = get_current_step(data)
    assert step["state_id"] == "contact"


def test_fsm_path_welcome_to_title_to_subtitle_back_to_title():
    """Path: welcome -> next -> title -> next -> title_subtitle -> back -> title."""
    from src.bot.project_submission_schema import first_step
    data = {}
    data = set_step_id(data, first_step()["state_id"])
    step = get_current_step(data)
    assert step["state_id"] == "welcome"
    next_id = transition(step, "next")
    assert next_id == "title"
    data = set_step_id(data, next_id)
    step = get_current_step(data)
    assert step["state_id"] == "title"
    next_id = transition(step, "next")
    assert next_id == "title_subtitle"
    data = set_step_id(data, next_id)
    step = get_current_step(data)
    assert step["state_id"] == "title_subtitle"
    back_id = transition(step, "back")
    assert back_id == "title"
    data = set_step_id(data, back_id)
    step = get_current_step(data)
    assert step["state_id"] == "title"


def test_fsm_path_skip_from_title_subtitle_to_description_intro():
    """Path: title_subtitle -> skip -> description_intro."""
    step = get_step("title_subtitle")
    next_id = transition(step, "skip")
    assert next_id == "description_intro"


def test_fsm_path_preview_to_confirm_back_to_preview():
    """Path: preview -> next -> confirm -> back -> preview."""
    step = get_step("preview")
    assert transition(step, "next") == "confirm"
    step = get_step("confirm")
    assert transition(step, "back") == "preview"


def test_fsm_path_skip_from_stack_other_to_link():
    """Path: stack_other (skippable) -> skip -> link."""
    step = get_step("stack_other")
    assert step.get("skippable") is True
    next_id = transition(step, "skip")
    assert next_id == "link"


def test_author_contact_type_conditional_routing():
    """author_contact_type: next with 'email' -> author_email, else -> author_telegram (V2 schema)."""
    from src.bot.project_submission_schema import get_project_submission_schema

    schema = get_project_submission_schema(True)
    step = schema.get_step("author_contact_type")
    if not step:
        pytest.skip("V2 schema without author_contact_type")
    assert transition(step, "next", "email") == "author_email"
    assert transition(step, "next", "Email") == "author_email"
    assert transition(step, "next", "e-mail") == "author_email"
    assert transition(step, "next", "telegram") == "author_telegram"
    assert transition(step, "next", "Telegram") == "author_telegram"
    assert transition(step, "next", None) == "author_telegram"
