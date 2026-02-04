"""
V2 UI Kit: единый интерфейс для рендеринга, клавиатур и callbacks.
"""
from src.v2.ui.callbacks import (
    V2_FORM_PREFIX,
    V2_PREVIEW_PREFIX,
    V2_MENU_PREFIX,
    V2_MOD_PREFIX,
    V2_CABINET_PREFIX,
    V2_FIX_PREFIX,
    parse_callback,
    build_callback,
    parse_submission_id,
)
from src.v2.ui.copy import V2Copy
from src.v2.ui.keyboards import (
    kb_step,
    kb_preview,
    kb_preview_confirm,
    kb_cabinet,
    kb_restart_confirm,
    kb_moderation_admin,
    kb_moderation_user_fix,
)
from src.v2.ui.render import (
    render_step,
    render_preview_card,
    render_error,
    render_cabinet_status,
)

__all__ = [
    # Callbacks
    "V2_FORM_PREFIX",
    "V2_PREVIEW_PREFIX",
    "V2_MENU_PREFIX",
    "V2_MOD_PREFIX",
    "V2_CABINET_PREFIX",
    "V2_FIX_PREFIX",
    "parse_callback",
    "build_callback",
    "parse_submission_id",
    # Copy
    "V2Copy",
    # Keyboards
    "kb_step",
    "kb_preview",
    "kb_preview_confirm",
    "kb_cabinet",
    "kb_restart_confirm",
    "kb_moderation_admin",
    "kb_moderation_user_fix",
    # Render
    "render_step",
    "render_preview_card",
    "render_error",
    "render_cabinet_status",
]
