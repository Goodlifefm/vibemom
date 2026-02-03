"""Step 4.5 verification: V2 validators, step registry, save message, step format."""
from src.v2.format_step import format_step_message, parse_copy_to_parts
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


def test_format_step_message_unified_template():
    """Единый шаблон: Шаг X из Y, пустая строка, заголовок, пояснение, пример."""
    text = format_step_message(
        step_num=1,
        total=21,
        title="Название проекта",
        intro="Короткое пояснение.",
        todo=None,
        example="AI-ассистент",
    )
    assert text.startswith("Шаг 1 из 21")
    assert "\n\n" in text
    assert "📌" in text
    assert "Название проекта" in text
    assert "Короткое пояснение" in text
    assert "Пример:" in text
    assert "AI-ассистент" in text


def test_parse_copy_to_parts():
    """Из копирайта извлекаются title, intro, example."""
    copy_text = "Заголовок шага\nПояснение строка.\nПример: значение"
    parts = parse_copy_to_parts(copy_text)
    assert parts["title"] == "Заголовок шага"
    assert "Пояснение" in (parts["intro"] or "")
    assert parts["example"] == "значение"
    assert parts["todo"] is None
