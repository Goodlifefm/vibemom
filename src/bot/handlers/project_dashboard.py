"""
V2 Project Dashboard: center of control for one project.
"""
import logging
import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.config import Settings
from src.bot.messages import get_copy
from src.bot.renderer import render_project_post, project_fields_to_answers, v2_answers_to_project_fields
from src.bot.services.project_service import (
    get_project,
    update_project_status,
    update_project_fields,
    list_projects_by_seller,
)
from src.bot.database.models import ProjectStatus
from src.bot.keyboards import admin_moderate_kb
from src.bot.editor_schema import missing_required_fields

router = Router()
logger = logging.getLogger(__name__)

DASH = "dash"


def _status_copy(status: ProjectStatus) -> str:
    m = {
        ProjectStatus.draft: "V2_STATUS_DRAFT",
        ProjectStatus.pending: "V2_STATUS_PENDING",
        ProjectStatus.needs_fix: "V2_STATUS_NEEDS_FIX",
        ProjectStatus.approved: "V2_STATUS_APPROVED",
        ProjectStatus.rejected: "V2_STATUS_REJECTED",
    }
    return get_copy(m.get(status, "V2_STATUS_DRAFT")).strip()


def dashboard_kb(project_id: uuid.UUID, needs_fix: bool = False) -> InlineKeyboardMarkup:
    pid = str(project_id)
    rows = []
    if needs_fix:
        rows.append([InlineKeyboardButton(text=get_copy("BTN_MAKE_EDIT").strip(), callback_data=f"{DASH}:needs_fix_edit:{pid}")])
    rows.extend([
        [InlineKeyboardButton(text=get_copy("V2_BTN_EDIT_BLOCKS").strip(), callback_data=f"{DASH}:edit:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_PREVIEW").strip(), callback_data=f"{DASH}:preview:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_SEND_MODERATION").strip(), callback_data=f"{DASH}:send:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_HISTORY").strip(), callback_data=f"{DASH}:history:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_ARCHIVE").strip(), callback_data=f"{DASH}:archive:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_BACK_TO_PROJECTS").strip(), callback_data=f"{DASH}:back")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_dashboard(message_or_callback: Message | CallbackQuery, state: FSMContext, project_id: uuid.UUID) -> None:
    project = await get_project(project_id)
    if not project:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(message_or_callback, state)
        return
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    await state.update_data(project_id=str(project.id), revision=1)
    title = (project.title or "—").strip()
    if title == "—":
        title = "Без названия"
    status_text = _status_copy(project.status)
    rev = (await state.get_data()).get("revision", 1)
    text = (
        get_copy("V2_DASHBOARD_TITLE").format(title=title) + "\n"
        + get_copy("V2_DASHBOARD_STATUS").format(status=status_text) + "\n"
        + get_copy("V2_DASHBOARD_REVISION").format(revision=rev)
    )
    needs_fix = project.status == ProjectStatus.needs_fix
    if needs_fix:
        text += "\n\n" + get_copy("NEEDS_FIX_MESSAGE").strip()
    await target.answer(text, reply_markup=dashboard_kb(project.id, needs_fix=needs_fix))


@router.callback_query(F.data == f"{DASH}:back")
async def dash_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    from src.bot.handlers.cabinet import show_cabinet
    await show_cabinet(callback, state)


@router.callback_query(F.data.startswith(f"{DASH}:edit:"))
async def dash_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    await state.update_data(project_id=pid)
    from src.bot.handlers.editor import show_block_menu
    await show_block_menu(callback, state, uuid.UUID(pid))


@router.callback_query(F.data.startswith(f"{DASH}:preview:"))
async def dash_preview(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    project = await get_project(uuid.UUID(pid))
    if not project:
        await callback.message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
        return
    answers = project_fields_to_answers(project)
    v2_fields = v2_answers_to_project_fields(answers)
    text = render_project_post(
        v2_fields["title"],
        v2_fields["description"],
        v2_fields["stack"],
        v2_fields["link"],
        v2_fields["price"],
        v2_fields["contact"],
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("BTN_SUBMIT_TO_MODERATION").strip(), callback_data=f"{DASH}:send:{pid}")],
        [InlineKeyboardButton(text=get_copy("BTN_EDIT_ANSWERS").strip(), callback_data=f"{DASH}:edit:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_BACK_TO_PROJECTS").strip(), callback_data=f"{DASH}:back")],
    ])
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith(f"{DASH}:send:"))
async def dash_send(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    project = await get_project(uuid.UUID(pid))
    if not project:
        await callback.message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
        return
    answers = project_fields_to_answers(project)
    missing = missing_required_fields(answers)
    if missing:
        fields_str = ", ".join(missing)
        await callback.message.answer(
            get_copy("V2_SEND_MISSING_FIELDS").format(fields=fields_str),
            reply_markup=dashboard_kb(project.id, needs_fix=(project.status == ProjectStatus.needs_fix)),
        )
        return
    v2_fields = v2_answers_to_project_fields(answers)
    await update_project_fields(
        project.id,
        title=v2_fields["title"],
        description=v2_fields["description"],
        stack=v2_fields["stack"],
        link=v2_fields["link"],
        price=v2_fields["price"],
        contact=v2_fields["contact"],
    )
    from src.bot.handlers import admin
    from src.bot.services import get_or_create_user
    settings = Settings()
    admin_chat_id = (settings.admin_chat_id or "").strip()
    await update_project_status(project.id, ProjectStatus.pending)
    data = await state.get_data()
    rev = data.get("revision", 1)
    await state.update_data(revision=rev + 1)
    if admin_chat_id:
        try:
            logger.info("v2 project_id=%s send to admin chat", project.id)
            preview = render_project_post(
                v2_fields["title"], v2_fields["description"], v2_fields["stack"],
                v2_fields["link"], v2_fields["price"], v2_fields["contact"],
            )
            await callback.bot.send_message(
                chat_id=admin_chat_id,
                text=preview,
                reply_markup=admin_moderate_kb(str(project.id)),
            )
        except Exception as e:
            logger.exception("v2 send to admin failed: %s", e)
            await callback.message.answer(get_copy("ERROR_MODERATION_SEND"))
            return
    await callback.message.answer(get_copy("V2_SENT_TO_MODERATION"), reply_markup=dashboard_kb(project.id, needs_fix=False))


@router.callback_query(F.data.startswith(f"{DASH}:history:"))
async def dash_history(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    project = await get_project(uuid.UUID(pid))
    if not project:
        return
    await callback.message.answer("История (read-only): редакция 1.", reply_markup=dashboard_kb(project.id, needs_fix=(project.status == ProjectStatus.needs_fix)))


@router.callback_query(F.data.startswith(f"{DASH}:needs_fix_edit:"))
async def dash_needs_fix_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Needs-fix: open block editor (blocks 1..7, then fields in block). Same as Edit blocks."""
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        return
    project = await get_project(project_id)
    if not project or project.status != ProjectStatus.needs_fix:
        await show_dashboard(callback, state, project_id)
        return
    from src.bot.handlers.editor import show_block_menu
    await show_block_menu(callback, state, project_id)


@router.callback_query(F.data.startswith(f"{DASH}:archive:"))
async def dash_archive(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    project = await get_project(uuid.UUID(pid))
    if not project:
        return
    await update_project_status(project.id, ProjectStatus.rejected)
    await state.clear()
    await callback.message.answer(get_copy("V2_ARCHIVED"))
    from src.bot.handlers.cabinet import show_cabinet
    await show_cabinet(callback, state)
