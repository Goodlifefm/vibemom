from src.bot.validators import (
    validate_title,
    validate_url,
    validate_url_or_empty,
    validate_max_len,
    validate_contact,
    parse_yes_no,
)


def test_validate_title():
    ok, val = validate_title("  Hello  ")
    assert ok is True
    assert val == "Hello"
    assert validate_title("")[0] is False
    assert validate_title(None)[0] is False
    assert validate_title("x" * 201)[0] is False


def test_validate_url():
    ok, val = validate_url("https://example.com/path")
    assert ok is True
    assert "example.com" in val
    assert validate_url("not a url")[0] is False
    assert validate_url("")[0] is False
    assert validate_url("http://ok.com")[0] is True


def test_validate_contact():
    ok, val = validate_contact("  @user  ")
    assert ok is True
    assert val == "@user"
    assert validate_contact("")[0] is False


def test_parse_yes_no():
    assert parse_yes_no("да") is True
    assert parse_yes_no("Да") is True
    assert parse_yes_no("нет") is False
    assert parse_yes_no("Нет") is False
    assert parse_yes_no("yes") is True
    assert parse_yes_no("no") is False
    assert parse_yes_no("что-то") is None
    assert parse_yes_no("") is None


def test_validate_url_max_len():
    ok, _ = validate_url("https://example.com/" + "a" * 1000, max_len=1000)
    assert ok is False
    ok, val = validate_url("https://example.com/short", max_len=1000)
    assert ok is True
    assert "short" in (val or "")


def test_validate_url_or_empty():
    ok, val = validate_url_or_empty("")
    assert ok is True
    assert val == ""
    ok, val = validate_url_or_empty("  ")
    assert ok is True
    assert val == ""
    ok, _ = validate_url_or_empty("not-a-url")
    assert ok is False
    ok, val = validate_url_or_empty("https://ok.com", max_len=100)
    assert ok is True
    assert "ok.com" in (val or "")


def test_validate_max_len():
    ok, val = validate_max_len("hello", 10)
    assert ok is True
    assert val == "hello"
    ok, _ = validate_max_len("too long text", 5)
    assert ok is False
    ok, val = validate_max_len("", 10, allow_empty=True)
    assert ok is True
    assert val == ""
    ok, val = validate_max_len("", 10, allow_empty=False)
    assert ok is False
    assert val is None


def test_validate_url_each_link():
    """Links: allow empty; if user enters, validate each (link collector)."""
    from src.bot.validators import validate_url
    urls = ["https://a.com", "https://b.com/path", "not-a-url", "http://ok.com"]
    results = [validate_url(u) for u in urls]
    assert results[0][0] is True and "a.com" in (results[0][1] or "")
    assert results[1][0] is True
    assert results[2][0] is False
    assert results[3][0] is True


def test_validate_time_spent_has_digit():
    """time_spent must contain at least one digit."""
    from src.bot.validators import validate_time_spent_has_digit
    assert validate_time_spent_has_digit("2 weeks")[0] is True
    assert validate_time_spent_has_digit("no digits")[0] is False
    assert validate_time_spent_has_digit("")[0] is False


def test_validate_email():
    """Email regex validation."""
    from src.bot.validators import validate_email
    assert validate_email("user@example.com")[0] is True
    assert validate_email("not-an-email")[0] is False
    assert validate_email("")[0] is False


def test_validate_int_optional_and_dev_cost_max():
    """dev_cost_min/max: numeric and max >= min when both set."""
    from src.bot.validators import validate_int_optional, validate_dev_cost_min_max
    ok, n = validate_int_optional("50000")
    assert ok is True and n == 50000
    ok, n = validate_int_optional("")
    assert ok is True and n is None
    ok, n = validate_dev_cost_min_max("120000", existing_min=50000)
    assert ok is True and n == 120000
    ok, n = validate_dev_cost_min_max("10000", existing_min=50000)
    assert ok is False
