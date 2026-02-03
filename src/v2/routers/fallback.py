"""V2 fallback: unknown callback_data -> prompt to open menu. Include this router LAST."""
import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from src.bot.messages import get_copy

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery) -> None:
    """Catch any callback not handled by form/preview/menu/start/moderation. Reply and answer to avoid loading."""
    logger.info("unknown_callback user_id=%s data=%s", callback.from_user.id if callback.from_user else 0, callback.data)
    await callback.answer()
    await callback.message.answer(get_copy("V2_UNKNOWN_BUTTON"))
