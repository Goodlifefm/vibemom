"""Templates from SPEC 05_RENDER_TEMPLATES. No inline copy."""

import json
from src.bot.messages import get_copy
from src.utils.text import escape_html


def project_fields_to_answers(project: object) -> dict:
    """Build answers dict from Project row (V2 editor). V2 draft may store JSON in description."""
    p = project
    desc = (p.description or "").strip()
    if desc.startswith("{"):
        try:
            data = json.loads(desc)
            if isinstance(data, dict):
                from src.bot.editor_schema import default_answers
                out = default_answers()
                for k, v in data.items():
                    if k in out:
                        out[k] = v
                    elif k == "_meta":
                        out["_meta"] = v
                return out
        except (json.JSONDecodeError, TypeError):
            pass
    from src.bot.editor_schema import default_answers
    out = default_answers()
    out["project_title"] = out["title"] = (p.title or "").strip()
    out["project_what"] = out["description"] = desc
    out["project_problem"] = desc  # required in editor_schema; legacy has single description blob
    out["stack_ai"] = out["stack"] = (p.stack or "").strip()
    out["link"] = (p.link or "").strip()
    out["econ_time"] = out["price"] = (p.price or "").strip()
    out["author_contact"] = out["contact"] = (p.contact or "").strip()
    return out


def v2_answers_to_project_fields(answers: dict) -> dict[str, str]:
    """Map V2 extended answers to 6 DB columns (title, description, stack, link, price, contact)."""
    def _s(k: str) -> str:
        v = answers.get(k)
        if v is None:
            return ""
        if isinstance(v, list):
            return "\n".join(str(x).strip() for x in v if str(x).strip())
        return str(v).strip()

    def _join(*keys: str, sep: str = "\n") -> str:
        parts = [_s(k) for k in keys if _s(k)]
        return sep.join(parts).strip()

    title = _s("project_title") or _s("title") or "—"
    description = _join("project_what", "project_problem", "audience_type", "working_now", "status", "metrics", "purpose", "inbound_ready", "gtm_notes")
    if not description:
        description = _s("description") or "—"
    stack = _join("stack_ai", "stack_tech", "stack_infra") or _s("stack") or "—"
    links_done = answers.get("links_done")
    if isinstance(links_done, list) and links_done:
        link = links_done[0] if links_done else "—"
    else:
        link = _s("links_done") or _s("link") or "—"
    price = _join("econ_time", "dev_cost", "monthly_cost", "monetization") or _s("price") or "—"
    contact = _join("author_name", "author_contact", "author_role") or _s("contact") or "—"
    return {"title": title, "description": description, "stack": stack, "link": link, "price": price, "contact": contact}


def answers_to_project_fields(answers: dict) -> dict[str, str]:
    """
    Build title, description, stack, link, price, contact from FSM answers (SPEC 05).
    Preserves backward compat: old 6-key answers used as-is when no new keys present.
    Supports V2 keys: project_title, author_*, econ_*, gtm_*, links, etc.
    """
    def _s(k: str) -> str:
        v = answers.get(k)
        if v is None:
            return ""
        if isinstance(v, list):
            return "\n".join(str(x).strip() for x in v if str(x).strip())
        return str(v).strip()

    def _join(*keys: str, sep: str = "\n") -> str:
        parts = [str((answers.get(k) or "")).strip() for k in keys if (answers.get(k) or "").strip()]
        return sep.join(parts).strip()

    # Backward compat: only old flat keys (no V2 / description_what)
    if answers.get("description") is not None and "description_what" not in answers and "project_title" not in answers:
        return {
            "title": str(answers.get("title") or "").strip(),
            "description": str(answers.get("description") or "").strip(),
            "stack": str(answers.get("stack") or "").strip(),
            "link": str(answers.get("link") or "").strip(),
            "price": str(answers.get("price") or "").strip(),
            "contact": str(answers.get("contact") or "").strip(),
        }
    # V2 keys
    if "project_title" in answers or "author_name" in answers:
        title = _s("project_title") or _s("title") or ""
        description = _join("project_subtitle", "project_problem", "project_audience_type", "product_working_now", "product_status", "goal_publication", "goal_inbound_ready")
        if not description:
            description = _join("description_intro", "description_what", "description_audience", "description_summary", "description_features") or _s("description")
        stack = _join("stack_ai", "stack_tech", "stack_infra") or _join("stack", "stack_list", "stack_other")
        links_list = answers.get("links")
        if isinstance(links_list, list) and links_list:
            link = (links_list[0] if links_list else "") or _s("link")
        else:
            link = _s("links_done") or _join("link", "link_demo", "link_confirm")
        price = _format_dev_cost_v2(answers) or _join("econ_monet_format", "econ_monet_details") or _join("price", "price_note", "price_currency")
        contact = _join("author_name", "author_telegram", "author_email", "author_role") or _join("contact", "contact_extra", "contact_preferred")
        gtm_stage = _s("gtm_stage")
        gtm_channels = answers.get("gtm_channels")
        gtm_traction = _s("gtm_traction")
        return {"title": title, "description": description, "stack": stack, "link": link, "price": price, "contact": contact, "gtm_stage": gtm_stage, "gtm_channels": gtm_channels, "gtm_traction": gtm_traction}
    # V1 keys
    title = _join("title", "title_subtitle", sep=" ") or str(answers.get("title") or "").strip()
    description = _join("description_intro", "description_what", "description_audience", "description_summary", "description_features")
    stack = _join("stack", "stack_list", "stack_other")
    link = _join("link", "link_demo", "link_confirm")
    price = _join("price", "price_note", "price_currency")
    contact = _join("contact", "contact_extra", "contact_preferred")
    return {"title": title, "description": description, "stack": stack, "link": link, "price": price, "contact": contact}


def _format_dev_cost_v2(answers: dict) -> str:
    """Format dev cost: HIDDEN => не раскрываю; range => ₽ 50 000 – 120 000.
    Supports budget_* (new single-step) and econ_dev_cost_* (legacy) keys."""
    if answers.get("budget_hidden") is True:
        return "не раскрываю"
    mn = answers.get("budget_min")
    mx = answers.get("budget_max")
    cur = (answers.get("budget_currency") or "").strip().upper()
    if mn is not None or mx is not None or cur:
        try:
            min_v = int(mn) if mn is not None else None
            max_v = int(mx) if mx is not None else None
        except (TypeError, ValueError):
            min_v = max_v = None
        currency = cur or "RUB"
    else:
        currency = (answers.get("econ_dev_cost_currency") or "").strip().upper()
        if currency == "HIDDEN":
            return "не раскрываю"
        min_v = answers.get("econ_dev_cost_min")
        max_v = answers.get("econ_dev_cost_max")
    if min_v is not None or max_v is not None:
        try:
            mn = int(min_v) if min_v is not None else None
            mx = int(max_v) if max_v is not None else None
        except (TypeError, ValueError):
            return ""
        if mn is not None and mx is not None:
            sep = " – "
            if currency == "RUB":
                return f"₽ {mn:,} {sep} {mx:,}".replace(",", " ")
            if currency == "USD":
                return f"$ {mn:,} {sep} {mx:,}".replace(",", " ")
        if mn is not None:
            return f"₽ {mn:,}".replace(",", " ") if currency == "RUB" else f"$ {mn:,}".replace(",", " ") if currency == "USD" else str(mn)
        if mx is not None:
            return f"₽ {mx:,}".replace(",", " ") if currency == "RUB" else f"$ {mx:,}".replace(",", " ") if currency == "USD" else str(mx)
    return ""


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
    *,
    gtm_stage: str = "",
    gtm_channels: str | list | None = None,
    gtm_traction: str = "",
) -> str:
    """
    PROJECT_POST template (SPEC 05).
    Clear sections, spacing, emojis. Empty optional sections omitted.
    GTM section near bottom when provided. All user content escaped for HTML parse_mode.
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

    # GTM section (V2)
    gtm_parts = []
    if (gtm_stage or "").strip():
        gtm_parts.append(f"— Stage: {escape_html((gtm_stage or '').strip())}")
    if gtm_channels:
        ch = gtm_channels if isinstance(gtm_channels, str) else ", ".join(str(x).strip() for x in gtm_channels if str(x).strip())
        if ch.strip():
            gtm_parts.append(f"— Channels: {escape_html(ch.strip())}")
    if (gtm_traction or "").strip():
        gtm_parts.append(f"— Traction: {escape_html((gtm_traction or '').strip())}")
    if gtm_parts:
        parts.append("<b>Go-to-market:</b>\n" + "\n".join(gtm_parts))

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
