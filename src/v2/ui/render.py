"""
Рендеринг сообщений V2 в едином стиле (HTML).
Единый контракт для шагов формы, превью, ошибок, кабинета.
"""
from typing import Any
from src.v2.format_step import format_step_message
from src.v2.ui.copy import V2Copy
from src.v2.rendering.project_renderer import render_post


def render_step(
    step_idx: int,
    total: int,
    title: str,
    prompt: str | None = None,
    current: str | None = None,
    example: str | None = None,
    note: str | None = None,
) -> str:
    """
    Рендерит сообщение шага формы в едином стиле (HTML).
    
    Формат:
    - "Шаг X из Y"
    - Пустая строка
    - "📌 <b>title</b>"
    - Пустая строка
    - prompt (если есть)
    - Текущее значение (если есть): "<i>Текущее: current</i>"
    - note (если есть)
    - Пример (если есть): "<i>Пример:</i> \"example\""
    
    Returns: HTML-строка для parse_mode="HTML"
    """
    return format_step_message(
        step_num=step_idx + 1,
        total=total,
        title=title,
        intro=prompt,
        todo=None,
        example=example,
    )


def render_preview_card(
    data: dict,
    mode: str = "preview",
    header: str | None = None,
) -> dict[str, Any]:
    """
    Рендерит карточку проекта как единую карточку (HTML).
    
    Формат карточки:
    - Заголовок (если mode="preview" и header задан)
    - Пустая строка
    - Блоки проекта (title, description, stack, link, price, contact)
    - Каждый блок: "<b>label</b>\\nvalue" с пустыми строками между
    
    Returns: {"text": str, "parse_mode": "HTML", "disable_web_page_preview": bool}
    """
    preview_header = header if mode == "preview" else None
    if not preview_header and mode == "preview":
        preview_header = V2Copy.get(V2Copy.PREVIEW_HEADER)
    return render_post(data, mode=mode, preview_header=preview_header)


def render_error(
    code: str,
    example: str | None = None,
    field_name: str | None = None,
) -> str:
    """
    Рендерит сообщение об ошибке валидации в едином стиле.
    
    Формат:
    - "❌ <b>Ошибка</b>"
    - Пустая строка
    - Текст ошибки из messages.py (V2_INVALID_*)
    - Пример (если есть): "<i>Пример:</i> \"example\""
    
    Returns: HTML-строка для parse_mode="HTML"
    """
    error_map = {
        "required": V2Copy.ERROR_REQUIRED,
        "email": V2Copy.ERROR_EMAIL,
        "link": V2Copy.ERROR_LINK,
        "time": V2Copy.ERROR_TIME,
        "cost": V2Copy.ERROR_COST,
        "budget": V2Copy.ERROR_BUDGET,
    }
    error_copy_id = error_map.get(code, V2Copy.ERROR_REQUIRED)
    error_text = V2Copy.get(error_copy_id)
    
    blocks = []
    blocks.append("❌ <b>Ошибка</b>")
    blocks.append("")
    blocks.append(error_text.strip())
    if example:
        blocks.append("")
        blocks.append(f'<i>Пример:</i> "{example}"')
    
    return "\n".join(blocks)


def render_cabinet_status(
    project_name: str | None,
    step_key: str | None,
    step_num: int,
    total: int,
) -> str:
    """
    Рендерит статус кабинета в едином стиле.
    
    Формат:
    - "📊 <b>Текущий проект:</b> {project_name или 'Не задан'}"
    - "📍 <b>Шаг:</b> {step_num} из {total} ({progress}%)"
    
    Returns: HTML-строка для parse_mode="HTML"
    """
    project = (project_name or "").strip() or V2Copy.get(V2Copy.MENU_STATUS_NO_PROJECT).strip()
    progress = round(step_num / total * 100) if total > 0 else 0
    step_str = f"{step_num} из {total}"
    
    blocks = []
    blocks.append(f"📊 <b>Текущий проект:</b> {project}")
    blocks.append(f"📍 <b>Шаг:</b> {step_str} ({progress}%)")
    
    return "\n".join(blocks)
