"""
Локальный тест публикации в канал FEED_CHAT_ID.
Загружает .env, отправляет тестовое сообщение в канал (или --dry-run только проверяет конфиг).
Не меняет прод: отправляет один пост; для реальной отправки не передавайте --dry-run.

Usage:
  python scripts/test_feed.py              # отправить тестовое сообщение в FEED_CHAT_ID
  python scripts/test_feed.py --dry-run    # только проверить, что FEED_CHAT_ID задан
"""
import argparse
import asyncio
import logging
import os
import sys

# project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test feed channel publish")
    parser.add_argument("--dry-run", action="store_true", help="Only check FEED_CHAT_ID, do not send")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    feed_chat_id = (os.environ.get("FEED_CHAT_ID") or "").strip()
    if not feed_chat_id:
        logger.warning("FEED_CHAT_ID not set. Set it in .env (e.g. @vibecode777 or numeric id).")
        sys.exit(1)

    if args.dry_run:
        logger.info("FEED_CHAT_ID=%s (dry-run, no send)", feed_chat_id)
        return

    bot_token = (os.environ.get("BOT_TOKEN") or "").strip()
    if not bot_token:
        logger.error("BOT_TOKEN not set. Needed to send message.")
        sys.exit(1)

    from aiogram import Bot
    from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramNotFound

    bot = Bot(token=bot_token)
    test_text = (
        "<b>Тест автопостинга</b>\n\n"
        "Если видишь это сообщение — бот может публиковать в канал.\n"
        "Контакт: @vibecode777"
    )
    try:
        sent = await bot.send_message(
            chat_id=feed_chat_id,
            text=test_text,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        logger.info("FEED test ok chat=%s msg_id=%s", feed_chat_id, sent.message_id)
    except (TelegramForbiddenError, TelegramBadRequest, TelegramNotFound) as e:
        logger.exception("FEED test failed: %s", e)
        sys.exit(1)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
