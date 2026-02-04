import os

import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    """
    Ensure test environment is isolated from production.

    Sets safe defaults for all required env vars so tests can run
    without real secrets (CI or local).
    """
    # Mark as test environment
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("CI", "true")

    # Safe dummy values for required settings
    if "BOT_TOKEN" not in os.environ or not os.environ["BOT_TOKEN"]:
        monkeypatch.setenv("BOT_TOKEN", "test_token_for_tests")

    if "DATABASE_URL" not in os.environ or not os.environ["DATABASE_URL"]:
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
        )

    # Ensure V2 is disabled by default in tests (unless explicitly set)
    if "V2_ENABLED" not in os.environ:
        monkeypatch.setenv("V2_ENABLED", "false")


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


@pytest.fixture
def test_settings():
    """Provide a Settings instance configured for testing."""
    from src.bot.config import Settings

    return Settings(
        bot_token="test_token",
        database_url="postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
        app_env="test",
        v2_enabled=False,
    )
