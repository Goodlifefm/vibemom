"""Centralized keyboard builders. Labels from messages.py; callback_data stable."""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from src.bot.messages import get_copy

PS = "ps"
MENU_PREFIX = "v2menu"


def reply_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard with single button: 🏠 Меню. Shown from any state."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_copy("V2_MENU_BTN").strip())]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def menu_cabinet_inline_kb(
    show_resume: bool = False,
    has_projects: bool = False,
) -> InlineKeyboardMarkup:
    """Inline keyboard for menu/cabinet: Continue, Current step, Project, Start over, My projects, Create, Help."""
    rows = []
    if show_resume:
        rows.append([InlineKeyboardButton(text=get_copy("V2_MENU_CONTINUE").strip(), callback_data=f"{MENU_PREFIX}:resume")])
    rows.extend([
        [
            InlineKeyboardButton(text=get_copy("V2_MENU_CURRENT_STEP").strip(), callback_data=f"{MENU_PREFIX}:current_step"),
            InlineKeyboardButton(text=get_copy("V2_MENU_PROJECT").strip(), callback_data=f"{MENU_PREFIX}:project"),
        ],
        [InlineKeyboardButton(text=get_copy("V2_MENU_RESTART").strip(), callback_data=f"{MENU_PREFIX}:restart")],
        [InlineKeyboardButton(text=get_copy("V2_MENU_MY_PROJECTS").strip(), callback_data=f"{MENU_PREFIX}:projects")],
        [InlineKeyboardButton(text=get_copy("V2_MENU_CREATE").strip(), callback_data=f"{MENU_PREFIX}:create")],
        [InlineKeyboardButton(text=get_copy("V2_MENU_HELP").strip(), callback_data=f"{MENU_PREFIX}:help")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
