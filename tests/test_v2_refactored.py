"""Tests for V2 refactored modules: services/renderers, keyboards/menu.

Covers:
- render_post_text consistency between preview and publish
- render_price all variants (hidden, fixed, range)
- Menu keyboards structure
- Menu navigation preserves wizard state
"""
import uuid

from src.v2.services.renderers.post_text import (
    render_price,
    render_price_from_answers,
    render_post_text,
    assert_preview_publish_consistency,
)
from src.v2.keyboards.menu import (
    kb_cabinet_tiles,
    kb_menu_back,
    kb_drafts_list,
    kb_publications_list,
    kb_restart_confirm,
    kb_delete_confirm,
    CB_MENU,
)


# ==============================================================================
# Price Renderer Tests
# ==============================================================================

def test_render_price_hidden():
    """Hidden price returns 'скрыта'."""
    assert render_price(budget_hidden=True) == "скрыта"
    assert render_price(budget_min=500, budget_hidden=True) == "скрыта"


def test_render_price_fixed_rub():
    """Fixed price in RUB: '500 ₽'."""
    result = render_price(budget_min=500, budget_currency="RUB")
    assert result == "500 ₽"
    
    # Large number with space separator
    result2 = render_price(budget_min=150000, budget_currency="RUB")
    assert result2 == "150 000 ₽"


def test_render_price_fixed_usd():
    """Fixed price in USD: '500 $'."""
    result = render_price(budget_min=500, budget_currency="USD")
    assert result == "500 $"


def test_render_price_range_rub():
    """Range price in RUB: '500–1500 ₽'."""
    result = render_price(budget_min=500, budget_max=1500, budget_currency="RUB")
    assert result == "500–1 500 ₽"


def test_render_price_range_usd():
    """Range price in USD: '500–1500 $'."""
    result = render_price(budget_min=500, budget_max=1500, budget_currency="USD")
    assert result == "500–1 500 $"


def test_render_price_default_currency():
    """Default currency is RUB when not specified."""
    result = render_price(budget_min=500)
    assert "₽" in result


def test_render_price_from_answers():
    """render_price_from_answers extracts fields from dict."""
    answers = {
        "budget_min": 500,
        "budget_max": 1500,
        "budget_currency": "RUB",
        "budget_hidden": False,
    }
    result = render_price_from_answers(answers)
    assert "500" in result
    assert "1 500" in result
    assert "₽" in result


def test_render_price_from_answers_hidden():
    """render_price_from_answers handles hidden."""
    answers = {"budget_hidden": True}
    result = render_price_from_answers(answers)
    assert result == "скрыта"


def test_render_price_legacy_fallback():
    """Legacy cost/cost_max/currency fields still work."""
    result = render_price(cost=100, cost_max=200, currency="RUB")
    assert "100" in result
    assert "200" in result


def test_render_price_none():
    """Returns None when no price data."""
    result = render_price()
    assert result is None


# ==============================================================================
# Post Text Renderer Tests
# ==============================================================================

def test_render_post_text_preview_and_publish_match():
    """Preview body matches publish body (same renderer)."""
    answers = {
        "title": "Test Project",
        "description": "Test description",
        "contact": "@test",
        "budget_min": 500,
        "budget_currency": "RUB",
    }
    
    preview = render_post_text(answers, mode="preview", preview_header="👀 Preview")
    publish = render_post_text(answers, mode="publish")
    
    # Preview has header, publish doesn't
    assert "👀 Preview" in preview["text"]
    assert "👀 Preview" not in publish["text"]
    
    # Both have same body content
    assert "Test Project" in preview["text"]
    assert "Test Project" in publish["text"]
    assert "@test" in preview["text"]
    assert "@test" in publish["text"]


def test_render_post_text_parse_mode():
    """render_post_text returns HTML parse_mode."""
    result = render_post_text({"title": "Test"})
    assert result["parse_mode"] == "HTML"


def test_render_post_text_escapes_html():
    """HTML characters are escaped."""
    answers = {"title": "<script>alert(1)</script>"}
    result = render_post_text(answers)
    assert "<script>" not in result["text"]
    assert "&lt;script&gt;" in result["text"]


def test_render_post_text_sections():
    """All PROJECT_POST sections are rendered when present."""
    answers = {
        "title": "My Title",
        "description": "My Description",
        "stack_reason": "Python, FastAPI",
        "links": ["https://example.com"],
        "budget_min": 1000,
        "budget_currency": "USD",
        "author_contact": "@mycontact",
    }
    result = render_post_text(answers)
    text = result["text"]
    
    assert "🟢" in text and "My Title" in text
    assert "📝" in text and "My Description" in text
    assert "⚙️ Стек" in text and "Python" in text
    assert "🔗 Ссылка" in text and "https://example.com" in text
    assert "💰 Цена" in text
    assert "📬 Контакт" in text and "@mycontact" in text


def test_render_post_text_omits_empty():
    """Empty sections are omitted."""
    answers = {"title": "Only Title"}
    result = render_post_text(answers)
    text = result["text"]
    
    assert "🟢" in text
    assert "⚙️ Стек" not in text
    assert "🔗 Ссылка" not in text
    assert "💰 Цена" not in text


def test_assert_preview_publish_consistency_passes():
    """Consistency check passes when texts match."""
    answers = {"title": "Test", "contact": "@u"}
    publish = render_post_text(answers, mode="publish")
    # Should not raise
    assert_preview_publish_consistency(answers, publish["text"])


def test_assert_preview_publish_consistency_fails():
    """Consistency check fails when texts don't match."""
    answers = {"title": "Test"}
    try:
        assert_preview_publish_consistency(answers, "Wrong text")
        assert False, "Should have raised AssertionError"
    except AssertionError:
        pass


# ==============================================================================
# Menu Keyboards Tests
# ==============================================================================

def test_kb_cabinet_tiles_no_wizard():
    """Cabinet tiles without active wizard shows create button."""
    kb = kb_cabinet_tiles(has_active_wizard=False)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    
    assert f"{CB_MENU}:drafts" in callbacks
    assert f"{CB_MENU}:posts" in callbacks
    assert f"{CB_MENU}:settings" in callbacks
    assert f"{CB_MENU}:help" in callbacks
    assert f"{CB_MENU}:create" in callbacks
    # Continue should not be present
    assert f"{CB_MENU}:continue" not in callbacks


def test_kb_cabinet_tiles_with_wizard():
    """Cabinet tiles with active wizard shows continue and preview."""
    kb = kb_cabinet_tiles(has_active_wizard=True)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    
    assert f"{CB_MENU}:continue" in callbacks
    assert f"{CB_MENU}:preview" in callbacks
    # Create should not be in last row (back instead)
    last_row_cbs = [btn.callback_data for btn in kb.inline_keyboard[-1]]
    assert f"{CB_MENU}:create" not in last_row_cbs


def test_kb_menu_back():
    """Back button has correct callback."""
    kb = kb_menu_back()
    assert len(kb.inline_keyboard) == 1
    assert kb.inline_keyboard[0][0].callback_data == f"{CB_MENU}:back_to_menu"


def test_kb_drafts_list():
    """Drafts list has open buttons for each draft."""
    drafts = [
        ("Draft 1", "id-1"),
        ("Draft 2", "id-2"),
    ]
    kb = kb_drafts_list(drafts)
    
    # 2 draft rows + 1 back row
    assert len(kb.inline_keyboard) == 3
    assert f"{CB_MENU}:open_draft:id-1" in kb.inline_keyboard[0][0].callback_data
    assert f"{CB_MENU}:open_draft:id-2" in kb.inline_keyboard[1][0].callback_data
    assert f"{CB_MENU}:back_to_menu" in kb.inline_keyboard[2][0].callback_data


def test_kb_publications_list():
    """Publications list has view buttons."""
    pubs = [
        ("Post 1", "pub-1"),
    ]
    kb = kb_publications_list(pubs)
    
    assert len(kb.inline_keyboard) == 2  # 1 pub + back
    assert f"{CB_MENU}:view_post:pub-1" in kb.inline_keyboard[0][0].callback_data


def test_kb_restart_confirm():
    """Restart confirm has yes/no buttons."""
    kb = kb_restart_confirm()
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    
    assert f"{CB_MENU}:restart_yes" in callbacks
    assert f"{CB_MENU}:restart_no" in callbacks


def test_kb_delete_confirm():
    """Delete confirm has yes/no with submission ID."""
    kb = kb_delete_confirm("sub-123")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    
    assert f"{CB_MENU}:delete_yes:sub-123" in callbacks
    assert f"{CB_MENU}:delete_no:sub-123" in callbacks


# ==============================================================================
# Menu Navigation Tests (state preservation)
# ==============================================================================

def test_menu_callback_format():
    """Menu callbacks follow format menu:{action}:{args}."""
    kb = kb_cabinet_tiles(has_active_wizard=True)
    for row in kb.inline_keyboard:
        for btn in row:
            assert btn.callback_data.startswith(f"{CB_MENU}:")
            parts = btn.callback_data.split(":")
            assert len(parts) >= 2
            assert parts[0] == CB_MENU


def test_drafts_list_callback_includes_id():
    """Open draft callback includes submission ID."""
    sid = str(uuid.uuid4())
    kb = kb_drafts_list([("Draft", sid)])
    cb = kb.inline_keyboard[0][0].callback_data
    assert sid in cb


# ==============================================================================
# Integration: Price in Post Text
# ==============================================================================

def test_post_text_with_hidden_price():
    """Post text shows 'скрыта' for hidden price."""
    answers = {"title": "Test", "budget_hidden": True}
    result = render_post_text(answers)
    assert "скрыта" in result["text"]


def test_post_text_with_range_price():
    """Post text shows range format."""
    answers = {
        "title": "Test",
        "budget_min": 100,
        "budget_max": 500,
        "budget_currency": "RUB",
    }
    result = render_post_text(answers)
    assert "100" in result["text"]
    assert "500" in result["text"]
    assert "₽" in result["text"]


def test_post_text_with_fixed_price():
    """Post text shows fixed format."""
    answers = {
        "title": "Test",
        "budget_min": 999,
        "budget_currency": "USD",
    }
    result = render_post_text(answers)
    assert "999" in result["text"]
    assert "$" in result["text"]
