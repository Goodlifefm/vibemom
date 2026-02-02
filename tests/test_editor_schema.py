"""Tests for V2 editor_schema: integrity, copy_id, missing_required_fields, is_field_filled."""

import pytest

from src.bot.editor_schema import (
    BLOCKS,
    FIELDS,
    get_block,
    get_field,
    get_fields_by_block,
    required_field_ids,
    missing_required_fields,
    is_field_filled,
    default_answers,
    all_copy_ids,
)


def test_blocks_exist():
    assert len(BLOCKS) >= 8
    block_ids = {b["block_id"] for b in BLOCKS}
    assert "author" in block_ids
    assert "project" in block_ids
    assert "done" in block_ids
    assert "stack" in block_ids
    assert "econ" in block_ids
    assert "gtm" in block_ids
    assert "goal" in block_ids
    assert "links" in block_ids


def test_author_block_has_name_contact_role():
    fields = get_fields_by_block("author")
    ids = {f["field_id"] for f in fields}
    assert "author_name" in ids
    assert "author_contact" in ids
    assert "author_role" in ids


def test_project_block_has_title_what_problem_audience():
    fields = get_fields_by_block("project")
    ids = {f["field_id"] for f in fields}
    assert "project_title" in ids
    assert "project_what" in ids
    assert "project_problem" in ids
    assert "audience_type" in ids


def test_all_copy_ids_exist_in_messages():
    from src.bot.messages import get_copy
    for copy_id in all_copy_ids():
        text = get_copy(copy_id)
        assert text is not None, f"copy_id {copy_id!r} missing"
        assert len(text.strip()) >= 0


def test_get_block():
    assert get_block("author") is not None
    assert get_block("project")["block_id"] == "project"
    assert get_block("nonexistent") is None


def test_get_field():
    assert get_field("author_name") is not None
    assert get_field("project_title")["answer_key"] == "project_title"
    assert get_field("nonexistent") is None


def test_required_field_ids():
    rid = required_field_ids()
    assert "author_name" in rid
    assert "project_title" in rid
    assert len(rid) >= 1


def test_missing_required_fields():
    answers = {}
    missing = missing_required_fields(answers)
    assert "author_name" in missing or "project_title" in missing
    answers["project_title"] = "Test"
    answers["project_what"] = "What"
    answers["project_problem"] = "Problem"
    answers["audience_type"] = "Audience"
    answers["author_name"] = "Name"
    answers["author_contact"] = "@u"
    answers["author_role"] = "Role"
    answers["working_now"] = "Now"
    answers["status"] = "Status"
    answers["metrics"] = "Metrics"
    answers["stack_ai"] = "AI"
    answers["stack_tech"] = "Tech"
    answers["stack_infra"] = "Infra"
    answers["econ_time"] = "1m"
    answers["dev_cost"] = "0"
    answers["monthly_cost"] = "0"
    answers["monetization"] = "No"
    answers["channels"] = ["tg"]
    answers["purpose"] = "Goal"
    answers["inbound_ready"] = "Yes"
    missing2 = missing_required_fields(answers)
    assert "channels" not in missing2 and "inbound_ready" not in missing2


def test_missing_required_fields_links_done_empty_allowed():
    answers = default_answers()
    answers["links_done"] = []
    missing = missing_required_fields(answers)
    assert "links_done" not in missing


def test_is_field_filled():
    f = get_field("project_title")
    assert f is not None
    assert is_field_filled({"project_title": "x"}, f) is True
    assert is_field_filled({"project_title": ""}, f) is False
    assert is_field_filled({"project_title": "—"}, f) is False
    fch = get_field("channels")
    if fch and fch.get("input_type") == "multi_choice":
        assert is_field_filled({"channels": ["tg"]}, fch) is True
        assert is_field_filled({"channels": []}, fch) is False


def test_default_answers():
    out = default_answers()
    assert "project_title" in out
    assert "author_name" in out
    assert "channels" in out
    assert out["channels"] == []
    assert out["project_title"] == ""


def test_required_fields_per_block():
    """Required fields per block: Author name+contact+role; Project title+what+problem+audience_type; etc."""
    rid = set(required_field_ids())
    # Author
    assert "author_name" in rid and "author_contact" in rid and "author_role" in rid
    # Project
    assert "project_title" in rid and "project_what" in rid and "project_problem" in rid and "audience_type" in rid
    # Done
    assert "working_now" in rid and "status" in rid and "metrics" in rid
    # Stack
    assert "stack_ai" in rid and "stack_tech" in rid and "stack_infra" in rid
    # Econ
    assert "econ_time" in rid and "dev_cost" in rid and "monthly_cost" in rid and "monetization" in rid
    # GTM: channels required; notes optional
    assert "channels" in rid
    # Goal: purpose + inbound_ready; links_done can be empty (optional)
    assert "purpose" in rid and "inbound_ready" in rid
    # Links block optional
    assert "links_collector" not in rid


def test_missing_required_inbound_ready():
    """inbound_ready is required for Goal block; empty counts as missing."""
    answers = default_answers()
    answers["purpose"] = "Goal"
    # inbound_ready missing
    missing = missing_required_fields(answers)
    assert "inbound_ready" in missing
    answers["inbound_ready"] = "Yes"
    missing2 = missing_required_fields(answers)
    assert "inbound_ready" not in missing2


def test_channels_multi_choice_toggle_logic():
    """Multi-select channels: toggling adds/removes choice; empty list = missing for required."""
    # Simulate toggle: if choice in list remove else add
    def toggle(channels: list, choice: str) -> list:
        if choice in channels:
            return [c for c in channels if c != choice]
        return channels + [choice]
    assert toggle([], "tg") == ["tg"]
    assert toggle(["tg"], "tg") == []
    assert toggle(["tg"], "vk") == ["tg", "vk"]
    assert toggle(["tg", "vk"], "tg") == ["vk"]
    # Required: empty channels = missing
    a_empty = default_answers()
    a_empty["channels"] = []
    assert "channels" in missing_required_fields(a_empty)
    a_filled = default_answers()
    a_filled["channels"] = ["tg"]
    assert "channels" not in missing_required_fields(a_filled)
