"""
Unified formatter for V2 form step messages (HTML).
Applied to all steps: initial, next, back, retry. Keeps readability and consistent style.
"""
import re


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


def format_step_message_html(progress: str, body: str) -> str:
    """
    Full step message: progress line (e.g. "Шаг X из N"), blank line, then formatted body.
    """
    formatted_body = format_step_body_html(body)
    if not progress.strip():
        return formatted_body
    return f"{progress.strip()}\n\n{formatted_body}"
