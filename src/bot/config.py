from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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
    v2_enabled: bool = False
    v2_canary_mode: bool = False
    v2_allowlist: str = ""

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
