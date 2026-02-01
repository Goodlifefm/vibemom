"""Formatting and escaping helpers for Telegram HTML parse_mode."""


def escape_html(s: str) -> str:
    """Escape <, >, & for Telegram HTML parse_mode. Safe for user-provided content."""
    if not s:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
