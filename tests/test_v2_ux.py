"""Step 4.5 verification: V2 validators, step registry, save message."""
from src.v2.validators import (
    validate_non_empty,
    validate_email,
    validate_link,
    validate_time,
    validate_cost,
    validate_contact,
)
from src.v2.fsm.steps import get_step, is_optional, is_multi_link, get_next_step, get_prev_step
from src.bot.messages import get_copy


def test_validators():
    assert validate_non_empty("") == (False, "V2_INVALID_REQUIRED")
    assert validate_non_empty("x") == (True, None)
    assert validate_email("bad") == (False, "V2_INVALID_EMAIL")
    assert validate_email("u@h.co") == (True, None)
    assert validate_link("ftp://x") == (False, "V2_INVALID_LINK")
    assert validate_link("https://x.co") == (True, None)
    assert validate_time("none") == (False, "V2_INVALID_TIME")
    assert validate_time("2 months") == (True, None)
    assert validate_cost("") == (False, "V2_INVALID_REQUIRED")
    assert validate_cost("не раскрываю") == (True, None)
    assert validate_contact("@u") == (True, None)


def test_step_registry_q8_q14_q18_optional():
    assert is_optional("q8") is True
    assert is_optional("q14") is True
    assert is_optional("q18") is True
    assert is_optional("q1") is False


def test_step_registry_q21_multi_link():
    assert is_multi_link("q21") is True
    assert is_multi_link("q1") is False
    s = get_step("q21")
    assert s is not None
    assert s["answer_key"] == "links"


def test_save_message_exact():
    msg = get_copy("V2_SAVED_RESUME")
    assert "Сохранено" in msg
    assert "/resume" in msg
