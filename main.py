import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from src.bot.config import Settings
from src.bot.database.session import init_db
from src.bot.handlers import setup_routers

# Structured logging: timestamp, level, logger, message (one line per event)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
)
_root = logging.getLogger()
_root.setLevel(logging.INFO)
_root.addHandler(_handler)
logger = logging.getLogger(__name__)


def _boot_version_line() -> str:
    """Build boot version info line for logging."""
    sha = os.getenv("GIT_SHA", "unknown")
    branch = os.getenv("GIT_BRANCH", "unknown")
    build_time = os.getenv("BUILD_TIME", "unknown")
    env = os.getenv("APP_ENV", "unknown")
    v2 = os.getenv("V2_ENABLED", "false")
    return f"BOOT: sha={sha}, branch={branch}, build={build_time}, env={env}, v2={v2}"


def _routing_mode_line(settings: Settings) -> str:
    if not settings.v2_enabled:
        return "Routing: V1 only"
    if not settings.v2_canary_mode:
        return "Routing: V2 for all"
    return "Routing: V2 canary (admin + allowlist)"


async def main() -> None:
    settings = Settings()
    settings.validate_for_runtime()  # Validates BOT_TOKEN in non-CI environments
    # Гарантированно инициализируем БД до регистрации хендлеров и polling
    init_db(settings)
    logger.info(_boot_version_line())
    logger.info("Bot started, DB initialized")
    logger.info(_routing_mode_line(settings))

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties())
    dp = Dispatcher()
    dp.include_router(setup_routers())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
