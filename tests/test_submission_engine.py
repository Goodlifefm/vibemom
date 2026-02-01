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
