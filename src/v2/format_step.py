"""
Unified formatter for V2 form step messages (HTML).
Applied to all steps: initial, next, back, retry. Keeps readability and consistent style.

Central template: format_step_message() builds "Шаг X из Y" + title + intro + todo + example
with empty lines between blocks; parse_mode="HTML" throughout.
"""
import re
from typing import TypedDict


class StepParts(TypedDict):
    title: str
    intro: str | None
    todo: list[str] | None
    example: str | None


def format_step_message(
    step_num: int,
    total: int,
    title: str,
    intro: str | None = None,
    todo: list[str] | None = None,
    example: str | None = None,
) -> str:
    """
    Единый шаблон сообщения шага для всех шагов формы (HTML).
    Пустые строки между блоками; заголовок с 📌; блок «Что нужно сделать» при наличии todo.
    """
    blocks = []
    blocks.append(f"Шаг {step_num} из {total}")
    blocks.append("")
    # Title: keep leading emoji if present, bold the rest or whole line
    title_stripped = (title or "").strip()
    if title_stripped:
        blocks.append(f"📌 <b>{title_stripped}</b>")
        blocks.append("")
    if intro and intro.strip():
        blocks.append(intro.strip())
        blocks.append("")
    if todo:
        blocks.append("📝 <b>Что нужно сделать:</b>")
        for i, item in enumerate(todo, 1):
            blocks.append(f"{i}) {_escape_html(item.strip())}")
        blocks.append("")
    if example and example.strip():
        blocks.append(f'<i>Пример:</i> "{example.strip()}"')
    return "\n".join(blocks).strip()


def _escape_html(s: str) -> str:
    """Escape <, >, & for HTML (Telegram parse_mode=HTML)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse_copy_to_parts(copy_text: str) -> StepParts:
    """
    Из одного текста копирайта (первая строка — заголовок, далее пояснение, Пример: ...)
    извлекает title, intro, todo=None, example. Не меняет смысл — только разбор для шаблона.
    """
    if not copy_text or not copy_text.strip():
        return StepParts(title="", intro=None, todo=None, example=None)
    lines = [ln.strip() for ln in copy_text.strip().split("\n") if ln.strip()]
    if not lines:
        return StepParts(title="", intro=None, todo=None, example=None)
    title = lines[0]
    intro_lines = []
    example = None
    for i in range(1, len(lines)):
        line = lines[i]
        if line.startswith("Пример:") or line.startswith("Например:") or line.startswith("Примеры:"):
            colon = line.find(":")
            example = line[colon + 1 :].strip() if colon >= 0 else ""
            break
        intro_lines.append(line)
    intro = "\n\n".join(intro_lines).strip() if intro_lines else None
    return StepParts(title=title, intro=intro or None, todo=None, example=example or None)


def format_step_message_html(progress: str, body: str) -> str:
    """
    Full step message: progress line (e.g. "Шаг X из N"), blank line, then formatted body.
    Legacy: used when body is passed as single string; prefer format_step_message() + parse_copy_to_parts().
    """
    formatted_body = format_step_body_html(body)
    if not progress.strip():
        return formatted_body
    return f"{progress.strip()}\n\n{formatted_body}"


def format_step_body_html(body: str) -> str:
    """
    Format a step copy string for Telegram HTML parse_mode.
    - First line → bold title; if it ends with (subtitle), subtitle on next line.
    - "Пример:" / "Например:" → blank line before + italic label.
    - Preserve emojis and existing structure; add paragraph breaks between blocks.
    """
    if not body or not body.strip():
        return body
    lines = [ln.strip() for ln in body.strip().split("\n") if ln.strip()]
    if not lines:
        return body.strip()

    # First line: title (bold); optional (subtitle) on next line
    first = lines[0]
    subtitle_match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", first)
    if subtitle_match:
        title_part = subtitle_match.group(1).strip()
        subtitle_part = "(" + subtitle_match.group(2) + ")"
        parts = [f"<b>{title_part}</b>", subtitle_part]
        rest_start = 1
    else:
        parts = [f"<b>{first}</b>"]
        rest_start = 1

    # Remaining lines: normalize "Пример:" / "Например:" and paragraph breaks
    rest = lines[rest_start:]
    i = 0
    while i < len(rest):
        line = rest[i]
        # Example block: blank line before + italic label
        if line.startswith("Пример:") or line.startswith("Например:") or line.startswith("Примеры:"):
            label = "Примеры:" if line.startswith("Примеры:") else ("Например:" if line.startswith("Например:") else "Пример:")
            tail = line[len(label) :].strip()
            parts.append("")
            if tail:
                parts.append(f"<i>{label}</i> {tail}")
            else:
                parts.append(f"<i>{label}</i>")
            i += 1
            continue
        # Unwrap single <i>...</i> line (hint) — keep as one paragraph
        if line.startswith("<i>") and "</i>" in line:
            parts.append("")
            parts.append(line)
            i += 1
            continue
        # Bullet normalization: "- " / "— " → "• "
        if re.match(r"^[-—]\s+", line) or line.startswith("• "):
            line = re.sub(r"^[-—]\s+", "• ", line) if not line.startswith("• ") else line
            parts.append("")
            parts.append(line)
            i += 1
            continue
        # Ordinary paragraph
        parts.append("")
        parts.append(line)
        i += 1

    # Join: double newline between blocks, single between title and subtitle
    result = parts[0]
    for j in range(1, len(parts)):
        if parts[j] == "":
            result += "\n\n"
        elif result.endswith("\n\n"):
            result += parts[j]
        else:
            result += "\n\n" + parts[j]
    return result.strip()
