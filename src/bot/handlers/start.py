from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.messages import get_copy
from src.bot.services import get_or_create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await message.answer(get_copy("START_MESSAGE"))
