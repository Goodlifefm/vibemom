"""
V2 Block Editor: block menu and universal field editor.
"""
import json
import logging
import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.messages import get_copy
from src.bot.renderer import project_fields_to_answers, v2_answers_to_project_fields
from src.bot.services.project_service import get_project, update_project_fields
from src.bot.editor_schema import (
    BLOCKS,
    get_field,
    get_fields_by_block,
    required_field_ids,
    is_field_filled,
    VALIDATORS,
)
from src.bot.fsm.states import EditorStates

router = Router()
logger = logging.getLogger(__name__)

ED = "ed"


def _v2_draft_payload(answers: dict) -> dict:
    """Include _meta.version for resume/schema detection."""
    payload = dict(answers)
    payload["_meta"] = {"version": 2}
    return payload


def block_menu_kb(project_id: uuid.UUID) -> InlineKeyboardMarkup:
    pid = str(project_id)
    rows = []
    rows.append([InlineKeyboardButton(text=get_copy("V2_GUIDED_FILL_STEPS").strip(), callback_data=f"{ED}:guided:{pid}")])
    for b in BLOCKS:
        label = f"{b.get('emoji', '')} {b['label']}".strip()
        rows.append([InlineKeyboardButton(text=label, callback_data=f"{ED}:block:{b['block_id']}:{pid}")])
    rows.append([InlineKeyboardButton(text=get_copy("V2_EDITOR_BACK_TO_PROJECT").strip(), callback_data=f"{ED}:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_block_menu(message_or_callback: Message | CallbackQuery, state: FSMContext, project_id: uuid.UUID) -> None:
    project = await get_project(project_id)
    if not project:
        from src.bot.handlers.project_dashboard import show_dashboard
        await show_dashboard(message_or_callback, state, project_id)
        return
    target = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    answers = project_fields_to_answers(project)
    await state.update_data(answers=answers)
    lines = ["✍️ Редактировать блоки\n"]
    for b in BLOCKS:
        fields_in_block = get_fields_by_block(b["block_id"])
        filled = sum(1 for f in fields_in_block if is_field_filled(answers, f))
        total = len(fields_in_block)
        lines.append(f"{b.get('emoji', '')} {b['label']}: {filled}/{total}")
    text = "\n".join(lines)
    await state.set_state(EditorStates.block_menu)
    await state.update_data(project_id=str(project_id))
    await target.answer(text, reply_markup=block_menu_kb(project_id))


@router.callback_query(F.data.startswith(f"{ED}:guided:"))
async def ed_guided(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 3)
    pid = parts[3] if len(parts) > 3 else (await state.get_data()).get("project_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        return
    await state.update_data(guided=True)
    rid = required_field_ids()
    if not rid:
        await show_block_menu(callback, state, project_id)
        return
    first_field = get_field(rid[0])
    if not first_field:
        await show_block_menu(callback, state, project_id)
        return
    await state.set_state(EditorStates.field_edit)
    await state.update_data(project_id=pid, editing_field_id=first_field["field_id"], guided=True)
    await _send_field_question(callback.message, first_field, guided=True, state=state)


@router.callback_query(F.data.startswith(f"{ED}:back"))
async def ed_back(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    pid = data.get("project_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    from src.bot.handlers.project_dashboard import show_dashboard
    await show_dashboard(callback, state, project_id)


@router.callback_query(F.data.startswith(f"{ED}:block:"))
async def ed_block(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 3)
    block_id = parts[2]
    pid = parts[3] if len(parts) > 3 else ""
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        data = await state.get_data()
        pid = data.get("project_id")
        project_id = uuid.UUID(pid) if pid else None
    if not project_id:
        await callback.message.answer(get_copy("V2_MY_PROJECTS_EMPTY"))
        return
    fields_in_block = get_fields_by_block(block_id)
    if not fields_in_block:
        await show_block_menu(callback, state, project_id)
        return
    first_field = fields_in_block[0]
    await state.set_state(EditorStates.field_edit)
    await state.update_data(project_id=str(project_id), editing_field_id=first_field["field_id"], guided=False)
    await _send_field_question(callback.message, first_field, guided=False, state=state)


def _channel_choice_to_value(choice: str) -> str:
    """Map callback choice to stored value (schema choices: tg, vk, site)."""
    return choice if choice in ("tg", "vk", "site") else choice


def _channel_kb(project_id: uuid.UUID, current: list) -> InlineKeyboardMarkup:
    pid = str(project_id)
    selected = set(current) if isinstance(current, list) else set()
    labels = [("tg", "V2_CHANNEL_TG"), ("vk", "V2_CHANNEL_VK"), ("site", "V2_CHANNEL_SITE")]
    rows = []
    for val, copy_key in labels:
        mark = " ✓" if val in selected else ""
        rows.append([InlineKeyboardButton(
            text=(get_copy(copy_key) or val).strip() + mark,
            callback_data=f"{ED}:ch:toggle:{val}:{pid}",
        )])
    rows.append([InlineKeyboardButton(text=get_copy("V2_CHANNEL_DONE").strip(), callback_data=f"{ED}:ch:done:{pid}")])
    rows.append([InlineKeyboardButton(text=get_copy("V2_EDITOR_BACK").strip(), callback_data=f"{ED}:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _links_kb(project_id: uuid.UUID) -> InlineKeyboardMarkup:
    pid = str(project_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_copy("V2_LINK_ADD").strip(), callback_data=f"{ED}:link:add:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_LINK_FINISH").strip(), callback_data=f"{ED}:link:finish:{pid}")],
        [InlineKeyboardButton(text=get_copy("V2_EDITOR_BACK").strip(), callback_data=f"{ED}:cancel")],
    ])


async def _send_field_question(message: Message, field: dict, guided: bool = False, state: FSMContext | None = None) -> None:
    data = (await state.get_data()) if state else {}
    answers = data.get("answers") or {}
    pid = data.get("project_id") or ""
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(message, state)
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(message, state)
        return
    text = get_copy(field["copy_id"])
    if field.get("input_type") == "multi_choice":
        current = answers.get("channels", [])
        if not isinstance(current, list):
            current = [current] if current else []
        kb = _channel_kb(project_id, current)
        await message.answer(text, reply_markup=kb)
        return
    if field.get("input_type") == "links":
        links = answers.get("links_done", [])
        if not isinstance(links, list):
            links = [links] if links else []
        if links:
            text += "\n\nСсылки:\n" + "\n".join(f"• {u}" for u in links[:20])
        else:
            text += "\n\nПока нет ссылок. Добавьте или нажмите «Завершить список ссылок»."
        await message.answer(text, reply_markup=_links_kb(project_id))
        return
    row = [InlineKeyboardButton(text=get_copy("V2_EDITOR_BACK").strip(), callback_data=f"{ED}:cancel")]
    if field.get("skippable"):
        row.append(InlineKeyboardButton(text=get_copy("SKIP_BUTTON").strip(), callback_data=f"{ED}:skip"))
    rows = [row]
    if guided:
        rows.append([InlineKeyboardButton(text=get_copy("V2_EDITOR_MODE").strip(), callback_data=f"{ED}:to_editor")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == f"{ED}:to_editor")
async def ed_to_editor(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(guided=False)
    data = await state.get_data()
    pid = data.get("project_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    await state.set_state(EditorStates.block_menu)
    await show_block_menu(callback, state, uuid.UUID(pid))


@router.callback_query(F.data == f"{ED}:cancel")
async def ed_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(guided=False)
    data = await state.get_data()
    pid = data.get("project_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    await state.set_state(EditorStates.block_menu)
    await show_block_menu(callback, state, uuid.UUID(pid))


@router.callback_query(F.data.startswith(f"{ED}:ch:toggle:"))
async def ed_channel_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 4)  # ed:ch:toggle:tg:uuid -> 5 parts
    choice = _channel_choice_to_value(parts[3]) if len(parts) >= 4 else ""
    pid = parts[4] if len(parts) >= 5 else (await state.get_data()).get("project_id")
    if not pid or not choice:
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        return
    project = await get_project(project_id)
    if not project:
        return
    data = await state.get_data()
    answers = data.get("answers") or project_fields_to_answers(project)
    answers = dict(answers)
    channels = list(answers.get("channels") or [])
    if not isinstance(channels, list):
        channels = [channels] if channels else []
    if choice in channels:
        channels = [c for c in channels if c != choice]
    else:
        channels = channels + [choice]
    answers["channels"] = channels
    v2_fields = v2_answers_to_project_fields(answers)
    await update_project_fields(
        project_id,
        title=v2_fields["title"],
        description=json.dumps(_v2_draft_payload(answers)),
        stack=v2_fields["stack"],
        link=v2_fields["link"],
        price=v2_fields["price"],
        contact=v2_fields["contact"],
    )
    await state.update_data(answers=answers)
    field = get_field("channels")
    if field:
        await _send_field_question(callback.message, field, guided=data.get("guided", False), state=state)


@router.callback_query(F.data.startswith(f"{ED}:ch:done:"))
async def ed_channel_done(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 3)
    pid = parts[3] if len(parts) > 3 else (await state.get_data()).get("project_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    data = await state.get_data()
    guided = data.get("guided")
    if guided:
        rid = required_field_ids()
        idx = next((i for i, fid in enumerate(rid) if fid == "channels"), -1)
        if idx >= 0 and idx + 1 < len(rid):
            next_field = get_field(rid[idx + 1])
            if next_field:
                await state.set_state(EditorStates.field_edit)
                await state.update_data(editing_field_id=next_field["field_id"])
                await callback.message.answer(get_copy("V2_SAVED_NEXT_FIELD").strip())
                await _send_field_question(callback.message, next_field, guided=True, state=state)
                return
    await state.set_state(EditorStates.block_menu)
    await state.update_data(editing_field_id=None, guided=False)
    await show_block_menu(callback, state, project_id)


@router.callback_query(F.data.startswith(f"{ED}:link:add:"))
async def ed_link_add(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 3)
    pid = parts[3] if len(parts) > 3 else (await state.get_data()).get("project_id")
    if not pid:
        return
    await state.update_data(links_waiting_url=True)
    await callback.message.answer(get_copy("V2_LINK_ADD_PROMPT").strip())


@router.callback_query(F.data.startswith(f"{ED}:link:finish:"))
async def ed_link_finish(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.split(":", 3)
    pid = parts[3] if len(parts) > 3 else (await state.get_data()).get("project_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    try:
        project_id = uuid.UUID(pid)
    except ValueError:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    await state.update_data(links_waiting_url=False)
    data = await state.get_data()
    field_id = data.get("editing_field_id")
    guided = data.get("guided")
    if guided and field_id:
        rid = required_field_ids()
        idx = next((i for i, fid in enumerate(rid) if fid == field_id), -1)
        if idx >= 0 and idx + 1 < len(rid):
            next_field = get_field(rid[idx + 1])
            if next_field:
                await state.set_state(EditorStates.field_edit)
                await state.update_data(editing_field_id=next_field["field_id"])
                await callback.message.answer(get_copy("V2_LINKS_SAVED_NEXT").strip())
                await _send_field_question(callback.message, next_field, guided=True, state=state)
                return
    await state.set_state(EditorStates.block_menu)
    await state.update_data(editing_field_id=None, guided=False)
    await show_block_menu(callback, state, project_id)


@router.callback_query(F.data == f"{ED}:skip")
async def ed_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    pid = data.get("project_id")
    field_id = data.get("editing_field_id")
    if not pid:
        from src.bot.handlers.cabinet import show_cabinet
        await show_cabinet(callback, state)
        return
    if not field_id:
        await show_block_menu(callback, state, uuid.UUID(pid))
        return
    field = get_field(field_id)
    if not field or not field.get("skippable"):
        await callback.message.answer(get_copy("ERROR_NOT_TEXT"))
        return
    project = await get_project(uuid.UUID(pid))
    if project:
        data = await state.get_data()
        answers = data.get("answers") or project_fields_to_answers(project)
        answers = dict(answers)
        answers[field["answer_key"]] = "" if field.get("input_type") != "links" else []
        v2_fields = v2_answers_to_project_fields(answers)
        await update_project_fields(
            uuid.UUID(pid),
            title=v2_fields["title"],
            description=json.dumps(_v2_draft_payload(answers)),
            stack=v2_fields["stack"],
            link=v2_fields["link"],
            price=v2_fields["price"],
            contact=v2_fields["contact"],
        )
        await state.update_data(answers=answers)
    data = await state.get_data()
    guided = data.get("guided")
    if guided:
        rid = required_field_ids()
        idx = next((i for i, fid in enumerate(rid) if fid == field_id), -1)
        if idx >= 0 and idx + 1 < len(rid):
            next_field = get_field(rid[idx + 1])
            if next_field:
                await state.set_state(EditorStates.field_edit)
                await state.update_data(editing_field_id=next_field["field_id"])
                await callback.message.answer(get_copy("V2_SKIPPED_NEXT").strip())
                await _send_field_question(callback.message, next_field, guided=True, state=state)
                return
    await state.set_state(EditorStates.block_menu)
    await state.update_data(editing_field_id=None, guided=False)
    await show_block_menu(callback, state, uuid.UUID(pid))


@router.message(EditorStates.field_edit, F.text)
async def ed_field_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    pid = data.get("project_id")
    field_id = data.get("editing_field_id")
    links_waiting = data.get("links_waiting_url")
    if not pid or not field_id:
        await state.clear()
        return
    field = get_field(field_id)
    if not field:
        await state.set_state(EditorStates.block_menu)
        await show_block_menu(message, state, uuid.UUID(pid))
        return
    if field.get("input_type") == "multi_choice":
        await message.answer("Выбери каналы кнопками выше и нажми «Готово».")
        return
    if field.get("input_type") == "links" and not links_waiting:
        await message.answer(get_copy("V2_LINK_ADD_OR_FINISH").strip())
        return
    # Link collector: user sent URL after "Добавить ссылку" — validate and append
    if links_waiting and field.get("input_type") == "links":
        url_fn = VALIDATORS.get("url_1000")
        if url_fn:
            ok, value = url_fn(message.text)
            if not ok:
                await message.answer(get_copy("ERROR_INVALID_URL"))
                return
            url_val = value if isinstance(value, str) else (str(value) if value else "")
        else:
            from src.bot import validators as v
            ok, value = v.validate_url(message.text, 1000)
            if not ok:
                await message.answer(get_copy("ERROR_INVALID_URL"))
                return
            url_val = value or ""
        project = await get_project(uuid.UUID(pid))
        if not project:
            await state.clear()
            return
        answers = data.get("answers") or project_fields_to_answers(project)
        answers = dict(answers)
        links = list(answers.get("links_done") or [])
        if not isinstance(links, list):
            links = [links] if links else []
        links.append(url_val)
        answers["links_done"] = links
        v2_fields = v2_answers_to_project_fields(answers)
        await update_project_fields(
            uuid.UUID(pid),
            title=v2_fields["title"],
            description=json.dumps(_v2_draft_payload(answers)),
            stack=v2_fields["stack"],
            link=v2_fields["link"],
            price=v2_fields["price"],
            contact=v2_fields["contact"],
        )
        await state.update_data(answers=answers, links_waiting_url=False)
        await message.answer(get_copy("V2_LINK_ADDED").strip())
        await _send_field_question(message, field, guided=data.get("guided", False), state=state)
        return
    validator_name = field.get("validator") or "non_empty_200"
    fn = VALIDATORS.get(validator_name)
    if fn:
        ok, value = fn(message.text)
        if not ok:
            err = get_copy("ERROR_NOT_TEXT")
            if "url" in validator_name:
                err = get_copy("ERROR_INVALID_URL")
            await message.answer(err)
            return
        text_value = value if isinstance(value, str) else (str(value) if value is not None else "")
    else:
        text_value = (message.text or "").strip()
    project = await get_project(uuid.UUID(pid))
    if not project:
        await state.clear()
        return
    data = await state.get_data()
    answers = data.get("answers") or project_fields_to_answers(project)
    answers = dict(answers)
    answers[field["answer_key"]] = text_value
    v2_fields = v2_answers_to_project_fields(answers)
    await update_project_fields(
        uuid.UUID(pid),
        title=v2_fields["title"],
        description=json.dumps(_v2_draft_payload(answers)),
        stack=v2_fields["stack"],
        link=v2_fields["link"],
        price=v2_fields["price"],
        contact=v2_fields["contact"],
    )
    await state.update_data(answers=answers)
    logger.info("v2 project_id=%s field_id=%s saved", pid, field_id)
    data = await state.get_data()
    guided = data.get("guided")
    if guided:
        rid = required_field_ids()
        idx = next((i for i, fid in enumerate(rid) if fid == field_id), -1)
        if idx >= 0 and idx + 1 < len(rid):
            next_field = get_field(rid[idx + 1])
            if next_field:
                await state.set_state(EditorStates.field_edit)
                await state.update_data(editing_field_id=next_field["field_id"])
                await message.answer(get_copy("V2_SAVED_NEXT_FIELD").strip())
                await _send_field_question(message, next_field, guided=True, state=state)
                return
    await state.set_state(EditorStates.block_menu)
    await state.update_data(editing_field_id=None, guided=False)
    await message.answer(get_copy("V2_SAVED").strip())
    await show_block_menu(message, state, uuid.UUID(pid))
