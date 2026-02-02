"""V2 form: generic handlers from step registry. Persist after each step; back/skip/save/resume."""
import uuid

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.messages import get_copy
from src.v2.repo import get_submission, update_answers_step
from src.v2.fsm.states import V2FormSteps
from src.v2.fsm.steps import (
    get_step,
    get_next_step,
    get_prev_step,
    is_optional,
    is_multi_link,
)
from src.v2.validators import validate

router = Router()
PREFIX = "v2form"

DATA_SUBMISSION_ID = "submission_id"
DATA_STEP_KEY = "current_step_key"


def _form_kb(step_key: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=get_copy("V2_BTN_BACK").strip(), callback_data=f"{PREFIX}:back")]]
    if is_optional(step_key):
        rows.append([InlineKeyboardButton(text=get_copy("V2_BTN_SKIP").strip(), callback_data=f"{PREFIX}:skip")])
    if is_multi_link(step_key):
        rows.append([InlineKeyboardButton(text=get_copy("V2_FINISH_LINKS").strip(), callback_data=f"{PREFIX}:finish_links")])
    rows.append([InlineKeyboardButton(text=get_copy("V2_SAVE_BTN").strip(), callback_data=f"{PREFIX}:save")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_question(message: Message, state: FSMContext, step_key: str) -> None:
    """Show question for step_key (repeat question for back/resume)."""
    step_def = get_step(step_key)
    if not step_def:
        return
    text = get_copy(step_def["copy_id"])
    await message.answer(text, reply_markup=_form_kb(step_key), parse_mode="HTML")


async def _persist_and_go_next(
    message: Message,
    state: FSMContext,
    sub_id: uuid.UUID,
    answers_delta: dict,
    next_step_key: str,
) -> None:
    await update_answers_step(sub_id, answers_delta, current_step=next_step_key)
    await state.update_data(**{DATA_STEP_KEY: next_step_key})
    if next_step_key == "preview":
        from src.v2.routers.preview import show_preview
        await show_preview(message, state)
    else:
        await show_question(message, state, next_step_key)


# ---- Text answer (generic) ----
@router.message(V2FormSteps.answering, F.text)
async def handle_text_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    if not sid or not step_key:
        await message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
        return
    try:
        sub_id = uuid.UUID(sid)
    except ValueError:
        return
    step_def = get_step(step_key)
    if not step_def:
        return
    text = (message.text or "").strip()
    validator = step_def["validator"]
    ok, error_copy_id = validate(validator, text)
    if not ok:
        err_msg = get_copy(error_copy_id or "V2_INVALID_REQUIRED")
        await message.answer(err_msg, parse_mode="HTML")
        await show_question(message, state, step_key)
        return
    answer_key = step_def["answer_key"]
    if is_multi_link(step_key):
        sub = await get_submission(sub_id)
        answers = dict(sub.answers or {})
        links = list(answers.get("links") or [])
        links.append(text)
        answers_delta = {"links": links}
        await update_answers_step(sub_id, answers_delta, current_step=step_key)
        await message.answer(get_copy("V2_LINK_ADDED"), parse_mode="HTML")
        await show_question(message, state, step_key)
        return
    next_step = get_next_step(step_key)
    if not next_step:
        return
    await _persist_and_go_next(message, state, sub_id, {answer_key: text}, next_step)


# ---- Back ----
@router.callback_query(F.data == f"{PREFIX}:back", StateFilter(V2FormSteps.answering))
async def handle_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    if not sid:
        await state.clear()
        from src.v2.routers.start import show_v2_cabinet
        await show_v2_cabinet(callback.message, state)
        return
    prev_step = get_prev_step(step_key or "")
    if not prev_step:
        await update_answers_step(uuid.UUID(sid), {}, current_step=None)
        await state.clear()
        from src.v2.routers.start import show_v2_cabinet
        await show_v2_cabinet(callback.message, state)
        return
    await update_answers_step(uuid.UUID(sid), {}, current_step=prev_step)
    await state.update_data(**{DATA_STEP_KEY: prev_step})
    await show_question(callback.message, state, prev_step)


# ---- Skip (only optional) ----
@router.callback_query(F.data == f"{PREFIX}:skip", StateFilter(V2FormSteps.answering))
async def handle_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    if not sid or not step_key:
        return
    if not is_optional(step_key):
        await callback.message.answer(get_copy("V2_INVALID_REQUIRED"), parse_mode="HTML")
        await show_question(callback.message, state, step_key)
        return
    step_def = get_step(step_key)
    if not step_def:
        return
    next_step = get_next_step(step_key)
    if not next_step:
        return
    try:
        sub_id = uuid.UUID(sid)
    except ValueError:
        return
    await _persist_and_go_next(
        callback.message,
        state,
        sub_id,
        {step_def["answer_key"]: ""},
        next_step,
    )


# ---- Save (exact response) ----
@router.callback_query(F.data == f"{PREFIX}:save", StateFilter(V2FormSteps.answering))
async def handle_save(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    if not sid:
        await callback.message.answer(get_copy("V2_SAVED_RESUME"))
        return
    try:
        sub_id = uuid.UUID(sid)
    except ValueError:
        return
    await update_answers_step(sub_id, {}, current_step=step_key)
    await callback.message.answer(get_copy("V2_SAVED_RESUME"))


# ---- Finish links (Q21) ----
@router.callback_query(F.data == f"{PREFIX}:finish_links", StateFilter(V2FormSteps.answering))
async def handle_finish_links(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    if not sid or step_key != "q21":
        return
    try:
        sub_id = uuid.UUID(sid)
    except ValueError:
        return
    await _persist_and_go_next(callback.message, state, sub_id, {}, "preview")


# ---- Legacy: show_form_step(step 1|2|3) for backward compat with start/cabinet ----
async def show_form_step(message: Message, state: FSMContext, step: int) -> None:
    """Legacy: map step 1..3 to q1..q3 and show question; set state answering."""
    step_key = f"q{step}" if 1 <= step <= 3 else "q1"
    await state.set_state(V2FormSteps.answering)
    await state.update_data(**{DATA_STEP_KEY: step_key})
    await show_question(message, state, step_key)
