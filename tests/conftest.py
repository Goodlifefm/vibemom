import pytest


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
