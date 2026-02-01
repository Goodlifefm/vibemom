from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.messages import get_copy
from src.bot.renderer import render_project_post
from src.bot.services import get_or_create_user, list_approved_projects

router = Router()


@router.message(Command("catalog"))
async def cmd_catalog(message: Message) -> None:
    await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    projects = await list_approved_projects()
    if not projects:
        await message.answer(get_copy("CATALOG_HEADER") + get_copy("CATALOG_EMPTY"))
        return
    header = get_copy("CATALOG_HEADER")
    parts = [header]
    for p in projects:
        parts.append(
            render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
        )
    text = "\n".join(parts)
    if len(text) > 4000:
        await message.answer(header)
        for p in projects:
            await message.answer(
                render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
            )
    else:
        await message.answer(text)
