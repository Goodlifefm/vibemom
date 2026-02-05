import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


def is_ci_or_test() -> bool:
    """Detect CI/test environment where BOT_TOKEN validation should be relaxed."""
    return (
        os.getenv("CI", "").lower() in ("true", "1", "yes")
        or os.getenv("APP_ENV", "").lower() in ("ci", "test", "testing")
        or os.getenv("PYTEST_CURRENT_TEST") is not None
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str = ""

    @field_validator("bot_token", mode="before")
    @classmethod
    def strip_token(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else ""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vibe_market"
    admin_telegram_ids: str = ""
    admin_ids: str = ""  # preferred over admin_telegram_ids (backward compat)
    admin_chat_id: str = ""
    feed_chat_id: str = ""  # FEED_CHAT_ID: канал для автопубликации одобренных проектов (@vibecode777 или id)
    log_level: str = "INFO"
    app_env: str = "local"  # local, ci, test, production
    auto_migrate: bool = True
    v2_enabled: bool = False
    v2_canary_mode: bool = False
    v2_allowlist: str = ""

    # Mini App WebApp URL (Telegram WebApp)
    webapp_url: str = ""  # e.g., https://myapp.vercel.app

    # Public API URL for Mini App frontend
    api_public_url: str = ""  # e.g., https://api.mydomain.com

    @property
    def is_ci_or_test(self) -> bool:
        """Check if running in CI/test environment."""
        return is_ci_or_test() or self.app_env.lower() in ("ci", "test", "testing")

    def validate_for_runtime(self) -> None:
        """Validate settings for production runtime. Call this in main.py before starting bot."""
        if self.is_ci_or_test:
            return  # Skip validation in CI/test
        if not self.bot_token or self.bot_token.startswith("test_"):
            raise RuntimeError(
                "BOT_TOKEN is required for runtime. "
                "Set a valid Telegram bot token in .env or environment."
            )

    def get_admin_ids(self) -> set[int]:
        raw = (self.admin_ids or self.admin_telegram_ids) or ""
        if not raw:
            return set()
        return {int(x.strip()) for x in raw.split(",") if x.strip()}

    def get_v2_allowlist_ids(self) -> set[int]:
        if not self.v2_allowlist:
            return set()
        return {int(x.strip()) for x in self.v2_allowlist.split(",") if x.strip()}

    def should_use_v2(self, telegram_id: int) -> bool:
        if not self.v2_enabled:
            return False
        if not self.v2_canary_mode:
            return True
        return telegram_id in self.get_admin_ids() or telegram_id in self.get_v2_allowlist_ids()
