"""
Единые билдеры клавиатур для V2.
Все кнопки используют copy из messages.py через V2Copy.
"""
import uuid
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.v2.ui.callbacks import (
    V2_FORM_PREFIX,
    V2_PREVIEW_PREFIX,
    V2_MENU_PREFIX,
    V2_MOD_PREFIX,
    V2_FIX_PREFIX,
    build_callback,
)
from src.v2.ui.copy import V2Copy


def kb_step(
    *,
    back: bool = True,
    skip: bool = False,
    finish_links: bool = False,
    save: bool = False,
) -> InlineKeyboardMarkup:
    """
    Единая клавиатура для шага формы.
    
    Порядок кнопок (сверху вниз):
    1. Навигация: back (если есть)
    2. Действия: skip, finish_links, save (если есть)
    
    Callback data: {PREFIX}:back, {PREFIX}:skip, и т.д.
    """
    rows = []
    if back:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_BACK).strip(),
            callback_data=build_callback(V2_FORM_PREFIX, "back"),
        )])
    if skip:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_SKIP).strip(),
            callback_data=build_callback(V2_FORM_PREFIX, "skip"),
        )])
    if finish_links:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_FINISH_LINKS).strip(),
            callback_data=build_callback(V2_FORM_PREFIX, "finish_links"),
        )])
    if save:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_SAVE).strip(),
            callback_data=build_callback(V2_FORM_PREFIX, "save"),
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_preview(
    *,
    submit: bool = True,
    edit: bool = True,
    menu: bool = True,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для превью.
    
    Кнопки:
    - "✅ Отправить на модерацию" (submit)
    - "✏️ Исправить ответы" (edit)
    - "🏠 Меню" (menu)
    
    Callback data: {PREFIX}:submit, {PREFIX}:back, {PREFIX}:menu
    """
    rows = []
    if submit:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_SUBMIT_TO_MODERATION).strip(),
            callback_data=build_callback(V2_PREVIEW_PREFIX, "submit"),
        )])
    if edit:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_EDIT_ANSWERS).strip(),
            callback_data=build_callback(V2_PREVIEW_PREFIX, "back"),
        )])
    if menu:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_MENU).strip(),
            callback_data=build_callback(V2_PREVIEW_PREFIX, "menu"),
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_preview_confirm() -> InlineKeyboardMarkup:
    """
    Подтверждение отправки на модерацию.
    
    Кнопки:
    - "✅ Да, отправить"
    - "❌ Нет, вернуться"
    
    Callback data: {PREFIX}:submit_yes, {PREFIX}:submit_no
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_YES_SEND).strip(),
            callback_data=build_callback(V2_PREVIEW_PREFIX, "submit_yes"),
        )],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_NO_RETURN).strip(),
            callback_data=build_callback(V2_PREVIEW_PREFIX, "submit_no"),
        )],
    ])


def kb_cabinet(
    *,
    show_resume: bool = False,
    has_projects: bool = False,
) -> InlineKeyboardMarkup:
    """
    Клавиатура кабинета (меню).
    
    Кнопки (по порядку):
    - "▶️ Продолжить" (если show_resume)
    - "📌 Текущий шаг" | "🗂 Проект" (в одной строке)
    - "🧭 Начать заново"
    - "📄 Мои проекты"
    - "➕ Создать проект"
    - "❓ Помощь"
    
    Callback data: {PREFIX}:resume, {PREFIX}:current_step, и т.д.
    """
    rows = []
    if show_resume:
        rows.append([InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_CONTINUE).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "resume"),
        )])
    rows.extend([
        [
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.MENU_CURRENT_STEP).strip(),
                callback_data=build_callback(V2_MENU_PREFIX, "current_step"),
            ),
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.MENU_PROJECT).strip(),
                callback_data=build_callback(V2_MENU_PREFIX, "project"),
            ),
        ],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_RESTART).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "restart"),
        )],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_MY_PROJECTS).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "projects"),
        )],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_CREATE).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "create"),
        )],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_HELP).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "help"),
        )],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_restart_confirm() -> InlineKeyboardMarkup:
    """
    Подтверждение "Начать заново".
    
    Кнопки:
    - "✅ Да"
    - "❌ Нет"
    
    Callback data: {PREFIX}:restart_yes, {PREFIX}:restart_no
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.YES_BUTTON).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "restart_yes"),
        )],
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.NO_BUTTON).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "restart_no"),
        )],
    ])


def kb_moderation_admin(submission_id: uuid.UUID) -> InlineKeyboardMarkup:
    """
    Клавиатура админа для модерации.
    
    Кнопки:
    - "✅ Одобрить" | "🛠 На доработку" | "❌ Отклонить" (в одной строке)
    - "📋 Копировать пост" | "👤 Контакт автора" (в одной строке)
    
    Callback data: {PREFIX}:approve:{id}, {PREFIX}:needs_fix:{id}, и т.д.
    """
    sid = str(submission_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=build_callback(V2_MOD_PREFIX, "approve", sid),
            ),
            InlineKeyboardButton(
                text="🛠 На доработку",
                callback_data=build_callback(V2_MOD_PREFIX, "needs_fix", sid),
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=build_callback(V2_MOD_PREFIX, "reject", sid),
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 Копировать пост",
                callback_data=build_callback(V2_MOD_PREFIX, "copy", sid),
            ),
            InlineKeyboardButton(
                text="👤 Контакт автора",
                callback_data=build_callback(V2_MOD_PREFIX, "author", sid),
            ),
        ],
    ])


def kb_moderation_user_fix(submission_id: uuid.UUID) -> InlineKeyboardMarkup:
    """
    Клавиатура пользователя после needs_fix.
    
    Кнопка:
    - "✏️ Внести правки"
    
    Callback data: v2fix:edit:{id}
    """
    sid = str(submission_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.BTN_MAKE_EDIT).strip(),
            callback_data=build_callback(V2_FIX_PREFIX, "edit", sid),
        )],
    ])
