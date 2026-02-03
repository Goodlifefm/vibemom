"""
V2 project renderer: SPEC 05 PROJECT_POST.
Safe HTML for Telegram parse_mode=HTML (html.escape). Optional sections omitted if empty.
"""
import html
from typing import Any

# SPEC 05: PROJECT_POST — title, description, stack, link, price, contact
_SECTIONS = (
    ("🟢", "title"),
    ("📝", "description"),
    ("⚙️ Стек", "stack"),
    ("🔗 Ссылка", "link"),
    ("💰 Цена", "price"),
    ("📬 Контакт", "contact"),
)


def _escape(s: Any) -> str:
    """Escape for Telegram HTML. None/empty → empty string. Escapes &, <, >, \"."""
    if s is None:
        return ""
    t = str(s).strip()
    if not t:
        return ""
    return html.escape(t, quote=True)


def _normalize(value: str | list[str] | None) -> str:
    """Single value or list joined by newline; empty → ''."""
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [_escape(x) for x in value if x is not None and str(x).strip()]
        return "\n".join(parts) if parts else ""
    return _escape(value)


def render_project_post_html(blocks: dict[str, str | list[str] | None]) -> str:
    """
    Build PROJECT_POST HTML per SPEC 05. blocks: title, description, stack, link, price, contact.
    All user-provided values escaped; section omitted if value empty.
    """
    parts = []
    for label, key in _SECTIONS:
        value = _normalize(blocks.get(key))
        if not value:
            continue
        # Label only (e.g. "🟢") or "⚙️ Стек" — no extra newline before value
        parts.append(f"<b>{label}</b>\n{value}")
    return "\n\n".join(parts)


def submission_answers_to_blocks(answers: dict | None) -> dict[str, str | list[str] | None]:
    """
    Map V2 submission.answers to PROJECT_POST blocks (title, description, stack, link, price, contact).
    SPEC POST_PLACEHOLDERS_MAPPING; V2 keys: title, subtitle, description, contact, author_contact, links, etc.
    """
    if not answers:
        answers = {}
    title_parts = []
    if answers.get("title"):
        title_parts.append(str(answers["title"]).strip())
    if answers.get("subtitle"):
        title_parts.append(str(answers["subtitle"]).strip())
    title = "\n".join(title_parts) if title_parts else None

    desc_parts = []
    for k in ("description", "niche", "what_done", "status"):
        if answers.get(k):
            desc_parts.append(str(answers[k]).strip())
    description = "\n".join(desc_parts) if desc_parts else None

    stack = answers.get("stack_reason") or answers.get("stack") or None
    if stack:
        stack = str(stack).strip()

    links = answers.get("links")
    if isinstance(links, list) and links:
        link = "\n".join(str(x).strip() for x in links if x and str(x).strip())
    else:
        link = answers.get("link") or None
    if link and not isinstance(link, str):
        link = str(link).strip() if link else None

    price_parts = []
    for k in ("currency", "cost", "cost_max"):
        if answers.get(k):
            price_parts.append(str(answers[k]).strip())
    price = " ".join(price_parts) if price_parts else (answers.get("price") or None)
    if price and isinstance(price, str):
        price = price.strip() or None

    contact = answers.get("author_contact") or answers.get("contact") or None
    if contact:
        contact = str(contact).strip()

    return {
        "title": title,
        "description": description,
        "stack": stack,
        "link": link,
        "price": price,
        "contact": contact,
    }


def render_submission_to_html(answers: dict | None) -> str:
    """
    Build safe HTML from submission.answers (V2). Uses PROJECT_POST; maps answers to blocks.
    """
    blocks = submission_answers_to_blocks(answers)
    return render_project_post_html(blocks)


def project_to_feed_answers(project: Any) -> dict:
    """
    V1 Project (title, description, stack, link, price, contact) → dict for render_for_feed.
    Duck-typed: any object with these attributes works.
    """
    return {
        "title": getattr(project, "title", None) or "",
        "description": getattr(project, "description", None) or "",
        "contact": getattr(project, "contact", None) or "",
        "author_contact": getattr(project, "contact", None) or "",
        "link": getattr(project, "link", None) or "",
        "links": [getattr(project, "link", None)] if getattr(project, "link", None) else [],
        "price": getattr(project, "price", None) or "",
        "cost": "",
        "cost_max": "",
        "currency": "",
        "niche": "",
        "stack": getattr(project, "stack", None) or "",
    }


def render_for_feed(answers: dict | None) -> str:
    """
    Post for channel feed: title, 1–2 lines description (~500 chars), contact, price, link, hashtags.
    Safe HTML for Telegram parse_mode=HTML.
    Accepts V2 answers dict or dict from project_to_feed_answers(V1 Project).
    """
    if not answers:
        answers = {}
    title = _escape(answers.get("title") or "").strip() or "—"
    desc = _escape(answers.get("description") or "").strip() or "—"
    contact = _escape(answers.get("author_contact") or answers.get("contact") or "").strip() or "—"
    cost = str(answers.get("cost") or "").strip()
    cost_max = str(answers.get("cost_max") or "").strip()
    currency = str(answers.get("currency") or "").strip()
    price_single = str(answers.get("price") or "").strip()
    if cost or cost_max or currency:
        if currency:
            price = f"{cost} – {cost_max} {currency}".strip(" –") if (cost or cost_max) else "—"
        else:
            price = f"{cost} – {cost_max}".strip(" –") or "—"
    else:
        price = _escape(price_single) if price_single else "—"
    links = answers.get("links")
    if isinstance(links, list) and links:
        link = next((str(x).strip() for x in links if x and str(x).strip()), "")
    else:
        link = (answers.get("link") or "").strip() if answers.get("link") else ""
    link = _escape(link) if link else ""
    niche = _escape(answers.get("niche") or "").strip()
    stack = answers.get("stack_reason") or answers.get("stack") or ""
    stack = str(stack).strip() if stack else ""
    tags = []
    if niche:
        tags.append("#" + niche.replace(" ", "_").replace(",", "_")[:30])
    if stack:
        for part in stack.split(",")[:3]:
            t = part.strip()[:20].replace(" ", "_")
            if t:
                tags.append("#" + t)
    hashtags = " ".join(tags) if tags else ""

    lines = [
        f"<b>{title}</b>",
        "",
        desc[:500] + ("…" if len(desc) > 500 else ""),
        "",
        f"<b>Контакт:</b> {contact}",
        f"<b>Цена:</b> {price}" if price != "—" else None,
        link if link else None,
        hashtags if hashtags else None,
    ]
    return "\n".join(x for x in lines if x is not None)
