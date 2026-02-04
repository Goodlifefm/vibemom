"""
Config-driven FSM schema for project submission (SPEC 03_FSM_PROJECT_SUBMISSION).
23 steps; integrity checks at import time.
"""

from __future__ import annotations

from typing import Any, Callable

# Filled after validators import
VALIDATORS: dict[str, Callable[[str | None], tuple[bool, str | None]]] = {}


def _register_validators() -> None:
    from src.bot import validators as v
    def yes_no(t: str | None) -> tuple[bool, bool | None]:
        yn = v.parse_yes_no(t)
        return (yn is not None, yn)

    VALIDATORS.update({
        "yes_no": yes_no,
        "non_empty_200": lambda t: v.validate_non_empty(t, 200),
        "non_empty_500": lambda t: v.validate_non_empty(t, 500),
        "non_empty_1000": lambda t: v.validate_non_empty(t, 1000),
        "max_50": lambda t: v.validate_max_len(t, 50, allow_empty=True),
        "max_100": lambda t: v.validate_max_len(t, 100, allow_empty=True),
        "max_150": lambda t: v.validate_max_len(t, 150, allow_empty=True),
        "max_200": lambda t: v.validate_max_len(t, 200, allow_empty=True),
        "max_300": lambda t: v.validate_max_len(t, 300, allow_empty=True),
        "max_400": lambda t: v.validate_max_len(t, 400, allow_empty=True),
        "max_500": lambda t: v.validate_max_len(t, 500, allow_empty=True),
        "max_1000": lambda t: v.validate_max_len(t, 1000, allow_empty=True),
        "non_empty_max_200": lambda t: v.validate_non_empty(t, 200),
        "non_empty_max_500": lambda t: v.validate_non_empty(t, 500),
        "non_empty_max_1000": lambda t: v.validate_non_empty(t, 1000),
        "url_1000": lambda t: v.validate_url(t, 1000),
        "url_or_empty_1000": lambda t: v.validate_url_or_empty(t, 1000),
    })


_register_validators()


def _step(
    state_id: str,
    copy_id: str,
    input_type: str,
    validator: str,
    answer_key: str | None,
    next_id: str | None,
    back_id: str | None,
    skip_id: str | None = None,
    skippable: bool = False,
) -> dict[str, Any]:
    return {
        "state_id": state_id,
        "copy_id": copy_id,
        "input_type": input_type,
        "validator": validator,
        "answer_key": answer_key,
        "next_id": next_id,
        "back_id": back_id,
        "skip_id": skip_id,
        "skippable": skippable,
    }


# 23 steps from SPEC 03 table (order matters)
STEPS: list[dict[str, Any]] = [
    _step("welcome", "SUBMIT_START", "buttons", "", None, "title", None),
    _step("title", "SUBMIT_Q1_TITLE", "text", "non_empty_200", "title", "title_subtitle", "welcome"),
    _step("title_subtitle", "SUBMIT_Q1_SUBTITLE", "text", "max_150", "title_subtitle", "description_intro", "title", "description_intro", True),
    _step("description_intro", "SUBMIT_Q2_INTRO", "text", "max_300", "description_intro", "description_what", "title_subtitle", "description_what", True),
    _step("description_what", "SUBMIT_Q2_WHAT_IT_DOES", "text", "non_empty_max_1000", "description_what", "description_audience", "description_intro"),
    _step("description_audience", "SUBMIT_Q2_FOR_WHOM", "text", "non_empty_max_500", "description_audience", "description_summary", "description_what"),
    _step("description_summary", "SUBMIT_Q2_SUMMARY", "text", "max_400", "description_summary", "description_features", "description_audience", "description_features", True),
    _step("description_features", "SUBMIT_Q2_KEY_FEATURES", "multi", "max_500", "description_features", "stack", "description_summary", "stack", True),
    _step("stack", "SUBMIT_Q3_STACK", "text", "non_empty_max_500", "stack", "stack_list", "description_features"),
    _step("stack_list", "SUBMIT_Q3_STACK_LIST", "text", "max_400", "stack_list", "stack_other", "stack", "stack_other", True),
    _step("stack_other", "SUBMIT_Q3_OTHER_TOOLS", "text", "max_300", "stack_other", "stack_confirm", "stack_list", "link", True),
    _step("stack_confirm", "SUBMIT_Q3_CONFIRM", "buttons", "", None, "link", "stack_other", "link", True),
    _step("link", "SUBMIT_Q4_LINK", "text", "url_1000", "link", "link_demo", "stack_confirm"),
    _step("link_demo", "SUBMIT_Q4_LINK_DEMO", "text", "url_or_empty_1000", "link_demo", "link_confirm", "link", "link_confirm", True),
    _step("link_confirm", "SUBMIT_Q4_LINK_CONFIRM", "text", "url_or_empty_1000", "link_confirm", "price", "link_demo", "price", True),
    _step("price", "SUBMIT_Q5_PRICE", "text", "non_empty_max_200", "price", "price_note", "link_confirm"),
    _step("price_note", "SUBMIT_Q5_PRICE_NOTE", "text", "max_300", "price_note", "price_currency", "price", "price_currency", True),
    _step("price_currency", "SUBMIT_Q5_CURRENCY", "text", "max_50", "price_currency", "contact", "price_note", "contact", True),
    _step("contact", "SUBMIT_Q6_CONTACT", "text", "non_empty_max_200", "contact", "contact_extra", "price_currency"),
    _step("contact_extra", "SUBMIT_Q6_CONTACT_EXTRA", "text", "max_200", "contact_extra", "contact_preferred", "contact", "contact_preferred", True),
    _step("contact_preferred", "SUBMIT_Q6_PREFERRED", "text", "max_100", "contact_preferred", "preview", "contact_extra", "preview", True),
    _step("preview", "SUBMIT_PREVIEW", "buttons", "", None, "confirm", "contact_preferred"),
    _step("confirm", "SUBMIT_Q7_CONFIRM", "yes_no", "yes_no", None, "__submit__", "preview"),
]

_STATE_IDS = {s["state_id"] for s in STEPS}


def _check_integrity() -> None:
    for step in STEPS:
        for key in ("next_id", "back_id", "skip_id"):
            ref = step.get(key)
            if ref and ref != "__submit__" and ref not in _STATE_IDS:
                raise ValueError(f"Step {step['state_id']}: {key}={ref!r} not in schema")
    if STEPS[0]["next_id"] != "title":
        raise ValueError("First step welcome must have next_id=title")


_check_integrity()


def first_step() -> dict[str, Any]:
    return STEPS[0]


def get_step(state_id: str) -> dict[str, Any] | None:
    for s in STEPS:
        if s["state_id"] == state_id:
            return s
    return None


def step_index(state_id: str) -> int:
    for i, s in enumerate(STEPS):
        if s["state_id"] == state_id:
            return i
    return -1


class _Schema:
    """Schema wrapper for V1 or V2."""
    def __init__(self, steps: list[dict], validators: dict, first_step_fn: Callable, get_step_fn: Callable, step_index_fn: Callable):
        self.STEPS = steps
        self.VALIDATORS = validators
        self._first_step_fn = first_step_fn
        self._get_step_fn = get_step_fn
        self._step_index_fn = step_index_fn
    
    def first_step(self) -> dict[str, Any]:
        return self._first_step_fn()
    
    def get_step(self, state_id: str) -> dict[str, Any] | None:
        return self._get_step_fn(state_id)
    
    def step_index(self, state_id: str) -> int:
        return self._step_index_fn(state_id)


def get_project_submission_schema(v2_enabled: bool) -> _Schema:
    """Return schema object for submission FSM. When v2_enabled=True uses V2 (25+ steps, new keys)."""
    if v2_enabled:
        from src.bot import project_submission_schema_v2 as v2
        return _Schema(
            steps=v2.STEPS,
            validators=v2.VALIDATORS,
            first_step_fn=v2.first_step,
            get_step_fn=v2.get_step,
            step_index_fn=v2.step_index,
        )
    return _Schema(
        steps=STEPS,
        validators=VALIDATORS,
        first_step_fn=first_step,
        get_step_fn=get_step,
        step_index_fn=step_index,
    )
