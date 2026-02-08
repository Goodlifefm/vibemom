"""
V2 validators: email, link (http/https), time (contains digit), cost (legacy), budget, contact.
Return (ok: bool, error_copy_id: str | None).
For budget: returns (ok, None) and stores parsed result via side effect — use parse_budget() for value.
"""
import re
from typing import Any

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
LINK_PREFIX = ("http://", "https://")
COST_HIDDEN_PHRASE = "не раскрываю"

# Currency detection: RUB, USD (case-insensitive)
CURRENCY_RE = re.compile(r"\b(RUB|USD|₽|\$)\b", re.IGNORECASE)
# Single number: digits, optional spaces as thousand separators
NUMBER_RE = re.compile(r"[\d\s]+")
# Range: X-Y or X–Y (en-dash) or X - Y
RANGE_RE = re.compile(r"^([\d\s]+)\s*[-–—]\s*([\d\s]+)\s*", re.IGNORECASE)


def parse_budget(text: str) -> dict[str, Any] | None:
    """
    Parse budget input into normalized structure.
    Returns dict with: budget_min, budget_max, budget_currency, budget_hidden.
    - HIDDEN => budget_hidden=True, others null
    - Single value => budget_min=value, budget_max=None, currency from text or RUB
    - Range X-Y => budget_min, budget_max, currency from text or RUB
    Returns None if parse failed.
    """
    if not text or not text.strip():
        return None
    t = text.strip()

    # HIDDEN
    if t.upper() == "HIDDEN":
        return {"budget_min": None, "budget_max": None, "budget_currency": None, "budget_hidden": True}

    # Extract currency (RUB/USD) if present
    currency = None
    currency_match = CURRENCY_RE.search(t)
    if currency_match:
        raw = currency_match.group(1).upper()
        if raw in ("RUB", "₽"):
            currency = "RUB"
        elif raw in ("USD", "$"):
            currency = "USD"
    if currency is None:
        currency = "RUB"  # default

    # Remove currency tokens for number parsing
    t_clean = CURRENCY_RE.sub("", t).strip()

    # Range: X-Y
    range_match = RANGE_RE.match(t_clean)
    if range_match:
        s1, s2 = range_match.group(1), range_match.group(2)
        n1 = _parse_int(s1)
        n2 = _parse_int(s2)
        if n1 is not None and n2 is not None and n1 <= n2:
            return {
                "budget_min": n1,
                "budget_max": n2,
                "budget_currency": currency,
                "budget_hidden": False,
            }
        if n1 is not None and n2 is not None and n1 > n2:
            # swap so min <= max
            return {
                "budget_min": n2,
                "budget_max": n1,
                "budget_currency": currency,
                "budget_hidden": False,
            }
        return None

    # Single number
    num = _parse_int(t_clean)
    if num is not None and num >= 0:
        return {
            "budget_min": num,
            "budget_max": None,
            "budget_currency": currency,
            "budget_hidden": False,
        }
    return None


def _parse_int(s: str) -> int | None:
    """Parse string to int, allowing spaces as thousand separators."""
    if not s:
        return None
    clean = "".join(c for c in s if c.isdigit())
    if not clean:
        return None
    try:
        return int(clean)
    except ValueError:
        return None


def validate_budget(value: str) -> tuple[bool, str | None]:
    """
    Validate budget input: HIDDEN, single number, or range X-Y.
    Returns (ok, error_copy_id).
    """
    if not value or not value.strip():
        return False, "V2_INVALID_REQUIRED"
    parsed = parse_budget(value)
    if parsed is None:
        return False, "V2_INVALID_BUDGET"
    return True, None


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
    "budget": validate_budget,
    "contact": validate_contact,
}


def validate(validator_name: str, value: str) -> tuple[bool, str | None]:
    fn = VALIDATOR_MAP.get(validator_name)
    if not fn:
        return True, None
    return fn(value)
