"""
V2 validators: email, link (http/https), time (contains digit), cost (currency + amount or "не раскрываю"), contact.
Return (ok: bool, error_copy_id: str | None).
"""
import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
LINK_PREFIX = ("http://", "https://")
COST_HIDDEN_PHRASE = "не раскрываю"


def validate_non_empty(value: str) -> tuple[bool, str | None]:
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    return True, None


def validate_email(value: str) -> tuple[bool, str | None]:
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    if not EMAIL_RE.match(value.strip()):
        return False, "V2_INVALID_EMAIL"
    return True, None


def validate_link(value: str) -> tuple[bool, str | None]:
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    v = value.strip()
    if not (v.startswith(LINK_PREFIX[0]) or v.startswith(LINK_PREFIX[1])):
        return False, "V2_INVALID_LINK"
    return True, None


def validate_time(value: str) -> tuple[bool, str | None]:
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    if not any(c.isdigit() for c in value):
        return False, "V2_INVALID_TIME"
    return True, None


def validate_cost(value: str) -> tuple[bool, str | None]:
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    v = value.strip().lower()
    if COST_HIDDEN_PHRASE in v:
        return True, None
    if any(c.isdigit() for c in v):
        return True, None
    return False, "V2_INVALID_COST"


def validate_contact(value: str) -> tuple[bool, str | None]:
    """Telegram (@...) or email."""
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    v = value.strip()
    if v.startswith("@"):
        return True, None
    return validate_email(v)


VALIDATOR_MAP = {
    "non_empty": validate_non_empty,
    "email": validate_email,
    "link": validate_link,
    "time": validate_time,
    "cost": validate_cost,
    "contact": validate_contact,
}


def validate(validator_name: str, value: str) -> tuple[bool, str | None]:
    fn = VALIDATOR_MAP.get(validator_name)
    if not fn:
        return True, None
    return fn(value)
