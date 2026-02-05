"""
Application configuration using pydantic-settings.

All settings are loaded from environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vibe_market"

    # Telegram Bot Token (for validating initData)
    bot_token: str = ""

    # JWT Settings
    api_jwt_secret: str = "change-me-in-production"
    api_jwt_ttl_min: int = 43200  # 30 days in minutes

    # CORS
    webapp_origins: str = ""  # Comma-separated list of allowed origins

    # Admin IDs
    admin_ids: str = ""
    admin_telegram_ids: str = ""  # Legacy fallback

    # Application info
    app_env: str = "local"
    log_level: str = "INFO"

    # Version info (set by CI/CD)
    git_sha: str = "unknown"
    git_branch: str = "unknown"
    build_time: str = "unknown"

    def get_admin_ids(self) -> set[int]:
        """Get set of admin telegram IDs."""
        raw = (self.admin_ids or self.admin_telegram_ids) or ""
        if not raw:
            return set()
        return {int(x.strip()) for x in raw.split(",") if x.strip()}

    def get_cors_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        if not self.webapp_origins:
            return []
        return [origin.strip() for origin in self.webapp_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
