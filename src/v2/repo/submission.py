"""V2 repo: submission lifecycle (draft -> submitted -> approved/rejected -> published_to_tg)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from src.bot.database import session as db_session
from src.bot.database.models import ProjectStatus, Submission


async def get_submission(submission_id: uuid.UUID) -> Submission | None:
    """Load submission by id (for form/preview)."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == submission_id))
        return r.scalar_one_or_none()


async def get_active_submission(user_id: int) -> Submission | None:
    """Latest submission for user in draft or rejected (editable). user_id = User.id (PK)."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Submission)
            .where(Submission.user_id == user_id)
            .where(Submission.status.in_([ProjectStatus.draft, ProjectStatus.rejected]))
            .order_by(Submission.updated_at.desc())
            .limit(1)
        )
        return r.scalar_one_or_none()


async def list_submissions_by_user(user_id: int, limit: int = 5) -> list[Submission]:
    """Last N submissions by user (any status). For V2 cabinet «My projects»."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Submission)
            .where(Submission.user_id == user_id)
            .order_by(Submission.updated_at.desc())
            .limit(limit)
        )
        return list(r.scalars().all())


async def create_submission(
    user_id: int,
    project_id: uuid.UUID | None = None,
    current_step: str | None = "q1",
) -> Submission:
    """Create draft submission. user_id = User.id (PK). current_step for resume."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        sub = Submission(
            user_id=user_id,
            project_id=project_id,
            status=ProjectStatus.draft,
            revision=0,
            answers=None,
            current_step=current_step,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub


async def update_answers_step(
    submission_id: uuid.UUID,
    answers: dict,
    current_step: str | None = None,
) -> Submission | None:
    """Merge answers into submission.answers; optionally set current_step. Persist after each step."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == submission_id))
        sub = r.scalar_one_or_none()
        if not sub:
            return None
        current = dict(sub.answers) if sub.answers else {}
        current.update(answers)
        sub.answers = current
        if current_step is not None:
            sub.current_step = current_step
        await session.commit()
        await session.refresh(sub)
        return sub


async def set_status(submission_id: uuid.UUID, status: ProjectStatus) -> Submission | None:
    """Set submission status; set submitted_at when status becomes submitted."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == submission_id))
        sub = r.scalar_one_or_none()
        if not sub:
            return None
        sub.status = status
        if status == ProjectStatus.submitted:
            sub.submitted_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(sub)
        return sub


async def set_moderated(
    submission_id: uuid.UUID,
    status: ProjectStatus,
    rejected_reason: str | None = None,
) -> Submission | None:
    """Set status + moderation timestamps; keep legacy moderated_at for older tooling."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == submission_id))
        sub = r.scalar_one_or_none()
        if not sub:
            return None
        sub.status = status
        now = datetime.now(timezone.utc)
        sub.moderated_at = now
        if status == ProjectStatus.approved:
            sub.approved_at = now
        elif status == ProjectStatus.rejected:
            sub.rejected_at = now
            if rejected_reason is not None:
                sub.rejected_reason = rejected_reason
        elif status == ProjectStatus.published_to_tg:
            sub.published_at = now
        await session.commit()
        await session.refresh(sub)
        return sub


async def set_published_to_tg(
    submission_id: uuid.UUID,
    *,
    tg_chat_id: int,
    tg_message_id: int,
    tg_post_url: str | None,
) -> Submission | None:
    """Mark submission as published to Telegram channel; persist message metadata."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == submission_id))
        sub = r.scalar_one_or_none()
        if not sub:
            return None
        now = datetime.now(timezone.utc)
        sub.status = ProjectStatus.published_to_tg
        sub.published = True  # Legacy flag used by older public storefront code
        sub.published_at = now
        sub.tg_chat_id = tg_chat_id
        sub.tg_message_id = tg_message_id
        sub.tg_post_url = (tg_post_url or "").strip() or None
        await session.commit()
        await session.refresh(sub)
        return sub


async def submit_for_moderation(submission_id: uuid.UUID, rendered_post: str) -> Submission | None:
    """Persist rendered_post, set status=submitted, submitted_at=now(), revision += 1 (Option A)."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Submission).where(Submission.id == submission_id))
        sub = r.scalar_one_or_none()
        if not sub:
            return None
        sub.rendered_post = rendered_post
        sub.status = ProjectStatus.submitted
        sub.submitted_at = datetime.now(timezone.utc)
        sub.revision = (sub.revision or 0) + 1
        sub.fix_request = None
        sub.rejected_reason = None
        sub.rejected_at = None
        await session.commit()
        await session.refresh(sub)
        return sub


async def delete_submission(submission_id: uuid.UUID, user_id: int) -> bool:
    """Delete submission if it belongs to user. Returns True if deleted, False if not found or not owner."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Submission).where(
                Submission.id == submission_id,
                Submission.user_id == user_id,
            )
        )
        sub = r.scalar_one_or_none()
        if not sub:
            return False
        await session.delete(sub)
        await session.commit()
        return True
