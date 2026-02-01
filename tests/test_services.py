"""Service layer: matching logic and SPEC 07 threshold."""
import uuid

from src.bot.matching import filter_and_sort_matches


def test_match_threshold_spec_07():
    """SPEC 07: score >= 10 to show project in «Мои заявки»."""
    projects = [
        {"id": str(uuid.uuid4()), "title": "Notion база", "description": "задачи", "price": "5000"},
        {"id": str(uuid.uuid4()), "title": "Совсем другое", "description": "нет совпадений", "price": "1"},
    ]
    matched = filter_and_sort_matches("база Notion", "5000", projects)
    assert len(matched) >= 1
    assert matched[0]["title"] == "Notion база"


def test_match_fallback_empty_spec_07():
    """SPEC 07: If no project scores >= 10, show empty list (no random suggestions)."""
    projects = [
        {"id": "1", "title": "Другое", "description": "другое", "price": "100"},
    ]
    matched = filter_and_sort_matches("дизайн логотипа", "10000", projects)
    assert len(matched) == 0
