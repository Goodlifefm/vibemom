"""Centralized keyboard builders. Labels from messages.py; callback_data stable."""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from src.bot.messages import get_copy
from src.v2.ui import callbacks as v2_callbacks

PS = "ps"
MENU_PREFIX = v2_callbacks.MENU_PREFIX

# Callback prefixes for namespacing
CB_MENU = "menu"  # menu:* actions
CB_WIZ = "wiz"    # wiz:* wizard actions
CB_POST = "post"  # post:* publish/moderation
CB_MOD = "moderation"  # moderation:* approve/reject


def persistent_reply_kb() -> ReplyKeyboardMarkup:
    """
    Persistent bottom reply keyboard with '☰ Меню' button.
    Always visible under input field. Works from any state.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_copy("V2_MENU_PERSISTENT_BTN").strip())]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def reply_menu_keyboard_full() -> ReplyKeyboardMarkup:
    """
    Full reply keyboard menu (bottom-sheet style) - matches cabinet menu.
    
    Layout:
    Row1: 📁 Мои проекты | 🏪 Каталог
    Row3: 🏠 Меню (full width)
    """
    return reply_menu_keyboard_with_actions()


def reply_menu_keyboard_with_actions() -> ReplyKeyboardMarkup:
    """
    Simplified reply keyboard matching the cabinet menu.
    
    Layout:
    Row1: 📁 Мои проекты | 🏪 Каталог
    Row3: 🏠 Меню (full width)
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📁 Мои проекты"),
                KeyboardButton(text="🏪 Каталог"),
            ],
            [KeyboardButton(text="🏠 Меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def reply_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard with single button: 🏠 Меню. Shown from any state.
    DEPRECATED: Use persistent_reply_kb() for the new '☰ Меню' button.
    """
    # Keep backward compatibility but use new persistent button
    return persistent_reply_kb()


def menu_cabinet_inline_kb(
    show_resume: bool = False,
    has_projects: bool = False,
) -> InlineKeyboardMarkup:
    """Inline keyboard for menu/cabinet - uses unified cabinet menu."""
    from src.v2.keyboards.menu import kb_cabinet_menu
    return kb_cabinet_menu(has_active_draft=show_resume)


def menu_restart_confirm_kb() -> InlineKeyboardMarkup:
    """Yes/No for 'Start over' confirmation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("YES_BUTTON").strip(), callback_data=f"{MENU_PREFIX}:restart_yes")],
        [InlineKeyboardButton(text=get_copy("NO_BUTTON").strip(), callback_data=f"{MENU_PREFIX}:restart_no")],
    ])


def yes_no_kb_submit() -> InlineKeyboardMarkup:
    """Yes/No for project submission confirm. callback_data: ps:submit_yes, ps:submit_no."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("BTN_YES_SEND").strip(), callback_data=f"{PS}:submit_yes")],
        [InlineKeyboardButton(text=get_copy("BTN_NO_RETURN").strip(), callback_data=f"{PS}:submit_no")],
    ])


def ps_nav_step(*, back: bool = True, next_: bool = True, save: bool = True, skip: bool = False) -> InlineKeyboardMarkup:
    """Project submission step nav. callback_data: ps:back, ps:next, ps:save, ps:skip."""
    row = []
    if back:
        row.append(InlineKeyboardButton(text=get_copy("BACK_BUTTON").strip(), callback_data=f"{PS}:back"))
    if next_:
        row.append(InlineKeyboardButton(text=get_copy("NEXT_BUTTON").strip(), callback_data=f"{PS}:next"))
    if save:
        row.append(InlineKeyboardButton(text=get_copy("SAVE_BUTTON").strip(), callback_data=f"{PS}:save"))
    if skip:
        row.append(InlineKeyboardButton(text=get_copy("SKIP_BUTTON").strip(), callback_data=f"{PS}:skip"))
    if not row:
        return InlineKeyboardMarkup(inline_keyboard=[])
    return InlineKeyboardMarkup(inline_keyboard=[row])


def ps_preview_kb() -> InlineKeyboardMarkup:
    """Preview: Submit to mod, Edit answers, Back. callback_data: ps:submit, ps:edit, ps:back."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_copy("BTN_SUBMIT_TO_MODERATION").strip(), callback_data=f"{PS}:submit"),
            InlineKeyboardButton(text=get_copy("BTN_EDIT_ANSWERS").strip(), callback_data=f"{PS}:edit"),
        ],
        [InlineKeyboardButton(text=get_copy("BACK_BUTTON").strip(), callback_data=f"{PS}:back")],
    ])


def ps_confirm_final_kb() -> InlineKeyboardMarkup:
    """Final confirm: Yes send, No return. callback_data: ps:submit_yes, ps:submit_no."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("BTN_YES_SEND").strip(), callback_data=f"{PS}:submit_yes")],
        [InlineKeyboardButton(text=get_copy("BTN_NO_RETURN").strip(), callback_data=f"{PS}:submit_no")],
    ])


def ps_resume_kb() -> InlineKeyboardMarkup:
    """After save draft: Continue. callback_data: ps:resume."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("BTN_RESUME").strip(), callback_data=f"{PS}:resume")],
    ])


def yes_no_kb_request() -> InlineKeyboardMarkup:
    """Yes/No for buyer request confirm. callback_data: req_yes, req_no."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("YES_BUTTON").strip(), callback_data="req_yes")],
        [InlineKeyboardButton(text=get_copy("NO_BUTTON").strip(), callback_data="req_no")],
    ])


def admin_moderate_kb(project_id: str) -> InlineKeyboardMarkup:
    """Admin moderation: approve / needs_fix / reject. callback_data: mod_approve_, mod_fix_, mod_reject_."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_copy("BTN_APPROVE").strip(), callback_data=f"mod_approve_{project_id}"),
            InlineKeyboardButton(text=get_copy("BTN_NEEDS_FIX").strip(), callback_data=f"mod_fix_{project_id}"),
            InlineKeyboardButton(text=get_copy("BTN_REJECT").strip(), callback_data=f"mod_reject_{project_id}"),
        ],
    ])


def moderation_kb(submission_id: str) -> InlineKeyboardMarkup:
    """Moderation for Mini App submissions: approve / reject. callback_data: moderation:approve:{id} moderation:reject:{id}."""
    sid = (submission_id or "").strip()
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_copy("BTN_APPROVE").strip(), callback_data=f"{CB_MOD}:approve:{sid}"),
            InlineKeyboardButton(text=get_copy("BTN_REJECT").strip(), callback_data=f"{CB_MOD}:reject:{sid}"),
        ],
    ])


def nav_keyboard(
    *,
    back: bool = True,
    next_: bool = True,
    save: bool = False,
    skip: bool = False,
    prefix: str = "nav",
) -> InlineKeyboardMarkup:
    """
    Unified nav buttons (generic). callback_data: {prefix}_back, {prefix}_next, etc.
    """
    row = []
    if back:
        row.append(InlineKeyboardButton(text=get_copy("BACK_BUTTON").strip(), callback_data=f"{prefix}:back"))
    if next_:
        row.append(InlineKeyboardButton(text=get_copy("NEXT_BUTTON").strip(), callback_data=f"{prefix}:next"))
    if save:
        row.append(InlineKeyboardButton(text=get_copy("SAVE_BUTTON").strip(), callback_data=f"{prefix}:save"))
    if skip:
        row.append(InlineKeyboardButton(text=get_copy("SKIP_BUTTON").strip(), callback_data=f"{prefix}:skip"))
    if not row:
        return InlineKeyboardMarkup(inline_keyboard=[])
    return InlineKeyboardMarkup(inline_keyboard=[row])


# =============================================================================
# Cabinet Menu (persistent menu refactor)
# =============================================================================

def cabinet_menu_inline_kb(
    *,
    has_active_wizard: bool = False,
    has_drafts: bool = False,
    has_publications: bool = False,
) -> InlineKeyboardMarkup:
    """
    Main cabinet menu inline keyboard - uses unified cabinet menu.
    
    Callback namespace: m:*
    """
    from src.v2.keyboards.menu import kb_cabinet_menu
    return kb_cabinet_menu(has_active_draft=has_active_wizard)


def menu_back_kb() -> InlineKeyboardMarkup:
    """Simple 'back to menu' button for placeholder screens."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_copy("V2_MENU_BACK").strip(),
            callback_data=f"{CB_MENU}:back_to_menu",
        )],
    ])


def drafts_list_kb(drafts: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """
    Drafts list keyboard.
    Each draft has title and submission_id.
    Callback: menu:open_draft:{submission_id}
    """
    rows = []
    for title, sid in drafts:
        display = title[:30] if title else "Без названия"
        rows.append([InlineKeyboardButton(
            text=f"📝 {display}",
            callback_data=f"{CB_MENU}:open_draft:{sid}",
        )])
    rows.append([InlineKeyboardButton(
        text=get_copy("V2_MENU_BACK").strip(),
        callback_data=f"{CB_MENU}:back_to_menu",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def publications_list_kb(publications: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """
    Publications list keyboard.
    Each publication has title and project_id.
    Callback: menu:view_post:{project_id}
    """
    rows = []
    for title, pid in publications:
        display = title[:30] if title else "Без названия"
        rows.append([InlineKeyboardButton(
            text=f"📌 {display}",
            callback_data=f"{CB_MENU}:view_post:{pid}",
        )])
    rows.append([InlineKeyboardButton(
        text=get_copy("V2_MENU_BACK").strip(),
        callback_data=f"{CB_MENU}:back_to_menu",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)
