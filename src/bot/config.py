from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str

    @field_validator("bot_token", mode="before")
    @classmethod
    def strip_token(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vibe_market"
    admin_telegram_ids: str = ""
    admin_chat_id: str = ""

    def get_admin_ids(self) -> set[int]:
        if not self.admin_telegram_ids:
            return set()
        return {int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()}
