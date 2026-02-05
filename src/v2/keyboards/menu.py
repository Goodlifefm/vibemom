"""
Menu inline keyboards: main menu card, sub-screens with edit_message_text.
Callback namespace: m:* (m:root, m:step, m:project, m:help, etc.)

Main Menu Card UX:
- Single message + inline keyboard
- All interactions edit the same message (no new messages)
- "✕ Закрыть" deletes or edits to "Меню закрыто"
"""
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logger = logging.getLogger(__name__)

# Callback prefix for menu
CB_PREFIX = "m"

# Legacy alias for backward compat
CB_MENU = "menu"


def _cb(*parts: str) -> str:
    """Build callback_data: m:{parts...}"""
    return ":".join([CB_PREFIX] + list(parts))


def _get_webapp_url() -> str | None:
    """Get WEBAPP_URL from settings, return None if not configured."""
    try:
        from src.bot.config import Settings
        settings = Settings()
        url = settings.webapp_url.strip()
        if url and url.startswith("https://"):
            return url
        return None
    except Exception:
        return None


# =============================================================================
# Main Cabinet Menu Keyboard (unified entrypoint)
# =============================================================================

def kb_cabinet_menu(*, has_active_draft: bool = False) -> InlineKeyboardMarkup:
    """
    Unified cabinet menu keyboard (the ONE menu).
    
    Layout (exactly as specified):
    - 🏠 Главное меню (m:home)
    - ▶️ Продолжить заполнение (m:resume) — only if has_active_draft
    - 📁 Мои проекты (m:my_projects)
    - 🏪 Каталог (m:catalog)
    - 📥 Реквесты (m:request)
    - 📊 Мои реквесты / Лиды (m:my_requests_leads)
    - 📱 Кабинет (Mini App) — WebApp button if configured
    - ✕ Закрыть (m:close)
    """
    rows = []
    
    # 🏠 Главное меню
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data=_cb("home"))])
    
    # ▶️ Продолжить заполнение (only if draft exists)
    if has_active_draft:
        rows.append([InlineKeyboardButton(text="▶️ Продолжить заполнение", callback_data=_cb("resume"))])
    
    # 📁 Мои проекты
    rows.append([InlineKeyboardButton(text="📁 Мои проекты", callback_data=_cb("my_projects"))])
    
    # 🏪 Каталог | 📥 Реквесты (one row)
    rows.append([
        InlineKeyboardButton(text="🏪 Каталог", callback_data=_cb("catalog")),
        InlineKeyboardButton(text="📥 Реквесты", callback_data=_cb("request")),
    ])
    
    # 📊 Мои реквесты / Лиды
    rows.append([InlineKeyboardButton(text="📊 Мои реквесты / Лиды", callback_data=_cb("my_requests_leads"))])
    
    # 📱 Кабинет (Mini App) — WebApp button
    webapp_url = _get_webapp_url()
    if webapp_url:
        rows.append([InlineKeyboardButton(
            text="📱 Кабинет (Mini App)",
            web_app=WebAppInfo(url=webapp_url),
        )])
    
    # ✕ Закрыть
    rows.append([InlineKeyboardButton(text="✕ Закрыть", callback_data=_cb("close"))])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_main_menu() -> InlineKeyboardMarkup:
    """
    Legacy main menu card keyboard. Use kb_cabinet_menu() for unified menu.
    Kept for backward compatibility.
    """
    return kb_cabinet_menu(has_active_draft=False)


# =============================================================================
# Sub-screen Keyboards (with Back and Close)
# =============================================================================

def kb_back_close() -> InlineKeyboardMarkup:
    """Back and Close buttons for sub-screens."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅ Назад", callback_data=_cb("back")),
            InlineKeyboardButton(text="✕ Закрыть", callback_data=_cb("close")),
        ],
    ])


def kb_to_menu_only() -> InlineKeyboardMarkup:
    """Single 'В меню' button for external handlers that sent new messages."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ В меню", callback_data=_cb("root"))],
    ])


# =============================================================================
# Project Screen Keyboard (📁 Проект)
# =============================================================================

def kb_project_screen() -> InlineKeyboardMarkup:
    """
    Project screen with command buttons.
    
    Commands:
    - /start — главное меню (m:cmd:start)
    - /menu — открыть меню (m:root)
    - /resume — продолжить заполнение (m:cmd:resume)
    - /catalog — каталог проектов (m:cmd:catalog)
    - /request — оставить заявку (m:cmd:request)
    - /my_requests — мои заявки (m:cmd:my_requests)
    - /leads — мои лиды (m:cmd:leads)
    + Back/Close row
    """
    rows = [
        [InlineKeyboardButton(text="/start — главное меню", callback_data=_cb("cmd", "start"))],
        [InlineKeyboardButton(text="/menu — меню", callback_data=_cb("root"))],
        [InlineKeyboardButton(text="/resume — продолжить", callback_data=_cb("cmd", "resume"))],
        [InlineKeyboardButton(text="/catalog — каталог", callback_data=_cb("cmd", "catalog"))],
        [InlineKeyboardButton(text="/request — заявка", callback_data=_cb("cmd", "request"))],
        [InlineKeyboardButton(text="/my_requests — мои заявки", callback_data=_cb("cmd", "my_requests"))],
        [InlineKeyboardButton(text="/leads — мои лиды", callback_data=_cb("cmd", "leads"))],
        [
            InlineKeyboardButton(text="⬅ Назад", callback_data=_cb("back")),
            InlineKeyboardButton(text="✕ Закрыть", callback_data=_cb("close")),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# =============================================================================
# Restart Confirmation Keyboard (new m:* format)
# =============================================================================

def kb_restart_confirm_new() -> InlineKeyboardMarkup:
    """Restart confirmation with new m:* callbacks."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, начать заново", callback_data=_cb("restart_yes"))],
        [InlineKeyboardButton(text="❌ Нет, вернуться", callback_data=_cb("back"))],
    ])


# =============================================================================
# Legacy keyboards (keep for backward compatibility with tests)
# Uses old CB_MENU = "menu" prefix
# =============================================================================

def _cb_legacy(action: str, *args: str) -> str:
    """Build legacy callback_data: menu:{action}:{args...}"""
    parts = [CB_MENU, action] + list(args)
    return ":".join(parts)


def kb_cabinet_tiles(
    *,
    has_active_wizard: bool = False,
    has_drafts: bool = False,
    has_publications: bool = False,
) -> InlineKeyboardMarkup:
    """
    Legacy cabinet menu with old menu:* callbacks.
    Kept for backward compatibility with tests.
    """
    rows = []
    
    if has_active_wizard:
        rows.append([InlineKeyboardButton(
            text="🧩 Продолжить заполнение",
            callback_data=_cb_legacy("continue"),
        )])
        rows.append([InlineKeyboardButton(
            text="👁 Предпросмотр",
            callback_data=_cb_legacy("preview"),
        )])
    
    rows.append([
        InlineKeyboardButton(text="🗂 Черновики", callback_data=_cb_legacy("drafts")),
        InlineKeyboardButton(text="📌 Публикации", callback_data=_cb_legacy("posts")),
    ])
    
    rows.append([
        InlineKeyboardButton(text="⚙️ Настройки", callback_data=_cb_legacy("settings")),
        InlineKeyboardButton(text="❓ Помощь", callback_data=_cb_legacy("help")),
    ])
    
    if has_active_wizard:
        rows.append([InlineKeyboardButton(
            text="↩️ Вернуться",
            callback_data=_cb_legacy("continue"),
        )])
    else:
        rows.append([InlineKeyboardButton(
            text="➕ Создать проект",
            callback_data=_cb_legacy("create"),
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_menu_back() -> InlineKeyboardMarkup:
    """Legacy: simple back button with menu:back_to_menu callback."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="↩️ Вернуться",
            callback_data=_cb_legacy("back_to_menu"),
        )],
    ])


def kb_drafts_list(drafts: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Legacy: drafts list with menu:open_draft callbacks."""
    rows = []
    for title, sid in drafts:
        display = (title[:30] if title else "Без названия")
        rows.append([InlineKeyboardButton(
            text=f"📝 {display}",
            callback_data=_cb_legacy("open_draft", sid),
        )])
    rows.append([InlineKeyboardButton(
        text="↩️ Вернуться",
        callback_data=_cb_legacy("back_to_menu"),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_publications_list(publications: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Legacy: publications list with menu:view_post callbacks."""
    rows = []
    for title, sid in publications:
        display = (title[:30] if title else "Без названия")
        rows.append([InlineKeyboardButton(
            text=f"📌 {display}",
            callback_data=_cb_legacy("view_post", sid),
        )])
    rows.append([InlineKeyboardButton(
        text="↩️ Вернуться",
        callback_data=_cb_legacy("back_to_menu"),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_delete_confirm(submission_id: str) -> InlineKeyboardMarkup:
    """Legacy: delete confirmation with menu:delete_yes/no callbacks."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data=_cb_legacy("delete_yes", submission_id)),
            InlineKeyboardButton(text="Нет", callback_data=_cb_legacy("delete_no", submission_id)),
        ],
    ])


def kb_restart_confirm() -> InlineKeyboardMarkup:
    """Legacy: restart confirmation with menu:restart_yes/no callbacks."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data=_cb_legacy("restart_yes"))],
        [InlineKeyboardButton(text="Нет", callback_data=_cb_legacy("restart_no"))],
    ])
