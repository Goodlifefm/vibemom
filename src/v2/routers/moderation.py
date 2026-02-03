"""V2 moderation: admin callbacks (approve/needs_fix/reject/copy/author) + FSM for fix/reject text."""
import logging
import uuid

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramNotFound

from src.bot.config import Settings
from src.bot.messages import get_copy
from src.bot.database.models import ProjectStatus, AdminActionType, Submission
from src.v2.repo import (
    get_submission,
    get_user_by_id,
    get_or_create_user,
    set_moderated,
    log_admin_action,
)
from src.v2.fsm.states import V2ModSteps
from src.v2.rendering import assert_preview_publish_consistency, render_post

router = Router()
PREFIX = "v2mod"
logger = logging.getLogger(__name__)


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in Settings().get_admin_ids()


def _parse_callback(data: str) -> tuple[str | None, uuid.UUID | None]:
    if not data.startswith(f"{PREFIX}:") or data.count(":") < 2:
        return None, None
    parts = data.split(":", 2)
    action, sid = parts[1], parts[2]
    try:
        return action, uuid.UUID(sid)
    except ValueError:
        return None, None


@router.callback_query(F.data.startswith(f"{PREFIX}:"))
async def handle_mod_callback(callback: CallbackQuery, state: FSMContext) -> None:
    tid = callback.from_user.id if callback.from_user else 0
    if not _is_admin(tid):
        await callback.answer(get_copy("V2_MOD_NO_RIGHTS"), show_alert=True)
        return
    action, sub_id = _parse_callback(callback.data or "")
    logger.info("button user_id=%s submission_id=%s step_id=mod action=%s", tid, str(sub_id) if sub_id else None, action)
    if not action or not sub_id:
        await callback.answer()
        return
    sub = await get_submission(sub_id)
    if not sub:
        await callback.answer(get_copy("V2_MOD_ALREADY"), show_alert=True)
        return
    admin_user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    admin_chat_id = (Settings().admin_chat_id or "").strip()
    msg = callback.message
    meta_msg_id = msg.message_id if msg else 0

    if action == "copy":
        await callback.answer()
        if sub.rendered_post and msg:
            await msg.reply(sub.rendered_post, parse_mode="HTML")
        return

    if action == "author":
        await callback.answer()
        author = await get_user_by_id(sub.user_id)
        lines = [
            f"telegram_id: {author.telegram_id}" if author else f"user_id: {sub.user_id}",
            f"username: @{author.username}" if author and author.username else "username: —",
        ]
        ans = sub.answers or {}
        for key in ("contact", "author_name", "author_contact"):
            if ans.get(key):
                lines.append(f"{key}: {ans.get(key)}")
        if msg:
            await msg.reply("\n".join(lines))
        return

    if action == "approve":
        if sub.status != ProjectStatus.pending:
            await callback.answer(get_copy("V2_MOD_ALREADY"), show_alert=True)
            return
        await set_moderated(sub_id, ProjectStatus.approved)
        await log_admin_action(admin_user.id, AdminActionType.approve, target_submission_id=sub_id)
        feed_chat_id = (Settings().feed_chat_id or "").strip()
        if not feed_chat_id:
            logger.warning("FEED_CHAT_ID not set; skipping auto-publish for project_id=%s", sub_id)
        else:
            # Same renderer as preview so published post matches preview exactly
            result = render_post(sub.answers or {}, mode="publish")
            rendered_post = result["text"]
            assert_preview_publish_consistency(sub.answers, rendered_post)
            logger.debug("publish post body (same as preview) len=%s", len(rendered_post))
            try:
                sent = await callback.bot.send_message(
                    chat_id=feed_chat_id,
                    text=rendered_post,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
                logger.info(
                    "FEED publish ok project_id=%s chat=%s msg_id=%s",
                    sub_id,
                    feed_chat_id,
                    sent.message_id,
                )
            except (TelegramForbiddenError, TelegramBadRequest, TelegramNotFound) as e:
                logger.exception("FEED publish failed project_id=%s chat=%s", sub_id, feed_chat_id)
                if admin_chat_id:
                    try:
                        await callback.bot.send_message(
                            chat_id=admin_chat_id,
                            text=f"⚠️ Ошибка публикации в канал: {feed_chat_id}\nproject_id={sub_id}\n{type(e).__name__}: {e}",
                        )
                    except Exception:
                        pass
            except Exception as e:
                logger.exception("FEED publish failed project_id=%s chat=%s", sub_id, feed_chat_id)
                if admin_chat_id:
                    try:
                        await callback.bot.send_message(
                            chat_id=admin_chat_id,
                            text=f"⚠️ Ошибка публикации в канал: {feed_chat_id}\nproject_id={sub_id}\n{type(e).__name__}: {e}",
                        )
                    except Exception:
                        pass
        user_text = get_copy("V2_MOD_APPROVE_USER")
        author = await get_user_by_id(sub.user_id)
        if author:
            try:
                await callback.bot.send_message(chat_id=author.telegram_id, text=user_text, parse_mode="HTML")
            except Exception as e:
                logger.warning("V2 mod: failed to notify user: %s", e)
        if msg:
            try:
                new_text = (msg.text or "") + "\n\n" + get_copy("V2_MOD_APPROVED_LABEL")
                await msg.edit_text(new_text, reply_markup=None)
            except Exception:
                try:
                    await callback.bot.send_message(chat_id=admin_chat_id, text=get_copy("V2_MOD_APPROVED_LABEL"))
                except Exception:
                    pass
        await callback.answer()
        return

    if action == "needs_fix":
        await callback.answer()
        await state.set_state(V2ModSteps.awaiting_fix_text)
        await state.update_data(mod_pending_sub_id=str(sub_id), mod_admin_chat_id=admin_chat_id, mod_admin_message_id=meta_msg_id)
        await callback.message.answer(get_copy("V2_MOD_ASK_FIX"))
        return

    if action == "reject":
        await callback.answer()
        await state.set_state(V2ModSteps.awaiting_reject_reason)
        await state.update_data(mod_pending_sub_id=str(sub_id), mod_admin_chat_id=admin_chat_id, mod_admin_message_id=meta_msg_id)
        await callback.message.answer(get_copy("V2_MOD_ASK_REJECT"))
        return


@router.message(StateFilter(V2ModSteps.awaiting_fix_text), F.text)
async def handle_fix_text(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else 0):
        await state.clear()
        return
    data = await state.get_data()
    sid_str = data.get("mod_pending_sub_id")
    if not sid_str:
        await state.clear()
        return
    try:
        sub_id = uuid.UUID(sid_str)
    except ValueError:
        await state.clear()
        return
    fix_request = (message.text or "").strip() or "—"
    sub = await get_submission(sub_id)
    if not sub:
        await state.clear()
        await message.answer(get_copy("V2_MOD_ALREADY"))
        return
    admin_user = await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await set_moderated(sub_id, ProjectStatus.needs_fix, fix_request=fix_request)
    await log_admin_action(admin_user.id, AdminActionType.needs_fix, target_submission_id=sub_id, comment=fix_request)
    user_text = get_copy("V2_MOD_NEEDS_FIX_USER").format(fix_request=fix_request)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("BTN_MAKE_EDIT").strip(), callback_data=f"v2fix:edit:{sid_str}")],
    ])
    author = await get_user_by_id(sub.user_id)
    if author:
        try:
            await message.bot.send_message(chat_id=author.telegram_id, text=user_text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.warning("V2 mod: failed to notify user: %s", e)
    admin_chat_id = data.get("mod_admin_chat_id") or ""
    meta_msg_id = data.get("mod_admin_message_id") or 0
    edit_text = (get_copy("V2_MOD_NEEDS_FIX_LABEL") + "\nДоработка: " + fix_request[:200])
    if admin_chat_id and meta_msg_id:
        try:
            await message.bot.edit_message_text(chat_id=admin_chat_id, message_id=meta_msg_id, text=edit_text)
        except Exception:
            try:
                await message.bot.send_message(chat_id=admin_chat_id, text=edit_text)
            except Exception:
                pass
    await state.clear()
    await message.answer(get_copy("V2_MOD_NEEDS_FIX_LABEL"))


@router.message(StateFilter(V2ModSteps.awaiting_reject_reason))
async def handle_reject_reason(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else 0):
        await state.clear()
        return
    data = await state.get_data()
    sid_str = data.get("mod_pending_sub_id")
    if not sid_str:
        await state.clear()
        return
    try:
        sub_id = uuid.UUID(sid_str)
    except ValueError:
        await state.clear()
        return
    reason = (getattr(message, "text", None) or "").strip() or "без комментариев"
    sub = await get_submission(sub_id)
    if not sub:
        await state.clear()
        await message.answer(get_copy("V2_MOD_ALREADY"))
        return
    admin_user = await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await set_moderated(sub_id, ProjectStatus.rejected)
    await log_admin_action(admin_user.id, AdminActionType.reject, target_submission_id=sub_id, comment=reason)
    user_text = get_copy("V2_MOD_REJECT_USER").format(reason=reason)
    author = await get_user_by_id(sub.user_id)
    if author:
        try:
            await message.bot.send_message(chat_id=author.telegram_id, text=user_text, parse_mode="HTML")
        except Exception as e:
            logger.warning("V2 mod: failed to notify user: %s", e)
    admin_chat_id = data.get("mod_admin_chat_id") or ""
    meta_msg_id = data.get("mod_admin_message_id") or 0
    if admin_chat_id and meta_msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=admin_chat_id,
                message_id=meta_msg_id,
                text=get_copy("V2_MOD_REJECTED_LABEL") + "\nПричина: " + reason[:200],
            )
        except Exception:
            try:
                await message.bot.send_message(chat_id=admin_chat_id, text=get_copy("V2_MOD_REJECTED_LABEL") + " " + reason[:200])
            except Exception:
                pass
    await state.clear()
    await message.answer(get_copy("V2_MOD_REJECTED_LABEL"))
