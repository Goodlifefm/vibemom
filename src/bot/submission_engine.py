"""
Generic FSM engine for project submission. Schema from get_project_submission_schema(V2_ENABLED).
Renders step text + keyboard, validates input, sets answers, transitions.
"""

from __future__ import annotations

from typing import Any

from src.bot.config import Settings
from src.bot.project_submission_schema import get_project_submission_schema
from src.bot.messages import get_copy
from src.bot.keyboards import (
    ps_nav_step,
    ps_preview_kb,
    ps_confirm_final_kb,
)
from src.bot.renderer import answers_to_project_fields, render_project_post


META_KEY = "_meta"
STATE_KEY = "project_submission_state"


def get_schema():
    """Return schema (V1 or V2) based on Settings().v2_enabled."""
    return get_project_submission_schema(Settings().v2_enabled)


def get_current_step_id(data: dict) -> str | None:
    meta = data.get(META_KEY) or {}
    return meta.get(STATE_KEY)


def get_current_step(data: dict) -> dict[str, Any] | None:
    sid = get_current_step_id(data)
    return get_schema().get_step(sid) if sid else None


def set_answer(data: dict, answer_key: str, value: Any) -> dict:
    """Write value into data[answer_key]. Return updated data (mutates in place)."""
    data = dict(data)
    if META_KEY not in data:
        data[META_KEY] = {}
    data[META_KEY] = dict(data[META_KEY])
    data[answer_key] = value
    return data


def set_step_id(data: dict, state_id: str) -> dict:
    data = dict(data)
    if META_KEY not in data:
        data[META_KEY] = {}
    data[META_KEY] = dict(data[META_KEY])
    data[META_KEY][STATE_KEY] = state_id
    return data


def validate_input(step: dict[str, Any], text: str | None) -> tuple[bool, Any]:
    """Validate user text for step. Returns (ok, value)."""
    vname = step.get("validator") or ""
    if not vname:
        return True, None
    fn = get_schema().VALIDATORS.get(vname)
    if not fn:
        return True, text
    return fn(text)


def transition(step: dict[str, Any], action: str) -> str | None:
    """action: 'next' | 'back' | 'skip'. Returns next state_id or __submit__."""
    if action == "back":
        return step.get("back_id")
    if action == "skip":
        return step.get("skip_id") or step.get("next_id")
    return step.get("next_id")


def render_step(step: dict[str, Any], data: dict) -> tuple[str, Any]:
    """
    Returns (text, reply_markup) for the current step.
    For preview step, text includes rendered project post.
    """
    state_id = step["state_id"]
    copy_id = step["copy_id"]
    text = get_copy(copy_id)

    if state_id == "welcome":
        reply_markup = ps_nav_step(back=False, next_=True, save=True, skip=False)
        return text, reply_markup

    if state_id == "preview":
        fields = answers_to_project_fields(data)
        post = render_project_post(
            fields["title"], fields["description"], fields["stack"],
            fields["link"], fields["price"], fields["contact"],
            gtm_stage=fields.get("gtm_stage") or "",
            gtm_channels=fields.get("gtm_channels"),
            gtm_traction=fields.get("gtm_traction") or "",
        )
        text = post + "\n\n" + get_copy("SUBMIT_PREVIEW")
        reply_markup = ps_preview_kb()
        return text, reply_markup

    if state_id == "confirm":
        reply_markup = ps_confirm_final_kb()
        return text, reply_markup

    back = bool(step.get("back_id"))
    next_ = bool(step.get("next_id"))
    skip = bool(step.get("skippable"))
    reply_markup = ps_nav_step(back=back, next_=next_, save=True, skip=skip)
    return text, reply_markup
