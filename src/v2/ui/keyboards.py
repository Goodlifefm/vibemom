"""
Единые билдеры клавиатур для V2.
Все кнопки используют copy из messages.py через V2Copy.
"""
import logging
import uuid
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.v2.ui.callbacks import (
    V2_FORM_PREFIX,
    V2_PREVIEW_PREFIX,
    V2_MENU_PREFIX,
    V2_MOD_PREFIX,
    V2_FIX_PREFIX,
    V2_CABINET_PREFIX,
    build_callback,
)
from src.v2.ui.copy import V2Copy

logger = logging.getLogger(__name__)


def _get_webapp_url() -> str | None:
    """Get WEBAPP_URL from settings, return None if not configured."""
    try:
        from src.bot.config import Settings
        settings = Settings()
        url = settings.webapp_url.strip()
        if url and url.startswith("https://"):
            return url
        if url:
            logger.warning("WEBAPP_URL must start with https://, got: %s", url[:50])
        return None
    except Exception as e:
        logger.warning("Failed to get WEBAPP_URL: %s", e)
        return None


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
    Unified cabinet keyboard (use kb_cabinet_menu from src/v2/keyboards/menu.py for new code).
    
    Cabinet menu items:
    - 🏠 Главное меню (m:home)
    - ▶️ Продолжить заполнение (m:resume) — only if show_resume
    - 📁 Мои проекты (m:my_projects)
    - 🏪 Каталог | 📥 Реквесты (m:catalog, m:request)
    - 📊 Мои реквесты / Лиды (m:my_requests_leads)
    - 📱 Кабинет (Mini App) — WebApp button
    - ✕ Закрыть (m:close)
    """
    from src.v2.keyboards.menu import kb_cabinet_menu
    return kb_cabinet_menu(has_active_draft=show_resume)


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


# ---- Backward-compatible wrappers for new UI kit naming ----
def menu_cabinet_inline_kb(*, show_resume: bool, has_projects: bool) -> InlineKeyboardMarkup:
    return kb_cabinet(show_resume=show_resume, has_projects=has_projects)


def menu_restart_confirm_kb() -> InlineKeyboardMarkup:
    return kb_restart_confirm()


def menu_current_step_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=V2Copy.get(V2Copy.MENU_CONTINUE).strip(),
            callback_data=build_callback(V2_MENU_PREFIX, "resume"),
        )],
    ])


def delete_confirm_kb(submission_id: uuid.UUID | str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления проекта."""
    sid = str(submission_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.YES_BUTTON).strip(),
                callback_data=build_callback(V2_MENU_PREFIX, "delete_yes", sid),
            ),
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.NO_BUTTON).strip(),
                callback_data=build_callback(V2_MENU_PREFIX, "delete_no", sid),
            ),
        ],
    ])


def projects_list_kb(projects: list[tuple[str, uuid.UUID | str]]) -> InlineKeyboardMarkup:
    rows = []
    for title, sid in projects:
        rows.append([
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.BTN_OPEN).strip() + f" ({title[:20]})",
                callback_data=build_callback(V2_CABINET_PREFIX, "open", str(sid)),
            ),
            InlineKeyboardButton(
                text=V2Copy.get(V2Copy.BTN_DELETE).strip(),
                callback_data=build_callback(V2_MENU_PREFIX, "delete", str(sid)),
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cabinet_inline_kb(*, show_resume: bool) -> InlineKeyboardMarkup:
    """Wrapper for backward compatibility."""
    from src.v2.keyboards.menu import kb_cabinet_menu
    return kb_cabinet_menu(has_active_draft=show_resume)


def form_step_kb(step_key: str) -> InlineKeyboardMarkup:
    from src.v2.fsm.steps import is_optional, is_multi_link
    return kb_step(
        back=True,
        skip=is_optional(step_key),
        finish_links=is_multi_link(step_key),
        save=True,
    )


def preview_kb() -> InlineKeyboardMarkup:
    return kb_preview(submit=True, edit=True, menu=True)


def preview_confirm_kb() -> InlineKeyboardMarkup:
    return kb_preview_confirm()


def admin_mod_kb(submission_id: uuid.UUID) -> InlineKeyboardMarkup:
    return kb_moderation_admin(submission_id)


def fix_edit_kb(submission_id: uuid.UUID | str) -> InlineKeyboardMarkup:
    return kb_moderation_user_fix(uuid.UUID(str(submission_id)))
