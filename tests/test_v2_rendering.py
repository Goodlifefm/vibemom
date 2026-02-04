"""Step 5 verification: V2 renderer per SPEC 05 (escape, structure, optional omitted)."""
from src.v2.rendering import (
    render_project_post_html,
    render_submission_to_html,
    submission_answers_to_blocks,
)


def test_html_escaping():
    """User-provided <, >, & must be escaped; no raw script or tags in output."""
    answers = {
        "title": "<script>alert(1)</script>",
        "description": "a & b <tag>",
        "contact": '">injected',
    }
    html_out = render_submission_to_html(answers)
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "&amp;" in html_out
    assert "&lt;" in html_out
    assert "&gt;" in html_out
    assert '">injected' not in html_out
    assert "&quot;" in html_out


def test_project_post_structure():
    """PROJECT_POST has title, description, stack, link, price, contact sections when present."""
    blocks = {
        "title": "My Project",
        "description": "Does X for Y",
        "stack": "Notion, Airtable",
        "link": "https://example.com",
        "price": "5 000 ₽",
        "contact": "@user",
    }
    html_out = render_project_post_html(blocks)
    assert "🟢" in html_out and "My Project" in html_out
    assert "📝" in html_out and "Does X for Y" in html_out
    assert "⚙️ Стек" in html_out and "Notion" in html_out
    assert "🔗 Ссылка" in html_out and "https://example.com" in html_out
    assert "💰 Цена" in html_out and "5 000" in html_out
    assert "📬 Контакт" in html_out and "@user" in html_out


def test_submission_answers_budget_format():
    """submission_answers_to_blocks: budget_min/max/currency/hidden produce price."""
    # Hidden price
    answers = {"title": "X", "budget_hidden": True}
    blocks = submission_answers_to_blocks(answers)
    assert blocks.get("price") == "скрыта"
    
    # Range price
    answers2 = {"title": "X", "budget_min": 150000, "budget_max": 300000, "budget_currency": "RUB"}
    blocks2 = submission_answers_to_blocks(answers2)
    assert "150" in (blocks2.get("price") or "")
    assert "300" in (blocks2.get("price") or "")
    assert "₽" in (blocks2.get("price") or "")
    
    # Fixed price
    answers3 = {"title": "X", "budget_min": 500, "budget_currency": "USD"}
    blocks3 = submission_answers_to_blocks(answers3)
    assert "500" in (blocks3.get("price") or "")
    assert "$" in (blocks3.get("price") or "")


def test_optional_sections_omitted():
    """Empty/absent stack, link, price are omitted from output."""
    blocks = {
        "title": "Only Title",
        "description": None,
        "stack": None,
        "link": "",
        "price": None,
        "contact": "me@x.com",
    }
    html_out = render_project_post_html(blocks)
    assert "🟢" in html_out and "Only Title" in html_out
    assert "📬 Контакт" in html_out and "me@x.com" in html_out
    assert "⚙️ Стек" not in html_out
    assert "🔗 Ссылка" not in html_out
    assert "💰 Цена" not in html_out
