import uuid
from datetime import datetime, timezone, timedelta
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy import select, func

from src.bot.config import Settings
from src.bot.database import session as db_session
from src.bot.database.models import ProjectStatus, Submission
from src.bot.keyboards import admin_moderate_kb
from src.bot.messages import get_copy
from src.bot.renderer import render_project_post
from src.bot.services import list_pending_projects, update_project_status

router = Router()


def _is_admin(telegram_id: int) -> bool:
    s = Settings()
    return telegram_id in s.get_admin_ids()


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else 0):
        return
    pending = await list_pending_projects()
    if not pending:
        await message.answer(get_copy("ADMIN_MODERATE_PROMPT") + get_copy("ADMIN_NO_PENDING"))
        return
    p = pending[0]
    text = render_project_post(p.title, p.description, p.stack, p.link, p.price, p.contact)
    await message.answer(get_copy("ADMIN_MODERATE_PROMPT"))
    await message.answer(text, reply_markup=admin_moderate_kb(str(p.id)))


@router.callback_query(F.data.startswith("mod_approve_"))
async def admin_approve(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return
    project_id = callback.data.replace("mod_approve_", "")
    await update_project_status(uuid.UUID(project_id), ProjectStatus.approved)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("ADMIN_APPROVE"))
    await callback.answer()


@router.callback_query(F.data.startswith("mod_fix_"))
async def admin_needs_fix(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return
    project_id = callback.data.replace("mod_fix_", "")
    await update_project_status(uuid.UUID(project_id), ProjectStatus.needs_fix)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("ADMIN_NEEDS_FIX"))
    await callback.answer()


@router.callback_query(F.data.startswith("mod_reject_"))
async def admin_reject(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else 0):
        await callback.answer()
        return
    project_id = callback.data.replace("mod_reject_", "")
    await update_project_status(uuid.UUID(project_id), ProjectStatus.rejected)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(get_copy("ADMIN_REJECT"))
    await callback.answer()


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
