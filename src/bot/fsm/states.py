from aiogram.fsm.state import State, StatesGroup


class ProjectSubmissionStates(StatesGroup):
    title = State()
    description = State()
    stack = State()
    link = State()
    price = State()
    contact = State()
    confirm = State()


class BuyerRequestStates(StatesGroup):
    what = State()
    budget = State()
    contact = State()
    confirm = State()
