"""
V2 Editor: single source of truth for editable fields.
Required fields per block:
  Author: name + contact + role
  Project: title + what + problem + audience_type
  Done: working_now + status + metrics
  Stack: ai + tech + infra
  Econ: time + dev_cost + monthly_cost + monetization
  GTM: channels + notes
  Goal: purpose + inbound_ready + links_done (list, can be empty)
  Links: allow empty; if user enters, validate each (link collector)
Maps to project columns (title, description, stack, link, price, contact) for DB.
"""
from __future__ import annotations

import json
from typing import Any, Callable

# Validator registry (filled from validators module)
VALIDATORS: dict[str, Callable[[str | None], tuple[bool, Any]]] = {}


def _register_validators() -> None:
    from src.bot import validators as v
    VALIDATORS.update({
        "non_empty_200": lambda t: v.validate_non_empty(t, 200),
        "non_empty_500": lambda t: v.validate_non_empty(t, 500),
        "non_empty_1000": lambda t: v.validate_non_empty(t, 1000),
        "max_200": lambda t: v.validate_max_len(t, 200, allow_empty=True),
        "max_500": lambda t: v.validate_max_len(t, 500, allow_empty=True),
        "max_1000": lambda t: v.validate_max_len(t, 1000, allow_empty=True),
        "url_1000": lambda t: v.validate_url(t, 1000),
        "url_or_empty_1000": lambda t: v.validate_url_or_empty(t, 1000),
    })
_register_validators()


def _field(
    field_id: str,
    block_id: str,
    label: str,
    copy_id: str,
    answer_key: str,
    input_type: str = "text",
    required: bool = True,
    skippable: bool = False,
    validator: str = "non_empty_200",
    choices: list[str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "field_id": field_id,
        "block_id": block_id,
        "label": label,
        "copy_id": copy_id,
        "answer_key": answer_key,
        "input_type": input_type,
        "required": required,
        "skippable": skippable,
        "validator": validator,
    }
    if choices is not None:
        out["choices"] = choices
    return out


# Blocks: Author, Project, Done, Stack, Econ, GTM, Goal, Links
BLOCKS: list[dict[str, Any]] = [
    {"block_id": "author", "label": "Автор", "emoji": "👤"},
    {"block_id": "project", "label": "Проект", "emoji": "📌"},
    {"block_id": "done", "label": "Что сделано", "emoji": "⚙️"},
    {"block_id": "stack", "label": "Vibe-стек", "emoji": "🧩"},
    {"block_id": "econ", "label": "Экономика", "emoji": "💰"},
    {"block_id": "gtm", "label": "GTM", "emoji": "📢"},
    {"block_id": "goal", "label": "Цель", "emoji": "🎯"},
    {"block_id": "links", "label": "Ссылки", "emoji": "🔗"},
]

# All fields; answer_key used in answers dict
FIELDS: list[dict[str, Any]] = [
    # Author: name + contact + role
    _field("author_name", "author", "Имя", "V2_AUTHOR_NAME", "author_name", required=True),
    _field("author_contact", "author", "Контакт", "SUBMIT_Q6_CONTACT", "author_contact", required=True),
    _field("author_role", "author", "Роль", "V2_AUTHOR_ROLE", "author_role", required=True),
    # Project: title + what + problem + audience_type
    _field("project_title", "project", "Название", "SUBMIT_Q1_TITLE", "project_title", required=True),
    _field("project_what", "project", "Что делает", "SUBMIT_Q2_WHAT_IT_DOES", "project_what", required=True),
    _field("project_problem", "project", "Проблема", "SUBMIT_Q2_DESCRIPTION", "project_problem", required=True),
    _field("audience_type", "project", "Аудитория", "SUBMIT_Q2_FOR_WHOM", "audience_type", required=True),
    # Done: working_now + status + metrics
    _field("working_now", "done", "Что сделано сейчас", "SUBMIT_Q2_DESCRIPTION", "working_now", required=True),
    _field("status", "done", "Статус", "SUBMIT_Q2_DESCRIPTION", "status", required=True),
    _field("metrics", "done", "Метрики", "SUBMIT_Q2_DESCRIPTION", "metrics", required=True),
    # Stack: ai + tech + infra
    _field("stack_ai", "stack", "AI", "SUBMIT_Q3_STACK", "stack_ai", required=True),
    _field("stack_tech", "stack", "Технологии", "SUBMIT_Q3_STACK", "stack_tech", required=True),
    _field("stack_infra", "stack", "Инфра", "SUBMIT_Q3_STACK", "stack_infra", required=True),
    # Econ: time + dev_cost + monthly_cost + monetization
    _field("econ_time", "econ", "Время", "SUBMIT_Q5_PRICE", "econ_time", required=True),
    _field("dev_cost", "econ", "Стоимость разработки", "SUBMIT_Q5_PRICE", "dev_cost", required=True),
    _field("monthly_cost", "econ", "Месячные затраты", "SUBMIT_Q5_PRICE", "monthly_cost", required=True),
    _field("monetization", "econ", "Монетизация", "SUBMIT_Q5_PRICE", "monetization", required=True),
    # GTM: channels (multi_choice) + notes
    _field("channels", "gtm", "Каналы", "V2_CHANNELS", "channels", input_type="multi_choice", required=True, choices=["tg", "vk", "site"]),
    _field("gtm_notes", "gtm", "Заметки", "SUBMIT_Q2_SUMMARY", "gtm_notes", required=False, skippable=True),
    # Goal: purpose + inbound_ready + links_done (list, can be empty)
    _field("purpose", "goal", "Цель", "SUBMIT_Q2_WHAT_IT_DOES", "purpose", required=True),
    _field("inbound_ready", "goal", "Inbound готовность", "SUBMIT_Q2_SUMMARY", "inbound_ready", required=True),
    _field("links_done", "goal", "Ссылки", "SUBMIT_Q4_LINK", "links_done", input_type="links", required=False, skippable=True),
    # Links block: link collector (same answer_key links_done)
    _field("links_collector", "links", "Список ссылок", "SUBMIT_Q4_LINK", "links_done", input_type="links", required=False, skippable=True),
]

# Legacy 6-key mapping for backward compat (project row)
LEGACY_KEYS = ("title", "description", "stack", "link", "price", "contact")


def get_block(block_id: str) -> dict[str, Any] | None:
    for b in BLOCKS:
        if b["block_id"] == block_id:
            return b
    return None


def get_field(field_id: str) -> dict[str, Any] | None:
    for f in FIELDS:
        if f["field_id"] == field_id:
            return f
    return None


def get_fields_by_block(block_id: str) -> list[dict[str, Any]]:
    return [f for f in FIELDS if f["block_id"] == block_id]


def required_field_ids() -> list[str]:
    return [f["field_id"] for f in FIELDS if f.get("required")]


def _normalize_value(val: Any) -> str | list:
    if val is None:
        return ""
    if isinstance(val, list):
        return list(val)
    s = str(val).strip()
    if s in ("", "—"):
        return ""
    return s


def missing_required_fields(answers: dict) -> list[str]:
    """Return field_ids that are required but empty. links_done can be empty list. multi_choice empty list = missing."""
    missing = []
    for f in FIELDS:
        if not f.get("required"):
            continue
        key = f["answer_key"]
        val = answers.get(key)
        if f.get("input_type") == "links":
            continue
        if f.get("input_type") == "multi_choice":
            if val is None or (isinstance(val, list) and len(val) == 0) or (isinstance(val, str) and (val or "").strip() in ("", "—")):
                missing.append(f["field_id"])
            continue
        s = (val or "").strip()
        if s in ("", "—"):
            missing.append(f["field_id"])
    return missing


def is_field_filled(answers: dict, field: dict[str, Any]) -> bool:
    """Whether the field has a non-empty value in answers (for block completion count)."""
    key = field["answer_key"]
    val = answers.get(key)
    if isinstance(val, list):
        return len(val) > 0
    s = (val or "").strip()
    return s not in ("", "—")


def all_copy_ids() -> set[str]:
    """All copy_id used in schema (for audit)."""
    return {f["copy_id"] for f in FIELDS}


def default_answers() -> dict[str, Any]:
    """Default empty answers for all answer_keys (for merge with project row)."""
    out: dict[str, Any] = {}
    for f in FIELDS:
        key = f["answer_key"]
        if key in out:
            continue
        if f.get("input_type") in ("multi_choice", "links"):
            out[key] = []
        else:
            out[key] = ""
    return out


def all_next_back_skip_valid() -> bool:
    """Schema integrity: no dangling refs (N/A for editor_schema; used in project_submission_schema)."""
    return True
