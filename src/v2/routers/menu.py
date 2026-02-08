"""
V2 Menu Card: Unified Cabinet Menu.

Callback namespace: m:* (m:home, m:resume, m:my_projects, m:catalog, m:request, etc.)
Commands: /menu, /catalog, /request, /my_requests, /leads
Text triggers: "🏠 Меню", "☰ Меню", "Меню"

Cabinet Menu Items (unified, no scatter):
- 🏠 Главное меню (m:home) - /start
- ▶️ Продолжить заполнение (m:resume) - resume draft
- 📁 Мои проекты (m:my_projects)
- 🏪 Каталог (m:catalog)
- 📥 Реквесты (m:request) - buyer request
- 📊 Мои реквесты / Лиды (m:my_requests_leads)
- 📱 Кабинет (Mini App) - WebApp button
- ✕ Закрыть (m:close)

UX:
- All interactions via inline keyboard EDIT the same message
- "✕ Закрыть" deletes the message or edits to "Меню закрыто"
- No AI-chat, no design/audio items — feels like a cabinet
"""
import logging
import uuid
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import persistent_reply_kb
from src.bot.messages import get_copy
from src.v2.keyboards.menu import (
    kb_cabinet_menu,
    kb_back_close,
    kb_to_menu_only,
)
from src.v2.repo import (
    get_or_create_user,
    get_submission,
    get_active_submission,
)
from src.v2.fsm.states import V2FormSteps
from src.v2.fsm.steps import get_step, get_step_index, STEP_KEYS


# Reply keyboard button texts (for message handlers)
REPLY_BTN_MAIN_MENU = "🏠 Меню"
REPLY_BTN_MENU_ALT = "☰ Меню"
REPLY_BTN_MY_PROJECTS = "📁 Мои проекты"
REPLY_BTN_CATALOG = "🏪 Каталог"
REPLY_BTN_REQUEST = "📥 Реквесты"
REPLY_BTN_MY_REQUESTS_LEADS = "📊 Мои реквесты / Лиды"

logger = logging.getLogger(__name__)

router = Router()

# Callback prefix
CB_PREFIX = "m"

# FSMContext data keys
DATA_SUBMISSION_ID = "submission_id"
DATA_STEP_KEY = "current_step_key"
DATA_MENU_MSG_ID = "menu_msg_id"


# =============================================================================
# Helper: Check if user has active draft
# =============================================================================

async def _has_active_draft(user_id: int) -> bool:
    """Check if user has an active draft submission."""
    try:
        user = await get_or_create_user(user_id, None, None)
        sub = await get_active_submission(user.id)
        return sub is not None
    except Exception:
        return False


async def _get_step_info(state: FSMContext) -> str:
    """Get current step info text for status display."""
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    
    if not sid or not step_key:
        return get_copy("V2_MENU_STEP_NO_ACTIVE")
    
    step = get_step(step_key)
    if not step:
        return get_copy("V2_MENU_STEP_NO_ACTIVE")
    
    step_num = get_step_index(step_key) + 1
    total = len(STEP_KEYS)
    progress = round(step_num / total * 100) if total > 0 else 0
    
    project_title = "—"
    try:
        sub = await get_submission(uuid.UUID(sid))
        if sub and sub.answers:
            project_title = sub.answers.get("title", "").strip() or "—"
    except (ValueError, TypeError):
        pass
    
    prompt_text = step.get("prompt", "").split("\n")[0][:60]
    
    lines = [
        f"<b>Проект:</b> {project_title}",
        f"<b>Шаг:</b> {step_num} из {total} ({progress}%)",
        "",
        "<b>Текущий вопрос:</b>",
        f"<i>{prompt_text}...</i>",
    ]
    return "\n".join(lines)


# =============================================================================
# Main Cabinet Menu: open_cabinet_menu
# =============================================================================

async def open_cabinet_menu(
    target: Message | CallbackQuery,
    state: FSMContext,
    *,
    is_edit: bool = False,
) -> Optional[Message]:
    """
    Open or edit cabinet menu card.
    
    Args:
        target: Message or CallbackQuery
        state: FSMContext
        is_edit: If True, edit existing message. If False, send new message.
    
    Returns:
        Sent/edited message or None
    """
    user_id = target.from_user.id if target.from_user else 0
    logger.info("open_cabinet_menu user_id=%s is_edit=%s", user_id, is_edit)
    
    has_draft = await _has_active_draft(user_id)
    
    text = get_copy("V2_CABINET_MENU_TITLE")
    kb = kb_cabinet_menu(has_active_draft=has_draft)
    
    if isinstance(target, CallbackQuery):
        message = target.message
        if is_edit and message:
            try:
                await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
                return message
            except Exception:
                pass
        if message:
            msg = await message.answer(text, reply_markup=kb, parse_mode="HTML")
            await state.update_data(**{DATA_MENU_MSG_ID: msg.message_id})
            return msg
    else:
        msg = await target.answer(text, reply_markup=kb, parse_mode="HTML")
        await state.update_data(**{DATA_MENU_MSG_ID: msg.message_id})
        await target.answer(
            get_copy("V2_MENU_HINT").strip(),
            reply_markup=persistent_reply_kb(),
        )
        return msg
    
    return None


# Legacy alias
async def open_main_menu(target: Message | CallbackQuery, state: FSMContext, *, is_edit: bool = False):
    return await open_cabinet_menu(target, state, is_edit=is_edit)


# =============================================================================
# Menu Triggers: /menu, "🏠 Меню", "☰ Меню", "Меню"
# =============================================================================

@router.message(F.text.in_(["☰ Меню", "🏠 Меню", "Меню", REPLY_BTN_MAIN_MENU, REPLY_BTN_MENU_ALT]))
@router.message(Command("menu"))
async def handle_menu_trigger(message: Message, state: FSMContext) -> None:
    """Open cabinet menu (inline keyboard)."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("menu_trigger user_id=%s action=open_cabinet_menu", user_id)
    await open_cabinet_menu(message, state, is_edit=False)


# =============================================================================
# Callback: m:home (🏠 Главное меню) -> /start
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:home")
async def cb_menu_home(callback: CallbackQuery, state: FSMContext) -> None:
    """Home button: show V2 cabinet greeting."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=home user_id=%s", user_id)
    
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    from src.v2.routers.start import show_v2_cabinet
    await show_v2_cabinet(callback, state)


# =============================================================================
# Callback: m:root, m:back (return to cabinet menu)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:root")
@router.callback_query(F.data == f"{CB_PREFIX}:back")
async def cb_menu_root(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to cabinet menu (edit current message)."""
    await callback.answer()
    logger.info("menu_action=root user_id=%s", callback.from_user.id if callback.from_user else 0)
    await open_cabinet_menu(callback, state, is_edit=True)


# =============================================================================
# Callback: m:resume (▶️ Продолжить заполнение)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:resume")
async def cb_menu_resume(callback: CallbackQuery, state: FSMContext) -> None:
    """Resume filling draft submission."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=resume user_id=%s", user_id)
    
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    from src.v2.routers.form import show_question
    from src.v2.routers.preview import show_preview
    
    await callback.message.answer(get_copy("V2_MENU_HINT").strip(), reply_markup=persistent_reply_kb())
    
    user = await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    sub = await get_active_submission(user.id)
    
    if not sub:
        await callback.message.answer(
            get_copy("V2_MENU_STEP_NO_ACTIVE"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    await state.update_data(**{DATA_SUBMISSION_ID: str(sub.id)})
    
    current_step = sub.current_step
    if current_step == "preview":
        await state.set_state(V2FormSteps.answering)
        await state.update_data(**{DATA_STEP_KEY: "preview"})
        await show_preview(callback.message, state)
        return
    
    if current_step and get_step(current_step):
        await state.set_state(V2FormSteps.answering)
        await state.update_data(**{DATA_STEP_KEY: current_step})
        await show_question(callback.message, state, current_step)
        return
    
    await state.set_state(V2FormSteps.answering)
    await state.update_data(**{DATA_STEP_KEY: "q1"})
    await show_question(callback.message, state, "q1")


# =============================================================================
# Callback: m:my_projects (📁 Мои проекты)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:my_projects")
async def cb_menu_my_projects(callback: CallbackQuery, state: FSMContext) -> None:
    """Show user's projects list."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=my_projects user_id=%s", user_id)
    
    from src.v2.repo import list_submissions_by_user
    from src.v2.ui.keyboards import projects_list_kb
    from src.bot.database.models import ProjectStatus
    
    user = await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    subs = await list_submissions_by_user(user.id, limit=10)
    
    if not subs:
        text = "<b>📁 Мои проекты</b>\n\nУ вас пока нет проектов.\n\nСоздайте новый проект через меню."
        if callback.message:
            try:
                await callback.message.edit_text(text, reply_markup=kb_back_close(), parse_mode="HTML")
            except Exception:
                await callback.message.answer(text, reply_markup=kb_back_close(), parse_mode="HTML")
        return
    
    status_labels = {
        ProjectStatus.draft: "📝 Черновик",
        ProjectStatus.pending: "⏳ На модерации",
        ProjectStatus.needs_fix: "🔧 На доработку",
        ProjectStatus.approved: "✅ Одобрен",
        ProjectStatus.rejected: "❌ Отклонён",
    }
    
    lines = ["<b>📁 Мои проекты</b>", ""]
    projects_for_kb = []
    for s in subs:
        title = (s.answers or {}).get("title", "Без названия") or "Без названия"
        status = status_labels.get(s.status, "❓")
        lines.append(f"• {title[:35]} — {status}")
        projects_for_kb.append((title[:20], s.id))
    
    text = "\n".join(lines)
    kb = projects_list_kb(projects_for_kb)
    
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


# =============================================================================
# Callback: m:catalog (🏪 Каталог)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:catalog")
async def cb_menu_catalog(callback: CallbackQuery, state: FSMContext) -> None:
    """Show catalog of approved projects."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=catalog user_id=%s", user_id)
    
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    from src.bot.services import list_approved_projects
    from src.bot.renderer import render_project_post
    
    await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    projects = await list_approved_projects()
    if not projects:
        text = "<b>🏪 Каталог проектов</b>\n\nПока нет активных проектов."
        await callback.message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")
        return
    
    header = "<b>🏪 Каталог проектов</b>\n"
    parts = [header]
    for p in projects:
        parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await callback.message.answer(header, parse_mode="HTML")
        for p in projects:
            await callback.message.answer(
                render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
            )
        await callback.message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await callback.message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


# =============================================================================
# Callback: m:request (📥 Реквесты) -> buyer request flow
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:request")
async def cb_menu_request(callback: CallbackQuery, state: FSMContext) -> None:
    """Buyer request flow is disabled (product simplification)."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=request (disabled) user_id=%s", user_id)

    if callback.message:
        await callback.message.answer(
            "Функция реквестов отключена.",
            reply_markup=kb_to_menu_only(),
        )
    await state.clear()


# =============================================================================
# Callback: m:my_requests_leads (📊 Мои реквесты / Лиды)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:my_requests_leads")
async def cb_menu_my_requests_leads(callback: CallbackQuery, state: FSMContext) -> None:
    """Requests/leads are disabled (product simplification)."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=my_requests_leads (disabled) user_id=%s", user_id)

    if callback.message:
        text = "Функция реквестов/лидов отключена."
        try:
            await callback.message.edit_text(text, reply_markup=kb_back_close())
        except Exception:
            await callback.message.answer(text, reply_markup=kb_back_close())
    await state.clear()


# =============================================================================
# Callback: m:help (placeholder for future help section)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:help")
async def cb_menu_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Show help screen."""
    await callback.answer()
    logger.info("menu_action=help user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    text = get_copy("V2_MENU_HELP_SCREEN")
    
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb_back_close(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb_back_close(), parse_mode="HTML")


# =============================================================================
# Callback: m:close (✕ Закрыть)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:close")
async def cb_menu_close(callback: CallbackQuery, state: FSMContext) -> None:
    """Close menu: delete message or edit to 'Меню закрыто'."""
    await callback.answer()
    logger.info("menu_action=close user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            try:
                await callback.message.edit_text(
                    get_copy("V2_MENU_CLOSED"),
                    reply_markup=None,
                    parse_mode="HTML",
                )
            except Exception:
                pass


# =============================================================================
# Legacy Command Callbacks: m:cmd:* (backward compat)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:cmd:start")
async def cb_cmd_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: m:cmd:start -> m:home"""
    await cb_menu_home(callback, state)


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:resume")
async def cb_cmd_resume(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: m:cmd:resume -> m:resume"""
    await cb_menu_resume(callback, state)


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:catalog")
async def cb_cmd_catalog(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: m:cmd:catalog -> m:catalog"""
    await cb_menu_catalog(callback, state)


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:request")
async def cb_cmd_request(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: m:cmd:request -> m:request"""
    await cb_menu_request(callback, state)


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:my_requests")
@router.callback_query(F.data == f"{CB_PREFIX}:cmd:leads")
async def cb_cmd_my_requests_leads(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: m:cmd:my_requests, m:cmd:leads -> m:my_requests_leads"""
    await cb_menu_my_requests_leads(callback, state)


# =============================================================================
# V2 Command Handlers for /catalog, /request, /my_requests, /leads
# =============================================================================

@router.message(Command("catalog"))
async def cmd_catalog_v2(message: Message, state: FSMContext) -> None:
    """V2 /catalog handler."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=catalog user_id=%s", user_id)
    
    from src.bot.services import list_approved_projects
    from src.bot.renderer import render_project_post
    
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    projects = await list_approved_projects()
    if not projects:
        text = "<b>🏪 Каталог проектов</b>\n\nПока нет активных проектов."
        await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")
        return
    
    header = "<b>🏪 Каталог проектов</b>\n"
    parts = [header]
    for p in projects:
        parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header, parse_mode="HTML")
        for p in projects:
            await message.answer(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


@router.message(Command("request"))
async def cmd_request_v2(message: Message, state: FSMContext) -> None:
    """V2 /request handler."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=request user_id=%s", user_id)

    # Requests/leads flow disabled (product simplification).
    await state.clear()
    await message.answer("Функция реквестов отключена.", reply_markup=kb_to_menu_only())
    return
    
    from src.bot.fsm.states import BuyerRequestStates
    
    await state.clear()
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await state.set_state(BuyerRequestStates.what)
    
    text = "<b>📥 Оставить заявку</b>\n\nОпишите, что вы ищете."
    await message.answer(text, parse_mode="HTML")
    await message.answer(get_copy("REQUEST_Q1_WHAT"))


@router.message(Command("my_requests"))
async def cmd_my_requests_v2(message: Message, state: FSMContext) -> None:
    """V2 /my_requests handler."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=my_requests user_id=%s", user_id)

    # Requests/leads flow disabled (product simplification).
    await state.clear()
    await message.answer("Функция реквестов/лидов отключена.", reply_markup=kb_to_menu_only())
    return
    
    from src.bot.services import list_my_requests_with_projects
    from src.bot.renderer import render_buyer_request_summary, render_project_post
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    requests_list, leads_list, all_projects = await list_my_requests_with_projects(user.id)
    
    if not requests_list:
        text = "<b>📋 Мои заявки</b>\n\nУ вас пока нет заявок.\n\nСоздайте заявку через /request"
        await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")
        return
    
    header = "<b>📋 Мои заявки</b>\n"
    lead_by_req = {}
    for lead in leads_list:
        if lead.buyer_request_id:
            lead_by_req.setdefault(lead.buyer_request_id, []).append(lead)
    
    parts = [header]
    for req in requests_list:
        parts.append(render_buyer_request_summary(req.what, req.budget, req.contact))
        for lead in lead_by_req.get(req.id, []):
            p = all_projects.get(lead.project_id)
            if p:
                parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header, parse_mode="HTML")
        for req in requests_list:
            await message.answer(render_buyer_request_summary(req.what, req.budget, req.contact))
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


@router.message(Command("leads"))
async def cmd_leads_v2(message: Message, state: FSMContext) -> None:
    """V2 /leads handler."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=leads user_id=%s", user_id)

    # Requests/leads flow disabled (product simplification).
    await state.clear()
    await message.answer("Функция реквестов/лидов отключена.", reply_markup=kb_to_menu_only())
    return
    
    from src.bot.services import list_leads_for_seller
    from src.bot.renderer import render_project_post
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    my_projects, leads_list = await list_leads_for_seller(user.id)
    
    if not my_projects or not leads_list:
        text = "<b>👥 Мои лиды</b>\n\nПока нет лидов.\n\nСоздайте проект, чтобы получать лиды."
        await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")
        return
    
    header = "<b>👥 Мои лиды</b>\n"
    proj_by_id = {p.id: p for p in my_projects}
    parts = [header]
    
    for lead in leads_list:
        p = proj_by_id.get(lead.project_id)
        if p:
            parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header, parse_mode="HTML")
        for lead in leads_list:
            p = proj_by_id.get(lead.project_id)
            if p:
                await message.answer(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


# =============================================================================
# Reply Keyboard Button Handlers (text message triggers)
# Simplified: all text buttons trigger cabinet menu
# =============================================================================

@router.message(F.text == REPLY_BTN_MY_PROJECTS)
async def handle_reply_my_projects(message: Message, state: FSMContext) -> None:
    """Handle '📁 Мои проекты' reply button."""
    await cmd_catalog_v2(message, state)


@router.message(F.text == REPLY_BTN_CATALOG)
async def handle_reply_catalog(message: Message, state: FSMContext) -> None:
    """Handle '🏪 Каталог' reply button."""
    await cmd_catalog_v2(message, state)


@router.message(F.text == REPLY_BTN_REQUEST)
async def handle_reply_request(message: Message, state: FSMContext) -> None:
    """Handle '📥 Реквесты' reply button."""
    await cmd_request_v2(message, state)


@router.message(F.text == REPLY_BTN_MY_REQUESTS_LEADS)
async def handle_reply_my_requests_leads(message: Message, state: FSMContext) -> None:
    """Handle '📊 Мои реквесты / Лиды' reply button."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=my_requests_leads (disabled) user_id=%s", user_id)

    # Requests/leads flow disabled (product simplification).
    await state.clear()
    await message.answer("Функция реквестов/лидов отключена.", reply_markup=kb_to_menu_only())
    return
    
    from src.bot.services import list_my_requests_with_projects, list_leads_for_seller
    from src.bot.renderer import render_buyer_request_summary
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    requests_list, leads_list, all_projects = await list_my_requests_with_projects(user.id)
    my_projects, seller_leads = await list_leads_for_seller(user.id)
    
    lines = ["<b>📊 Мои реквесты / Лиды</b>", ""]
    
    if requests_list:
        lines.append("<b>📥 Мои заявки (покупатель)</b>")
        lines.append("")
        for req in requests_list[:5]:
            lines.append(render_buyer_request_summary(req.what, req.budget, req.contact))
        lines.append("")
    
    if my_projects and seller_leads:
        lines.append("<b>👥 Мои лиды (продавец)</b>")
        lines.append("")
        proj_by_id = {p.id: p for p in my_projects}
        for lead in seller_leads[:5]:
            p = proj_by_id.get(lead.project_id)
            if p:
                lines.append(f"• {p.title[:40]} — лид")
        lines.append("")
    
    if not requests_list and not seller_leads:
        lines.append("Пока нет заявок и лидов.")
    
    text = "\n".join(lines)
    await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


# =============================================================================
# Legacy callback handlers (backward compat for old menu:* namespace)
# =============================================================================

@router.callback_query(F.data == "menu:back_to_menu")
async def cb_legacy_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:back_to_menu -> m:root"""
    await cb_menu_root(callback, state)


@router.callback_query(F.data == "menu:continue")
async def cb_legacy_continue(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:continue -> m:resume"""
    await cb_menu_resume(callback, state)


@router.callback_query(F.data == "menu:create")
async def cb_legacy_create(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:create -> redirect to V2 cabinet."""
    await callback.answer()
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    from src.v2.routers.start import show_v2_cabinet
    await show_v2_cabinet(callback, state)


@router.callback_query(F.data == "menu:help")
async def cb_legacy_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:help -> m:help"""
    await cb_menu_help(callback, state)


@router.callback_query(F.data == "menu:drafts")
async def cb_legacy_drafts(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:drafts -> m:my_projects"""
    await cb_menu_my_projects(callback, state)


@router.callback_query(F.data == "menu:posts")
async def cb_legacy_posts(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:posts -> m:catalog"""
    await cb_menu_catalog(callback, state)


@router.callback_query(F.data == "menu:settings")
async def cb_legacy_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:settings -> show help (settings not implemented)."""
    await cb_menu_help(callback, state)


@router.callback_query(F.data == "menu:preview")
async def cb_legacy_preview(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:preview -> m:resume"""
    await cb_menu_resume(callback, state)
