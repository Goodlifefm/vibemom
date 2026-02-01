"""Templates from SPEC 05_RENDER_TEMPLATES. No inline copy."""

from src.bot.messages import get_copy
from src.utils.text import escape_html


def _section(label: str, value: str) -> str:
    """One section: label + value, or empty string if value is empty."""
    v = (value or "").strip()
    if not v:
        return ""
    return f"{label}\n{escape_html(v)}"


def render_project_post(
    title: str,
    description: str,
    stack: str,
    link: str,
    price: str,
    contact: str,
) -> str:
    """
    PROJECT_POST template (SPEC 05).
    Clear sections, spacing, emojis. Empty optional sections omitted.
    All user content escaped for HTML parse_mode.
    """
    emoji_title = get_copy("TEMPLATE_EMOJI_TITLE")
    emoji_desc = get_copy("TEMPLATE_EMOJI_DESC")
    section_stack = get_copy("TEMPLATE_SECTION_STACK")
    section_link = get_copy("TEMPLATE_SECTION_LINK")
    section_price = get_copy("TEMPLATE_SECTION_PRICE")
    section_contact = get_copy("TEMPLATE_SECTION_CONTACT")

    title_s = (title or "").strip()
    if not title_s:
        title_s = "—"
    parts = [f"{emoji_title} {escape_html(title_s)}"]

    desc_block = _section(emoji_desc, description)
    if desc_block:
        parts.append(desc_block)

    stack_block = _section(section_stack, stack)
    if stack_block:
        parts.append(stack_block)

    link_block = _section(section_link, link)
    if link_block:
        parts.append(link_block)

    price_block = _section(section_price, price)
    if price_block:
        parts.append(price_block)

    contact_block = _section(section_contact, contact)
    if contact_block:
        parts.append(contact_block)

    return "\n\n".join(parts).strip()


def render_buyer_request_summary(what: str, budget: str, contact: str) -> str:
    """BUYER_REQUEST_SUMMARY template (SPEC 05). User content escaped."""
    claim = get_copy("TEMPLATE_CLAIM")
    budget_label = get_copy("TEMPLATE_BUDGET")
    contact_label = get_copy("TEMPLATE_CONTACT_LABEL")
    return f"""---
{claim} {escape_html((what or "").strip())}
{budget_label} {escape_html((budget or "").strip())}
{contact_label} {escape_html((contact or "").strip())}
---""".strip()
