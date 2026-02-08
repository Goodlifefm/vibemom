import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import MenuButtonWebApp, WebAppInfo, MenuButtonDefault
from src.bot.config import Settings
from src.bot.database.session import init_db
from src.bot.handlers import setup_routers

# Structured logging: timestamp, level, logger, message (one line per event)
def _get_log_level() -> int:
    """Get log level from LOG_LEVEL env var, default to INFO."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
)
_root = logging.getLogger()
_root.setLevel(_get_log_level())
_root.addHandler(_handler)
logger = logging.getLogger(__name__)


def _boot_version_line() -> str:
    """Build boot version info line for logging."""
    sha = os.getenv("GIT_SHA", "unknown")
    branch = os.getenv("GIT_BRANCH", "unknown")
    build_time = os.getenv("BUILD_TIME", "unknown")
    env = os.getenv("APP_ENV", "unknown")
    v2 = os.getenv("V2_ENABLED", "false")
    webapp_url = os.getenv("WEBAPP_URL", "(not set)")
    api_public_url = os.getenv("API_PUBLIC_URL", "(not set)")
    return (
        f"BOOT: sha={sha}, branch={branch}, build={build_time}, env={env}, v2={v2}, "
        f"webapp_url={webapp_url}, api_public_url={api_public_url}"
    )


def _routing_mode_line(settings: Settings) -> str:
    if not settings.v2_enabled:
        return "Routing: V1 only"
    if not settings.v2_canary_mode:
        return "Routing: V2 for all"
    return "Routing: V2 canary (admin + allowlist)"


async def _setup_webapp_menu_button(bot: Bot, settings: Settings) -> None:
    """
    Set up Telegram Menu Button with WebApp link.
    
    If WEBAPP_URL is configured and starts with https://, sets MenuButtonWebApp.
    Otherwise, resets to default menu button.
    """
    webapp_url = settings.webapp_url.strip() if settings.webapp_url else ""
    
    if webapp_url and webapp_url.startswith("https://"):
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="📱 Кабинет",
                    web_app=WebAppInfo(url=webapp_url),
                )
            )
            logger.info(f"WebApp Menu Button set: {webapp_url}")
        except Exception as e:
            logger.warning(f"Failed to set WebApp Menu Button: {e}")
    elif webapp_url:
        logger.warning(
            f"WEBAPP_URL must start with https://, got: {webapp_url[:50]}... "
            "Menu button not set."
        )
    else:
        logger.info("WEBAPP_URL not configured, Menu Button not set")


async def main() -> None:
    settings = Settings()
    settings.validate_for_runtime()  # Validates BOT_TOKEN in non-CI environments
    
    # Reconfigure log level from Settings (pydantic-settings loads .env file)
    # This is needed because module-level logging setup only sees shell env vars,
    # not values from .env file which pydantic-settings loads later.
    configured_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    if _root.level != configured_level:
        _root.setLevel(configured_level)
        logger.debug(f"Log level reconfigured to {settings.log_level.upper()}")
    
    # Гарантированно инициализируем БД до регистрации хендлеров и polling
    init_db(settings)
    logger.info(_boot_version_line())
    logger.info("Bot started, DB initialized")
    logger.info(_routing_mode_line(settings))

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties())
    dp = Dispatcher()
    dp.include_router(setup_routers())
    
    # Set up WebApp Menu Button (if WEBAPP_URL configured)
    await _setup_webapp_menu_button(bot, settings)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
