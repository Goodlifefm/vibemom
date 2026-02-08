from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.bot.config import Settings
from src.bot.messages import get_copy
from src.bot.services import get_or_create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    settings = Settings()
    tg_id = message.from_user.id if message.from_user else 0
    if settings.should_use_v2(tg_id):
        from src.v2.routers.start import show_v2_cabinet
        await show_v2_cabinet(message, state)
    else:
        await message.answer(get_copy("START_MESSAGE"))


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    settings = Settings()
    tg_id = message.from_user.id if message.from_user else 0
    if settings.should_use_v2(tg_id):
        from src.bot.keyboards import reply_menu_keyboard
        await message.answer(get_copy("V2_HELP_TEXT"), reply_markup=reply_menu_keyboard())
    else:
        await message.answer(get_copy("START_MESSAGE"))
