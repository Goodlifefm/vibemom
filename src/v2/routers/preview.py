"""V2 preview: show answers summary (safe HTML) + Submit. submit_for_moderation + admin notify."""
import logging
import uuid

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.config import Settings
from src.bot.messages import get_copy
from src.v2.repo import get_submission, submit_for_moderation, get_user_by_id
from src.v2.rendering import render_submission_to_html

router = Router()
PREFIX = "v2preview"
V2MOD = "v2mod"
logger = logging.getLogger(__name__)


def _admin_mod_kb(submission_id: uuid.UUID) -> InlineKeyboardMarkup:
    sid = str(submission_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"{V2MOD}:approve:{sid}"),
            InlineKeyboardButton(text="🛠 Needs fix", callback_data=f"{V2MOD}:needs_fix:{sid}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"{V2MOD}:reject:{sid}"),
        ],
        [
            InlineKeyboardButton(text="📋 Copy post", callback_data=f"{V2MOD}:copy:{sid}"),
            InlineKeyboardButton(text="👤 Author contact", callback_data=f"{V2MOD}:author:{sid}"),
        ],
    ])


def _preview_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("BTN_SUBMIT_TO_MODERATION").strip(), callback_data=f"{PREFIX}:submit")],
        [InlineKeyboardButton(text=get_copy("BTN_EDIT_ANSWERS").strip(), callback_data=f"{PREFIX}:back")],
    ])


async def show_preview(message: Message, state: FSMContext) -> None:
    """Show preview text + answers summary + Submit button."""
    data = await state.get_data()
    sid = data.get("submission_id")
    if not sid:
        await message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
        return
    try:
        sub_id = uuid.UUID(sid)
    except ValueError:
        return
    sub = await get_submission(sub_id)
    if not sub:
        await message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
        return
    answers = sub.answers or {}
    body_html = render_submission_to_html(answers)
    text = get_copy("V2_PREVIEW_POST") + "\n\n" + body_html
    await message.answer(text, reply_markup=_preview_kb(), parse_mode="HTML")


@router.callback_query(F.data == f"{PREFIX}:submit")
async def cb_submit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get("submission_id")
    if not sid:
        await callback.message.answer(get_copy("V2_SUBMIT_CONFIRM"))
        await state.clear()
        return
    try:
        sub_id = uuid.UUID(sid)
    except ValueError:
        await state.clear()
        return
    sub = await get_submission(sub_id)
    if not sub:
        await state.clear()
        from src.v2.routers.start import show_v2_cabinet
        await show_v2_cabinet(callback.message, state)
        return
    rendered_post = render_submission_to_html(sub.answers or {})
    settings = Settings()
    admin_chat_id = (settings.admin_chat_id or "").strip()
    if not admin_chat_id:
        logger.error("V2 submit: ADMIN_CHAT_ID not set; cannot send to moderation")
        await callback.message.answer(get_copy("V2_ADMIN_CHAT_MISSING"))
        return
    sub = await submit_for_moderation(sub_id, rendered_post)
    if not sub:
        await callback.message.answer(get_copy("V2_ADMIN_CHAT_MISSING"))
        return
    try:
        await callback.bot.send_message(
            chat_id=admin_chat_id,
            text=rendered_post,
            parse_mode="HTML",
        )
        author = await get_user_by_id(sub.user_id)
        author_str = f"@{author.username}" if author and author.username else (f"id:{sub.user_id}" if author else str(sub.user_id))
        summary = (
            f"Submission: {sub.id}\n"
            f"Author: {author_str}\n"
            f"Created: {sub.created_at}\n"
            f"Submitted: {sub.submitted_at}\n"
            f"Revision: {sub.revision}"
        )
        await callback.bot.send_message(
            chat_id=admin_chat_id,
            text=summary,
            reply_markup=_admin_mod_kb(sub.id),
        )
    except Exception as e:
        logger.exception("V2 submit: failed to send to admin chat: %s", e)
        await callback.message.answer(get_copy("ERROR_MODERATION_SEND"))
        return
    await callback.message.answer(get_copy("V2_SUBMIT_CONFIRM"))
    await state.clear()
    from src.v2.routers.start import show_v2_cabinet
    await show_v2_cabinet(callback.message, state)


@router.callback_query(F.data == f"{PREFIX}:back")
async def cb_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from src.v2.fsm.states import V2FormSteps
    from src.v2.routers.form import show_question
    await state.set_state(V2FormSteps.answering)
    await state.update_data(current_step_key="q21")
    await show_question(callback.message, state, "q21")
