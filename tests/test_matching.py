from src.bot.matching import score_match, filter_and_sort_matches, _tokenize


def test_tokenize():
    tokens = _tokenize("Нужна база в Notion для задач")
    assert "база" in tokens or "нужна" in tokens
    assert "и" not in tokens
    assert "в" not in tokens


def test_score_match_keyword_overlap():
    s = score_match(
        request_what="база Notion задачи",
        request_budget="5000",
        project_title="Notion база",
        project_description="База для учёта задач",
        project_price="5000 руб",
    )
    assert s >= 10


def test_score_match_no_overlap():
    s = score_match(
        request_what="дизайн логотипа",
        request_budget="10000",
        project_title="Notion база",
        project_description="База для учёта",
        project_price="5000",
    )
    assert s >= 0


def test_filter_and_sort_matches():
    projects = [
        {"id": "1", "title": "Notion база", "description": "задачи", "price": "5000"},
        {"id": "2", "title": "Другое", "description": "другое", "price": "100"},
    ]
    matched = filter_and_sort_matches("база Notion задачи", "5000", projects)
    assert len(matched) >= 1
    assert matched[0]["title"] == "Notion база"


def test_filter_and_sort_matches_threshold():
    projects = [
        {"id": "1", "title": "Совсем другое", "description": "нет совпадений", "price": "1"},
    ]
    matched = filter_and_sort_matches("база Notion", "5000", projects)
    assert len(matched) == 0
