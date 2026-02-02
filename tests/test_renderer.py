from src.bot.renderer import (
    render_project_post,
    render_buyer_request_summary,
    answers_to_project_fields,
    project_fields_to_answers,
    v2_answers_to_project_fields,
)


def test_render_project_post():
    out = render_project_post(
        title="Test",
        description="Desc",
        stack="Notion",
        link="https://x.com",
        price="100",
        contact="@u",
    )
    assert "Test" in out
    assert "Desc" in out
    assert "Notion" in out
    assert "https://x.com" in out
    assert "100" in out
    assert "@u" in out
    assert "Стек" in out
    assert "Ссылка" in out
    assert "Цена" in out
    assert "Контакт" in out


def test_render_project_post_omits_empty_sections():
    out = render_project_post(
        title="Only title",
        description="",
        stack="",
        link="",
        price="",
        contact="",
    )
    assert "Only title" in out
    assert "🟢" in out
    assert "Стек" not in out
    assert "Ссылка" not in out
    assert "Цена" not in out
    assert "Контакт" not in out


def test_render_project_post_escaping():
    out = render_project_post(
        title="A <script> & \"x\"",
        description="B > C",
        stack="D & E",
        link="https://a.com",
        price="1",
        contact="@u",
    )
    assert "&lt;" in out
    assert "&gt;" in out
    assert "&amp;" in out
    assert "<script>" not in out
    assert "A <script>" not in out


def test_render_project_post_spacing():
    out = render_project_post(
        title="T",
        description="D",
        stack="S",
        link="https://x.com",
        price="P",
        contact="C",
    )
    assert "\n\n" in out
    parts = out.split("\n\n")
    assert len(parts) >= 2


def test_render_buyer_request_summary():
    out = render_buyer_request_summary("Ищу базу", "5000", "@u")
    assert "Ищу базу" in out
    assert "5000" in out
    assert "@u" in out
    assert "Заявка:" in out
    assert "Бюджет:" in out
    assert "Контакт:" in out


def test_render_buyer_request_summary_escaping():
    out = render_buyer_request_summary("A & B <c>", "1", "@u")
    assert "&amp;" in out
    assert "&lt;" in out
    assert "&gt;" in out


def test_answers_to_project_fields_backward_compat():
    """Old 6-key answers map to project fields as-is."""
    answers = {
        "title": "T",
        "description": "D",
        "stack": "S",
        "link": "https://x.com",
        "price": "P",
        "contact": "C",
    }
    out = answers_to_project_fields(answers)
    assert out["title"] == "T"
    assert out["description"] == "D"
    assert out["stack"] == "S"
    assert out["link"] == "https://x.com"
    assert out["price"] == "P"
    assert out["contact"] == "C"


def test_render_project_post_section_order():
    """Section order stable: title -> description -> stack -> link -> price -> contact."""
    out = render_project_post(
        title="T",
        description="D",
        stack="S",
        link="https://x.com",
        price="P",
        contact="C",
    )
    idx_title = out.find("T")
    idx_desc = out.find("D")
    idx_stack = out.find("S")
    idx_link = out.find("https://x.com")
    idx_price = out.find("P")
    idx_contact = out.find("C")
    assert idx_title < idx_desc < idx_stack < idx_link < idx_price < idx_contact


def test_answers_to_project_fields_expanded():
    """New SPEC keys compose title, description, stack, link, price, contact."""
    answers = {
        "title": "Foo",
        "title_subtitle": "Bar",
        "description_what": "What it does",
        "description_audience": "For whom",
        "stack": "Notion",
        "stack_list": "Make",
        "link": "https://a.com",
        "link_demo": "https://b.com",
        "price": "100",
        "price_note": "Packages",
        "contact": "@u",
        "contact_extra": "email@x.com",
    }
    out = answers_to_project_fields(answers)
    assert "Foo" in out["title"]
    assert "Bar" in out["title"]
    assert "What it does" in out["description"]
    assert "For whom" in out["description"]
    assert "Notion" in out["stack"]
    assert "Make" in out["stack"]
    assert "https://a.com" in out["link"]
    assert "https://b.com" in out["link"]
    assert "100" in out["price"]
    assert "Packages" in out["price"]
    assert "@u" in out["contact"]
    assert "email@x.com" in out["contact"]


def test_v2_answers_to_project_fields():
    """V2 extended answers map to 6 columns."""
    answers = {
        "project_title": "My Project",
        "project_what": "What",
        "project_problem": "Problem",
        "audience_type": "Audience",
        "author_name": "Alice",
        "author_contact": "@alice",
        "author_role": "Dev",
        "stack_ai": "GPT",
        "stack_tech": "Python",
        "stack_infra": "AWS",
        "econ_time": "1m",
        "dev_cost": "0",
        "monthly_cost": "10",
        "monetization": "No",
        "links_done": ["https://a.com", "https://b.com"],
    }
    out = v2_answers_to_project_fields(answers)
    assert out["title"] == "My Project"
    assert "What" in out["description"]
    assert "GPT" in out["stack"]
    assert out["link"] == "https://a.com"
    assert "1m" in out["price"]
    assert "Alice" in out["contact"]


def test_project_fields_to_answers_legacy():
    """Legacy 6-column project returns 6 keys + V2 keys."""
    class Project:
        title = "T"
        description = "Plain text"
        stack = "S"
        link = "https://x.com"
        price = "P"
        contact = "C"
    out = project_fields_to_answers(Project())
    assert out.get("project_title") == "T" or out.get("title") == "T"
    assert out.get("description") == "Plain text" or out.get("project_what") == "Plain text"


def test_project_fields_to_answers_json():
    """Project with JSON in description returns full answers."""
    import json
    class Project:
        title = "—"
        description = json.dumps({"project_title": "FromJSON", "author_name": "Bob"})
        stack = "—"
        link = "—"
        price = "—"
        contact = "—"
    out = project_fields_to_answers(Project())
    assert out.get("project_title") == "FromJSON"
    assert out.get("author_name") == "Bob"


def test_render_project_post_v2_fields_included():
    """Renderer includes V2 extended fields when built from v2_answers_to_project_fields."""
    answers = {
        "project_title": "V2 Project",
        "project_what": "What",
        "project_problem": "Problem",
        "audience_type": "Audience",
        "author_name": "Alice",
        "author_contact": "@alice",
        "author_role": "Dev",
        "stack_ai": "GPT",
        "stack_tech": "Python",
        "econ_time": "1m",
        "dev_cost": "0",
        "monthly_cost": "10",
        "monetization": "No",
        "links_done": ["https://example.com"],
    }
    fields = v2_answers_to_project_fields(answers)
    out = render_project_post(
        fields["title"], fields["description"], fields["stack"],
        fields["link"], fields["price"], fields["contact"],
    )
    assert "V2 Project" in out
    assert "What" in out
    assert "Alice" in out
    assert "GPT" in out
    assert "https://example.com" in out
    assert "\n\n" in out


def test_render_project_post_gtm_section():
    """Renderer includes GTM section when gtm_* provided."""
    out = render_project_post(
        "T", "D", "S", "https://x.com", "P", "C",
        gtm_stage="Early", gtm_channels="tg, vk", gtm_traction="100 users",
    )
    assert "Go-to-market" in out
    assert "Stage" in out
    assert "Channels" in out
    assert "Traction" in out
    assert "Early" in out


def test_render_project_post_missing_optional_no_crash():
    """Renderer does not crash for missing optional fields."""
    out = render_project_post("T", "", "", "", "", "", gtm_stage="", gtm_channels=None, gtm_traction="")
    assert "T" in out
    assert "\n\n" in out or out.strip()


def test_answers_to_project_fields_v2_dev_cost():
    """V2 answers: dev cost HIDDEN => не раскрываю, range => formatted."""
    from src.bot.renderer import answers_to_project_fields
    answers = {"project_title": "P", "econ_dev_cost_currency": "HIDDEN"}
    fields = answers_to_project_fields(answers)
    assert fields.get("price") == "не раскрываю"
    answers2 = {"project_title": "P", "econ_dev_cost_currency": "RUB", "econ_dev_cost_min": 50000, "econ_dev_cost_max": 120000}
    fields2 = answers_to_project_fields(answers2)
    assert "50" in (fields2.get("price") or "")
    assert "120" in (fields2.get("price") or "")
