"""Step 4.5 verification: V2 validators, step registry, save message, step format.
Step 5: V2 UI Kit UX contracts (render_step, render_error, keyboards, callbacks)."""
from src.v2.format_step import format_step_message, parse_copy_to_parts
from src.v2.validators import (
    validate_non_empty,
    validate_email,
    validate_link,
    validate_time,
    validate_cost,
    validate_budget,
    parse_budget,
    validate_contact,
)
from src.v2.fsm.steps import get_step, is_optional, is_multi_link
from src.bot.messages import get_copy
from src.v2.ui import (
    render_step,
    render_error,
    render_preview_card,
    render_cabinet_status,
    kb_step,
    kb_preview,
    kb_cabinet,
    kb_moderation_admin,
    V2_FORM_PREFIX,
    V2_PREVIEW_PREFIX,
    V2_MENU_PREFIX,
    V2_MOD_PREFIX,
    build_callback,
    parse_callback,
)
import uuid


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
    assert validate_budget("") == (False, "V2_INVALID_REQUIRED")
    assert validate_budget("HIDDEN") == (True, None)
    assert validate_budget("150000-300000 RUB") == (True, None)
    assert validate_budget("500 USD") == (True, None)
    assert validate_budget("invalid") == (False, "V2_INVALID_BUDGET")
    assert validate_contact("@u") == (True, None)


def test_parse_budget():
    assert parse_budget("HIDDEN") == {"budget_min": None, "budget_max": None, "budget_currency": None, "budget_hidden": True}
    assert parse_budget("500 USD") == {"budget_min": 500, "budget_max": None, "budget_currency": "USD", "budget_hidden": False}
    assert parse_budget("150000-300000 RUB") == {"budget_min": 150000, "budget_max": 300000, "budget_currency": "RUB", "budget_hidden": False}
    assert parse_budget("100") == {"budget_min": 100, "budget_max": None, "budget_currency": "RUB", "budget_hidden": False}


def test_step_registry_q8_q12_q16_optional():
    assert is_optional("q8") is True
    assert is_optional("q12") is True
    assert is_optional("q16") is True
    assert is_optional("q1") is False


def test_step_registry_q19_multi_link():
    assert is_multi_link("q19") is True
    assert is_multi_link("q1") is False
    s = get_step("q19")
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
        total=19,
        title="Название проекта",
        intro="Короткое пояснение.",
        todo=None,
        example="AI-ассистент",
    )
    assert text.startswith("Шаг 1 из 19")
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


# ---- Button / callback routing (invariants) ----
def test_callback_prefixes_single_source():
    """Key callback_data prefixes used by V2 routers (v2form, v2preview, v2menu, v2mod)."""
    from src.v2.routers.form import PREFIX as FORM_PREFIX
    from src.v2.routers.preview import PREFIX as PREVIEW_PREFIX
    from src.bot.keyboards import MENU_PREFIX
    from src.v2.routers.moderation import PREFIX as MOD_PREFIX
    assert FORM_PREFIX == "v2form"
    assert PREVIEW_PREFIX == "v2preview"
    assert MENU_PREFIX == "v2menu"
    assert MOD_PREFIX == "v2mod"


def test_submit_no_returns_to_preview():
    """Submit No must not end flow: handler calls show_preview (return to Preview)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from src.v2.routers.preview import cb_submit_no

    callback = MagicMock()
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    state = MagicMock()
    state.get_data = AsyncMock(return_value={"submission_id": "00000000-0000-0000-0000-000000000001", "current_step_key": "preview"})

    async def run():
        with patch("src.v2.routers.preview.show_preview", new_callable=AsyncMock) as show_preview:
            await cb_submit_no(callback, state)
            show_preview.assert_called_once_with(callback.message, state)

    asyncio.run(run())


def test_menu_handler_shows_cabinet():
    """Menu trigger (any state) must show cabinet; handler calls show_cabinet_menu."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from src.v2.routers.menu import handle_menu_trigger

    message = MagicMock()
    message.from_user = MagicMock(id=123)
    state = MagicMock()
    state.get_data = AsyncMock(return_value={})

    async def run():
        with patch("src.v2.routers.menu.show_cabinet_menu", new_callable=AsyncMock) as show_cabinet:
            await handle_menu_trigger(message, state)
            show_cabinet.assert_called_once_with(message, state)

    asyncio.run(run())


def test_persistent_reply_kb():
    """persistent_reply_kb creates reply keyboard with ☰ Меню button."""
    from src.bot.keyboards import persistent_reply_kb
    kb = persistent_reply_kb()
    assert kb is not None
    assert kb.keyboard is not None
    assert len(kb.keyboard) == 1
    assert len(kb.keyboard[0]) == 1
    assert "Меню" in kb.keyboard[0][0].text
    assert kb.resize_keyboard is True
    assert kb.one_time_keyboard is False


def test_cabinet_menu_inline_kb():
    """cabinet_menu_inline_kb creates inline keyboard with menu options."""
    from src.bot.keyboards import cabinet_menu_inline_kb, CB_MENU
    
    # Without active wizard
    kb = cabinet_menu_inline_kb(has_active_wizard=False)
    assert kb is not None
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert f"{CB_MENU}:drafts" in callbacks
    assert f"{CB_MENU}:posts" in callbacks
    assert f"{CB_MENU}:settings" in callbacks
    assert f"{CB_MENU}:help" in callbacks
    assert f"{CB_MENU}:create" in callbacks
    # Continue should not be present when no active wizard
    assert f"{CB_MENU}:continue" not in callbacks
    
    # With active wizard
    kb2 = cabinet_menu_inline_kb(has_active_wizard=True)
    callbacks2 = [btn.callback_data for row in kb2.inline_keyboard for btn in row]
    assert f"{CB_MENU}:continue" in callbacks2
    assert f"{CB_MENU}:preview" in callbacks2


def test_menu_mode_constants():
    """Menu mode constants are defined in keyboards module."""
    from src.bot.keyboards import CB_MENU, CB_WIZ, CB_POST
    assert CB_MENU == "menu"
    assert CB_WIZ == "wiz"
    assert CB_POST == "post"


def test_new_menu_copy_strings():
    """New menu copy strings are present in messages module."""
    from src.bot.messages import get_copy
    
    # Check that new copy strings exist
    assert get_copy("V2_MENU_PERSISTENT_BTN") != ""
    assert get_copy("V2_MENU_SCREEN_TITLE") != ""
    assert get_copy("V2_MENU_CONTINUE_WIZARD") != ""
    assert get_copy("V2_MENU_PREVIEW") != ""
    assert get_copy("V2_MENU_DRAFTS") != ""
    assert get_copy("V2_MENU_PUBLICATIONS") != ""
    assert get_copy("V2_MENU_SETTINGS") != ""
    assert get_copy("V2_MENU_HELP_BTN") != ""
    assert get_copy("V2_MENU_BACK") != ""
    assert get_copy("V2_DRAFTS_HEADER") != ""
    assert get_copy("V2_SETTINGS_HEADER") != ""


# ---- UI Kit UX Contracts (Step 5) ----
def test_render_step_contract():
    """render_step returns string with "Шаг X из Y" and HTML formatting."""
    # Using the new render_step signature: (step_key, answers)
    text = render_step(
        step_key="q1",
        answers=None,
    )
    assert isinstance(text, str)
    assert "Шаг 1 из 19" in text
    assert "📌" in text
    assert "<b>" in text  # HTML formatting
    # The title is from the copy, not a direct argument
    assert "Название проекта" in text or "проект" in text.lower()
    assert "Пример:" in text or "example" in text.lower()


def test_render_error_contract():
    """render_error returns string with "❌ <b>Ошибка</b>" and error message."""
    text = render_error("required")
    assert isinstance(text, str)
    assert "❌" in text
    assert "<b>Ошибка</b>" in text
    assert "Нужен ответ" in text or "ответ" in text.lower()


def test_render_preview_card_contract():
    """render_preview_card returns dict with text, parse_mode, disable_web_page_preview."""
    data = {
        "title": "Test Project",
        "description": "Test description",
        "contact": "@test",
    }
    result = render_preview_card(data, mode="preview")
    assert isinstance(result, dict)
    assert "text" in result
    assert result["parse_mode"] == "HTML"
    assert "disable_web_page_preview" in result
    assert "Test Project" in result["text"]


def test_render_cabinet_status_contract():
    """render_cabinet_status returns HTML string with project and step info."""
    text = render_cabinet_status(
        project_name="Test Project",
        step_key="q1",
        step_num=1,
        total=19,
    )
    assert isinstance(text, str)
    assert "📊" in text
    assert "<b>Текущий проект:</b>" in text
    assert "Test Project" in text
    assert "📍" in text
    assert "<b>Шаг:</b>" in text
    assert "1 из 19" in text


def test_kb_step_contract():
    """kb_step returns InlineKeyboardMarkup with back button."""
    kb = kb_step(back=True, skip=False, save=False)
    assert kb is not None
    assert len(kb.inline_keyboard) > 0
    assert any(btn.callback_data == build_callback(V2_FORM_PREFIX, "back") 
               for row in kb.inline_keyboard for btn in row)


def test_kb_preview_contract():
    """kb_preview returns InlineKeyboardMarkup with submit, edit, menu buttons."""
    kb = kb_preview(submit=True, edit=True, menu=True)
    assert kb is not None
    assert len(kb.inline_keyboard) > 0
    # Check that submit callback exists
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert any(cb == build_callback(V2_PREVIEW_PREFIX, "submit") for cb in callbacks)


def test_kb_cabinet_contract():
    """kb_cabinet returns InlineKeyboardMarkup with menu buttons."""
    kb = kb_cabinet(show_resume=True, has_projects=True)
    assert kb is not None
    assert len(kb.inline_keyboard) > 0
    # Check that resume callback exists when show_resume=True
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert any(cb == build_callback(V2_MENU_PREFIX, "resume") for cb in callbacks)


def test_kb_moderation_admin_contract():
    """kb_moderation_admin returns InlineKeyboardMarkup with approve/needs_fix/reject buttons."""
    sub_id = uuid.uuid4()
    kb = kb_moderation_admin(sub_id)
    assert kb is not None
    assert len(kb.inline_keyboard) > 0
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert any(build_callback(V2_MOD_PREFIX, "approve", str(sub_id)) in cb for cb in callbacks)


def test_callback_prefixes_from_ui_kit():
    """Callback prefixes come from UI Kit callbacks module."""
    assert V2_FORM_PREFIX == "v2form"
    assert V2_PREVIEW_PREFIX == "v2preview"
    assert V2_MENU_PREFIX == "v2menu"
    assert V2_MOD_PREFIX == "v2mod"


def test_build_callback_contract():
    """build_callback creates callback_data string."""
    cb = build_callback("v2form", "back")
    assert cb == "v2form:back"
    cb2 = build_callback("v2mod", "approve", "123")
    assert cb2 == "v2mod:approve:123"


def test_parse_callback_contract():
    """parse_callback parses callback_data into (prefix, action, args)."""
    prefix, action, args = parse_callback("v2form:back")
    assert prefix == "v2form"
    assert action == "back"
    assert args == []
    
    prefix2, action2, args2 = parse_callback("v2mod:approve:123")
    assert prefix2 == "v2mod"
    assert action2 == "approve"
    assert args2 == ["123"]
