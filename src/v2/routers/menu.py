"""
V2 Menu Card: ReplyKeyboardMarkup (bottom-sheet) + InlineKeyboardMarkup.

Callback namespace: m:* (m:root, m:step, m:project, m:help, m:close, etc.)
Commands: /menu, /catalog, /request, /my_requests, /leads
Text triggers: "🏠 Меню", "☰ Меню", "Меню"

UX:
- /menu shows ReplyKeyboardMarkup (bottom-sheet) + inline menu card
- Reply keyboard layout:
  Row1: 📌 Текущий шаг | 📁 Проект
  Row2: ♻️ Начать заново (full width)
  Row3: 📄 Мои проекты (full width)
  Row4: ➕ Создать проект (full width)
  Row5: 📚 Каталог | ✍️ Реквест
  Row6: 🧾 Мои реквесты | 👥 Лиды
  Row7: ❓ Помощь / Команды (full width)

- All interactions via inline keyboard EDIT the same message (no new messages)
- "✕ Закрыть" deletes the message or edits to "Меню закрыто"
- Command buttons (m:cmd:*) call existing handlers and offer "В меню" button

Sections:
- 📌 Текущий шаг (m:step) - current wizard step info
- 📁 Проект (m:project) - project commands screen
- ♻️ Начать заново (m:restart) - restart wizard
- 📄 Мои проекты (m:my_projects) - /catalog handler
- ➕ Создать проект (m:create_project) - /submit wizard
- 📚 Каталог - /catalog handler
- ✍️ Реквест - /request handler (buyer request)
- 🧾 Мои реквесты - /my_requests handler
- 👥 Лиды - /leads handler
- ❓ Помощь/Команды (m:help) - help text
- ✕ Закрыть (m:close) - close menu
"""
import logging
import uuid
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import persistent_reply_kb, reply_menu_keyboard_full, reply_menu_keyboard_with_actions
from src.bot.messages import get_copy
from src.v2.keyboards.menu import (
    kb_main_menu,
    kb_back_close,
    kb_project_screen,
    kb_restart_confirm_new,
    kb_to_menu_only,
)
from src.v2.repo import (
    get_or_create_user,
    get_submission,
    create_submission,
)
from src.v2.fsm.states import V2FormSteps
from src.v2.fsm.steps import get_step, get_step_index, STEP_KEYS


# Reply keyboard button texts (for message handlers)
REPLY_BTN_CURRENT_STEP = "📌 Текущий шаг"
REPLY_BTN_PROJECT = "📁 Проект"
REPLY_BTN_RESTART = "♻️ Начать заново"
REPLY_BTN_MY_PROJECTS = "📄 Мои проекты"
REPLY_BTN_CREATE = "➕ Создать проект"
REPLY_BTN_HELP = "❓ Помощь / Команды"
REPLY_BTN_MAIN_MENU = "🏠 Меню"
REPLY_BTN_CATALOG = "📚 Каталог"
REPLY_BTN_REQUEST = "✍️ Реквест"
REPLY_BTN_MY_REQUESTS = "🧾 Мои реквесты"
REPLY_BTN_LEADS = "👥 Лиды"

logger = logging.getLogger(__name__)

router = Router()

# Callback prefix
CB_PREFIX = "m"

# FSMContext data keys
DATA_SUBMISSION_ID = "submission_id"
DATA_STEP_KEY = "current_step_key"
DATA_MENU_MSG_ID = "menu_msg_id"  # Track menu message for edits


# =============================================================================
# Helper: Get current step info
# =============================================================================

async def _get_step_info(state: FSMContext) -> str:
    """Get current step info text for 📌 Текущий шаг screen."""
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    
    if not sid or not step_key:
        return get_copy("V2_MENU_STEP_NO_ACTIVE")
    
    step = get_step(step_key)
    if not step:
        return get_copy("V2_MENU_STEP_NO_ACTIVE")
    
    # Get step number and total
    step_num = get_step_index(step_key) + 1
    total = len(STEP_KEYS)
    progress = round(step_num / total * 100) if total > 0 else 0
    
    # Get project title if available
    project_title = "—"
    try:
        sub = await get_submission(uuid.UUID(sid))
        if sub and sub.answers:
            project_title = sub.answers.get("title", "").strip() or "—"
    except (ValueError, TypeError):
        pass
    
    # Build info text
    prompt_text = step.get("prompt", "").split("\n")[0][:60]  # First line, truncated
    
    lines = [
        f"Проект: {project_title}",
        f"Шаг: {step_num} из {total} ({progress}%)",
        "",
        f"Текущий вопрос:",
        f"<i>{prompt_text}...</i>",
    ]
    return "\n".join(lines)


# =============================================================================
# Main Menu Card: open_main_menu
# =============================================================================

async def open_main_menu(
    target: Message | CallbackQuery,
    state: FSMContext,
    *,
    is_edit: bool = False,
) -> Optional[Message]:
    """
    Open or edit main menu card.
    
    Args:
        target: Message or CallbackQuery
        state: FSMContext
        is_edit: If True, edit existing message. If False, send new message.
    
    Returns:
        Sent/edited message or None
    """
    user_id = target.from_user.id if target.from_user else 0
    logger.info("open_main_menu user_id=%s is_edit=%s", user_id, is_edit)
    
    text = get_copy("V2_MENU_CARD_TITLE")
    kb = kb_main_menu()
    
    if isinstance(target, CallbackQuery):
        message = target.message
        if is_edit and message:
            try:
                await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
                return message
            except Exception:
                pass
        # Fallback: answer new message
        if message:
            msg = await message.answer(text, reply_markup=kb, parse_mode="HTML")
            await state.update_data(**{DATA_MENU_MSG_ID: msg.message_id})
            return msg
    else:
        msg = await target.answer(text, reply_markup=kb, parse_mode="HTML")
        await state.update_data(**{DATA_MENU_MSG_ID: msg.message_id})
        # Also send persistent keyboard hint
        await target.answer(
            get_copy("V2_MENU_HINT").strip(),
            reply_markup=persistent_reply_kb(),
        )
        return msg
    
    return None


# =============================================================================
# Menu Triggers: /menu, "🏠 Меню", "☰ Меню", "Меню"
# =============================================================================

@router.message(F.text.in_(["☰ Меню", "🏠 Меню", "Меню", REPLY_BTN_MAIN_MENU]))
@router.message(Command("menu"))
async def handle_menu_trigger(message: Message, state: FSMContext) -> None:
    """
    Open main menu with ReplyKeyboardMarkup (bottom-sheet style).
    Sends message + reply keyboard with all menu buttons.
    """
    user_id = message.from_user.id if message.from_user else 0
    logger.info("menu_trigger user_id=%s action=open_reply_menu", user_id)
    
    # Send menu message with reply keyboard
    text = get_copy("V2_REPLY_MENU_TITLE")
    await message.answer(text, reply_markup=reply_menu_keyboard_with_actions())
    
    # Also send inline menu card for additional options
    await open_main_menu(message, state, is_edit=False)


# =============================================================================
# Callback: m:root (back to main menu)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:root")
@router.callback_query(F.data == f"{CB_PREFIX}:back")
async def cb_menu_root(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to main menu (edit current message)."""
    await callback.answer()
    logger.info("menu_action=root user_id=%s", callback.from_user.id if callback.from_user else 0)
    await open_main_menu(callback, state, is_edit=True)


# =============================================================================
# Callback: m:step (📌 Текущий шаг)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:step")
async def cb_menu_step(callback: CallbackQuery, state: FSMContext) -> None:
    """Show current step info (edit message)."""
    await callback.answer()
    logger.info("menu_action=step user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    step_info = await _get_step_info(state)
    text = get_copy("V2_MENU_STEP_SCREEN").format(step_info=step_info)
    
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb_back_close(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb_back_close(), parse_mode="HTML")


# =============================================================================
# Callback: m:project (📁 Проект)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:project")
async def cb_menu_project(callback: CallbackQuery, state: FSMContext) -> None:
    """Show project commands screen (edit message)."""
    await callback.answer()
    logger.info("menu_action=project user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    text = get_copy("V2_MENU_PROJECT_SCREEN")
    
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb_project_screen(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb_project_screen(), parse_mode="HTML")


# =============================================================================
# Callback: m:restart (🧭 Начать заново)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:restart")
async def cb_menu_restart(callback: CallbackQuery, state: FSMContext) -> None:
    """Show restart confirmation (edit message)."""
    await callback.answer()
    logger.info("menu_action=restart user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    text = get_copy("V2_MENU_RESTART_CONFIRM_TEXT")
    
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb_restart_confirm_new(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb_restart_confirm_new(), parse_mode="HTML")


@router.callback_query(F.data == f"{CB_PREFIX}:restart_yes")
async def cb_menu_restart_yes(callback: CallbackQuery, state: FSMContext) -> None:
    """Confirm restart: clear state and return to menu."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=restart_yes user_id=%s", user_id)
    
    # Clear wizard state but preserve menu_msg_id
    data = await state.get_data()
    menu_msg_id = data.get(DATA_MENU_MSG_ID)
    await state.clear()
    if menu_msg_id:
        await state.update_data(**{DATA_MENU_MSG_ID: menu_msg_id})
    
    # Show confirmation then return to menu
    if callback.message:
        text = get_copy("V2_MENU_RESTART_DONE")
        await callback.message.edit_text(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


# =============================================================================
# Callback: m:my_projects (📄 Мои проекты) -> /catalog
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:my_projects")
async def cb_menu_my_projects(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Show catalog (existing /catalog handler logic).
    Sends new message with catalog, then offers "В меню" button.
    """
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=my_projects user_id=%s", user_id)
    
    # Close menu card
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            try:
                await callback.message.edit_text(get_copy("V2_MENU_CLOSED"), reply_markup=None)
            except Exception:
                pass
    
    # Call existing catalog logic
    from src.bot.services import list_approved_projects
    from src.bot.renderer import render_project_post
    
    await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    projects = await list_approved_projects()
    if not projects:
        text = get_copy("CATALOG_HEADER") + get_copy("CATALOG_EMPTY")
        await callback.message.answer(text, reply_markup=kb_to_menu_only())
        return
    
    header = get_copy("CATALOG_HEADER")
    parts = [header]
    for p in projects:
        parts.append(
            render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
        )
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await callback.message.answer(header)
        for p in projects:
            await callback.message.answer(
                render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
            )
        await callback.message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await callback.message.answer(text, reply_markup=kb_to_menu_only())


# =============================================================================
# Callback: m:create_project (➕ Создать проект) -> /request
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:create_project")
async def cb_menu_create_project(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Start new project (existing request handler logic).
    """
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=create_project user_id=%s", user_id)
    
    # Close menu card
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            try:
                await callback.message.edit_text(get_copy("V2_MENU_CLOSED"), reply_markup=None)
            except Exception:
                pass
    
    # Start wizard (create new submission)
    user = await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    sub = await create_submission(user.id, current_step="q1")
    await state.update_data(**{
        DATA_SUBMISSION_ID: str(sub.id),
        DATA_STEP_KEY: "q1",
    })
    await state.set_state(V2FormSteps.answering)
    
    # Show first step
    from src.v2.routers.form import show_question
    await callback.message.answer(
        get_copy("V2_MENU_HINT").strip(),
        reply_markup=persistent_reply_kb(),
    )
    await show_question(callback.message, state, "q1")
    
    logger.info("create_project_done user_id=%s submission_id=%s", user_id, sub.id)


# =============================================================================
# Callback: m:help (❓ Помощь/Команды)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:help")
async def cb_menu_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Show help text (edit message)."""
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
# Command Callbacks: m:cmd:* (call existing handlers)
# =============================================================================

@router.callback_query(F.data == f"{CB_PREFIX}:cmd:start")
async def cb_cmd_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Call /start handler logic."""
    await callback.answer()
    logger.info("menu_action=cmd:start user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    # Close menu and trigger start
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    # Call start cabinet
    from src.v2.routers.start import show_v2_cabinet
    await show_v2_cabinet(callback, state)


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:resume")
async def cb_cmd_resume(callback: CallbackQuery, state: FSMContext) -> None:
    """Call /resume handler logic."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=cmd:resume user_id=%s", user_id)
    
    # Close menu
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    # Resume logic
    from src.v2.repo import get_active_submission
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
    
    # Default to first step
    await state.set_state(V2FormSteps.answering)
    await state.update_data(**{DATA_STEP_KEY: "q1"})
    await show_question(callback.message, state, "q1")


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:catalog")
async def cb_cmd_catalog(callback: CallbackQuery, state: FSMContext) -> None:
    """Call /catalog handler logic (same as m:my_projects)."""
    await cb_menu_my_projects(callback, state)


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:request")
async def cb_cmd_request(callback: CallbackQuery, state: FSMContext) -> None:
    """Call /request handler logic (buyer request)."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=cmd:request user_id=%s", user_id)
    
    # Close menu
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    # Start buyer request flow
    from src.bot.fsm.states import BuyerRequestStates
    
    await state.clear()
    await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    await state.set_state(BuyerRequestStates.what)
    await callback.message.answer(get_copy("REQUEST_START"))
    await callback.message.answer(get_copy("REQUEST_Q1_WHAT"))


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:my_requests")
async def cb_cmd_my_requests(callback: CallbackQuery, state: FSMContext) -> None:
    """Call /my_requests handler logic."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=cmd:my_requests user_id=%s", user_id)
    
    # Close menu
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    # Call existing logic
    from src.bot.services import list_my_requests_with_projects
    from src.bot.renderer import render_buyer_request_summary, render_project_post
    
    user = await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    requests_list, leads_list, all_projects = await list_my_requests_with_projects(user.id)
    
    if not requests_list:
        await callback.message.answer(
            get_copy("MY_REQUESTS_HEADER") + get_copy("MY_REQUESTS_EMPTY"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    header = get_copy("MY_REQUESTS_HEADER")
    lead_by_req: dict = {}
    for lead in leads_list:
        if lead.buyer_request_id:
            lead_by_req.setdefault(lead.buyer_request_id, []).append(lead)
    
    parts = [header]
    for req in requests_list:
        parts.append(render_buyer_request_summary(req.what, req.budget, req.contact))
        for lead in lead_by_req.get(req.id, []):
            p = all_projects.get(lead.project_id)
            if p:
                parts.append(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await callback.message.answer(header)
        for req in requests_list:
            await callback.message.answer(render_buyer_request_summary(req.what, req.budget, req.contact))
            for lead in lead_by_req.get(req.id, []):
                p = all_projects.get(lead.project_id)
                if p:
                    await callback.message.answer(
                        render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                    )
        await callback.message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await callback.message.answer(text, reply_markup=kb_to_menu_only())


@router.callback_query(F.data == f"{CB_PREFIX}:cmd:leads")
async def cb_cmd_leads(callback: CallbackQuery, state: FSMContext) -> None:
    """Call /leads handler logic."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_action=cmd:leads user_id=%s", user_id)
    
    # Close menu
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    # Call existing logic
    from src.bot.services import list_leads_for_seller
    from src.bot.renderer import render_project_post
    
    user = await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    my_projects, leads_list = await list_leads_for_seller(user.id)
    
    if not my_projects or not leads_list:
        await callback.message.answer(
            get_copy("LEADS_HEADER") + get_copy("LEADS_EMPTY"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    header = get_copy("LEADS_HEADER")
    proj_by_id = {p.id: p for p in my_projects}
    parts = [header]
    
    for lead in leads_list:
        p = proj_by_id.get(lead.project_id)
        if p:
            parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await callback.message.answer(header)
        for lead in leads_list:
            p = proj_by_id.get(lead.project_id)
            if p:
                await callback.message.answer(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
        await callback.message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await callback.message.answer(text, reply_markup=kb_to_menu_only())


# =============================================================================
# V2 Command Handlers for /catalog, /request, /my_requests, /leads
# These override V1 handlers when V2 is enabled
# =============================================================================

@router.message(Command("catalog"))
async def cmd_catalog_v2(message: Message, state: FSMContext) -> None:
    """V2 /catalog handler -> call handle_reply_catalog logic."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=catalog user_id=%s action=show_catalog", user_id)
    
    from src.bot.services import list_approved_projects
    from src.bot.renderer import render_project_post
    
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    projects = await list_approved_projects()
    if not projects:
        text = get_copy("CATALOG_HEADER") + get_copy("CATALOG_EMPTY")
        await message.answer(text, reply_markup=kb_to_menu_only())
        return
    
    header = get_copy("CATALOG_HEADER")
    parts = [header]
    for p in projects:
        parts.append(
            render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
        )
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for p in projects:
            await message.answer(
                render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
            )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


@router.message(Command("request"))
async def cmd_request_v2(message: Message, state: FSMContext) -> None:
    """V2 /request handler -> start buyer request flow."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=request user_id=%s action=start_buyer_request", user_id)
    
    from src.bot.fsm.states import BuyerRequestStates
    
    await state.clear()
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await state.set_state(BuyerRequestStates.what)
    await message.answer(get_copy("REQUEST_START"))
    await message.answer(get_copy("REQUEST_Q1_WHAT"))


@router.message(Command("my_requests"))
async def cmd_my_requests_v2(message: Message, state: FSMContext) -> None:
    """V2 /my_requests handler -> show buyer requests."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=my_requests user_id=%s action=show_my_requests", user_id)
    
    from src.bot.services import list_my_requests_with_projects
    from src.bot.renderer import render_buyer_request_summary, render_project_post
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    requests_list, leads_list, all_projects = await list_my_requests_with_projects(user.id)
    
    if not requests_list:
        await message.answer(
            get_copy("MY_REQUESTS_HEADER") + get_copy("MY_REQUESTS_EMPTY"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    header = get_copy("MY_REQUESTS_HEADER")
    lead_by_req: dict = {}
    for lead in leads_list:
        if lead.buyer_request_id:
            lead_by_req.setdefault(lead.buyer_request_id, []).append(lead)
    
    parts = [header]
    for req in requests_list:
        parts.append(render_buyer_request_summary(req.what, req.budget, req.contact))
        for lead in lead_by_req.get(req.id, []):
            p = all_projects.get(lead.project_id)
            if p:
                parts.append(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for req in requests_list:
            await message.answer(render_buyer_request_summary(req.what, req.budget, req.contact))
            for lead in lead_by_req.get(req.id, []):
                p = all_projects.get(lead.project_id)
                if p:
                    await message.answer(
                        render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                    )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


@router.message(Command("leads"))
async def cmd_leads_v2(message: Message, state: FSMContext) -> None:
    """V2 /leads handler -> show seller leads."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("cmd=leads user_id=%s action=show_leads", user_id)
    
    from src.bot.services import list_leads_for_seller
    from src.bot.renderer import render_project_post
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    my_projects, leads_list = await list_leads_for_seller(user.id)
    
    if not my_projects or not leads_list:
        await message.answer(
            get_copy("LEADS_HEADER") + get_copy("LEADS_EMPTY"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    header = get_copy("LEADS_HEADER")
    proj_by_id = {p.id: p for p in my_projects}
    parts = [header]
    
    for lead in leads_list:
        p = proj_by_id.get(lead.project_id)
        if p:
            parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for lead in leads_list:
            p = proj_by_id.get(lead.project_id)
            if p:
                await message.answer(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


# =============================================================================
# Reply Keyboard Button Handlers (text message triggers)
# =============================================================================

@router.message(F.text == REPLY_BTN_CURRENT_STEP)
async def handle_reply_current_step(message: Message, state: FSMContext) -> None:
    """Handle '📌 Текущий шаг' reply button -> show current step info."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=current_step user_id=%s", user_id)
    
    step_info = await _get_step_info(state)
    text = get_copy("V2_MENU_STEP_SCREEN").format(step_info=step_info)
    await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


@router.message(F.text == REPLY_BTN_PROJECT)
async def handle_reply_project(message: Message, state: FSMContext) -> None:
    """Handle '📁 Проект' reply button -> show project commands screen."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=project user_id=%s", user_id)
    
    text = get_copy("V2_MENU_PROJECT_SCREEN")
    await message.answer(text, reply_markup=kb_project_screen(), parse_mode="HTML")


@router.message(F.text == REPLY_BTN_RESTART)
async def handle_reply_restart(message: Message, state: FSMContext) -> None:
    """Handle '♻️ Начать заново' reply button -> show restart confirmation."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=restart user_id=%s", user_id)
    
    text = get_copy("V2_MENU_RESTART_CONFIRM_TEXT")
    await message.answer(text, reply_markup=kb_restart_confirm_new(), parse_mode="HTML")


@router.message(F.text == REPLY_BTN_MY_PROJECTS)
async def handle_reply_my_projects(message: Message, state: FSMContext) -> None:
    """Handle '📄 Мои проекты' reply button -> call /catalog logic."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=my_projects user_id=%s", user_id)
    
    # Call existing catalog logic
    from src.bot.services import list_approved_projects
    from src.bot.renderer import render_project_post
    
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    projects = await list_approved_projects()
    if not projects:
        text = get_copy("CATALOG_HEADER") + get_copy("CATALOG_EMPTY")
        await message.answer(text, reply_markup=kb_to_menu_only())
        return
    
    header = get_copy("CATALOG_HEADER")
    parts = [header]
    for p in projects:
        parts.append(
            render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
        )
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for p in projects:
            await message.answer(
                render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
            )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


@router.message(F.text == REPLY_BTN_CREATE)
async def handle_reply_create(message: Message, state: FSMContext) -> None:
    """Handle '➕ Создать проект' reply button -> start wizard."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=create_project user_id=%s", user_id)
    
    # Start wizard (create new submission)
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    sub = await create_submission(user.id, current_step="q1")
    await state.update_data(**{
        DATA_SUBMISSION_ID: str(sub.id),
        DATA_STEP_KEY: "q1",
    })
    await state.set_state(V2FormSteps.answering)
    
    # Show first step
    from src.v2.routers.form import show_question
    await message.answer(
        get_copy("V2_MENU_HINT").strip(),
        reply_markup=persistent_reply_kb(),
    )
    await show_question(message, state, "q1")
    
    logger.info("create_project_done user_id=%s submission_id=%s", user_id, sub.id)


@router.message(F.text == REPLY_BTN_HELP)
async def handle_reply_help(message: Message, state: FSMContext) -> None:
    """Handle '❓ Помощь / Команды' reply button -> show help text."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=help user_id=%s", user_id)
    
    text = get_copy("V2_MENU_HELP_SCREEN")
    await message.answer(text, reply_markup=kb_to_menu_only(), parse_mode="HTML")


@router.message(F.text == REPLY_BTN_CATALOG)
async def handle_reply_catalog(message: Message, state: FSMContext) -> None:
    """Handle '📚 Каталог' reply button -> call /catalog logic."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=catalog user_id=%s action=show_catalog", user_id)
    
    # Same logic as handle_reply_my_projects
    from src.bot.services import list_approved_projects
    from src.bot.renderer import render_project_post
    
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    projects = await list_approved_projects()
    if not projects:
        text = get_copy("CATALOG_HEADER") + get_copy("CATALOG_EMPTY")
        await message.answer(text, reply_markup=kb_to_menu_only())
        return
    
    header = get_copy("CATALOG_HEADER")
    parts = [header]
    for p in projects:
        parts.append(
            render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
        )
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for p in projects:
            await message.answer(
                render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
            )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


@router.message(F.text == REPLY_BTN_REQUEST)
async def handle_reply_request(message: Message, state: FSMContext) -> None:
    """Handle '✍️ Реквест' reply button -> start buyer request flow."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=request user_id=%s action=start_buyer_request", user_id)
    
    # Start buyer request flow
    from src.bot.fsm.states import BuyerRequestStates
    
    await state.clear()
    await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await state.set_state(BuyerRequestStates.what)
    await message.answer(get_copy("REQUEST_START"))
    await message.answer(get_copy("REQUEST_Q1_WHAT"))


@router.message(F.text == REPLY_BTN_MY_REQUESTS)
async def handle_reply_my_requests(message: Message, state: FSMContext) -> None:
    """Handle '🧾 Мои реквесты' reply button -> call /my_requests logic."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=my_requests user_id=%s action=show_my_requests", user_id)
    
    # Call existing logic
    from src.bot.services import list_my_requests_with_projects
    from src.bot.renderer import render_buyer_request_summary, render_project_post
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    requests_list, leads_list, all_projects = await list_my_requests_with_projects(user.id)
    
    if not requests_list:
        await message.answer(
            get_copy("MY_REQUESTS_HEADER") + get_copy("MY_REQUESTS_EMPTY"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    header = get_copy("MY_REQUESTS_HEADER")
    lead_by_req: dict = {}
    for lead in leads_list:
        if lead.buyer_request_id:
            lead_by_req.setdefault(lead.buyer_request_id, []).append(lead)
    
    parts = [header]
    for req in requests_list:
        parts.append(render_buyer_request_summary(req.what, req.budget, req.contact))
        for lead in lead_by_req.get(req.id, []):
            p = all_projects.get(lead.project_id)
            if p:
                parts.append(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for req in requests_list:
            await message.answer(render_buyer_request_summary(req.what, req.budget, req.contact))
            for lead in lead_by_req.get(req.id, []):
                p = all_projects.get(lead.project_id)
                if p:
                    await message.answer(
                        render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                    )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


@router.message(F.text == REPLY_BTN_LEADS)
async def handle_reply_leads(message: Message, state: FSMContext) -> None:
    """Handle '👥 Лиды' reply button -> call /leads logic."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("reply_btn=leads user_id=%s action=show_leads", user_id)
    
    # Call existing logic
    from src.bot.services import list_leads_for_seller
    from src.bot.renderer import render_project_post
    
    user = await get_or_create_user(
        user_id,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    
    my_projects, leads_list = await list_leads_for_seller(user.id)
    
    if not my_projects or not leads_list:
        await message.answer(
            get_copy("LEADS_HEADER") + get_copy("LEADS_EMPTY"),
            reply_markup=kb_to_menu_only(),
        )
        return
    
    header = get_copy("LEADS_HEADER")
    proj_by_id = {p.id: p for p in my_projects}
    parts = [header]
    
    for lead in leads_list:
        p = proj_by_id.get(lead.project_id)
        if p:
            parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    
    text = "\n".join(parts)
    
    if len(text) > 4000:
        await message.answer(header)
        for lead in leads_list:
            p = proj_by_id.get(lead.project_id)
            if p:
                await message.answer(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
        await message.answer("—", reply_markup=kb_to_menu_only())
    else:
        await message.answer(text, reply_markup=kb_to_menu_only())


# =============================================================================
# Legacy callback handlers (backward compat for old menu:* namespace)
# =============================================================================

@router.callback_query(F.data == "menu:back_to_menu")
async def cb_legacy_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:back_to_menu -> m:root"""
    await cb_menu_root(callback, state)


@router.callback_query(F.data == "menu:continue")
async def cb_legacy_continue(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:continue -> m:cmd:resume"""
    await cb_cmd_resume(callback, state)


@router.callback_query(F.data == "menu:create")
async def cb_legacy_create(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:create -> m:create_project"""
    await cb_menu_create_project(callback, state)


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
    """Legacy: menu:posts -> m:my_projects"""
    await cb_menu_my_projects(callback, state)


@router.callback_query(F.data == "menu:settings")
async def cb_legacy_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:settings -> show help (settings not implemented)."""
    await cb_menu_help(callback, state)


@router.callback_query(F.data == "menu:preview")
async def cb_legacy_preview(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: menu:preview -> m:cmd:resume (shows preview if at preview step)."""
    await cb_cmd_resume(callback, state)
