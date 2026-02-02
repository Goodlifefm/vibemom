"""
V2 Cabinet: user dashboard. Shown when V2_ENABLED and /start.
"""
import logging
import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.messages import get_copy
from src.bot.services import get_or_create_user
from src.bot.services.project_service import list_projects_by_seller, create_draft_project, get_project
from src.bot.database.models import ProjectStatus

router = Router()
logger = logging.getLogger(__name__)

CAB = "cab"


def _status_copy(status: ProjectStatus) -> str:
    m = {
        ProjectStatus.draft: "V2_STATUS_DRAFT",
        ProjectStatus.pending: "V2_STATUS_PENDING",
        ProjectStatus.needs_fix: "V2_STATUS_NEEDS_FIX",
        ProjectStatus.approved: "V2_STATUS_APPROVED",
        ProjectStatus.rejected: "V2_STATUS_REJECTED",
    }
    return get_copy(m.get(status, "V2_STATUS_DRAFT")).strip()


def cabinet_kb(show_resume: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if show_resume:
        rows.append([InlineKeyboardButton(text=get_copy("V2_BTN_RESUME_PROJECT").strip(), callback_data=f"{CAB}:resume")])
    rows.extend([
        [InlineKeyboardButton(text=get_copy("V2_BTN_CREATE_PROJECT").strip(), callback_data=f"{CAB}:create")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_MY_PROJECTS").strip(), callback_data=f"{CAB}:projects")],
        [InlineKeyboardButton(text=get_copy("V2_BTN_HOW_IT_WORKS").strip(), callback_data=f"{CAB}:how")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_cabinet(message_or_callback: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    show_resume = False
    if state:
        data = await state.get_data()
        show_resume = bool(data.get("project_id"))
    await target.answer(get_copy("V2_CABINET_GREETING"), reply_markup=cabinet_kb(show_resume=show_resume))


@router.callback_query(F.data == f"{CAB}:resume")
async def cab_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    pid = data.get("project_id")
    if not pid:
        await show_cabinet(callback, state)
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        await show_cabinet(callback, state)
        return
    from src.bot.handlers.project_dashboard import show_dashboard
    project = await get_project(project_id)
    if project:
        await show_dashboard(callback, state, project.id)
    else:
        await state.update_data(project_id=None)
        await show_cabinet(callback, state)


@router.callback_query(F.data == f"{CAB}:create")
async def cab_create(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    project = await create_draft_project(user.id)
    await state.update_data(project_id=str(project.id), revision=1, _meta={"version": 2})
    logger.info("v2 project_id=%s user_id=%s action=create", project.id, user.id)
    from src.bot.handlers.project_dashboard import show_dashboard
    await show_dashboard(callback, state, project.id)


@router.callback_query(F.data == f"{CAB}:projects")
async def cab_my_projects(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    projects = await list_projects_by_seller(user.id, limit=5)
    if not projects:
        await callback.message.answer(
            get_copy("V2_MY_PROJECTS_HEADER") + "\n\n" + get_copy("V2_MY_PROJECTS_EMPTY"),
            reply_markup=cabinet_kb(show_resume=bool((await state.get_data()).get("project_id"))),
        )
        return
    text = get_copy("V2_MY_PROJECTS_HEADER") + "\n\n"
    kb_rows = []
    for p in projects:
        title = (p.title or "—").strip()
        if title == "—":
            title = "Без названия"
        text += f"• {title} — {_status_copy(p.status)}\n"
        kb_rows.append([InlineKeyboardButton(text=get_copy("V2_BTN_OPEN").strip() + f" ({title[:20]})", callback_data=f"{CAB}:open:{p.id}")])
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


@router.callback_query(F.data.startswith(f"{CAB}:open:"))
async def cab_open_project(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    pid = callback.data.split(":", 2)[2]
    await state.update_data(project_id=pid, revision=1, _meta={"version": 2})
    from src.bot.handlers.project_dashboard import show_dashboard
    from src.bot.services.project_service import get_project
    import uuid
    project = await get_project(uuid.UUID(pid))
    if project:
        await show_dashboard(callback, state, project.id)
    else:
        await callback.message.answer(get_copy("V2_MY_PROJECTS_EMPTY"), reply_markup=cabinet_kb())


@router.callback_query(F.data == f"{CAB}:how")
async def cab_how(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        get_copy("V2_HOW_IT_WORKS"),
        reply_markup=cabinet_kb(show_resume=bool((await state.get_data()).get("project_id"))),
    )
