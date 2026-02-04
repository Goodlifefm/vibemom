"""
V2 menu: persistent ☰ Меню button and cabinet from any state.
High-priority router — catches menu triggers before wizard handlers.

Mode concept:
- FSMContext data["mode"] in {"wizard", "menu", "browse", "admin"}
- Wizard state is preserved when entering menu mode
- User can return to wizard from menu

Callback namespace:
- menu:* for menu actions (continue, preview, drafts, posts, settings, help)
- wiz:* for wizard actions (handled in form.py)
- post:* for publish/moderation actions (handled in moderation.py)
"""
import logging
import uuid
from typing import Literal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    persistent_reply_kb,
    cabinet_menu_inline_kb,
    menu_back_kb,
    drafts_list_kb,
    publications_list_kb,
    CB_MENU,
)
from src.bot.messages import get_copy
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

# Mode type for FSMContext data
ModeType = Literal["wizard", "menu", "browse", "admin"]

# FSMContext data keys
DATA_MODE = "mode"
DATA_SUBMISSION_ID = "submission_id"
DATA_STEP_KEY = "current_step_key"
DATA_SAVED_STEP = "saved_wizard_step"


# =============================================================================
# Helper functions
# =============================================================================

async def get_mode(state: FSMContext) -> ModeType:
    """Get current mode from FSMContext data."""
    data = await state.get_data()
    return data.get(DATA_MODE, "wizard")


async def set_mode(state: FSMContext, mode: ModeType) -> None:
    """Set mode in FSMContext data."""
    await state.update_data(**{DATA_MODE: mode})


async def has_active_wizard(state: FSMContext) -> bool:
    """Check if user has an active wizard session."""
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY)
    return bool(sid and step_key)


async def save_wizard_state(state: FSMContext) -> None:
    """Save current wizard step before entering menu mode."""
    data = await state.get_data()
    step_key = data.get(DATA_STEP_KEY)
    if step_key:
        await state.update_data(**{DATA_SAVED_STEP: step_key})


def _build_menu_status_text(
    project_name: str | None,
    step_key: str | None,
    step_num: int,
    total: int,
) -> str:
    """Build status line for menu screen."""
    project = project_name or get_copy("V2_MENU_STATUS_NO_PROJECT").strip()
    if step_key and get_step(step_key) and total > 0:
        step_str = f"{step_num} из {total}"
        progress = round(step_num / total * 100)
    else:
        step_str = "—"
        progress = 0
    
    lines = [
        f"📁 <b>{get_copy('V2_MENU_SCREEN_TITLE').strip()}</b>",
        "",
        f"Проект: {project}",
    ]
    if step_key:
        lines.append(f"Шаг: {step_str} ({progress}%)")
    
    return "\n".join(lines)


async def send_with_reply_kb(message: Message, text: str, **kwargs) -> Message:
    """Send message with persistent reply keyboard."""
    return await message.answer(text, reply_markup=persistent_reply_kb(), **kwargs)


# =============================================================================
# Main menu screen
# =============================================================================

async def show_cabinet_menu(
    target: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Show the main cabinet menu screen.
    
    - Displays status (project, step, progress) if wizard is active
    - Shows inline keyboard with menu options
    - Attaches persistent reply keyboard
    """
    message = target.message if isinstance(target, CallbackQuery) else target
    user_id = target.from_user.id if target.from_user else 0
    
    # Save wizard state before entering menu
    await save_wizard_state(state)
    await set_mode(state, "menu")
    
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY) or ""
    
    # Gather info for status display
    step_num, total = 1, len(STEP_KEYS)
    project_name = None
    has_wizard = bool(sid and step_key)
    
    if sid:
        try:
            sub = await get_submission(uuid.UUID(sid))
            if sub:
                project_name = (sub.answers or {}).get("title", "").strip() or None
                if step_key and get_step(step_key):
                    step_num = get_step_index(step_key) + 1
        except (ValueError, TypeError):
            pass
    
    # Check if user has drafts/publications
    has_drafts = False
    has_publications = False
    try:
        user = await get_or_create_user(
            user_id,
            target.from_user.username if target.from_user else None,
            target.from_user.full_name if target.from_user else None,
        )
        subs = await list_submissions_by_user(user.id, limit=10)
        for s in subs:
            if s.status == ProjectStatus.draft:
                has_drafts = True
            elif s.status == ProjectStatus.approved:
                has_publications = True
    except Exception:
        pass
    
    # Build menu text
    status_text = _build_menu_status_text(project_name, step_key, step_num, total)
    
    # Build inline keyboard
    kb = cabinet_menu_inline_kb(
        has_active_wizard=has_wizard,
        has_drafts=has_drafts,
        has_publications=has_publications,
    )
    
    # Send menu message with inline keyboard
    await message.answer(status_text, reply_markup=kb, parse_mode="HTML")
    
    # Send persistent reply keyboard message
    await message.answer(
        get_copy("V2_MENU_HINT").strip(),
        reply_markup=persistent_reply_kb(),
    )
    
    logger.info("menu_open user_id=%s mode=menu", user_id)


# =============================================================================
# Menu trigger handlers (text "☰ Меню", "🏠 Меню", "Меню", /menu)
# =============================================================================

@router.message(F.text.in_(["☰ Меню", "🏠 Меню", "Меню"]))
@router.message(Command("menu"))
async def handle_menu_trigger(message: Message, state: FSMContext) -> None:
    """
    Global escape hatch: show cabinet from any state.
    Works from wizard steps, preview, anywhere.
    Preserves draft (submission_id) so user can continue.
    """
    await show_cabinet_menu(message, state)


# =============================================================================
# Menu callback handlers (menu:*)
# =============================================================================

@router.callback_query(F.data == f"{CB_MENU}:continue")
async def cb_menu_continue(callback: CallbackQuery, state: FSMContext) -> None:
    """Continue wizard: return to current/saved step."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_continue user_id=%s", user_id)
    
    await set_mode(state, "wizard")
    
    # Use render_current_step to restore wizard
    await render_current_step(callback.message, state)


@router.callback_query(F.data == f"{CB_MENU}:preview")
async def cb_menu_preview(callback: CallbackQuery, state: FSMContext) -> None:
    """Show preview from menu."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_preview user_id=%s", user_id)
    
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    
    if not sid:
        await callback.message.answer(
            get_copy("V2_MENU_NO_ACTIVE_WIZARD").strip(),
            reply_markup=menu_back_kb(),
        )
        return
    
    # Delegate to preview router
    from src.v2.routers.preview import show_preview
    await set_mode(state, "wizard")
    await show_preview(callback.message, state)


@router.callback_query(F.data == f"{CB_MENU}:drafts")
async def cb_menu_drafts(callback: CallbackQuery, state: FSMContext) -> None:
    """Show drafts list."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_drafts user_id=%s", user_id)
    
    try:
        user = await get_or_create_user(
            user_id,
            callback.from_user.username if callback.from_user else None,
            callback.from_user.full_name if callback.from_user else None,
        )
        subs = await list_submissions_by_user(user.id, limit=10)
        drafts = [
            (
                (s.answers or {}).get("title", "") or "Без названия",
                str(s.id),
            )
            for s in subs
            if s.status == ProjectStatus.draft
        ]
    except Exception:
        drafts = []
    
    if not drafts:
        await callback.message.answer(
            f"<b>{get_copy('V2_DRAFTS_HEADER').strip()}</b>\n\n{get_copy('V2_DRAFTS_EMPTY').strip()}",
            reply_markup=menu_back_kb(),
            parse_mode="HTML",
        )
        return
    
    text = f"<b>{get_copy('V2_DRAFTS_HEADER').strip()}</b>\n\nВыберите черновик:"
    await callback.message.answer(
        text,
        reply_markup=drafts_list_kb(drafts),
        parse_mode="HTML",
    )


@router.callback_query(F.data == f"{CB_MENU}:posts")
async def cb_menu_posts(callback: CallbackQuery, state: FSMContext) -> None:
    """Show publications list."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_posts user_id=%s", user_id)
    
    try:
        user = await get_or_create_user(
            user_id,
            callback.from_user.username if callback.from_user else None,
            callback.from_user.full_name if callback.from_user else None,
        )
        subs = await list_submissions_by_user(user.id, limit=10)
        publications = [
            (
                (s.answers or {}).get("title", "") or "Без названия",
                str(s.id),
            )
            for s in subs
            if s.status == ProjectStatus.approved
        ]
    except Exception:
        publications = []
    
    if not publications:
        await callback.message.answer(
            f"<b>{get_copy('V2_PUBLICATIONS_HEADER').strip()}</b>\n\n{get_copy('V2_PUBLICATIONS_EMPTY').strip()}",
            reply_markup=menu_back_kb(),
            parse_mode="HTML",
        )
        return
    
    text = f"<b>{get_copy('V2_PUBLICATIONS_HEADER').strip()}</b>\n\nВаши публикации:"
    await callback.message.answer(
        text,
        reply_markup=publications_list_kb(publications),
        parse_mode="HTML",
    )


@router.callback_query(F.data == f"{CB_MENU}:settings")
async def cb_menu_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """Show settings (placeholder)."""
    await callback.answer()
    logger.info("menu_settings user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    await callback.message.answer(
        f"<b>{get_copy('V2_SETTINGS_HEADER').strip()}</b>\n\n{get_copy('V2_SETTINGS_PLACEHOLDER').strip()}",
        reply_markup=menu_back_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == f"{CB_MENU}:help")
async def cb_menu_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Show help text."""
    await callback.answer()
    logger.info("menu_help user_id=%s", callback.from_user.id if callback.from_user else 0)
    
    await callback.message.answer(
        get_copy("V2_HELP_TEXT").strip(),
        reply_markup=menu_back_kb(),
    )


@router.callback_query(F.data == f"{CB_MENU}:back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to main menu from placeholder screens."""
    await callback.answer()
    await show_cabinet_menu(callback, state)


@router.callback_query(F.data == f"{CB_MENU}:create")
async def cb_menu_create(callback: CallbackQuery, state: FSMContext) -> None:
    """Create new project from menu."""
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("menu_create user_id=%s", user_id)
    
    user = await get_or_create_user(
        user_id,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    
    # Create new submission
    sub = await create_submission(user.id, current_step="q1")
    await state.update_data(**{
        DATA_SUBMISSION_ID: str(sub.id),
        DATA_STEP_KEY: "q1",
        DATA_MODE: "wizard",
    })
    await state.set_state(V2FormSteps.answering)
    
    # Show first step
    from src.v2.routers.form import show_question
    await callback.message.answer(
        get_copy("V2_MENU_HINT").strip(),
        reply_markup=persistent_reply_kb(),
    )
    await show_question(callback.message, state, "q1")
    
    logger.info("menu_create_done user_id=%s submission_id=%s", user_id, sub.id)


@router.callback_query(F.data.startswith(f"{CB_MENU}:open_draft:"))
async def cb_open_draft(callback: CallbackQuery, state: FSMContext) -> None:
    """Open a draft from drafts list."""
    await callback.answer()
    
    try:
        sid_str = callback.data.split(":", 2)[2]
        sub_id = uuid.UUID(sid_str)
    except (ValueError, IndexError):
        await show_cabinet_menu(callback, state)
        return
    
    sub = await get_submission(sub_id)
    if not sub:
        await show_cabinet_menu(callback, state)
        return
    
    # Set as current submission and continue wizard
    step_key = sub.current_step or "q1"
    await state.update_data(**{
        DATA_SUBMISSION_ID: str(sub.id),
        DATA_STEP_KEY: step_key,
        DATA_MODE: "wizard",
    })
    await state.set_state(V2FormSteps.answering)
    
    await render_current_step(callback.message, state)


@router.callback_query(F.data.startswith(f"{CB_MENU}:view_post:"))
async def cb_view_post(callback: CallbackQuery, state: FSMContext) -> None:
    """View a publication."""
    await callback.answer()
    
    try:
        sid_str = callback.data.split(":", 2)[2]
        sub_id = uuid.UUID(sid_str)
    except (ValueError, IndexError):
        await show_cabinet_menu(callback, state)
        return
    
    sub = await get_submission(sub_id)
    if not sub:
        await callback.message.answer(
            "Публикация не найдена.",
            reply_markup=menu_back_kb(),
        )
        return
    
    # Render the post
    from src.v2.rendering import render_submission_to_html
    body_html = render_submission_to_html(sub.answers or {})
    await callback.message.answer(
        body_html,
        reply_markup=menu_back_kb(),
        parse_mode="HTML",
    )


# =============================================================================
# Render current wizard step (helper for menu:continue and resume)
# =============================================================================

async def render_current_step(message: Message, state: FSMContext) -> None:
    """
    Render the current wizard step.
    Reads current_step_key from state and shows the appropriate question.
    Always attaches persistent reply keyboard.
    """
    data = await state.get_data()
    sid = data.get(DATA_SUBMISSION_ID)
    step_key = data.get(DATA_STEP_KEY) or data.get(DATA_SAVED_STEP)
    
    if not sid:
        # No active wizard, show menu
        await show_cabinet_menu(message, state)
        return
    
    if not step_key or not get_step(step_key):
        # Try to get step from submission
        try:
            sub = await get_submission(uuid.UUID(sid))
            if sub and sub.current_step:
                step_key = sub.current_step
                await state.update_data(**{DATA_STEP_KEY: step_key})
        except (ValueError, TypeError):
            pass
    
    if not step_key or not get_step(step_key):
        # Still no valid step, show first step
        step_key = "q1"
        await state.update_data(**{DATA_STEP_KEY: step_key})
    
    # Set wizard mode
    await set_mode(state, "wizard")
    await state.set_state(V2FormSteps.answering)
    
    # Handle preview step
    if step_key == "preview":
        from src.v2.routers.preview import show_preview
        await show_preview(message, state)
        return
    
    # Show form step
    from src.v2.routers.form import show_question
    await message.answer(
        get_copy("V2_MENU_HINT").strip(),
        reply_markup=persistent_reply_kb(),
    )
    await show_question(message, state, step_key)


# =============================================================================
# Legacy compatibility handlers (v2menu:* prefix)
# =============================================================================

# Import old callbacks module for backward compat
from src.v2.ui import callbacks as old_callbacks

@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_RESUME))
async def cb_legacy_resume(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:resume -> menu:continue"""
    await callback.answer()
    await cb_menu_continue(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_RESTART))
async def cb_legacy_restart(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:restart -> confirm restart."""
    await callback.answer()
    from src.v2.ui.keyboards import kb_restart_confirm
    await callback.message.answer(
        get_copy("V2_MENU_RESTART_CONFIRM").strip(),
        reply_markup=kb_restart_confirm(),
    )


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_RESTART_YES))
async def cb_legacy_restart_yes(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:restart_yes -> clear state and show menu."""
    await callback.answer()
    await state.clear()
    logger.info("menu_restart_yes user_id=%s", callback.from_user.id if callback.from_user else 0)
    await show_cabinet_menu(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_RESTART_NO))
async def cb_legacy_restart_no(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:restart_no -> return to menu."""
    await callback.answer()
    await show_cabinet_menu(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_PROJECTS))
async def cb_legacy_projects(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:projects -> drafts."""
    await cb_menu_drafts(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_CREATE))
async def cb_legacy_create(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:create -> create."""
    await cb_menu_create(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_HELP))
async def cb_legacy_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:help -> help."""
    await cb_menu_help(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_CURRENT_STEP))
async def cb_legacy_current_step(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:current_step -> continue wizard."""
    await cb_menu_continue(callback, state)


@router.callback_query(F.data == old_callbacks.menu(old_callbacks.MENU_PROJECT))
async def cb_legacy_project(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy: v2menu:project -> preview."""
    await cb_menu_preview(callback, state)


# Legacy delete handlers (keep for backward compat)
@router.callback_query(F.data.startswith(old_callbacks.menu(old_callbacks.MENU_DELETE) + ":"))
async def cb_legacy_delete(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy delete confirmation."""
    await callback.answer()
    from src.v2.ui.keyboards import delete_confirm_kb
    from src.v2.ui import copy
    
    try:
        sid_str = callback.data.split(":", 2)[2]
        sub_id = uuid.UUID(sid_str)
    except (ValueError, IndexError):
        await show_cabinet_menu(callback, state)
        return
    
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    sub = await get_submission(sub_id)
    if not sub or sub.user_id != user.id:
        await show_cabinet_menu(callback, state)
        return
    
    title = (sub.answers or {}).get("title", "Без названия") or "Без названия"
    confirm_text = get_copy("V2_DELETE_CONFIRM").format(title=title[:50])
    await callback.message.answer(
        confirm_text,
        reply_markup=delete_confirm_kb(sub_id),
    )


@router.callback_query(F.data.startswith(old_callbacks.menu(old_callbacks.MENU_DELETE_YES) + ":"))
async def cb_legacy_delete_yes(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy delete yes."""
    await callback.answer()
    from src.v2.repo import delete_submission
    
    try:
        sid_str = callback.data.split(":", 2)[2]
        sub_id = uuid.UUID(sid_str)
    except (ValueError, IndexError):
        await show_cabinet_menu(callback, state)
        return
    
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    deleted = await delete_submission(sub_id, user.id)
    if deleted:
        data = await state.get_data()
        if data.get(DATA_SUBMISSION_ID) == str(sub_id):
            await state.update_data(**{DATA_SUBMISSION_ID: None, DATA_STEP_KEY: None})
        await callback.message.answer(get_copy("V2_DELETED").strip())
    await show_cabinet_menu(callback, state)


@router.callback_query(F.data.startswith(old_callbacks.menu(old_callbacks.MENU_DELETE_NO) + ":"))
async def cb_legacy_delete_no(callback: CallbackQuery, state: FSMContext) -> None:
    """Legacy delete no."""
    await callback.answer()
    await callback.message.answer(get_copy("V2_DELETE_CANCELLED").strip())
    await show_cabinet_menu(callback, state)
