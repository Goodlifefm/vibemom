import uuid
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from src.bot.fsm.states import BuyerRequestStates
from src.bot.messages import get_copy
from src.bot.keyboards import yes_no_kb_request
from src.bot.validators import validate_what, validate_budget, validate_contact, parse_yes_no
from src.bot.services import (
    get_or_create_user,
    create_buyer_request,
    match_request_to_projects,
    create_leads_for_request,
)

router = Router()


def _is_back_button(text: str) -> bool:
    if not text or not text.strip():
        return False
    back_text = get_copy("BACK_BUTTON").strip()
    return text.strip() == back_text or text.strip().lower() == back_text.lower()


@router.message(Command("request"))
async def cmd_request(message: Message, state: FSMContext) -> None:
    await state.clear()
    await get_or_create_user(
        message.from_user.id if message.from_user else 0,
        message.from_user.username if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )
    await state.set_state(BuyerRequestStates.what)
    await message.answer(get_copy("REQUEST_START"))
    await message.answer(get_copy("REQUEST_Q1_WHAT"))


@router.message(BuyerRequestStates.what, F.text)
async def request_what(message: Message, state: FSMContext) -> None:
    ok, val = validate_what(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"))
        return
    await state.update_data(what=val)
    await state.set_state(BuyerRequestStates.budget)
    await message.answer(get_copy("REQUEST_Q2_BUDGET"))


@router.message(BuyerRequestStates.budget, F.text)
async def request_budget(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(BuyerRequestStates.what)
        await message.answer(get_copy("REQUEST_Q1_WHAT"))
        return
    ok, val = validate_budget(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"))
        return
    await state.update_data(budget=val)
    await state.set_state(BuyerRequestStates.contact)
    await message.answer(get_copy("REQUEST_Q3_CONTACT"))


@router.message(BuyerRequestStates.contact, F.text)
async def request_contact(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(BuyerRequestStates.budget)
        await message.answer(get_copy("REQUEST_Q2_BUDGET"))
        return
    ok, val = validate_contact(message.text)
    if not ok:
        await message.answer(get_copy("ERROR_NOT_TEXT"))
        return
    await state.update_data(contact=val)
    await state.set_state(BuyerRequestStates.confirm)
    await message.answer(get_copy("REQUEST_Q4_CONFIRM"), reply_markup=yes_no_kb_request())


@router.callback_query(BuyerRequestStates.confirm, F.data == "req_yes")
async def request_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = await get_or_create_user(
        callback.from_user.id if callback.from_user else 0,
        callback.from_user.username if callback.from_user else None,
        callback.from_user.full_name if callback.from_user else None,
    )
    req = await create_buyer_request(
        buyer_id=user.id,
        what=data["what"],
        budget=data["budget"],
        contact=data["contact"],
    )
    matched = await match_request_to_projects(req.what, req.budget)
    if matched:
        await create_leads_for_request(req.id, [uuid.UUID(p["id"]) for p in matched])
    await state.clear()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("REQUEST_SENT"))
    await callback.answer()


@router.callback_query(BuyerRequestStates.confirm, F.data == "req_no")
async def request_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("REQUEST_CANCELLED"))
    await callback.answer()


@router.message(BuyerRequestStates.confirm, F.text)
async def request_confirm_text(message: Message, state: FSMContext) -> None:
    if _is_back_button(message.text or ""):
        await state.set_state(BuyerRequestStates.contact)
        await message.answer(get_copy("REQUEST_Q4_CONFIRM"), reply_markup=yes_no_kb_request())
        return
    yn = parse_yes_no(message.text)
    if yn is True:
        data = await state.get_data()
        user = await get_or_create_user(
            message.from_user.id if message.from_user else 0,
            message.from_user.username if message.from_user else None,
            message.from_user.full_name if message.from_user else None,
        )
        req = await create_buyer_request(
            buyer_id=user.id,
            what=data["what"],
            budget=data["budget"],
            contact=data["contact"],
        )
        matched = await match_request_to_projects(req.what, req.budget)
        if matched:
            await create_leads_for_request(req.id, [uuid.UUID(p["id"]) for p in matched])
        await state.clear()
        await message.answer(get_copy("REQUEST_SENT"))
    elif yn is False:
        await state.clear()
        await message.answer(get_copy("REQUEST_CANCELLED"))
    else:
        await message.answer(get_copy("ERROR_INVALID_YESNO"))
