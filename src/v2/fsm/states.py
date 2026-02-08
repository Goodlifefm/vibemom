"""V2 FSM: one state per question via step_key in data; persist after each step."""
from aiogram.fsm.state import State, StatesGroup


class V2FormSteps(StatesGroup):
    """Generic answering state; current_step_key in FSM data + DB current_step for resume."""
    answering = State()

    # Legacy step1/2/3 kept for backward compat with start.py resume until fully migrated
    step1 = State()
    step2 = State()
    step3 = State()


class V2ModSteps(StatesGroup):
    """Admin moderation: awaiting fix text or reject reason. Data: mod_pending_sub_id."""
    awaiting_fix_text = State()
    awaiting_reject_reason = State()
