"""
Unified post text renderer: same output for preview and publish.
Single source of truth for PROJECT_POST body and price formatting.
"""
import html
from typing import Any


# ==============================================================================
# Price Formatting
# ==============================================================================

def render_price(
    budget_min: int | None = None,
    budget_max: int | None = None,
    budget_currency: str | None = None,
    budget_hidden: bool = False,
    *,
    # Legacy fallback
    cost: Any = None,
    cost_max: Any = None,
    currency: str | None = None,
) -> str | None:
    """
    Format price for display.
    
    Variants:
    - hidden=True → "скрыта"
    - single value → "500 RUB"
    - range → "500–1500 RUB"
    
    Args:
        budget_min: Minimum price (int)
        budget_max: Maximum price (int) 
        budget_currency: "RUB" or "USD"
        budget_hidden: If True, return "скрыта"
        cost/cost_max/currency: Legacy fields fallback
    
    Returns:
        Formatted price string or None if no price data
    """
    if budget_hidden is True:
        return "скрыта"
    
    cur = (budget_currency or currency or "").strip().upper() or "RUB"
    symbol = "₽" if cur == "RUB" else "$" if cur == "USD" else cur
    
    # New budget fields
    if budget_min is not None or budget_max is not None:
        try:
            mn = int(budget_min) if budget_min is not None else None
            mx = int(budget_max) if budget_max is not None else None
        except (TypeError, ValueError):
            mn = mx = None
        
        if mn is not None and mx is not None:
            # Range: "500–1500 RUB"
            return f"{mn:,}–{mx:,} {symbol}".replace(",", " ")
        elif mn is not None:
            # Fixed: "500 RUB"
            return f"{mn:,} {symbol}".replace(",", " ")
        elif mx is not None:
            # Max only
            return f"до {mx:,} {symbol}".replace(",", " ")
    
    # Legacy fallback: cost/cost_max
    if cost is not None or cost_max is not None:
        try:
            c = int(cost) if cost is not None else None
        except (TypeError, ValueError):
            c = None
        try:
            c_max = int(cost_max) if cost_max is not None else None
        except (TypeError, ValueError):
            c_max = None
        
        if c is not None and c_max is not None:
            return f"{c:,}–{c_max:,} {symbol}".replace(",", " ")
        elif c is not None:
            return f"{c:,} {symbol}".replace(",", " ")
        elif c_max is not None:
            return f"до {c_max:,} {symbol}".replace(",", " ")
    
    return None


def render_price_from_answers(answers: dict) -> str | None:
    """
    Extract and format price from answers dict.
    Supports both new budget_* fields and legacy cost/cost_max/currency.
    """
    return render_price(
        budget_min=answers.get("budget_min"),
        budget_max=answers.get("budget_max"),
        budget_currency=answers.get("budget_currency"),
        budget_hidden=answers.get("budget_hidden", False),
        cost=answers.get("cost"),
        cost_max=answers.get("cost_max"),
        currency=answers.get("currency"),
    )


# ==============================================================================
# Post Text Rendering
# ==============================================================================

def _escape(s: Any) -> str:
    """Escape for Telegram HTML. None/empty → empty string."""
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


# Section definitions: (emoji_label, key)
_POST_SECTIONS = (
    ("🟢", "title"),
    ("📝", "description"),
    ("⚙️ Стек", "stack"),
    ("🔗 Ссылка", "link"),
    ("💰 Цена", "price"),
    ("📬 Контакт", "contact"),
)


def render_post_text(
    answers: dict | None,
    *,
    mode: str = "publish",
    preview_header: str | None = None,
) -> dict[str, Any]:
    """
    Render PROJECT_POST body from answers dict.
    Single source of truth — same output for preview and publish.
    
    Args:
        answers: Submission answers dict
        mode: "preview" adds header, "publish" is body only
        preview_header: Header text for preview mode
    
    Returns:
        {"text": str, "parse_mode": "HTML", "disable_web_page_preview": bool}
    """
    if not answers:
        answers = {}
    
    blocks = _answers_to_blocks(answers)
    body = _render_blocks_html(blocks)
    
    if mode == "preview" and preview_header:
        text = preview_header.strip() + "\n\n" + body
    else:
        text = body
    
    return {
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }


def _answers_to_blocks(answers: dict) -> dict[str, str | list[str] | None]:
    """
    Map V2 answers to PROJECT_POST blocks.
    Keys: title, description, stack, link, price, contact.
    """
    # Title: title + subtitle
    title_parts = []
    if answers.get("title"):
        title_parts.append(str(answers["title"]).strip())
    if answers.get("subtitle"):
        title_parts.append(str(answers["subtitle"]).strip())
    title = "\n".join(title_parts) if title_parts else None
    
    # Description: description + niche + what_done + status
    desc_parts = []
    for k in ("description", "niche", "what_done", "status"):
        if answers.get(k):
            desc_parts.append(str(answers[k]).strip())
    description = "\n".join(desc_parts) if desc_parts else None
    
    # Stack
    stack = answers.get("stack_reason") or answers.get("stack")
    if stack:
        stack = str(stack).strip()
    
    # Links
    links = answers.get("links")
    if isinstance(links, list) and links:
        link = "\n".join(str(x).strip() for x in links if x and str(x).strip())
    else:
        link = answers.get("link")
    if link and not isinstance(link, str):
        link = str(link).strip() if link else None
    
    # Price (using unified renderer)
    price = render_price_from_answers(answers)
    if not price:
        # Fallback to raw price field
        price = answers.get("price")
        if price:
            price = str(price).strip() or None
    
    # Contact
    contact = answers.get("author_contact") or answers.get("contact")
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


def _render_blocks_html(blocks: dict[str, str | list[str] | None]) -> str:
    """
    Build PROJECT_POST HTML from blocks.
    All user-provided values escaped; section omitted if value empty.
    """
    parts = []
    for label, key in _POST_SECTIONS:
        value = _normalize(blocks.get(key))
        if not value:
            continue
        parts.append(f"<b>{label}</b>\n{value}")
    return "\n\n".join(parts)


def assert_preview_publish_consistency(answers: dict | None, publish_text: str) -> None:
    """
    Regression check: body from publish must match body from unified renderer.
    Raises AssertionError if they differ.
    """
    import logging
    expected = render_post_text(answers, mode="publish")["text"]
    if publish_text != expected:
        log = logging.getLogger(__name__)
        log.error(
            "preview/publish mismatch: len expected=%s got=%s",
            len(expected), len(publish_text),
        )
        raise AssertionError(
            f"Publish text must match render_post_text. "
            f"Len expected={len(expected)} got={len(publish_text)}"
        )
