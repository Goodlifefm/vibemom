import os

import pytest


@pytest.fixture(autouse=True)
def _test_env():
    """Ensure BOT_TOKEN is set so Settings() does not fail (CI sets it; local may not)."""
    if "BOT_TOKEN" not in os.environ:
        os.environ["BOT_TOKEN"] = "dummy"


@pytest.fixture
def sample_project():
    return {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Notion база",
        "description": "База для учёта задач и проектов",
        "stack": "Notion, Make",
        "price": "5000 руб",
        "link": "https://example.com",
    }


@pytest.fixture
def sample_request():
    return {
        "what": "Нужна база в Notion для задач",
        "budget": "5000",
        "contact": "@user",
    }
