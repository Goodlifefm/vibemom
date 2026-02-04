"""
Централизованные callback prefixes и утилиты для парсинга.
Единый источник истины для всех V2 callback_data.
"""
import uuid


# Prefixes для V2 роутеров
V2_FORM_PREFIX = "v2form"
V2_PREVIEW_PREFIX = "v2preview"
V2_MENU_PREFIX = "v2menu"
V2_MOD_PREFIX = "v2mod"
V2_CABINET_PREFIX = "v2cab"  # legacy, использовать v2menu
V2_FIX_PREFIX = "v2fix"

# ---- Backward-compatible aliases for older imports ----
MENU_PREFIX = V2_MENU_PREFIX
FORM_PREFIX = V2_FORM_PREFIX
PREVIEW_PREFIX = V2_PREVIEW_PREFIX
MOD_PREFIX = V2_MOD_PREFIX
CABINET_PREFIX = V2_CABINET_PREFIX
FIX_PREFIX = V2_FIX_PREFIX

# Legacy placeholders used in some V1 code paths (if any)
BACK_PREFIX = V2_FORM_PREFIX
CANCEL_PREFIX = V2_FORM_PREFIX
SUBMIT_PREFIX = V2_PREVIEW_PREFIX
CAB_PREFIX = V2_CABINET_PREFIX  # backward compat alias

# Menu action constants (for menu() helper)
MENU_RESUME = "resume"
MENU_RESTART = "restart"
MENU_RESTART_YES = "restart_yes"
MENU_RESTART_NO = "restart_no"
MENU_PROJECTS = "projects"
MENU_CREATE = "create"
MENU_HELP = "help"
MENU_CURRENT_STEP = "current_step"
MENU_PROJECT = "project"

# Form action constants (for form() helper)
FORM_BACK = "back"
FORM_SKIP = "skip"
FORM_SAVE = "save"
FORM_FINISH_LINKS = "finish_links"


def menu(action: str) -> str:
    """
    Build menu callback_data: menu(action) -> "v2menu:{action}".
    
    Examples:
    - menu(MENU_RESUME) -> "v2menu:resume"
    - menu("help") -> "v2menu:help"
    """
    return build_callback(V2_MENU_PREFIX, action)


def form(action: str) -> str:
    """
    Build form callback_data: form(action) -> "v2form:{action}".
    
    Examples:
    - form(FORM_BACK) -> "v2form:back"
    - form("skip") -> "v2form:skip"
    """
    return build_callback(V2_FORM_PREFIX, action)


def parse_callback(data: str) -> tuple[str | None, str | None, list[str]]:
    """
    Парсит callback_data в (prefix, action, args).
    
    Примеры:
    - "v2form:back" → ("v2form", "back", [])
    - "v2preview:submit" → ("v2preview", "submit", [])
    - "v2mod:approve:uuid" → ("v2mod", "approve", ["uuid"])
    """
    if not data or ":" not in data:
        return None, None, []
    parts = data.split(":")
    if len(parts) < 2:
        return None, None, []
    prefix = parts[0]
    action = parts[1]
    args = parts[2:] if len(parts) > 2 else []
    return prefix, action, args


def build_callback(prefix: str, action: str, *args: str) -> str:
    """
    Строит callback_data из prefix, action и опциональных args.
    
    Примеры:
    - build_callback("v2form", "back") → "v2form:back"
    - build_callback("v2mod", "approve", "uuid") → "v2mod:approve:uuid"
    """
    parts = [prefix, action] + list(args)
    return ":".join(parts)


def parse_submission_id(data: str) -> uuid.UUID | None:
    """
    Извлекает submission_id из callback_data (последний аргумент после action).
    
    Примеры:
    - "v2mod:approve:123e4567-e89b-12d3-a456-426614174000" → UUID
    - "v2form:back" → None
    """
    _, _, args = parse_callback(data)
    if not args:
        return None
    try:
        return uuid.UUID(args[-1])
    except (ValueError, TypeError):
        return None

