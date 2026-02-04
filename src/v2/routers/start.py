"""V2 start: cabinet (Create, Resume, My projects). Uses Submission + v2.repo."""
import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.v2.repo import (
    get_or_create_user,
    get_active_submission,
    get_submission,
    list_submissions_by_user,
    create_submission,
)
from src.v2.fsm.states import V2FormSteps
from src.v2.routers.preview import show_preview
from src.bot.database.models import ProjectStatus
from src.bot.keyboards import reply_menu_keyboard
from src.v2.ui import callbacks, copy, keyboards

router = Router()
PREFIX = callbacks.CAB_PREFIX


def _status_copy(status: ProjectStatus) -> str:
    m = {
        ProjectStatus.draft: copy.STATUS_DRAFT,
        ProjectStatus.pending: copy.STATUS_PENDING,
        ProjectStatus.needs_fix: copy.STATUS_NEEDS_FIX,
        ProjectStatus.approved: copy.STATUS_APPROVED,
        ProjectStatus.rejected: copy.STATUS_REJECTED,
    }
    return copy.t(m.get(status, copy.STATUS_DRAFT)).strip()


async def show_v2_cabinet(message_or_callback: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    """Show V2 cabinet (greeting + menu inline kb) and set persistent 🏠 Меню reply keyboard."""
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    show_resume = False
    has_projects = False
    if state:
        data = await state.get_data()
        show_resume = bool(data.get("submission_id"))
    try:
        u = getattr(message_or_callback, "from_user", None)
        user = await get_or_create_user(
            u.id if u else 0,
            u.username if u else None,
            u.full_name if u else None,
        )
        subs = await list_submissions_by_user(user.id, limit=1)
        has_projects = bool(subs)
    except Exception:
        pass
    kb = keyboards.cabinet_inline_kb(show_resume=show_resume)
    await target.answer(copy.t(copy.CABINET_GREETING), reply_markup=kb)
    await target.answer(copy.t(copy.MENU_HINT), reply_markup=reply_menu_keyboard())


async def _do_resume(message: Message, state: FSMContext) -> None:
    """Load active submission, restore current_step, show question (for /resume and Resume button)."""
    from src.v2.repo import get_or_create_user
    await message.answer(copy.t(copy.MENU_HINT), reply_markup=reply_menu_keyboard())
    user = await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    sub = await get_active_submission(user.id)
    if not sub:
        await show_v2_cabinet(message, state)
        return
    await state.update_data(submission_id=str(sub.id))
    from src.v2.routers.form import show_form_step, show_question
    from src.v2.fsm.steps import get_step
    current_step = sub.current_step
    if current_step == "preview":
        await state.set_state(V2FormSteps.answering)
        await state.update_data(current_step_key="preview")
        await show_preview(message, state)
        return
    if current_step and get_step(current_step):
        await state.set_state(V2FormSteps.answering)
        await state.update_data(current_step_key=current_step)
        await show_question(message, state, current_step)
        return
    answers = sub.answers or {}
    if "title" not in answers:
        await show_form_step(message, state, 1)
    elif "description" not in answers:
        await show_form_step(message, state, 2)
    elif "contact" not in answers:
        await show_form_step(message, state, 3)
    else:
        await show_preview(message, state)


@router.message(Command("resume"))
async def cmd_resume(message: Message, state: FSMContext) -> None:
    """V2: /resume restores FSM from DB current_step and repeats the question."""
    await _do_resume(message, state)


@router.callback_query(F.data == f"{PREFIX}:resume")
async def cb_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await _do_resume(callback.message, state)


@router.callback_query(F.data == f"{PREFIX}:create")
async def cb_create(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    sub = await create_submission(user.id, current_step="q1")
    await state.update_data(submission_id=str(sub.id))
    from src.v2.routers.form import show_form_step
    await show_form_step(callback.message, state, 1)


@router.callback_query(F.data == f"{PREFIX}:projects")
async def cb_projects(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    subs = await list_submissions_by_user(user.id, limit=5)
    if not subs:
        await callback.message.answer(
            V2Copy.get(V2Copy.MY_PROJECTS_HEADER) + "\n\n" + V2Copy.get(V2Copy.MY_PROJECTS_EMPTY),
            reply_markup=keyboards.cabinet_inline_kb(show_resume=bool((await state.get_data()).get("submission_id"))),
        )
        return
    text = V2Copy.get(V2Copy.MY_PROJECTS_HEADER) + "\n\n"
    projects: list[tuple[str, uuid.UUID]] = []
    for s in subs:
        title = (s.answers or {}).get("title", copy.CARD_EMPTY_VALUE) or copy.CARD_EMPTY_VALUE
        if title == copy.CARD_EMPTY_VALUE:
            title = copy.UNTITLED_PROJECT
        text += f"• {title[:40]} — {_status_copy(s.status)}\n"
        projects.append((title, s.id))
    await callback.message.answer(text, reply_markup=keyboards.projects_list_kb(projects))


@router.callback_query(F.data.startswith(f"{PREFIX}:open:"))
async def cb_open(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    sid = callback.data.split(":", 2)[2]
    await state.update_data(submission_id=sid)
    from src.v2.routers.form import show_form_step, show_question
    from src.v2.fsm.steps import get_step
    try:
        sub = await get_submission(uuid.UUID(sid))
    except ValueError:
        await show_v2_cabinet(callback, state)
        return
    if not sub:
        await show_v2_cabinet(callback, state)
        return
    current_step = sub.current_step
    if current_step and get_step(current_step):
        await state.set_state(V2FormSteps.answering)
        await state.update_data(current_step_key=current_step)
        await show_question(callback.message, state, current_step)
        return
    answers = sub.answers or {}
    if "title" not in answers:
        await show_form_step(callback.message, state, 1)
    elif "description" not in answers:
        await show_form_step(callback.message, state, 2)
    elif "contact" not in answers:
        await show_form_step(callback.message, state, 3)
    else:
        await show_preview(callback.message, state)


@router.callback_query(F.data == f"{PREFIX}:how")
async def cb_how(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        copy.t(copy.HOW_IT_WORKS),
        reply_markup=keyboards.cabinet_inline_kb(show_resume=bool((await state.get_data()).get("submission_id"))),
    )


@router.callback_query(F.data.startswith("v2fix:edit:"))
async def cb_fix_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Needs-fix: user pressed «Внести правки» — return to form for this submission."""
    await callback.answer()
    try:
        sid = callback.data.split(":", 2)[2]
        sub_id = uuid.UUID(sid)
    except (ValueError, IndexError):
        await show_v2_cabinet(callback, state)
        return
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    sub = await get_submission(sub_id)
    if not sub or sub.user_id != user.id or sub.status != ProjectStatus.needs_fix:
        await show_v2_cabinet(callback, state)
        return
    await state.set_state(V2FormSteps.answering)
    await state.update_data(submission_id=sid, current_step_key=sub.current_step or "q1")
    from src.v2.routers.form import show_question
    from src.v2.fsm.steps import get_step
    step_key = sub.current_step or "q1"
    if step_key == "preview":
        await show_preview(callback.message, state)
        return
    if get_step(step_key):
        await show_question(callback.message, state, step_key)
        return
    from src.v2.routers.form import show_form_step
    answers = sub.answers or {}
    if "title" not in answers:
        await show_form_step(callback.message, state, 1)
    elif "description" not in answers:
        await show_form_step(callback.message, state, 2)
    elif "contact" not in answers:
        await show_form_step(callback.message, state, 3)
    else:
        await show_preview(callback.message, state)
