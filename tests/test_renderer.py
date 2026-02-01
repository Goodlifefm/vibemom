from src.bot.renderer import render_project_post, render_buyer_request_summary


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
