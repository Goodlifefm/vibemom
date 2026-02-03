"""V2 menu: persistent 🏠 Меню button and cabinet from any state. High-priority router."""
import logging
import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.bot.messages import get_copy
from src.bot.keyboards import (
    reply_menu_keyboard,
    menu_cabinet_inline_kb,
    menu_restart_confirm_kb,
    MENU_PREFIX,
)
from src.v2.repo import (
    get_or_create_user,
    get_active_submission,
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
    from src.bot.messages import get_copy
    m = {
        ProjectStatus.draft: "V2_STATUS_DRAFT",
        ProjectStatus.pending: "V2_STATUS_PENDING",
        ProjectStatus.needs_fix: "V2_STATUS_NEEDS_FIX",
        ProjectStatus.approved: "V2_STATUS_APPROVED",
        ProjectStatus.rejected: "V2_STATUS_REJECTED",
    }
    return get_copy(m.get(status, "V2_STATUS_DRAFT")).strip()


async def _send_menu_keyboard(target: Message) -> None:
    """Send second message to set persistent reply keyboard."""
    await target.answer(get_copy("V2_MENU_HINT"), reply_markup=reply_menu_keyboard())


async def show_menu_cabinet(message_or_callback: Message | CallbackQuery, state: FSMContext) -> None:
    """Show cabinet (greeting + inline menu) and set reply keyboard. Works from any state."""
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    data = await state.get_data() if state else {}
    show_resume = bool(data.get("submission_id"))
    user_id = (message_or_callback.from_user.id if message_or_callback.from_user else 0) if hasattr(message_or_callback, "from_user") else 0
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
    kb = menu_cabinet_inline_kb(show_resume=show_resume, has_projects=has_projects)
    await target.answer(get_copy("V2_CABINET_GREETING"), reply_markup=kb)
    await _send_menu_keyboard(target)
    logger.info("menu_open user_id=%s", user_id)


# ---- Text: 🏠 Меню, Меню, /menu (any state) ----
@router.message(F.text.in_(["🏠 Меню", "Меню"]))
@router.message(Command("menu"))
async def handle_menu_trigger(message: Message, state: FSMContext) -> None:
    """Global: show menu from any state."""
    await show_menu_cabinet(message, state)


# ---- Callback: Продолжить ----
@router.callback_query(F.data == f"{MENU_PREFIX}:resume")
async def cb_menu_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from src.v2.routers.start import _do_resume
    logger.info("menu_continue user_id=%s", callback.from_user.id if callback.from_user else 0)
    await _do_resume(callback.message, state)


# ---- Callback: Начать заново (confirm) ----
@router.callback_query(F.data == f"{MENU_PREFIX}:restart")
async def cb_menu_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        get_copy("V2_MENU_RESTART_CONFIRM"),
        reply_markup=menu_restart_confirm_kb(),
    )


@router.callback_query(F.data == f"{MENU_PREFIX}:restart_yes")
async def cb_menu_restart_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    from src.v2.routers.start import show_v2_cabinet
    logger.info("menu_restart_yes user_id=%s", callback.from_user.id if callback.from_user else 0)
    await show_menu_cabinet(callback.message, state)


@router.callback_query(F.data == f"{MENU_PREFIX}:restart_no")
async def cb_menu_restart_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_menu_cabinet(callback.message, state)


# ---- Callback: Мои проекты ----
@router.callback_query(F.data == f"{MENU_PREFIX}:projects")
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
            get_copy("V2_MY_PROJECTS_HEADER") + "\n\n" + get_copy("V2_MY_PROJECTS_EMPTY"),
            reply_markup=menu_cabinet_inline_kb(show_resume=bool((await state.get_data()).get("submission_id")), has_projects=False),
        )
        return
    text = get_copy("V2_MY_PROJECTS_HEADER") + "\n\n"
    kb_rows = []
    for s in subs:
        title = (s.answers or {}).get("title", "—") or "—"
        if title == "—":
            title = "Без названия"
        text += f"• {title[:40]} — {_status_copy(s.status)}\n"
        from aiogram.types import InlineKeyboardButton
        kb_rows.append([InlineKeyboardButton(
            text=get_copy("V2_BTN_OPEN").strip() + f" ({title[:20]})",
            callback_data=f"v2cab:open:{s.id}",
        )])
    from aiogram.types import InlineKeyboardMarkup
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


# ---- Callback: Создать проект ----
@router.callback_query(F.data == f"{MENU_PREFIX}:create")
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
@router.callback_query(F.data == f"{MENU_PREFIX}:help")
async def cb_menu_help(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        get_copy("V2_HELP_TEXT"),
        reply_markup=menu_cabinet_inline_kb(
            show_resume=bool((await state.get_data()).get("submission_id")),
            has_projects=True,
        ),
    )


# ---- Callback: Статус ----
@router.callback_query(F.data == f"{MENU_PREFIX}:status")
async def cb_menu_status(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    sid = data.get("submission_id")
    step_key = data.get("current_step_key") or ""
    step_label = step_key or "—"
    if step_key and get_step(step_key):
        idx = get_step_index(step_key)
        total = len(STEP_KEYS)
        step_label = f"Шаг {idx + 1} из {total} ({step_key})"
    project_line = get_copy("V2_MENU_STATUS_NO_PROJECT")
    extra = ""
    if sid:
        try:
            sub = await get_submission(uuid.UUID(sid))
            if sub:
                title = (sub.answers or {}).get("title", "—") or "—"
                project_line = f"{title[:50]} — {_status_copy(sub.status)}"
        except (ValueError, Exception):
            pass
    text = get_copy("V2_MENU_STATUS_TEMPLATE").format(
        step=step_label,
        project=project_line,
        extra=extra or "—",
    )
    await callback.message.answer(
        text,
        reply_markup=menu_cabinet_inline_kb(
            show_resume=bool(sid),
            has_projects=True,
        ),
    )
