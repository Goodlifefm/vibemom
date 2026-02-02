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


# V2 validators
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(text: str | None, max_len: int = 200) -> tuple[bool, str | None]:
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t or len(t) > max_len:
        return False, None
    if not EMAIL_PATTERN.match(t):
        return False, None
    return True, t


def validate_time_spent_has_digit(text: str | None, max_len: int = 200) -> tuple[bool, str | None]:
    """Time spent must contain at least one digit."""
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t or len(t) > max_len:
        return False, None
    if not re.search(r"\d", t):
        return False, None
    return True, t


def validate_int_optional(text: str | None, max_val: int | None = None) -> tuple[bool, int | None]:
    """Parse optional integer. Empty allowed. Returns (ok, value)."""
    if text is None or not isinstance(text, str):
        return False, None
    t = text.strip()
    if not t:
        return True, None
    try:
        n = int(t)
    except ValueError:
        return False, None
    if n < 0:
        return False, None
    if max_val is not None and n > max_val:
        return False, None
    return True, n


def validate_dev_cost_min_max(
    text: str | None, existing_min: int | None = None
) -> tuple[bool, int | None]:
    """Parse int for dev_cost_max; if existing_min set, require value >= existing_min. Returns (ok, value)."""
    ok, n = validate_int_optional(text, max_val=10**9)
    if not ok:
        return ok, n
    if n is not None and existing_min is not None and n < existing_min:
        return False, None
    return True, n
