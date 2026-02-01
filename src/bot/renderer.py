"""Templates from SPEC 05_RENDER_TEMPLATES. No inline copy."""

from src.bot.messages import get_copy
from src.utils.text import escape_html


def answers_to_project_fields(answers: dict) -> dict[str, str]:
    """
    Build title, description, stack, link, price, contact from FSM answers (SPEC 05).
    Preserves backward compat: old 6-key answers used as-is when no new keys present.
    """
    def _join(*keys: str, sep: str = "\n") -> str:
        parts = [str((answers.get(k) or "")).strip() for k in keys if (answers.get(k) or "").strip()]
        return sep.join(parts).strip()

    # Backward compat: only old flat keys
    if answers.get("description") is not None and "description_what" not in answers:
        return {
            "title": str(answers.get("title") or "").strip(),
            "description": str(answers.get("description") or "").strip(),
            "stack": str(answers.get("stack") or "").strip(),
            "link": str(answers.get("link") or "").strip(),
            "price": str(answers.get("price") or "").strip(),
            "contact": str(answers.get("contact") or "").strip(),
        }
    title = _join("title", "title_subtitle", sep=" ") or str(answers.get("title") or "").strip()
    description = _join("description_intro", "description_what", "description_audience", "description_summary", "description_features")
    stack = _join("stack", "stack_list", "stack_other")
    link = _join("link", "link_demo", "link_confirm")
    price = _join("price", "price_note", "price_currency")
    contact = _join("contact", "contact_extra", "contact_preferred")
    return {"title": title, "description": description, "stack": stack, "link": link, "price": price, "contact": contact}


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
