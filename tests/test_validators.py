from src.bot.validators import (
    validate_title,
    validate_description,
    validate_stack,
    validate_url,
    validate_price,
    validate_contact,
    validate_what,
    validate_budget,
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
