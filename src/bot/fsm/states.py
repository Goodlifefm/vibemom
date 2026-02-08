from aiogram.fsm.state import State, StatesGroup


class ProjectSubmissionStates(StatesGroup):
    """Single state for config-driven submission (step_id in data[_meta][project_submission_state])."""
    filling = State()


class BuyerRequestStates(StatesGroup):
    what = State()
    budget = State()
    contact = State()
    confirm = State()


class EditorStates(StatesGroup):
    """V2 block editor: block menu and field edit."""
    block_menu = State()
    field_edit = State()


class ModerationStates(StatesGroup):
    """Admin moderation: collecting reject reason after pressing ❌ Reject."""
    awaiting_reject_reason = State()
