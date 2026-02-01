"""Input validation for FSM. No user-facing copy here."""

import re

URL_PATTERN = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$",
    re.IGNORECASE,
)


def validate_non_empty(text: str | None, max_len: int = 10000) -> tuple[bool, str | None]:
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t:
        return False, None
    if len(t) > max_len:
        return False, None
    return True, t


def validate_title(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=200)


def validate_description(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=2000)


def validate_stack(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=500)


def validate_url(text: str | None, max_len: int | None = None) -> tuple[bool, str | None]:
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t:
        return False, None
    if not URL_PATTERN.match(t):
        return False, None
    if max_len is not None and len(t) > max_len:
        return False, None
    return True, t


def validate_url_or_empty(text: str | None, max_len: int = 10000) -> tuple[bool, str | None]:
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t:
        return True, ""
    if len(t) > max_len:
        return False, None
    if not URL_PATTERN.match(t):
        return False, None
    return True, t


def validate_max_len(text: str | None, max_len: int, allow_empty: bool = False) -> tuple[bool, str | None]:
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t:
        return allow_empty, t if allow_empty else None
    if len(t) > max_len:
        return False, None
    return True, t


def validate_price(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=200)


def validate_contact(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=200)


def validate_what(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=2000)


def validate_budget(text: str | None) -> tuple[bool, str | None]:
    return validate_non_empty(text, max_len=200)


YES_VALUES = {"да", "yes", "д", "y"}
NO_VALUES = {"нет", "no", "н", "n"}


def parse_yes_no(text: str | None) -> bool | None:
    if text is None or not isinstance(text, str):
        return None
    t = text.strip().lower()
    if t in YES_VALUES:
        return True
    if t in NO_VALUES:
        return False
    return None
