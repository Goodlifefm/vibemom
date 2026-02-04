"""V2 preview: show answers summary (safe HTML) + Submit. submit_for_moderation + admin notify."""
import logging
import uuid

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from src.bot.config import Settings
from src.bot.messages import get_copy
from src.v2.repo import get_submission, submit_for_moderation, get_user_by_id
from src.v2.rendering import render_post
from src.v2.ui import (
    V2_PREVIEW_PREFIX,
    V2_MOD_PREFIX,
    kb_preview,
    kb_preview_confirm,
    render_preview_card,
)
from src.v2.ui.keyboards import kb_moderation_admin
from src.v2.ui.copy import V2Copy

router = Router()
PREFIX = V2_PREVIEW_PREFIX
V2MOD = V2_MOD_PREFIX
logger = logging.getLogger(__name__)


def _admin_mod_kb(submission_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Build admin moderation keyboard using UI Kit."""
    return kb_moderation_admin(submission_id)


def _preview_kb() -> InlineKeyboardMarkup:
    """Build preview keyboard using UI Kit."""
    return kb_preview(submit=True, edit=True, menu=True)


def _preview_confirm_kb() -> InlineKeyboardMarkup:
    """Yes/No for submit confirmation using UI Kit."""
    return kb_preview_confirm()


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
        await message.answer(V2Copy.get(V2Copy.MY_PROJECTS_EMPTY))
        return
    answers = sub.answers or {}
    result = render_preview_card(
        data=answers,
        mode="preview",
        header=V2Copy.get(V2Copy.PREVIEW_HEADER),
    )
    await message.answer(
        result["text"],
        reply_markup=_preview_kb(),
        parse_mode=result["parse_mode"],
        disable_web_page_preview=result.get("disable_web_page_preview", False),
    )


@router.callback_query(F.data == f"{PREFIX}:submit")
async def cb_submit(callback: CallbackQuery, state: FSMContext) -> None:
    """Show submit confirmation (Yes/No). Submit_yes does send; submit_no returns to Preview."""
    await callback.answer()
    data = await state.get_data()
    sid = data.get("submission_id")
    step_key = data.get("current_step_key") or "preview"
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("button user_id=%s submission_id=%s step_id=%s action=submit", user_id, sid, step_key)
    if not sid:
        await callback.message.answer(V2Copy.get(V2Copy.MY_PROJECTS_EMPTY))
        return
    await callback.message.answer(
        V2Copy.get(V2Copy.PREVIEW_SUBMIT_CONFIRM),
        reply_markup=_preview_confirm_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == f"{PREFIX}:submit_no")
async def cb_submit_no(callback: CallbackQuery, state: FSMContext) -> None:
    """No on submit confirm: return to Preview (do not end flow)."""
    await callback.answer()
    data = await state.get_data()
    sid = data.get("submission_id")
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("button user_id=%s submission_id=%s step_id=preview action=submit_no", user_id, sid)
    await show_preview(callback.message, state)


@router.callback_query(F.data == f"{PREFIX}:submit_yes")
async def cb_submit_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get("submission_id")
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("button user_id=%s submission_id=%s step_id=preview action=submit_yes", user_id, sid)
    if not sid:
        await callback.message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
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
        from src.v2.routers.menu import show_cabinet_menu
        await show_cabinet_menu(callback, state)
        return
    # Same renderer as preview so published post matches preview layout exactly
    publish_result = render_post(sub.answers or {}, mode="publish")
    rendered_post = publish_result["text"]
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
    await callback.message.answer(V2Copy.get(V2Copy.PREVIEW_SUCCESS))
    await state.clear()
    from src.v2.routers.menu import show_cabinet_menu
    await show_cabinet_menu(callback, state)


@router.callback_query(F.data == f"{PREFIX}:menu")
async def cb_preview_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """From Preview: go to cabinet (global escape hatch)."""
    await callback.answer()
    from src.v2.routers.menu import show_cabinet_menu
    await show_cabinet_menu(callback, state)


@router.callback_query(F.data == f"{PREFIX}:back")
async def cb_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Edit answers: return to last form step (q19)."""
    await callback.answer()
    data = await state.get_data()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("button user_id=%s submission_id=%s step_id=preview action=edit", user_id, data.get("submission_id"))
    from src.v2.fsm.states import V2FormSteps
    from src.v2.routers.form import show_question
    await state.set_state(V2FormSteps.answering)
    await state.update_data(current_step_key="q19")
    await show_question(callback.message, state, "q19")
