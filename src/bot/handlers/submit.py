import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.bot.config import Settings
from src.bot.fsm.states import ProjectSubmissionStates
from src.bot.messages import get_copy
from src.bot.keyboards import ps_nav_step, ps_resume_kb, admin_moderate_kb
from src.bot.project_submission_schema import first_step, get_step
from src.bot.submission_engine import (
    get_current_step,
    get_current_step_id,
    set_answer,
    set_step_id,
    validate_input,
    transition,
    render_step,
    META_KEY,
    STATE_KEY,
)
from src.bot.renderer import answers_to_project_fields, render_project_post
from src.bot.validators import parse_yes_no
from src.bot.services import get_or_create_user, create_project

router = Router()
logger = logging.getLogger(__name__)

PS = "ps"


def _is_back_button(text: str) -> bool:
    if not text or not text.strip():
        return False
    back_text = get_copy("BACK_BUTTON").strip()
    return text.strip() == back_text or text.strip().lower() == back_text.lower()


def _is_skip_button(text: str) -> bool:
    if not text or not text.strip():
        return False
    skip_text = get_copy("SKIP_BUTTON").strip()
    return text.strip() == skip_text or text.strip().lower() == skip_text.lower()


async def _send_step(message_or_callback: Message | CallbackQuery, step: dict, data: dict) -> None:
    text, reply_markup = render_step(step, data)
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await target.answer(text, reply_markup=reply_markup)


# ---- /submit ----
@router.message(Command("submit"))
async def cmd_submit(message: Message, state: FSMContext) -> None:
    await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    # Resume: if we have saved step in data, use it; else start from welcome
    data = await state.get_data()
    saved_step_id = (data.get(META_KEY) or {}).get(STATE_KEY)
    if saved_step_id and get_step(saved_step_id):
        step_id = saved_step_id
    else:
        step_id = first_step()["state_id"]
    data = set_step_id(data, step_id)
    await state.set_data(data)
    await state.set_state(ProjectSubmissionStates.filling)
    step = get_step(step_id)
    if step:
        await _send_step(message, step, data)
    else:
        await message.answer(get_copy("SUBMIT_START"))


# ---- Generic text handler ----
@router.message(ProjectSubmissionStates.filling, F.text)
async def submit_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step = get_current_step(data)
    if not step:
        await message.answer(get_copy("SUBMIT_START"))
        return

    text_in = (message.text or "").strip()
    state_id = step["state_id"]
    input_type = step.get("input_type") or ""

    # Buttons-only step: ignore text, re-send step with keyboard
    if input_type == "buttons":
        await _send_step(message, step, data)
        return

    # Back button
    if _is_back_button(text_in):
        next_sid = transition(step, "back")
        if next_sid:
            data = set_step_id(data, next_sid)
            await state.set_data(data)
            next_step = get_step(next_sid)
            if next_step:
                await _send_step(message, next_step, data)
        return

    # Skip button (for multi / optional steps)
    if _is_skip_button(text_in) and step.get("skippable"):
        answer_key = step.get("answer_key")
        if answer_key:
            data = set_answer(data, answer_key, "")
        next_sid = transition(step, "skip")
        if next_sid:
            data = set_step_id(data, next_sid)
            await state.set_data(data)
            next_step = get_step(next_sid)
            if next_step:
                await _send_step(message, next_step, data)
        return

    # Confirm step: yes/no
    if state_id == "confirm":
        yn = parse_yes_no(message.text)
        if yn is True:
            await _do_submit(message, state, data)
            return
        if yn is False:
            next_sid = "preview"
            data = set_step_id(data, next_sid)
            await state.set_data(data)
            preview_step = get_step("preview")
            if preview_step:
                await _send_step(message, preview_step, data)
            return
        _, reply_markup = render_step(step, data)
        await message.answer(get_copy("ERROR_INVALID_YESNO"), reply_markup=reply_markup)
        return

    # Text/multi step: validate and save
    ok, value = validate_input(step, message.text)
    if not ok:
        err = get_copy("ERROR_NOT_TEXT")
        if "url" in (step.get("validator") or ""):
            err = get_copy("ERROR_INVALID_URL")
        _, reply_markup = render_step(step, data)
        await message.answer(err, reply_markup=reply_markup)
        return

    answer_key = step.get("answer_key")
    if answer_key:
        data = set_answer(data, answer_key, value)
    next_sid = transition(step, "next")
    if next_sid == "__submit__":
        await _do_submit(message, state, data)
        return
    if next_sid:
        data = set_step_id(data, next_sid)
        await state.set_data(data)
        next_step = get_step(next_sid)
        if next_step:
            await _send_step(message, next_step, data)


# ---- Generic callback handler ----
@router.callback_query(ProjectSubmissionStates.filling, F.data.startswith(f"{PS}:"))
async def submit_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    step = get_current_step(data)
    if not step:
        await callback.message.answer(get_copy("SUBMIT_START"))
        return

    action = callback.data.split(":", 1)[1] if ":" in callback.data else ""
    state_id = step["state_id"]

    if action == "save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return

    if action == "resume":
        await _send_step(callback, step, data)
        return

    if action == "back":
        next_sid = transition(step, "back")
        if next_sid:
            data = set_step_id(data, next_sid)
            await state.set_data(data)
            next_step = get_step(next_sid)
            if next_step:
                await _send_step(callback, next_step, data)
        return

    if action == "skip":
        answer_key = step.get("answer_key")
        if answer_key:
            data = set_answer(data, answer_key, "")
        next_sid = transition(step, "skip")
        if next_sid:
            data = set_step_id(data, next_sid)
            await state.set_data(data)
            next_step = get_step(next_sid)
            if next_step:
                await _send_step(callback, next_step, data)
        return

    if action == "next":
        next_sid = transition(step, "next")
        if next_sid == "__submit__":
            await _do_submit_callback(callback, state, data)
            return
        if next_sid:
            data = set_step_id(data, next_sid)
            await state.set_data(data)
            next_step = get_step(next_sid)
            if next_step:
                await _send_step(callback, next_step, data)
        return

    if action == "submit_yes":
        await _do_submit_callback(callback, state, data)
        return

    if action == "submit_no":
        data = set_step_id(data, "preview")
        await state.set_data(data)
        preview_step = get_step("preview")
        if preview_step:
            await _send_step(callback, preview_step, data)
        return

    if action == "edit":
        data = set_step_id(data, "contact_preferred")
        await state.set_data(data)
        next_step = get_step("contact_preferred")
        if next_step:
            await _send_step(callback, next_step, data)
        return


async def _do_submit(message: Message, state: FSMContext, data: dict) -> None:
    fields = answers_to_project_fields(data)
    user = await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    project = await create_project(
        seller_id=user.id,
        title=fields["title"],
        description=fields["description"],
        stack=fields["stack"],
        link=fields["link"],
        price=fields["price"],
        contact=fields["contact"],
    )
    settings = Settings()
    admin_chat_id = (settings.admin_chat_id or "").strip()
    if admin_chat_id:
        try:
            logger.info("Sending project to admin chat, admin_chat_id=%s", admin_chat_id)
            preview = render_project_post(
                project.title, project.description, project.stack,
                project.link, project.price, project.contact,
            )
            await message.bot.send_message(
                chat_id=admin_chat_id,
                text=preview,
                reply_markup=admin_moderate_kb(str(project.id)),
            )
        except Exception as e:
            logger.exception("Failed to send to admin chat: %s", e)
            await message.answer(get_copy("ERROR_MODERATION_SEND"))
            return
    await state.clear()
    await message.answer(get_copy("SUBMIT_SENT"))


async def _do_submit_callback(callback: CallbackQuery, state: FSMContext, data: dict) -> None:
    fields = answers_to_project_fields(data)
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    project = await create_project(
        seller_id=user.id,
        title=fields["title"],
        description=fields["description"],
        stack=fields["stack"],
        link=fields["link"],
        price=fields["price"],
        contact=fields["contact"],
    )
    settings = Settings()
    admin_chat_id = (settings.admin_chat_id or "").strip()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    if admin_chat_id:
        try:
            logger.info("Sending project to admin chat, admin_chat_id=%s", admin_chat_id)
            preview = render_project_post(
                project.title, project.description, project.stack,
                project.link, project.price, project.contact,
            )
            await callback.bot.send_message(
                chat_id=admin_chat_id,
                text=preview,
                reply_markup=admin_moderate_kb(str(project.id)),
            )
        except Exception as e:
            logger.exception("Failed to send to admin chat: %s", e)
            await callback.message.answer(get_copy("ERROR_MODERATION_SEND"))
            return
    await state.clear()
    await callback.message.answer(get_copy("SUBMIT_SENT"))
