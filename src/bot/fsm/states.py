from aiogram.fsm.state import State, StatesGroup


class ProjectSubmissionStates(StatesGroup):
    """Single state for config-driven submission (step_id in data[_meta][project_submission_state])."""
    filling = State()


class BuyerRequestStates(StatesGroup):
    what = State()
    budget = State()
    contact = State()
    confirm = State()
