import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from src.bot.config import Settings
from src.bot.database.session import init_db
from src.bot.handlers import setup_routers

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings()
    # Гарантированно инициализируем БД до регистрации хендлеров и polling
    init_db(settings)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties())
    dp = Dispatcher()
    dp.include_router(setup_routers())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
