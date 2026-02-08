"""
Application configuration using pydantic-settings.

All settings are loaded from environment variables.
"""

from functools import lru_cache
from urllib.parse import urlparse
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

    # Channel for auto-posting approved projects.
    # Prefer TARGET_CHANNEL_ID; FEED_CHAT_ID is kept for backward compatibility.
    target_channel_id: str = ""
    feed_chat_id: str = ""  # Legacy alias for target_channel_id

    # JWT Settings
    api_jwt_secret: str = "change-me-in-production"
    api_jwt_ttl_min: int = 43200  # 30 days in minutes

    # CORS configuration (comma-separated list of allowed origins)
    # Priority: allowed_origins > api_cors_origins > webapp_origins
    allowed_origins: str = ""  # Preferred: comma-separated allowed origins
    webapp_origins: str = ""  # Legacy: comma-separated list of allowed origins
    api_cors_origins: str = ""  # Legacy: alternative CORS config

    # Mini App URLs (for CORS and diagnostics)
    webapp_url: str = ""  # e.g., https://myapp.vercel.app
    api_public_url: str = ""  # e.g., https://api.mydomain.com

    # Admin IDs
    admin_ids: str = ""
    admin_telegram_ids: str = ""  # Legacy fallback

    # Application info
    app_env: str = "local"
    log_level: str = "INFO"

    # Telegram initData validation
    tg_init_data_skip_verify: bool = False  # MVP: skip HMAC validation (WARNING: insecure)

    # Version info (set by CI/CD)
    git_sha: str = "unknown"
    git_branch: str = "unknown"
    build_time: str = "unknown"

    # Temporary diagnostics: allow extremely permissive CORS on /debug/echo until this moment.
    # Examples:
    # - "2026-02-07T10:15:00Z"
    # - "1770459300" (unix seconds)
    debug_echo_permissive_cors_until: str = ""

    def get_admin_ids(self) -> set[int]:
        """Get set of admin telegram IDs."""
        raw = (self.admin_ids or self.admin_telegram_ids) or ""
        if not raw:
            return set()
        return {int(x.strip()) for x in raw.split(",") if x.strip()}

    def get_target_channel_id(self) -> str:
        """Get configured channel ID/username for auto-posting (TARGET_CHANNEL_ID preferred)."""
        return (self.target_channel_id or self.feed_chat_id or "").strip()

    def get_cors_origins(self) -> list[str]:
        """
        Get list of allowed CORS origins.
        
        Auto-includes:
        - Origins from ALLOWED_ORIGINS, API_CORS_ORIGINS or WEBAPP_ORIGINS (comma-separated)
        - WEBAPP_URL (normalized to scheme+host)
        - First-party domains: vibemom.ru, www.vibemom.ru, app.vibemom.ru
        - Dev origins: http://localhost:5173, http://127.0.0.1:5173
        - Telegram origins: https://web.telegram.org, https://t.me
        """
        origins: set[str] = set()
        
        # Add explicit origins (priority: allowed_origins > api_cors_origins > webapp_origins)
        cors_config = self.allowed_origins or self.api_cors_origins or self.webapp_origins
        if cors_config:
            for origin in cors_config.split(","):
                origin = origin.strip()
                if origin:
                    origins.add(origin)
        
        # Auto-add WEBAPP_URL (normalized to scheme+host, no trailing path)
        if self.webapp_url:
            webapp = self.webapp_url.strip().rstrip("/")
            if webapp:
                # Extract scheme+host (remove path if any)
                parsed = urlparse(webapp)
                if parsed.scheme and parsed.netloc:
                    origins.add(f"{parsed.scheme}://{parsed.netloc}")

        # Always allow first-party production webapp domains
        origins.add("https://vibemom.ru")
        origins.add("https://www.vibemom.ru")
        origins.add("https://app.vibemom.ru")
        
        # Always add dev origins for local development
        origins.add("http://localhost:5173")
        origins.add("http://127.0.0.1:5173")
        
        # Always add Telegram origins for WebApp
        origins.add("https://web.telegram.org")
        origins.add("https://webapp.telegram.org")
        origins.add("https://t.me")

        # Telegram WebView/WKWebView sometimes sends `Origin: null`.
        # This is a real origin string in CORS and must be explicitly allowed.
        origins.add("null")
        
        return sorted(origins)

    def get_cors_origin_regex(self) -> str | None:
        """
        Get regex pattern for CORS origin validation.
        
        Supports:
        - *.vercel.app (any Vercel deployment)
        - vibemom.ru and its subdomains (production domains)
        """
        # Regex for dynamic Vercel previews and first-party vibemom domains.
        return r"^https://([a-z0-9-]+\.)?vercel\.app$|^https://([a-z0-9-]+\.)?vibemom\.ru$"

    def is_debug_echo_permissive_cors_enabled(self) -> bool:
        """Check if /debug/echo should allow very permissive CORS (time-bounded)."""
        raw = (self.debug_echo_permissive_cors_until or "").strip()
        if not raw:
            return False

        try:
            from datetime import datetime, timezone

            # Unix seconds
            if raw.isdigit():
                until = datetime.fromtimestamp(int(raw), tz=timezone.utc)
            else:
                # ISO 8601 (accepts trailing Z)
                iso = raw.replace("Z", "+00:00")
                until = datetime.fromisoformat(iso)
                if until.tzinfo is None:
                    until = until.replace(tzinfo=timezone.utc)
                else:
                    until = until.astimezone(timezone.utc)

            return datetime.now(timezone.utc) < until
        except Exception:
            # Fail closed if parsing fails.
            return False

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
