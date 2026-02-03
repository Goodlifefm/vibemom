"""
V2 step registry: single source of truth.
step_key -> answer_key, copy_id, validator, optional, multi_link, next_step, prev_step.
Q8, Q12, Q16 optional; Q19 multi_link (links array). Budget is single step q10.
"""
from typing import TypedDict


class StepDef(TypedDict):
    step_key: str
    answer_key: str
    copy_id: str
    validator: str
    optional: bool
    multi_link: bool
    next_step: str | None
    prev_step: str | None


def _step(
    step_key: str,
    answer_key: str,
    copy_id: str,
    validator: str = "non_empty",
    optional: bool = False,
    multi_link: bool = False,
    next_step: str | None = None,
    prev_step: str | None = None,
) -> StepDef:
    return StepDef(
        step_key=step_key,
        answer_key=answer_key,
        copy_id=copy_id,
        validator=validator,
        optional=optional,
        multi_link=multi_link,
        next_step=next_step,
        prev_step=prev_step,
    )


# 19 steps: q1..q10 (budget), q11..q18, preview. Q8, Q14, Q17 optional. Q18 multi_link.
# Budget: single step (replaces old currency, cost, cost_max).
_STEPS: list[StepDef] = [
    _step("q1", "title", "V2_FORM_STEP1", "non_empty", False, False, "q2", None),
    _step("q2", "description", "V2_FORM_STEP2", "non_empty", False, False, "q3", "q1"),
    _step("q3", "contact", "V2_FORM_STEP3", "contact", False, False, "q4", "q2"),
    _step("q4", "subtitle", "V2_PROJECT_SUBTITLE", "non_empty", False, False, "q5", "q3"),
    _step("q5", "niche", "V2_PROJECT_NICHE", "non_empty", False, False, "q6", "q4"),
    _step("q6", "what_done", "V2_PRODUCT_WORKING_NOW", "non_empty", False, False, "q7", "q5"),
    _step("q7", "status", "V2_PRODUCT_STATUS", "non_empty", False, False, "q8", "q6"),
    _step("q8", "stack_reason", "V2_STACK_REASON", "non_empty", True, False, "q9", "q7"),
    _step("q9", "time_spent", "V2_ECON_TIME_SPENT", "time", False, False, "q10", "q8"),
    _step("q10", "budget", "V2_ECON_BUDGET", "budget", False, False, "q11", "q9"),
    _step("q11", "potential", "V2_ECON_POTENTIAL", "non_empty", False, False, "q12", "q10"),
    _step("q12", "traction", "V2_GTM_TRACTION", "non_empty", True, False, "q13", "q11"),
    _step("q13", "gtm_stage", "V2_GTM_STAGE", "non_empty", False, False, "q14", "q12"),
    _step("q14", "goal_pub", "V2_GOAL_PUBLICATION", "non_empty", False, False, "q15", "q13"),
    _step("q15", "goal_inbound", "V2_GOAL_INBOUND_READY", "non_empty", False, False, "q16", "q14"),
    _step("q16", "channels", "V2_CHANNELS", "non_empty", True, False, "q17", "q15"),
    _step("q17", "author_name", "V2_AUTHOR_NAME", "non_empty", False, False, "q18", "q16"),
    _step("q18", "author_contact", "V2_AUTHOR_EMAIL", "contact", False, False, "q19", "q17"),
    _step("q19", "links", "V2_LINK_ADD_PROMPT", "link", False, True, "preview", "q18"),
]

STEP_REGISTRY: list[StepDef] = _STEPS

STEP_KEYS: list[str] = [s["step_key"] for s in _STEPS]


def get_step(step_key: str) -> StepDef | None:
    for s in _STEPS:
        if s["step_key"] == step_key:
            return s
    return None


def get_step_index(step_key: str) -> int:
    for i, s in enumerate(_STEPS):
        if s["step_key"] == step_key:
            return i
    return -1


def get_next_step(step_key: str) -> str | None:
    s = get_step(step_key)
    return s["next_step"] if s else None


def get_prev_step(step_key: str) -> str | None:
    s = get_step(step_key)
    return s["prev_step"] if s else None


def is_optional(step_key: str) -> bool:
    s = get_step(step_key)
    return s["optional"] if s else False


def is_multi_link(step_key: str) -> bool:
    s = get_step(step_key)
    return s["multi_link"] if s else False
