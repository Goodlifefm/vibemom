from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.messages import get_copy
from src.bot.renderer import render_project_post, render_buyer_request_summary
from src.bot.services import get_or_create_user, list_leads_for_seller, list_my_requests_with_projects

router = Router()


@router.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    user = await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    my_projects, leads_list = await list_leads_for_seller(user.id)
    if not my_projects:
        await message.answer(get_copy("LEADS_HEADER") + get_copy("LEADS_EMPTY"))
        return
    if not leads_list:
        await message.answer(get_copy("LEADS_HEADER") + get_copy("LEADS_EMPTY"))
        return
    header = get_copy("LEADS_HEADER")
    proj_by_id = {p.id: p for p in my_projects}
    parts = [header]
    for lead in leads_list:
        p = proj_by_id.get(lead.project_id)
        if p:
            parts.append(render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact))
    text = "\n".join(parts)
    if len(text) > 4000:
        await message.answer(header)
        for lead in leads_list:
            p = proj_by_id.get(lead.project_id)
            if p:
                await message.answer(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
    else:
        await message.answer(text)


@router.message(Command("my_requests"))
async def cmd_my_requests(message: Message) -> None:
    user = await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    requests_list, leads_list, all_projects = await list_my_requests_with_projects(user.id)
    if not requests_list:
        await message.answer(get_copy("MY_REQUESTS_HEADER") + get_copy("MY_REQUESTS_EMPTY"))
        return
    header = get_copy("MY_REQUESTS_HEADER")
    lead_by_req: dict = {}
    for lead in leads_list:
        if lead.buyer_request_id:
            lead_by_req.setdefault(lead.buyer_request_id, []).append(lead)
    parts = [header]
    for req in requests_list:
        parts.append(render_buyer_request_summary(req.what, req.budget, req.contact))
        for lead in lead_by_req.get(req.id, []):
            p = all_projects.get(lead.project_id)
            if p:
                parts.append(
                    render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                )
    text = "\n".join(parts)
    if len(text) > 4000:
        await message.answer(header)
        for req in requests_list:
            await message.answer(render_buyer_request_summary(req.what, req.budget, req.contact))
            for lead in lead_by_req.get(req.id, []):
                p = all_projects.get(lead.project_id)
                if p:
                    await message.answer(
                        render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
                    )
    else:
        await message.answer(text)
