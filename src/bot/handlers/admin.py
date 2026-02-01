import uuid
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from src.bot.config import Settings
from src.bot.messages import get_copy
from src.bot.keyboards import admin_moderate_kb
from src.bot.renderer import render_project_post
from src.bot.database.models import ProjectStatus
from src.bot.services import list_pending_projects, update_project_status

router = Router()


def _is_admin(telegram_id: int) -> bool:
    s = Settings()
    return telegram_id in s.get_admin_ids()


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else 0):
        return
    pending = await list_pending_projects()
    if not pending:
        await message.answer(get_copy("ADMIN_MODERATE_PROMPT") + get_copy("ADMIN_NO_PENDING"))
        return
    p = pending[0]
    text = render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
    await message.answer(get_copy("ADMIN_MODERATE_PROMPT"))
    await message.answer(text, reply_markup=admin_moderate_kb(str(p.id)))


@router.callback_query(F.data.startswith("mod_approve_"))
async def admin_approve(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return
    project_id = callback.data.replace("mod_approve_", "")
    await update_project_status(uuid.UUID(project_id), ProjectStatus.approved)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("ADMIN_APPROVE"))
    await callback.answer()


@router.callback_query(F.data.startswith("mod_fix_"))
async def admin_needs_fix(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return
    project_id = callback.data.replace("mod_fix_", "")
    await update_project_status(uuid.UUID(project_id), ProjectStatus.needs_fix)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("ADMIN_NEEDS_FIX"))
    await callback.answer()


@router.callback_query(F.data.startswith("mod_reject_"))
async def admin_reject(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return
    project_id = callback.data.replace("mod_reject_", "")
    await update_project_status(uuid.UUID(project_id), ProjectStatus.rejected)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("ADMIN_REJECT"))
    await callback.answer()
