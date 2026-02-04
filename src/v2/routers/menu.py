"""V2 menu: persistent 🏠 Меню button and cabinet from any state. High-priority router."""
import logging
import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.v2.ui import callbacks, copy, keyboards, render
from src.v2.repo import (
    get_or_create_user,
    get_submission,
    list_submissions_by_user,
    create_submission,
)
from src.v2.fsm.states import V2FormSteps
from src.v2.fsm.steps import get_step, get_step_index, STEP_KEYS
from src.bot.database.models import ProjectStatus

logger = logging.getLogger(__name__)

router = Router()


def _status_copy(status: ProjectStatus) -> str:
    m = {
        ProjectStatus.draft: copy.STATUS_DRAFT,
        ProjectStatus.pending: copy.STATUS_PENDING,
        ProjectStatus.needs_fix: copy.STATUS_NEEDS_FIX,
        ProjectStatus.approved: copy.STATUS_APPROVED,
        ProjectStatus.rejected: copy.STATUS_REJECTED,
    }
    return copy.t(m.get(status, copy.STATUS_DRAFT)).strip()


async def _send_menu_keyboard(target: Message) -> None:
    """Send second message to set persistent reply keyboard."""
    await target.answer(copy.t(copy.MENU_HINT), reply_markup=keyboards.reply_menu_keyboard())


def _cabinet_status_text(step_key: str | None, step_num: int, total: int, project_name: str | None) -> str:
    """Cabinet status block: project name, step X/Y, progress %."""
    project = (project_name or "").strip() or copy.t(copy.MENU_STATUS_NO_PROJECT).strip()
    if step_key and get_step(step_key) and total > 0:
        step_str = f"{step_num} из {total}"
        progress = round(step_num / total * 100)
    else:
        step_str = copy.CARD_EMPTY_VALUE
        progress = 0
    return copy.fmt(copy.CABINET_STATUS, project=project, step=step_str, progress=progress)


async def show_menu_cabinet(message_or_callback: Message | CallbackQuery, state: FSMContext) -> None:
    """Show cabinet: status (project, step X of Y, progress %) + greeting + inline menu. Set reply keyboard."""
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    data = await state.get_data() if state else {}
    sid = data.get("submission_id")
    step_key = data.get("current_step_key") or ""
    show_resume = bool(sid)
    step_num, total = 1, len(STEP_KEYS)
    project_name = None
    if sid:
        try:
            sub = await get_submission(uuid.UUID(sid))
            if sub:
                project_name = (sub.answers or {}).get("title", "").strip() or None
                if step_key and get_step(step_key):
                    step_num = get_step_index(step_key) + 1
        except (ValueError, TypeError):
            pass
    status_text = _cabinet_status_text(step_key, step_num, total, project_name)
    try:
        user = await get_or_create_user(
            message_or_callback.from_user.id if message_or_callback.from_user else 0,
            message_or_callback.from_user.username if message_or_callback.from_user else None,
            message_or_callback.from_user.full_name if message_or_callback.from_user else None,
        )
        subs = await list_submissions_by_user(user.id, limit=1)
        has_projects = bool(subs)
    except Exception:
        has_projects = False
    kb = keyboards.menu_cabinet_inline_kb(show_resume=show_resume, has_projects=has_projects)
    body = status_text + "\n\n" + copy.t(copy.CABINET_GREETING)
    await target.answer(body, reply_markup=kb)
    await _send_menu_keyboard(target)
    user_id = (message_or_callback.from_user.id if message_or_callback.from_user else 0) if hasattr(message_or_callback, "from_user") else 0
    logger.info("menu_open user_id=%s", user_id)


# ---- Text: 🏠 Меню, Меню, /menu (any state) ----
@router.message(F.text.in_(["🏠 Меню", "Меню"]))
@router.message(Command("menu"))
async def handle_menu_trigger(message: Message, state: FSMContext) -> None:
    """Global escape hatch: show cabinet from any state. Keeps draft (submission_id) so Continue works."""
    await show_menu_cabinet(message, state)


# ---- Callback: Продолжить ----
@router.callback_query(F.data == callbacks.menu(callbacks.MENU_RESUME))
async def cb_menu_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from src.v2.routers.start import _do_resume
    logger.info("menu_continue user_id=%s", callback.from_user.id if callback.from_user else 0)
    await _do_resume(callback.message, state)


# ---- Callback: Начать заново (confirm) ----
@router.callback_query(F.data == callbacks.menu(callbacks.MENU_RESTART))
async def cb_menu_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        copy.t(copy.MENU_RESTART_CONFIRM),
        reply_markup=keyboards.menu_restart_confirm_kb(),
    )


@router.callback_query(F.data == callbacks.menu(callbacks.MENU_RESTART_YES))
async def cb_menu_restart_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    logger.info("menu_restart_yes user_id=%s", callback.from_user.id if callback.from_user else 0)
    await show_menu_cabinet(callback.message, state)


@router.callback_query(F.data == callbacks.menu(callbacks.MENU_RESTART_NO))
async def cb_menu_restart_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_menu_cabinet(callback.message, state)


# ---- Callback: Мои проекты ----
@router.callback_query(F.data == callbacks.menu(callbacks.MENU_PROJECTS))
async def cb_menu_projects(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    subs = await list_submissions_by_user(user.id, limit=5)
    if not subs:
        await callback.message.answer(
            copy.t(copy.MY_PROJECTS_HEADER) + "\n\n" + copy.t(copy.MY_PROJECTS_EMPTY),
            reply_markup=keyboards.menu_cabinet_inline_kb(
                show_resume=bool((await state.get_data()).get("submission_id")), has_projects=False
            ),
        )
        return
    text = copy.t(copy.MY_PROJECTS_HEADER) + "\n\n"
    projects: list[tuple[str, uuid.UUID]] = []
    for s in subs:
        title = (s.answers or {}).get("title", copy.CARD_EMPTY_VALUE) or copy.CARD_EMPTY_VALUE
        if title == copy.CARD_EMPTY_VALUE:
            title = copy.UNTITLED_PROJECT
        text += f"• {title[:40]} — {_status_copy(s.status)}\n"
        projects.append((title, s.id))
    await callback.message.answer(text, reply_markup=keyboards.projects_list_kb(projects))


# ---- Callback: Создать проект ----
@router.callback_query(F.data == callbacks.menu(callbacks.MENU_CREATE))
async def cb_menu_create(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    sub = await create_submission(user.id, current_step="q1")
    await state.update_data(submission_id=str(sub.id))
    from src.v2.routers.form import show_form_step
    await state.set_state(V2FormSteps.answering)
    await state.update_data(current_step_key="q1")
    await show_form_step(callback.message, state, 1)
    logger.info("menu_create user_id=%s", callback.from_user.id if callback.from_user else 0)


# ---- Callback: Помощь ----
@router.callback_query(F.data == callbacks.menu(callbacks.MENU_HELP))
async def cb_menu_help(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        copy.t(copy.HELP_TEXT),
        reply_markup=keyboards.menu_cabinet_inline_kb(
            show_resume=bool((await state.get_data()).get("submission_id")),
            has_projects=True,
        ),
    )


@router.callback_query(F.data == callbacks.menu(callbacks.MENU_CURRENT_STEP))
async def cb_menu_current_step(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    step_key = data.get("current_step_key") or ""
    if not step_key or not get_step(step_key):
        await callback.message.answer(
            copy.t(copy.MENU_STATUS_NO_PROJECT),
            reply_markup=keyboards.menu_cabinet_inline_kb(
                show_resume=bool(data.get("submission_id")), has_projects=True
            ),
        )
        return
    answers = None
    sid = data.get("submission_id")
    if sid:
        try:
            sub = await get_submission(uuid.UUID(sid))
            answers = sub.answers if sub else None
        except (ValueError, TypeError):
            answers = None
    text = render.render_step(step_key, answers)
    if not text:
        return
    await callback.message.answer(text, reply_markup=keyboards.menu_current_step_kb(), parse_mode="HTML")


# ---- Callback: Проект (резюме / собранные данные) ----
@router.callback_query(F.data == callbacks.menu(callbacks.MENU_PROJECT))
async def cb_menu_project(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get("submission_id")
    if not sid:
        await callback.message.answer(
            copy.t(copy.PROJECT_NO_DATA),
            reply_markup=keyboards.menu_cabinet_inline_kb(show_resume=False, has_projects=True),
        )
        return
    try:
        sub = await get_submission(uuid.UUID(sid))
    except (ValueError, TypeError):
        await callback.message.answer(
            copy.t(copy.PROJECT_NO_DATA),
            reply_markup=keyboards.menu_cabinet_inline_kb(show_resume=False, has_projects=True),
        )
        return
    if not sub:
        await callback.message.answer(
            copy.t(copy.PROJECT_NO_DATA),
            reply_markup=keyboards.menu_cabinet_inline_kb(show_resume=False, has_projects=True),
        )
        return
    answers = sub.answers or {}
    if not answers:
        await callback.message.answer(
            copy.t(copy.PROJECT_NO_DATA),
            reply_markup=keyboards.menu_cabinet_inline_kb(show_resume=True, has_projects=True),
        )
        return
    from src.v2.rendering import render_submission_to_html
    body_html = render_submission_to_html(answers)
    await callback.message.answer(
        body_html,
        reply_markup=keyboards.menu_current_step_kb(),
        parse_mode="HTML",
    )
