import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from src.bot.config import Settings
from src.bot.fsm.states import ProjectSubmissionStates
from src.bot.messages import get_copy
from src.bot.keyboards import (
    ps_nav_step,
    ps_preview_kb,
    ps_confirm_final_kb,
    ps_resume_kb,
)
from src.bot.renderer import render_project_post
from src.bot.validators import (
    validate_title,
    validate_description,
    validate_stack,
    validate_url,
    validate_price,
    validate_contact,
    parse_yes_no,
)
from src.bot.services import get_or_create_user, create_project
from src.bot.keyboards import admin_moderate_kb

router = Router()
logger = logging.getLogger(__name__)

PS = "ps"

def _is_back_button(text: str) -> bool:
    if not text or not text.strip():
        return False
    back_text = get_copy("BACK_BUTTON").strip()
    return text.strip() == back_text or text.strip().lower() == back_text.lower()


# ---- /submit ----
@router.message(Command("submit"))
async def cmd_submit(message: Message, state: FSMContext) -> None:
    await state.clear()
    await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await state.set_state(ProjectSubmissionStates.title)
    await message.answer(get_copy("SUBMIT_START"))
    await message.answer(get_copy("SUBMIT_Q1_TITLE"), reply_markup=ps_nav_step(back=False, next_=True, save=True, skip=False))


# ---- Title ----
@router.message(ProjectSubmissionStates.title, F.text)
async def submit_title(message: Message, state: FSMContext) -> None:
    ok, val = validate_title(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"), reply_markup=ps_nav_step(back=False, next_=True, save=True))
        return
    await state.update_data(title=val)
    await state.set_state(ProjectSubmissionStates.description)
    await message.answer(get_copy("SUBMIT_Q2_DESCRIPTION"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.title, F.data == f"{PS}:next")
@router.callback_query(ProjectSubmissionStates.title, F.data == f"{PS}:save")
async def submit_title_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == f"{PS}:save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return
    await callback.message.answer(get_copy("SUBMIT_Q1_TITLE"), reply_markup=ps_nav_step(back=False, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.title, F.data == f"{PS}:resume")
async def submit_title_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(get_copy("SUBMIT_Q1_TITLE"), reply_markup=ps_nav_step(back=False, next_=True, save=True))


# ---- Description ----
@router.message(ProjectSubmissionStates.description, F.text)
async def submit_description(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(ProjectSubmissionStates.title)
        await message.answer(get_copy("SUBMIT_Q1_TITLE"), reply_markup=ps_nav_step(back=False, next_=True, save=True))
        return
    ok, val = validate_description(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    await state.update_data(description=val)
    await state.set_state(ProjectSubmissionStates.stack)
    await message.answer(get_copy("SUBMIT_Q3_STACK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.description, F.data == f"{PS}:back")
async def submit_desc_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProjectSubmissionStates.title)
    await callback.message.answer(get_copy("SUBMIT_Q1_TITLE"), reply_markup=ps_nav_step(back=False, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.description, F.data == f"{PS}:next")
@router.callback_query(ProjectSubmissionStates.description, F.data == f"{PS}:save")
async def submit_desc_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == f"{PS}:save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return
    await callback.message.answer(get_copy("SUBMIT_Q2_DESCRIPTION"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.description, F.data == f"{PS}:resume")
async def submit_desc_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(get_copy("SUBMIT_Q2_DESCRIPTION"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


# ---- Stack ----
@router.message(ProjectSubmissionStates.stack, F.text)
async def submit_stack(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(ProjectSubmissionStates.description)
        await message.answer(get_copy("SUBMIT_Q2_DESCRIPTION"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    ok, val = validate_stack(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    await state.update_data(stack=val)
    await state.set_state(ProjectSubmissionStates.link)
    await message.answer(get_copy("SUBMIT_Q4_LINK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.stack, F.data == f"{PS}:back")
async def submit_stack_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProjectSubmissionStates.description)
    await callback.message.answer(get_copy("SUBMIT_Q2_DESCRIPTION"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.stack, F.data.in_([f"{PS}:next", f"{PS}:save"]))
async def submit_stack_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == f"{PS}:save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return
    await callback.message.answer(get_copy("SUBMIT_Q3_STACK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.stack, F.data == f"{PS}:resume")
async def submit_stack_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(get_copy("SUBMIT_Q3_STACK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


# ---- Link ----
@router.message(ProjectSubmissionStates.link, F.text)
async def submit_link(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(ProjectSubmissionStates.stack)
        await message.answer(get_copy("SUBMIT_Q3_STACK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    ok, val = validate_url(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_INVALID_URL"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    await state.update_data(link=val)
    await state.set_state(ProjectSubmissionStates.price)
    await message.answer(get_copy("SUBMIT_Q5_PRICE"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.link, F.data == f"{PS}:back")
async def submit_link_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProjectSubmissionStates.stack)
    await callback.message.answer(get_copy("SUBMIT_Q3_STACK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.link, F.data.in_([f"{PS}:next", f"{PS}:save"]))
async def submit_link_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == f"{PS}:save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return
    await callback.message.answer(get_copy("SUBMIT_Q4_LINK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.link, F.data == f"{PS}:resume")
async def submit_link_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(get_copy("SUBMIT_Q4_LINK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


# ---- Price ----
@router.message(ProjectSubmissionStates.price, F.text)
async def submit_price(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(ProjectSubmissionStates.link)
        await message.answer(get_copy("SUBMIT_Q4_LINK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    ok, val = validate_price(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    await state.update_data(price=val)
    await state.set_state(ProjectSubmissionStates.contact)
    await message.answer(get_copy("SUBMIT_Q6_CONTACT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.price, F.data == f"{PS}:back")
async def submit_price_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProjectSubmissionStates.link)
    await callback.message.answer(get_copy("SUBMIT_Q4_LINK"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.price, F.data.in_([f"{PS}:next", f"{PS}:save"]))
async def submit_price_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == f"{PS}:save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return
    await callback.message.answer(get_copy("SUBMIT_Q5_PRICE"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.price, F.data == f"{PS}:resume")
async def submit_price_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(get_copy("SUBMIT_Q5_PRICE"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


# ---- Contact ----
@router.message(ProjectSubmissionStates.contact, F.text)
async def submit_contact(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(ProjectSubmissionStates.price)
        await message.answer(get_copy("SUBMIT_Q5_PRICE"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    ok, val = validate_contact(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    await state.update_data(contact=val)
    await state.set_state(ProjectSubmissionStates.confirm)
    data = await state.get_data()
    preview = render_project_post(
        data["title"], data["description"], data["stack"], data["link"], data["price"], data["contact"]
    )
    await message.answer(preview)
    await message.answer(get_copy("SUBMIT_Q7_CONFIRM"), reply_markup=ps_preview_kb())


@router.callback_query(ProjectSubmissionStates.contact, F.data == f"{PS}:back")
async def submit_contact_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProjectSubmissionStates.price)
    await callback.message.answer(get_copy("SUBMIT_Q5_PRICE"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.contact, F.data.in_([f"{PS}:next", f"{PS}:save"]))
async def submit_contact_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == f"{PS}:save":
        await callback.message.answer(get_copy("SAVE_DRAFT_OK"), reply_markup=ps_resume_kb())
        return
    await callback.message.answer(get_copy("SUBMIT_Q6_CONTACT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.contact, F.data == f"{PS}:resume")
async def submit_contact_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(get_copy("SUBMIT_Q6_CONTACT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


# ---- Confirm: preview + Submit / Edit / Back ----
@router.callback_query(ProjectSubmissionStates.confirm, F.data == f"{PS}:submit")
async def submit_confirm_show_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("SUBMIT_Q7_SEND_PROMPT"), reply_markup=ps_confirm_final_kb())


@router.callback_query(ProjectSubmissionStates.confirm, F.data == f"{PS}:edit")
@router.callback_query(ProjectSubmissionStates.confirm, F.data == f"{PS}:back")
async def submit_confirm_back_to_contact(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProjectSubmissionStates.contact)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("SUBMIT_Q6_CONTACT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))


@router.callback_query(ProjectSubmissionStates.confirm, F.data == f"{PS}:submit_no")
async def submit_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    preview = render_project_post(
        data["title"], data["description"], data["stack"], data["link"], data["price"], data["contact"]
    )
    await callback.message.answer(preview)
    await callback.message.answer(get_copy("SUBMIT_Q7_CONFIRM"), reply_markup=ps_preview_kb())


@router.callback_query(ProjectSubmissionStates.confirm, F.data == f"{PS}:submit_yes")
async def submit_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    project = await create_project(
        seller_id=user.id,
        title=data["title"],
        description=data["description"],
        stack=data["stack"],
        link=data["link"],
        price=data["price"],
        contact=data["contact"],
    )
    settings = Settings()
    admin_chat_id = (settings.admin_chat_id or "").strip()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)

    if admin_chat_id:
        try:
            logger.info("Sending project to admin chat, admin_chat_id=%s", admin_chat_id)
            preview = render_project_post(
                project.title, project.description, project.stack, project.link, project.price, project.contact
            )
            await callback.bot.send_message(
                chat_id=admin_chat_id,
                text=preview,
                reply_markup=admin_moderate_kb(str(project.id)),
            )
        except Exception as e:
            logger.exception("Failed to send to admin chat: %s", e)
            await callback.message.answer(get_copy("ERROR_MODERATION_SEND"))
            await callback.answer()
            return

    await state.clear()
    await callback.message.answer(get_copy("SUBMIT_SENT"))
    await callback.answer()


# ---- Confirm: text fallback (Back / Yes / No) ----
@router.message(ProjectSubmissionStates.confirm, F.text)
async def submit_confirm_text(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(ProjectSubmissionStates.contact)
        await message.answer(get_copy("SUBMIT_Q6_CONTACT"), reply_markup=ps_nav_step(back=True, next_=True, save=True))
        return
    yn = parse_yes_no(message.text)
    if yn is True:
        data = await state.get_data()
        user = await get_or_create_user(
            message.from_user.id if message.from_user else 0,
            message.from_user.username if message.from_user else None,
            message.from_user.full_name if message.from_user else None,
        )
        project = await create_project(
            seller_id=user.id,
            title=data["title"],
            description=data["description"],
            stack=data["stack"],
            link=data["link"],
            price=data["price"],
            contact=data["contact"],
        )
        settings = Settings()
        admin_chat_id = (settings.admin_chat_id or "").strip()
        if admin_chat_id:
            try:
                logger.info("Sending project to admin chat, admin_chat_id=%s", admin_chat_id)
                preview = render_project_post(
                    project.title, project.description, project.stack, project.link, project.price, project.contact
                )
                bot = message.bot
                await bot.send_message(
                    chat_id=admin_chat_id,
                    text=preview,
                    reply_markup=admin_moderate_kb(str(project.id)),
                )
            except Exception as e:
                logger.exception("Failed to send to admin chat: %s", e)
                await message.answer(get_copy("ERROR_MODERATION_SEND"))
                return
        await state.clear()
        await message.answer(get_copy("SUBMIT_SENT"))
    elif yn is False:
        data = await state.get_data()
        preview = render_project_post(
            data["title"], data["description"], data["stack"], data["link"], data["price"], data["contact"]
        )
        await message.answer(preview)
        await message.answer(get_copy("SUBMIT_Q7_CONFIRM"), reply_markup=ps_preview_kb())
    else:
        await message.answer(get_copy("ERROR_INVALID_YESNO"), reply_markup=ps_preview_kb())
