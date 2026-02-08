"""
V2 project submission schema: 25 steps, new answer keys.
Used when v2_enabled=True. get_project_submission_schema(True) returns this.
"""

from __future__ import annotations

from typing import Any, Callable

VALIDATORS: dict[str, Callable[[str | None], tuple[bool, Any]]] = {}


def _register_validators() -> None:
    from src.bot import validators as v
    def yes_no(t: str | None) -> tuple[bool, bool | None]:
        yn = v.parse_yes_no(t)
        return (yn is not None, yn)

    def time_spent(t: str | None) -> tuple[bool, str | None]:
        return v.validate_time_spent_has_digit(t, 200)

    def int_optional(t: str | None) -> tuple[bool, int | None]:
        return v.validate_int_optional(t)

    def email_val(t: str | None) -> tuple[bool, str | None]:
        return v.validate_email(t, 200)

    VALIDATORS.update({
        "yes_no": yes_no,
        "non_empty_200": lambda t: v.validate_non_empty(t, 200),
        "non_empty_500": lambda t: v.validate_non_empty(t, 500),
        "max_100": lambda t: v.validate_max_len(t, 100, allow_empty=True),
        "max_200": lambda t: v.validate_max_len(t, 200, allow_empty=True),
        "max_300": lambda t: v.validate_max_len(t, 300, allow_empty=True),
        "max_500": lambda t: v.validate_max_len(t, 500, allow_empty=True),
        "max_1000": lambda t: v.validate_max_len(t, 1000, allow_empty=True),
        "non_empty_max_200": lambda t: v.validate_non_empty(t, 200),
        "non_empty_max_500": lambda t: v.validate_non_empty(t, 500),
        "non_empty_max_1000": lambda t: v.validate_non_empty(t, 1000),
        "url_1000": lambda t: v.validate_url(t, 1000),
        "url_or_empty_1000": lambda t: v.validate_url_or_empty(t, 1000),
        "time_spent": time_spent,
        "int_optional": int_optional,
        "email": email_val,
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


# 25 steps: new answer keys (author_name, author_contact_type, project_title, ...)
STEPS: list[dict[str, Any]] = [
    _step("welcome", "SUBMIT_START", "buttons", "", None, "author_name", None),
    _step("author_name", "V2_AUTHOR_NAME", "text", "non_empty_200", "author_name", "author_contact_type", "welcome"),
    _step("author_contact_type", "V2_AUTHOR_CONTACT_TYPE", "choice", "non_empty_200", "author_contact_type", "author_telegram", "author_name"),
    _step("author_telegram", "V2_AUTHOR_TELEGRAM", "text", "non_empty_200", "author_telegram", "author_role", "author_contact_type"),
    _step("author_email", "V2_AUTHOR_EMAIL", "text", "email", "author_email", "author_role", "author_contact_type"),
    _step("author_role", "V2_AUTHOR_ROLE", "text", "non_empty_200", "author_role", "project_title", "author_contact_type"),
    _step("project_title", "SUBMIT_Q1_TITLE", "text", "non_empty_200", "project_title", "project_subtitle", "author_role"),
    _step("project_subtitle", "V2_PROJECT_SUBTITLE", "text", "max_500", "project_subtitle", "project_problem", "project_title"),
    _step("project_problem", "SUBMIT_Q2_WHAT_IT_DOES", "text", "non_empty_max_1000", "project_problem", "project_audience_type", "project_subtitle"),
    _step("project_audience_type", "SUBMIT_Q2_FOR_WHOM", "text", "non_empty_max_500", "project_audience_type", "project_niche", "project_problem"),
    _step("project_niche", "V2_PROJECT_NICHE", "text", "max_300", "project_niche", "product_working_now", "project_audience_type", "product_working_now", True),
    _step("product_working_now", "V2_PRODUCT_WORKING_NOW", "text", "non_empty_max_500", "product_working_now", "product_status", "project_niche"),
    _step("product_status", "V2_PRODUCT_STATUS", "text", "non_empty_max_200", "product_status", "stack_ai", "product_working_now"),
    _step("stack_ai", "SUBMIT_Q3_STACK", "text", "non_empty_max_500", "stack_ai", "stack_tech", "product_status"),
    _step("stack_tech", "SUBMIT_Q3_STACK_LIST", "text", "max_500", "stack_tech", "stack_infra", "stack_ai"),
    _step("stack_infra", "SUBMIT_Q3_OTHER_TOOLS", "text", "max_300", "stack_infra", "stack_reason", "stack_tech"),
    _step("stack_reason", "V2_STACK_REASON", "text", "max_300", "stack_reason", "econ_time_spent", "stack_infra", "econ_time_spent", True),
    _step("econ_time_spent", "V2_ECON_TIME_SPENT", "text", "time_spent", "econ_time_spent", "econ_dev_cost_currency", "stack_reason"),
    _step("econ_dev_cost_currency", "V2_ECON_DEV_COST_CURRENCY", "choice", "non_empty_200", "econ_dev_cost_currency", "econ_dev_cost_min", "econ_time_spent"),
    _step("econ_dev_cost_min", "V2_ECON_DEV_COST_MIN", "text", "int_optional", "econ_dev_cost_min", "econ_dev_cost_max", "econ_dev_cost_currency"),
    _step("econ_dev_cost_max", "V2_ECON_DEV_COST_MAX", "text", "int_optional", "econ_dev_cost_max", "econ_monet_format", "econ_dev_cost_min"),
    _step("econ_monet_format", "SUBMIT_Q5_PRICE", "text", "non_empty_max_200", "econ_monet_format", "econ_monet_details", "econ_dev_cost_max"),
    _step("econ_monet_details", "SUBMIT_Q5_PRICE_NOTE", "text", "max_500", "econ_monet_details", "econ_potential", "econ_monet_format"),
    _step("econ_potential", "V2_ECON_POTENTIAL", "text", "max_300", "econ_potential", "gtm_stage", "econ_monet_details", "gtm_stage", True),
    _step("gtm_stage", "V2_GTM_STAGE", "text", "non_empty_max_200", "gtm_stage", "gtm_channels", "econ_potential"),
    _step("gtm_channels", "V2_CHANNELS", "multi_choice", "", "gtm_channels", "gtm_traction", "gtm_stage"),
    _step("gtm_traction", "V2_GTM_TRACTION", "text", "max_500", "gtm_traction", "goal_publication", "gtm_channels"),
    _step("goal_publication", "V2_GOAL_PUBLICATION", "text", "non_empty_max_300", "goal_publication", "goal_inbound_ready", "gtm_traction"),
    _step("goal_inbound_ready", "V2_GOAL_INBOUND_READY", "text", "max_300", "goal_inbound_ready", "links", "goal_publication"),
    _step("links", "SUBMIT_Q4_LINK", "multi_link", "url_1000", "links", "preview", "goal_inbound_ready"),
    _step("preview", "SUBMIT_PREVIEW", "buttons", "", None, "confirm", "links"),
    _step("confirm", "SUBMIT_Q7_CONFIRM", "yes_no", "yes_no", None, "__submit__", "preview"),
]

# Fix author_role back_id: can be author_telegram or author_email depending on type - use author_contact_type
# Fix author_telegram/author_email: only one is used; we need conditional next. For simplicity author_role back_id = author_telegram
_STATE_IDS = {s["state_id"] for s in STEPS}


def _check_integrity() -> None:
    for step in STEPS:
        for key in ("next_id", "back_id", "skip_id"):
            ref = step.get(key)
            if ref and ref != "__submit__" and ref not in _STATE_IDS:
                raise ValueError(f"Step {step['state_id']}: {key}={ref!r} not in schema")
    if STEPS[0]["next_id"] != "author_name":
        raise ValueError("First step welcome must have next_id=author_name")


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
