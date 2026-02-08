import logging
import os
import html
import uuid
from datetime import datetime, timezone, timedelta
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramNotFound
from sqlalchemy import select, func

from src.bot.config import Settings
from src.bot.database import session as db_session
from src.bot.database.models import ProjectStatus, Submission, User
from src.bot.fsm.states import ModerationStates
from src.bot.keyboards import moderation_kb
from src.bot.messages import get_copy


router = Router()
logger = logging.getLogger(__name__)


# =============================================================================
# Version info (for debugging deployments)
# =============================================================================

def get_version_info() -> dict[str, str]:
    """Get version info from environment variables."""
    return {
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "git_branch": os.getenv("GIT_BRANCH", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "environment": os.getenv("APP_ENV", "unknown"),
        "v2_enabled": os.getenv("V2_ENABLED", "false"),
        "webapp_url": os.getenv("WEBAPP_URL", "(not set)"),
        "api_public_url": os.getenv("API_PUBLIC_URL", "(not set)"),
    }


@router.message(Command("version"))
async def cmd_version(message: Message) -> None:
    """Show version info — available to everyone for deployment verification."""
    info = get_version_info()
    text = (
        "<b>🔧 Version Info</b>\n\n"
        f"<b>SHA:</b> <code>{info['git_sha']}</code>\n"
        f"<b>Branch:</b> {info['git_branch']}\n"
        f"<b>Build:</b> {info['build_time']}\n"
        f"<b>Env:</b> {info['environment']}\n"
        f"<b>V2:</b> {info['v2_enabled']}\n\n"
        f"<b>WebApp URL:</b> {info['webapp_url']}\n"
        f"<b>API URL:</b> {info['api_public_url']}"
    )
    await message.answer(text, parse_mode="HTML")


def _is_admin(telegram_id: int) -> bool:
    s = Settings()
    return telegram_id in s.get_admin_ids()

def _escape(text: str) -> str:
    return html.escape(str(text or "").strip(), quote=True)


def _get_value(answers: dict, *keys: str) -> str | None:
    for key in keys:
        if key not in answers:
            continue
        value = answers.get(key)
        if value is None or value == "" or value == []:
            continue
        if isinstance(value, list):
            parts = [str(v).strip() for v in value if v is not None and str(v).strip()]
            joined = ", ".join(parts)
            return joined or None
        return str(value).strip() or None
    return None


def _format_price(answers: dict) -> str | None:
    # Hidden price
    if answers.get("cost_hidden") is True or answers.get("budget_hidden") is True:
        return "скрыта"

    min_val = answers.get("cost_amount") or answers.get("budget_min")
    max_val = answers.get("cost_max") or answers.get("budget_max")
    currency = answers.get("cost_currency") or answers.get("budget_currency") or answers.get("currency") or "RUB"

    try:
        mn = int(min_val) if min_val is not None else None
        mx = int(max_val) if max_val is not None else None
    except (TypeError, ValueError):
        mn = mx = None

    cur = str(currency or "").strip().upper() or "RUB"
    symbol = "₽" if cur == "RUB" else "$" if cur == "USD" else "€" if cur == "EUR" else cur

    if mn is not None and mx is not None and mn != mx:
        return f"{mn:,}–{mx:,} {symbol}".replace(",", " ")
    if mn is not None:
        return f"{mn:,} {symbol}".replace(",", " ")
    if mx is not None:
        return f"до {mx:,} {symbol}".replace(",", " ")

    price_str = answers.get("price")
    if price_str:
        return str(price_str).strip() or None

    return None


def render_submission_post_html(
    answers: dict | None,
    *,
    show_contacts: bool = True,
    public_url: str | None = None,
) -> str:
    """Render a Telegram HTML card from Mini App answers (project_title/problem/etc)."""
    answers = dict(answers or {})
    sections: list[str] = []

    title = _get_value(answers, "project_title", "title")
    subtitle = _get_value(answers, "project_subtitle", "subtitle")
    title_text = title or ""
    if subtitle:
        title_text = f"{title_text}\n{subtitle}" if title_text else subtitle
    if title_text:
        sections.append(f"<b>🟠</b>\n{_escape(title_text)}")

    desc_parts: list[str] = []
    # First non-empty "main" description field
    for key in ["problem", "description", "niche", "what_done", "project_status", "status"]:
        val = _get_value(answers, key)
        if val:
            desc_parts.append(val)
            break
    # Add niche/what_done if present
    for key in ["niche", "what_done"]:
        val = _get_value(answers, key)
        if val and val not in desc_parts:
            desc_parts.append(val)
    if desc_parts:
        sections.append(f"<b>📝</b>\n{_escape(chr(10).join(desc_parts))}")

    stack = _get_value(answers, "stack_reason", "stack")
    if not stack:
        stack_parts: list[str] = []
        for key in ["stack_ai", "stack_tech", "stack_infra"]:
            val = _get_value(answers, key)
            if val:
                stack_parts.append(val)
        stack = ", ".join(stack_parts) if stack_parts else None
    if stack:
        sections.append(f"<b>⚙️ Стек</b>\n{_escape(stack)}")

    links = answers.get("links")
    link = None
    if isinstance(links, list) and links:
        first = str(links[0]).strip() if links[0] is not None else ""
        link = first or None
    elif not links:
        link = _get_value(answers, "link")
    if link:
        sections.append(f"<b>🔗 Ссылка</b>\n{_escape(str(link))}")

    if public_url:
        sections.append(f"<b>🌐 Публичная страница</b>\n{_escape(public_url)}")

    price = _format_price(answers)
    if price:
        sections.append(f"<b>💰 Цена</b>\n{_escape(price)}")

    if show_contacts:
        contact = _get_value(answers, "author_contact_value", "author_contact", "contact")
        if contact:
            author_name = _get_value(answers, "author_name")
            contact_text = f"{author_name}\n{contact}" if author_name else contact
            sections.append(f"<b>📬 Контакт</b>\n{_escape(contact_text)}")

    return "\n\n".join(sections) or "<b>Проект</b>\n(пусто)"


def _parse_chat_id(raw: str) -> int | str | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value.lstrip("-").isdigit():
        return int(value)
    return value


def _tg_post_url(*, chat_id: int, username: str | None, message_id: int) -> str | None:
    if username:
        return f"https://t.me/{username}/{message_id}"
    s = str(chat_id)
    if s.startswith("-100"):
        return f"https://t.me/c/{s[4:]}/{message_id}"
    return None


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    # Backward-compatible alias. The moderation flow lives in /moderation.
    await cmd_moderation(message, state)


@router.message(Command("moderation"))
async def cmd_moderation(message: Message, state: FSMContext) -> None:
    """Admin moderation queue: list submitted projects with ✅/❌ buttons."""
    if not _is_admin(message.from_user.id if message.from_user else 0):
        return

    # If admin was entering a reject reason, reset to avoid accidental carry-over.
    try:
        await state.clear()
    except Exception:
        pass

    if db_session.async_session_maker is None:
        db_session.init_db()

    limit = 20
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Submission)
            .where(Submission.status == ProjectStatus.submitted)
            .order_by(Submission.submitted_at.asc().nullslast(), Submission.created_at.asc())
            .limit(limit)
        )
        submitted = list(r.scalars().all())

    if not submitted:
        await message.answer("Нет проектов на модерации.")
        return

    await message.answer(f"На модерации: {len(submitted)}")
    for sub in submitted:
        post = render_submission_post_html(sub.answers or {})
        meta = f"\n\n<b>ID:</b> <code>{sub.id}</code>"
        await message.answer(
            post + meta,
            parse_mode="HTML",
            reply_markup=moderation_kb(str(sub.id)),
            disable_web_page_preview=False,
        )


@router.callback_query(F.data.startswith("moderation:approve:"))
async def moderation_approve(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return

    parts = (callback.data or "").split(":", 2)
    if len(parts) != 3:
        await callback.answer()
        return
    sid_str = parts[2].strip()
    try:
        sub_id = uuid.UUID(sid_str)
    except ValueError:
        await callback.answer()
        return

    if db_session.async_session_maker is None:
        db_session.init_db()

    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == sub_id))
        sub = r.scalar_one_or_none()
        if not sub:
            await callback.answer("Не найдено", show_alert=True)
            return
        if sub.status != ProjectStatus.submitted:
            await callback.answer("Уже обработано", show_alert=True)
            return

        channel_raw = Settings().get_target_channel_id()
        channel = _parse_chat_id(channel_raw)
        if channel is None:
            await callback.answer("TARGET_CHANNEL_ID не задан", show_alert=True)
            return

        public_id = (sub.public_slug or "").strip() or str(sub.id)
        base = (Settings().webapp_url or "https://app.vibemom.ru").strip().rstrip("/")
        public_url = f"{base}/p/{public_id}" if base else None

        post_html = render_submission_post_html(
            sub.answers or {},
            show_contacts=bool(getattr(sub, "show_contacts", False)),
            public_url=public_url,
        )
        try:
            sent = await callback.bot.send_message(
                chat_id=channel,
                text=post_html,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
        except (TelegramForbiddenError, TelegramBadRequest, TelegramNotFound) as e:
            logger.exception("Publish failed submission_id=%s channel=%s", sub_id, channel_raw)
            await callback.answer("Ошибка публикации", show_alert=True)
            return

        tg_chat_id = sent.chat.id
        tg_username = getattr(sent.chat, "username", None)
        tg_post_url = _tg_post_url(chat_id=tg_chat_id, username=tg_username, message_id=sent.message_id)

        now = datetime.now(timezone.utc)
        sub.status = ProjectStatus.published
        sub.reviewed_at = now
        sub.approved_at = now  # legacy
        sub.rejected_at = None
        sub.rejected_reason = None
        sub.published = True
        sub.published_at = now
        sub.tg_chat_id = tg_chat_id
        sub.tg_message_id = sent.message_id
        sub.tg_post_url = tg_post_url
        sub.updated_at = now

        await session.commit()

        # Notify owner (best-effort)
        r_user = await session.execute(select(User).where(User.id == sub.user_id))
        owner = r_user.scalar_one_or_none()
        if owner:
            lines = ["✅ Ваш проект опубликован."]
            if public_url:
                lines.append(public_url)
            if tg_post_url:
                lines.append(tg_post_url)
            try:
                await callback.bot.send_message(chat_id=owner.telegram_id, text="\n".join(lines))
            except Exception:
                pass

    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
    await callback.answer("Опубликовано")


@router.callback_query(F.data.startswith("moderation:reject:"))
async def moderation_reject(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return

    parts = (callback.data or "").split(":", 2)
    if len(parts) != 3:
        await callback.answer()
        return
    sid_str = parts[2].strip()
    try:
        uuid.UUID(sid_str)
    except ValueError:
        await callback.answer()
        return

    await state.set_state(ModerationStates.awaiting_reject_reason)
    await state.update_data(
        mod_submission_id=sid_str,
        mod_admin_chat_id=str(callback.message.chat.id) if callback.message else "",
        mod_admin_message_id=int(callback.message.message_id) if callback.message else 0,
    )
    await callback.answer()
    await callback.message.answer("Введите причину отклонения (одним сообщением):")


@router.message(StateFilter(ModerationStates.awaiting_reject_reason), F.text)
async def moderation_reject_reason(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else 0):
        await state.clear()
        return

    data = await state.get_data()
    sid_str = (data.get("mod_submission_id") or "").strip()
    try:
        sub_id = uuid.UUID(sid_str)
    except ValueError:
        await state.clear()
        return

    reason = (message.text or "").strip()
    if not reason:
        await message.answer("Причина обязательна. Отправьте текстом:")
        return

    if db_session.async_session_maker is None:
        db_session.init_db()

    owner_tg_id: int | None = None
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == sub_id))
        sub = r.scalar_one_or_none()
        if not sub:
            await state.clear()
            await message.answer("Проект не найден.")
            return
        if sub.status != ProjectStatus.submitted:
            await state.clear()
            await message.answer("Уже обработано.")
            return

        now = datetime.now(timezone.utc)
        sub.status = ProjectStatus.rejected
        sub.reviewed_at = now
        sub.rejected_at = now  # legacy
        sub.rejected_reason = reason
        sub.updated_at = now

        r_user = await session.execute(select(User).where(User.id == sub.user_id))
        owner = r_user.scalar_one_or_none()
        if owner:
            owner_tg_id = owner.telegram_id

        await session.commit()

    # Notify owner (best-effort)
    if owner_tg_id is not None:
        try:
            await message.bot.send_message(
                chat_id=owner_tg_id,
                text="❌ Ваш проект отклонен.\nПричина:\n" + reason + "\n\nВы можете отредактировать и отправить снова.",
            )
        except Exception:
            pass

    # Remove buttons from the original moderation card (best-effort).
    admin_chat_id = (data.get("mod_admin_chat_id") or "").strip()
    admin_message_id = int(data.get("mod_admin_message_id") or 0)
    if admin_chat_id and admin_message_id:
        try:
            await message.bot.edit_message_reply_markup(chat_id=int(admin_chat_id), message_id=admin_message_id, reply_markup=None)
        except Exception:
            try:
                await message.bot.edit_message_reply_markup(chat_id=admin_chat_id, message_id=admin_message_id, reply_markup=None)
            except Exception:
                pass

    await state.clear()
    await message.answer("Отклонено.")


def _status_counts_default() -> dict[str, int]:
    return {s.value: 0 for s in ProjectStatus}


async def _stats_status_counts(session, *, since: datetime | None = None) -> dict[str, int]:
    q = select(Submission.status, func.count()).select_from(Submission).group_by(Submission.status)
    if since is not None:
        q = q.where(Submission.updated_at >= since)
    r = await session.execute(q)
    counts = _status_counts_default()
    for row in r:
        counts[row[0].value] = row[1]
    return counts


async def _stats_top_niches(session, since: datetime, limit: int = 5) -> list[tuple[str, int]]:
    from sqlalchemy import text
    stmt = text("""
        SELECT trim(answers->>'niche') AS niche, count(*) AS cnt
        FROM submission
        WHERE updated_at >= :cutoff
          AND answers->>'niche' IS NOT NULL
          AND trim(answers->>'niche') != ''
        GROUP BY trim(answers->>'niche')
        ORDER BY cnt DESC
        LIMIT :lim
    """)
    r = await session.execute(stmt, {"cutoff": since, "lim": limit})
    return [(row[0], row[1]) for row in r]


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    tg_id = message.from_user.id if message.from_user else 0
    if not _is_admin(tg_id):
        return
    if db_session.async_session_maker is None:
        db_session.init_db()
    now = datetime.now(timezone.utc)
    since_7d = now - timedelta(days=7)
    since_30d = now - timedelta(days=30)
    async with db_session.async_session_maker() as session:
        all_time = await _stats_status_counts(session)
        last_7d = await _stats_status_counts(session, since=since_7d)
        last_30d = await _stats_status_counts(session, since=since_30d)
        top_niches = await _stats_top_niches(session, since_30d, limit=5)
    lines = [
        "<b>📊 Stats (V2 submissions)</b>",
        "",
        "<b>All-time by status</b>",
        *[f"  {s}: {all_time[s]}" for s in _status_counts_default()],
        "",
        "<b>Last 7 days by status</b>",
        *[f"  {s}: {last_7d[s]}" for s in _status_counts_default()],
        "",
        "<b>Last 30 days by status</b>",
        *[f"  {s}: {last_30d[s]}" for s in _status_counts_default()],
        "",
        "<b>Top 5 niches (last 30 days)</b>",
    ]
    if top_niches:
        for niche, cnt in top_niches:
            safe = str(niche).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f"  • {safe}: {cnt}")
    else:
        lines.append("  (none)")
    await message.answer("\n".join(lines), parse_mode="HTML")
