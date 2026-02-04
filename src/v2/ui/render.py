"""
Рендеринг сообщений V2 в едином стиле (HTML).
Единый контракт для шагов формы, превью, ошибок, кабинета.
"""
from typing import Any
from src.v2.format_step import format_step_message, parse_copy_to_parts
from src.v2.ui.copy import V2Copy, t as get_copy_text
from src.v2.rendering.project_renderer import render_post
from src.v2.fsm.steps import get_step, get_step_index, STEP_KEYS


def render_step(
    step_key: str,
    answers: dict | None = None,
) -> str:
    """
    Рендерит сообщение шага формы в едином стиле (HTML).
    
    Args:
        step_key: ключ шага (например, "q1", "q2")
        answers: словарь ответов для показа текущего значения (опционально)
    
    Returns: HTML-строка для parse_mode="HTML"
    """
    step_def = get_step(step_key)
    if not step_def:
        return ""
    
    step_idx = get_step_index(step_key)
    total = len(STEP_KEYS)
    copy_id = step_def["copy_id"]
    copy_text = get_copy_text(copy_id)
    
    # Парсим копирайт на части
    parts = parse_copy_to_parts(copy_text)
    
    # Получаем текущее значение из answers
    current_value = None
    if answers:
        answer_key = step_def.get("answer_key")
        if answer_key:
            current_value = answers.get(answer_key)
            if isinstance(current_value, list):
                current_value = ", ".join(str(v) for v in current_value if v)
            elif current_value:
                current_value = str(current_value).strip()
            else:
                current_value = None
    
    # Формируем сообщение
    text = format_step_message(
        step_num=step_idx + 1,
        total=total,
        title=parts["title"],
        intro=parts["intro"],
        todo=parts["todo"],
        example=parts["example"],
    )
    
    # Добавляем текущее значение если есть
    if current_value:
        text += "\n\n"
        text += f'<i>Текущее:</i> "{current_value}"'
    
    return text


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
    
    Args:
        code: код ошибки (например, "required", "email") или copy ID (например, "V2_INVALID_REQUIRED")
        example: пример правильного значения (опционально)
        field_name: название поля (не используется, для совместимости)
    
    Returns: HTML-строка для parse_mode="HTML"
    """
    # Если code уже является copy ID (начинается с "V2_"), используем его напрямую
    if code.startswith("V2_"):
        error_copy_id = code
    else:
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
