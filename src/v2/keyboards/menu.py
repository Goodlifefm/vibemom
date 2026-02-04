"""
Menu inline keyboards: cabinet tiles, drafts/publications lists.
Callback prefixes: menu:*
Centralized keyboard builders for menu screens.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.v2.ui.copy import V2Copy

# Callback prefix for menu actions
CB_MENU = "menu"


def _cb(action: str, *args: str) -> str:
    """Build menu callback_data: menu:{action}:{args...}"""
    parts = [CB_MENU, action] + list(args)
    return ":".join(parts)


def kb_cabinet_tiles(
    *,
    has_active_wizard: bool = False,
    has_drafts: bool = False,
    has_publications: bool = False,
) -> InlineKeyboardMarkup:
    """
    Main cabinet menu with tile-style inline buttons.
    
    Layout:
    - Row 1: Continue wizard (if active)
    - Row 2: Preview (if active)
    - Row 3: Drafts | Publications (tile pair)
    - Row 4: Settings | Help (tile pair)
    - Row 5: Back/Continue OR Create new
    
    Callbacks: menu:continue, menu:preview, menu:drafts, menu:posts, etc.
    """
    rows = []
    
    # Continue wizard (only if active)
    if has_active_wizard:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_CONTINUE_WIZARD).strip(),
            callback_data=_cb("continue"),
        )])
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_PREVIEW).strip(),
            callback_data=_cb("preview"),
        )])
    
    # Drafts | Publications tile row
    rows.append([
        InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_DRAFTS).strip(),
            callback_data=_cb("drafts"),
        ),
        InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_PUBLICATIONS).strip(),
            callback_data=_cb("posts"),
        ),
    ])
    
    # Settings | Help tile row
    rows.append([
        InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_SETTINGS).strip(),
            callback_data=_cb("settings"),
        ),
        InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_HELP_BTN).strip(),
            callback_data=_cb("help"),
        ),
    ])
    
    # Bottom row: Back (if wizard) or Create (if no wizard)
    if has_active_wizard:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_BACK).strip(),
            callback_data=_cb("continue"),
        )])
    else:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_CREATE).strip(),
            callback_data=_cb("create"),
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_menu_back() -> InlineKeyboardMarkup:
    """Simple 'back to menu' button for sub-screens."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_BACK).strip(),
            callback_data=_cb("back_to_menu"),
        )],
    ])


def kb_drafts_list(drafts: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """
    Drafts list with open buttons.
    
    Args:
        drafts: List of (title, submission_id) tuples
    
    Callbacks: menu:open_draft:{id}
    """
    rows = []
    for title, sid in drafts:
        display = (title[:30] if title else "Без названия")
        rows.append([InlineKeyboardButton(
            text=f"📝 {display}",
            callback_data=_cb("open_draft", sid),
        )])
    rows.append([InlineKeyboardButton(
        text=V2Copy.get(V2Copy.MENU_BACK).strip(),
        callback_data=_cb("back_to_menu"),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_publications_list(publications: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """
    Publications list with view buttons.
    
    Args:
        publications: List of (title, submission_id) tuples
    
    Callbacks: menu:view_post:{id}
    """
    rows = []
    for title, sid in publications:
        display = (title[:30] if title else "Без названия")
        rows.append([InlineKeyboardButton(
            text=f"📌 {display}",
            callback_data=_cb("view_post", sid),
        )])
    rows.append([InlineKeyboardButton(
        text=V2Copy.get(V2Copy.MENU_BACK).strip(),
        callback_data=_cb("back_to_menu"),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_restart_confirm() -> InlineKeyboardMarkup:
    """Confirmation for 'Start over' action."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.YES_BUTTON).strip(),
            callback_data=_cb("restart_yes"),
        )],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.NO_BUTTON).strip(),
            callback_data=_cb("restart_no"),
        )],
    ])


def kb_delete_confirm(submission_id: str) -> InlineKeyboardMarkup:
    """Confirmation for delete action."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.YES_BUTTON).strip(),
                callback_data=_cb("delete_yes", submission_id),
            ),
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.NO_BUTTON).strip(),
                callback_data=_cb("delete_no", submission_id),
            ),
        ],
    ])
