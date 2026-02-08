"""
Projects service for business logic.

Handles project CRUD operations, field normalization, and preview rendering.
"""

import html
import uuid
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import BigInteger, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text, VARCHAR, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.dto.models import (
    NextActionDTO,
    NextActionType,
    PublicProjectDTO,
    PublicProjectListItemDTO,
    ProjectDetailsDTO,
    ProjectFieldsDTO,
    ProjectListItemDTO,
    ProjectStatus,
    ProjectPatchDTO,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class ProjectStatusConflictError(Exception):
    """Raised when an action is not allowed for the current project status."""


class TelegramPublishError(Exception):
    """Raised when Telegram channel publishing fails."""


# =============================================================================
# Database Models (inline to avoid circular imports with bot)
# =============================================================================


class Base(DeclarativeBase):
    pass


class Submission(Base):
    """V2 submission model (matches bot's model)."""

    __tablename__ = "submission"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("draft", "submitted", "rejected", "published", name="projectstatus"),
        default="draft",
        nullable=False,
    )
    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rendered_post: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_step: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    # Mini App public publishing (MVP).
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public_slug: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    # Telegram autopost metadata (filled after channel publishing).
    tg_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tg_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tg_post_url: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    show_contacts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Moderation metadata (new flow).
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Legacy moderation fields (kept for backward compatibility / old rows).
    fix_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class User(Base):
    """User model (matches bot's model)."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# =============================================================================
# Required Fields Configuration
# =============================================================================

# Required fields for submission (from MINIAPP_DATA_CONTRACT.md section P)
REQUIRED_FIELDS = [
    "project_title",
    "problem",
    "audience_type",
    "niche",
    "what_done",
    "project_status",
    "dev_time",
    "potential",
    "goal",
    "inbound_ready",
    "author_name",
    "author_contact_mode",
    "author_contact_value",
]

# MVP-required fields for the Mini App wizard publish flow (7/7).
# Keep this in sync with `services/webapp/src/lib/mvpWizard.ts`.
MVP_REQUIRED_FIELDS = [
    "project_title",
    "problem",
    "audience_type",
    "niche",
    "goal",
    "author_name",
    "author_contact_value",
]

# All known answer keys (for completion calculation)
ALL_ANSWER_KEYS = [
    "author_name",
    "author_contact_mode",
    "author_contact_value",
    "role",
    "project_title",
    "project_subtitle",
    "problem",
    "audience_type",
    "niche",
    "what_done",
    "project_status",
    "stack_ai",
    "stack_tech",
    "stack_infra",
    "stack_reason",
    "dev_time",
    "cost_currency",
    "cost_amount",
    "cost_max",
    "cost_hidden",
    "monetization_format",
    "monetization_text",
    "potential",
    "cool_part",
    "hardest_part",
    "goal",
    "inbound_ready",
    "links",
]

# Legacy key mappings (V1 → V2 fallback)
LEGACY_KEY_MAP = {
    "title": "project_title",
    "subtitle": "project_subtitle",
    "description": "problem",
    "status": "project_status",
    "contact": "author_contact_value",
    "author_contact": "author_contact_value",
}


# =============================================================================
# Projects Service
# =============================================================================


class ProjectsService:
    """Service for project operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _parse_target_chat_id(raw: str) -> int | str:
        value = (raw or "").strip()
        if not value:
            raise TelegramPublishError("TARGET_CHANNEL_ID is not configured")
        if value.lstrip("-").isdigit():
            return int(value)
        return value

    @staticmethod
    def _build_tg_post_url(*, chat_id: int, username: str | None, message_id: int) -> str | None:
        if username:
            return f"https://t.me/{username}/{message_id}"
        s = str(chat_id)
        if s.startswith("-100"):
            # Private chats/channels use an internal id in t.me/c links (strip the -100 prefix).
            return f"https://t.me/c/{s[4:]}/{message_id}"
        return None

    async def _tg_send_message(
        self,
        *,
        bot_token: str,
        chat_id: int | str,
        text: str,
        disable_web_page_preview: bool = False,
    ) -> dict[str, Any]:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": bool(disable_web_page_preview),
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TelegramPublishError(f"Telegram sendMessage failed: {type(exc).__name__}: {exc}") from exc

        try:
            data = resp.json()
        except Exception as exc:
            raise TelegramPublishError("Telegram sendMessage returned non-JSON response") from exc

        if not isinstance(data, dict) or not data.get("ok"):
            desc = None
            if isinstance(data, dict):
                desc = data.get("description")
            raise TelegramPublishError(f"Telegram sendMessage error: {desc or 'unknown error'}")

        result = data.get("result")
        if not isinstance(result, dict):
            raise TelegramPublishError("Telegram sendMessage returned unexpected payload")
        return result

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
    ) -> User:
        """Get existing user or create new one."""
        user = await self.get_user_by_telegram_id(telegram_id)

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Created new user: telegram_id={telegram_id}")
        else:
            # Update user info if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            if updated:
                await self.session.commit()
                logger.info(f"Updated user info: telegram_id={telegram_id}")

        return user

    async def get_user_projects(self, user_id: int) -> list[ProjectListItemDTO]:
        """Get all projects for a user."""
        result = await self.session.execute(
            select(Submission)
            .where(Submission.user_id == user_id)
            .order_by(Submission.updated_at.desc())
        )
        submissions = result.scalars().all()

        return [self._to_list_item_dto(s) for s in submissions]

    async def _create_draft_submission(self, user_id: int, answers: dict | None = None) -> Submission:
        """Create a draft submission row and return the ORM object."""
        submission = Submission(
            user_id=user_id,
            status="draft",
            revision=0,
            answers=answers or {},
            current_step="q1",
        )
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)

        logger.info(f"Created draft submission: id={submission.id}, user_id={user_id}")

        return submission

    async def create_draft(self, user_id: int) -> ProjectDetailsDTO:
        """Create a new draft submission."""
        submission = await self._create_draft_submission(user_id=user_id, answers={})
        return self._to_details_dto(submission)

    async def create_seed_draft(self, user_id: int, title: str = "Первый проект") -> ProjectDetailsDTO:
        """Create a first draft project so the Mini App never shows an empty screen."""
        submission = await self._create_draft_submission(
            user_id=user_id,
            answers={
                "project_title": title,
            },
        )
        return self._to_details_dto(submission)

    async def get_project_by_id(
        self,
        project_id: str,
        user_id: int | None = None,
        is_admin: bool = False,
    ) -> ProjectDetailsDTO | None:
        """Get project details by ID."""
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(
            select(Submission).where(Submission.id == pid)
        )
        submission = result.scalar_one_or_none()

        if submission is None:
            return None

        # Check access: owner or admin
        if not is_admin and user_id is not None and submission.user_id != user_id:
            return None

        return self._to_details_dto(submission)

    async def patch_project_answers(
        self,
        project_id: str,
        patch: ProjectPatchDTO,
        user_id: int | None = None,
        is_admin: bool = False,
    ) -> ProjectDetailsDTO | None:
        """Partially update submission.answers and return updated details.

        Access control:
        - Owner can update their own projects
        - Admin can update any project
        """
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(select(Submission).where(Submission.id == pid))
        submission = result.scalar_one_or_none()
        if submission is None:
            return None

        if not is_admin and user_id is not None and submission.user_id != user_id:
            return None

        status = ProjectStatus(submission.status)
        if status not in (ProjectStatus.draft, ProjectStatus.rejected):
            raise ProjectStatusConflictError("In moderation. Withdraw first.")

        updates = patch.model_dump(exclude_unset=True)
        if not updates:
            return self._to_details_dto(submission)

        # Basic type validation and guardrails
        allowed_contact_modes = {"telegram", "email", "phone"}
        if "author_contact_mode" in updates:
            mode = updates.get("author_contact_mode")
            if mode is not None:
                mode_norm = str(mode).strip().lower()
                if mode_norm not in allowed_contact_modes:
                    raise ValueError(f"Invalid author_contact_mode: {mode_norm}")
                updates["author_contact_mode"] = mode_norm

        answers: dict[str, Any] = dict(submission.answers or {})
        for key, value in updates.items():
            answers[key] = value

        submission.answers = answers
        submission.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(submission)

        return self._to_details_dto(submission)

    # =========================================================================
    # Moderation Flow (Mini App MVP)
    # =========================================================================

    async def submit_project(
        self,
        project_id: str,
        user_id: int,
        *,
        show_contacts: bool | None = None,
    ) -> ProjectDetailsDTO | None:
        """Submit project for moderation (author only)."""
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(select(Submission).where(Submission.id == pid))
        submission = result.scalar_one_or_none()
        if submission is None or submission.user_id != user_id:
            return None

        status = ProjectStatus(submission.status)
        if status not in (ProjectStatus.draft, ProjectStatus.rejected):
            raise ProjectStatusConflictError("In moderation. Withdraw first.")

        answers: dict[str, Any] = dict(submission.answers or {})
        missing = self._calculate_mvp_missing(answers)
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        now = datetime.utcnow()
        submission.status = ProjectStatus.submitted.value
        submission.submitted_at = now
        submission.updated_at = now

        if show_contacts is not None:
            submission.show_contacts = bool(show_contacts)

        # Clear previous review metadata for a fresh moderation cycle.
        submission.reviewed_at = None
        submission.approved_at = None
        submission.rejected_at = None
        submission.rejected_reason = None

        await self.session.commit()
        await self.session.refresh(submission)

        logger.info(
            "Submitted project for moderation",
            extra={
                "project_id": str(submission.id),
                "user_id": user_id,
            },
        )

        return self._to_details_dto(submission)

    async def withdraw_project(self, project_id: str, user_id: int) -> ProjectDetailsDTO | None:
        """Withdraw a submitted project back to draft (author only)."""
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(select(Submission).where(Submission.id == pid))
        submission = result.scalar_one_or_none()
        if submission is None or submission.user_id != user_id:
            return None

        status = ProjectStatus(submission.status)
        if status != ProjectStatus.submitted:
            raise ProjectStatusConflictError("Only submitted projects can be withdrawn.")

        now = datetime.utcnow()
        submission.status = ProjectStatus.draft.value
        submission.submitted_at = None
        submission.updated_at = now

        await self.session.commit()
        await self.session.refresh(submission)

        logger.info(
            "Withdrew project from moderation",
            extra={
                "project_id": str(submission.id),
                "user_id": user_id,
            },
        )

        return self._to_details_dto(submission)

    async def delete_project(self, project_id: str, user_id: int) -> bool:
        """Delete project (author only). Allowed only for draft/rejected."""
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return False

        result = await self.session.execute(select(Submission).where(Submission.id == pid))
        submission = result.scalar_one_or_none()
        if submission is None or submission.user_id != user_id:
            return False

        status = ProjectStatus(submission.status)
        if status not in (ProjectStatus.draft, ProjectStatus.rejected):
            raise ProjectStatusConflictError("In moderation. Withdraw first.")

        await self.session.delete(submission)
        await self.session.commit()

        logger.info(
            "Deleted project",
            extra={
                "project_id": project_id,
                "user_id": user_id,
            },
        )

        return True

    # =========================================================================
    # Admin Moderation (approve/reject)
    # =========================================================================

    async def approve_project(self, project_id: str) -> ProjectDetailsDTO | None:
        """
        Approve a submitted project and publish it to the Telegram channel.

        Rules:
        - Allowed only when status == submitted
        - Sets status = published
        - Persists tg_chat_id/tg_message_id/tg_post_url
        """
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(select(Submission).where(Submission.id == pid))
        submission = result.scalar_one_or_none()
        if submission is None:
            return None

        status = ProjectStatus(submission.status)
        if status != ProjectStatus.submitted:
            raise ProjectStatusConflictError("Only submitted projects can be approved.")

        from app.config import get_settings

        settings = get_settings()
        bot_token = (settings.bot_token or "").strip()
        if not bot_token:
            raise TelegramPublishError("BOT_TOKEN is not configured")

        target_chat_id_raw = ""
        if hasattr(settings, "get_target_channel_id"):
            target_chat_id_raw = str(settings.get_target_channel_id() or "")
        else:
            # Backward-compatible envs.
            target_chat_id_raw = str(getattr(settings, "target_channel_id", "") or getattr(settings, "feed_chat_id", "") or "")

        target_chat_id = self._parse_target_chat_id(target_chat_id_raw)

        public_url = self._build_public_url(self._public_id(submission))
        post_html = self.render_preview(
            submission.answers or {},
            show_contacts=bool(submission.show_contacts),
            public_url=public_url,
        )
        tg_result = await self._tg_send_message(
            bot_token=bot_token,
            chat_id=target_chat_id,
            text=post_html,
            disable_web_page_preview=False,
        )

        try:
            message_id = int(tg_result.get("message_id"))
        except Exception as exc:
            raise TelegramPublishError("Telegram sendMessage returned missing/invalid message_id") from exc

        chat = tg_result.get("chat") if isinstance(tg_result.get("chat"), dict) else {}
        try:
            tg_chat_id = int(chat.get("id")) if chat and chat.get("id") is not None else None
        except Exception:
            tg_chat_id = None
        username = chat.get("username") if chat else None

        # Best-effort link build (username preferred).
        tg_post_url = None
        if tg_chat_id is not None:
            tg_post_url = self._build_tg_post_url(chat_id=tg_chat_id, username=username, message_id=message_id)

        now = datetime.utcnow()
        submission.status = ProjectStatus.published.value
        submission.reviewed_at = now
        submission.approved_at = now  # legacy/backward-compatible
        submission.rejected_at = None
        submission.rejected_reason = None
        submission.published = True  # legacy flag
        submission.published_at = now
        submission.tg_chat_id = tg_chat_id
        submission.tg_message_id = message_id
        submission.tg_post_url = tg_post_url
        submission.updated_at = now

        await self.session.commit()
        await self.session.refresh(submission)

        return self._to_details_dto(submission)

    async def reject_project(self, project_id: str, *, reason: str) -> ProjectDetailsDTO | None:
        """
        Reject a submitted project (admin-only).

        Rules:
        - Allowed only when status == submitted
        - Requires a non-empty reason
        - Sets status = rejected and persists rejected_reason
        """
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(select(Submission).where(Submission.id == pid))
        submission = result.scalar_one_or_none()
        if submission is None:
            return None

        status = ProjectStatus(submission.status)
        if status != ProjectStatus.submitted:
            raise ProjectStatusConflictError("Only submitted projects can be rejected.")

        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise ValueError("Rejection reason is required.")

        now = datetime.utcnow()
        submission.status = ProjectStatus.rejected.value
        submission.reviewed_at = now
        submission.rejected_at = now  # legacy/backward-compatible
        submission.rejected_reason = clean_reason
        submission.updated_at = now

        await self.session.commit()
        await self.session.refresh(submission)

        return self._to_details_dto(submission)

    async def list_public_projects(self, limit: int = 50, offset: int = 0) -> list[PublicProjectListItemDTO]:
        """List projects published to Telegram channel (no-auth)."""
        limit = max(1, min(50, int(limit)))
        offset = max(0, int(offset))

        result = await self.session.execute(
            select(Submission)
            .where(Submission.status == ProjectStatus.published.value)
            .order_by(Submission.published_at.desc().nullslast(), Submission.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        submissions = result.scalars().all()
        return [self._to_public_list_item_dto(s) for s in submissions]

    async def get_public_project_by_identifier(self, id_or_slug: str) -> PublicProjectDTO | None:
        """Get a project published to Telegram by UUID or public_slug (no-auth)."""
        raw = (id_or_slug or "").strip()
        if not raw:
            return None

        stmt = select(Submission).where(Submission.status == ProjectStatus.published.value)
        try:
            pid = uuid.UUID(raw)
            stmt = stmt.where(Submission.id == pid)
        except ValueError:
            stmt = stmt.where(Submission.public_slug == raw)

        result = await self.session.execute(stmt)
        submission = result.scalar_one_or_none()
        if submission is None:
            return None

        return self._to_public_project_dto(submission)

    def render_preview(
        self,
        answers: dict[str, Any] | None,
        *,
        show_contacts: bool = True,
        public_url: str | None = None,
    ) -> str:
        """
        Render project post HTML from answers.

        Single source of truth — same output for preview and publish.
        All user content is HTML-escaped.
        """
        if not answers:
            answers = {}

        sections = []

        # Title: project_title + project_subtitle
        title = self._get_value(answers, "project_title", "title")
        subtitle = self._get_value(answers, "project_subtitle", "subtitle")
        title_text = title or ""
        if subtitle:
            title_text = f"{title_text}\n{subtitle}" if title_text else subtitle
        if title_text:
            sections.append(f"<b>🟢</b>\n{self._escape(title_text)}")

        # Description: problem + niche + what_done + project_status
        desc_parts = []
        for key in ["problem", "description", "niche", "what_done", "project_status", "status"]:
            val = self._get_value(answers, key)
            if val:
                desc_parts.append(val)
                break  # Only use first non-empty
        for key in ["niche", "what_done"]:
            val = self._get_value(answers, key)
            if val and val not in desc_parts:
                desc_parts.append(val)
        if desc_parts:
            sections.append(f"<b>📝</b>\n{self._escape(chr(10).join(desc_parts))}")

        # Stack
        stack = self._get_value(answers, "stack_reason", "stack")
        if not stack:
            stack_parts = []
            for key in ["stack_ai", "stack_tech", "stack_infra"]:
                val = self._get_value(answers, key)
                if val:
                    stack_parts.append(val)
            stack = ", ".join(stack_parts) if stack_parts else None
        if stack:
            sections.append(f"<b>⚙️ Стек</b>\n{self._escape(stack)}")

        # Links
        links = answers.get("links")
        link = None
        if isinstance(links, list) and links:
            link = links[0]
        elif not links:
            link = self._get_value(answers, "link")
        if link:
            sections.append(f"<b>🔗 Ссылка</b>\n{self._escape(str(link))}")

        # Public page (optional)
        if public_url:
            sections.append(f"<b>🌐 Публичная страница</b>\n{self._escape(public_url)}")

        # Price
        price = self._format_price(answers)
        if price:
            sections.append(f"<b>💰 Цена</b>\n{self._escape(price)}")

        # Contact
        if show_contacts:
            contact = self._get_value(answers, "author_contact_value", "author_contact", "contact")
            if contact:
                author_name = self._get_value(answers, "author_name")
                if author_name:
                    contact = f"{author_name}\n{contact}"
                sections.append(f"<b>📬 Контакт</b>\n{self._escape(contact)}")

        return "\n\n".join(sections)

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _to_list_item_dto(self, submission: Submission) -> ProjectListItemDTO:
        """Convert Submission to ProjectListItemDTO."""
        answers = submission.answers or {}
        status = ProjectStatus(submission.status)

        # Calculate completion
        filled, missing = self._calculate_completion(answers)
        mvp_missing = self._calculate_mvp_missing(answers)
        completion_percent = int(len(filled) / len(REQUIRED_FIELDS) * 100) if REQUIRED_FIELDS else 0

        # Get title
        title = self._get_value(answers, "project_title", "title") or "Без названия"
        title_short = title[:50] + "..." if len(title) > 50 else title

        # Determine next action
        next_action = self._get_next_action(status, missing)

        # Access control flags
        can_edit = status in (ProjectStatus.draft, ProjectStatus.rejected)
        can_submit = status in (ProjectStatus.draft, ProjectStatus.rejected) and len(mvp_missing) == 0
        can_archive = False  # Reserved for future (no archive endpoint in Mini App MVP).
        can_delete = status in (ProjectStatus.draft, ProjectStatus.rejected)

        return ProjectListItemDTO(
            id=str(submission.id),
            status=status,
            revision=submission.revision,
            title_short=title_short,
            completion_percent=completion_percent,
            next_action=next_action,
            can_edit=can_edit,
            can_submit=can_submit,
            can_archive=can_archive,
            can_delete=can_delete,
            created_at=submission.created_at,
            updated_at=submission.updated_at,
            submitted_at=submission.submitted_at,
            reviewed_at=submission.reviewed_at,
            approved_at=submission.approved_at,
            rejected_at=submission.rejected_at,
            rejected_reason=submission.rejected_reason,
            published_at=submission.published_at,
            tg_post_url=submission.tg_post_url,
            current_step=submission.current_step,
            missing_fields=missing,
            published=status == ProjectStatus.published,
            public_slug=submission.public_slug,
            show_contacts=submission.show_contacts,
        )

    def _to_details_dto(self, submission: Submission) -> ProjectDetailsDTO:
        """Convert Submission to ProjectDetailsDTO."""
        answers = submission.answers or {}
        status = ProjectStatus(submission.status)

        # Calculate completion
        filled, missing = self._calculate_completion(answers)
        mvp_missing = self._calculate_mvp_missing(answers)
        completion_percent = int(len(filled) / len(REQUIRED_FIELDS) * 100) if REQUIRED_FIELDS else 0

        # Normalize fields
        fields = self._normalize_fields(answers)

        # Determine next action
        next_action = self._get_next_action(status, missing)

        # Render preview (same template used for publishing).
        public_url = self._build_public_url(self._public_id(submission)) if status == ProjectStatus.published else None
        preview_html = self.render_preview(
            answers,
            show_contacts=bool(submission.show_contacts),
            public_url=public_url,
        )

        # Access control flags
        can_edit = status in (ProjectStatus.draft, ProjectStatus.rejected)
        can_submit = status in (ProjectStatus.draft, ProjectStatus.rejected) and len(mvp_missing) == 0
        can_archive = False  # Reserved for future (no archive endpoint in Mini App MVP).
        can_delete = status in (ProjectStatus.draft, ProjectStatus.rejected)

        return ProjectDetailsDTO(
            id=str(submission.id),
            status=status,
            revision=submission.revision,
            current_step=submission.current_step,
            answers=answers,
            fields=fields,
            preview_html=preview_html,
            completion_percent=completion_percent,
            missing_fields=missing,
            filled_fields=filled,
            next_action=next_action,
            can_edit=can_edit,
            can_submit=can_submit,
            can_archive=can_archive,
            can_delete=can_delete,
            reviewed_at=submission.reviewed_at,
            approved_at=submission.approved_at,
            rejected_at=submission.rejected_at,
            rejected_reason=submission.rejected_reason,
            tg_post_url=submission.tg_post_url,
            created_at=submission.created_at,
            updated_at=submission.updated_at,
            submitted_at=submission.submitted_at,
            published=status == ProjectStatus.published,
            published_at=submission.published_at,
            public_slug=submission.public_slug,
            show_contacts=submission.show_contacts,
        )

    def _calculate_completion(self, answers: dict[str, Any]) -> tuple[list[str], list[str]]:
        """Calculate filled and missing required fields."""
        filled = []
        missing = []

        for key in REQUIRED_FIELDS:
            value = self._get_value_raw(answers, key)

            # Check if field is considered filled
            if value is not None and value != "" and value != []:
                filled.append(key)
            else:
                missing.append(key)

        return filled, missing

    def _calculate_mvp_missing(self, answers: dict[str, Any]) -> list[str]:
        """Missing MVP-required fields for the Mini App wizard (7/7)."""
        missing: list[str] = []
        for key in MVP_REQUIRED_FIELDS:
            value = self._get_value_raw(answers, key)
            if value is None or value == "" or value == []:
                missing.append(key)
        return missing

    def _build_public_url(self, public_id: str) -> str:
        """Build a shareable public URL for a published project."""
        from app.config import get_settings

        settings = get_settings()
        base = (settings.webapp_url or "https://app.vibemom.ru").strip().rstrip("/")
        return f"{base}/p/{public_id}"

    def _public_id(self, submission: Submission) -> str:
        slug = (submission.public_slug or "").strip()
        return slug or str(submission.id)

    def _to_public_list_item_dto(self, submission: Submission) -> PublicProjectListItemDTO:
        answers: dict[str, Any] = dict(submission.answers or {})
        public_id = self._public_id(submission)
        title = self._get_value(answers, "project_title", "title") or "Без названия"

        return PublicProjectListItemDTO(
            id=str(submission.id),
            slug=submission.public_slug,
            public_id=public_id,
            public_url=self._build_public_url(public_id),
            published_at=submission.published_at,
            title=title,
            problem=self._get_value(answers, "problem", "description"),
            audience_type=self._get_value(answers, "audience_type"),
            niche=self._get_value(answers, "niche"),
        )

    def _to_public_project_dto(self, submission: Submission) -> PublicProjectDTO:
        answers: dict[str, Any] = dict(submission.answers or {})
        public_id = self._public_id(submission)

        # Stack: prefer explicit free-form field, fallback to structured parts.
        stack = self._get_value(answers, "stack_reason", "stack")
        if not stack:
            stack_parts = []
            for key in ["stack_ai", "stack_tech", "stack_infra"]:
                val = self._get_value(answers, key)
                if val:
                    stack_parts.append(val)
            stack = ", ".join(stack_parts) if stack_parts else None

        show_contacts = bool(submission.show_contacts)
        contact_value = (
            self._get_value(answers, "author_contact_value", "author_contact", "contact") if show_contacts else None
        )
        contact_mode = self._get_value(answers, "author_contact_mode") if show_contacts else None

        return PublicProjectDTO(
            id=str(submission.id),
            slug=submission.public_slug,
            public_id=public_id,
            public_url=self._build_public_url(public_id),
            published_at=submission.published_at,
            show_contacts=show_contacts,
            title=self._get_value(answers, "project_title", "title") or "Без названия",
            problem=self._get_value(answers, "problem", "description"),
            audience_type=self._get_value(answers, "audience_type"),
            niche=self._get_value(answers, "niche"),
            what_done=self._get_value(answers, "what_done"),
            stack=stack,
            dev_time=self._get_value(answers, "dev_time", "time_spent"),
            potential=self._get_value(answers, "potential"),
            goal=self._get_value(answers, "goal", "goal_pub"),
            author_name=self._get_value(answers, "author_name"),
            contact_mode=contact_mode,
            contact_value=contact_value,
        )

    def _get_next_action(self, status: ProjectStatus, missing_fields: list[str]) -> NextActionDTO:
        """Determine next action based on status and completion."""
        action_map = {
            ProjectStatus.draft: (
                NextActionType.continue_form,
                "Продолжить заполнение",
                True,
            ),
            ProjectStatus.submitted: (
                NextActionType.wait,
                "Ожидает модерации",
                False,
            ),
            ProjectStatus.rejected: (
                NextActionType.continue_form,
                "Исправить и отправить снова",
                True,
            ),
            ProjectStatus.published: (
                NextActionType.view,
                "Открыть",
                True,
            ),
        }

        action_type, label, cta_enabled = action_map.get(
            status,
            (NextActionType.view, "Посмотреть", True)
        )

        return NextActionDTO(
            action=action_type,
            label=label,
            cta_enabled=cta_enabled,
        )

    def _normalize_fields(self, answers: dict[str, Any]) -> ProjectFieldsDTO:
        """Normalize answers to ProjectFieldsDTO."""
        links = answers.get("links", [])
        if isinstance(links, str):
            links = [links] if links else []
        elif not isinstance(links, list):
            links = []

        return ProjectFieldsDTO(
            author_name=self._get_value(answers, "author_name"),
            author_contact=self._get_value(answers, "author_contact_value", "author_contact", "contact"),
            author_role=self._get_value(answers, "role"),
            project_title=self._get_value(answers, "project_title", "title"),
            project_subtitle=self._get_value(answers, "project_subtitle", "subtitle"),
            problem=self._get_value(answers, "problem", "description"),
            audience_type=self._get_value(answers, "audience_type"),
            niche=self._get_value(answers, "niche"),
            what_done=self._get_value(answers, "what_done"),
            project_status=self._get_value(answers, "project_status", "status"),
            stack_ai=self._get_value(answers, "stack_ai"),
            stack_tech=self._get_value(answers, "stack_tech"),
            stack_infra=self._get_value(answers, "stack_infra"),
            stack_reason=self._get_value(answers, "stack_reason", "stack"),
            dev_time=self._get_value(answers, "dev_time", "time_spent"),
            price_display=self._format_price(answers),
            monetization=self._get_value(answers, "monetization_text", "monetization_format"),
            potential=self._get_value(answers, "potential"),
            goal=self._get_value(answers, "goal", "goal_pub"),
            inbound_ready=self._get_value(answers, "inbound_ready", "goal_inbound"),
            links=links,
            cool_part=self._get_value(answers, "cool_part"),
            hardest_part=self._get_value(answers, "hardest_part"),
        )

    def _get_value(self, answers: dict[str, Any], *keys: str) -> str | None:
        """Get first non-empty value from answers using key priority."""
        for key in keys:
            value = self._get_value_raw(answers, key)
            if value is not None and value != "" and value != []:
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value if v)
                return str(value).strip()
        return None

    def _get_value_raw(self, answers: dict[str, Any], key: str) -> Any:
        """Get raw value from answers with legacy fallback."""
        if key in answers:
            return answers[key]
        # Try legacy mapping
        for legacy_key, v2_key in LEGACY_KEY_MAP.items():
            if v2_key == key and legacy_key in answers:
                return answers[legacy_key]
        return None

    def _format_price(self, answers: dict[str, Any]) -> str | None:
        """Format price display string."""
        # Check if hidden
        if answers.get("cost_hidden") is True or answers.get("budget_hidden") is True:
            return "скрыта"

        # Get values (V2 keys first, then legacy)
        min_val = answers.get("cost_amount") or answers.get("budget_min")
        max_val = answers.get("cost_max") or answers.get("budget_max")
        currency = (
            answers.get("cost_currency")
            or answers.get("budget_currency")
            or answers.get("currency")
            or "RUB"
        )

        # Check legacy hidden
        if str(currency).upper() == "HIDDEN":
            return "скрыта"

        # Get symbol
        cur = str(currency).upper()
        symbol = "₽" if cur == "RUB" else "$" if cur == "USD" else "€" if cur == "EUR" else cur

        # Format price
        try:
            mn = int(min_val) if min_val is not None else None
            mx = int(max_val) if max_val is not None else None
        except (TypeError, ValueError):
            mn = mx = None

        if mn is not None and mx is not None and mn != mx:
            return f"{mn:,}–{mx:,} {symbol}".replace(",", " ")
        elif mn is not None:
            return f"{mn:,} {symbol}".replace(",", " ")
        elif mx is not None:
            return f"до {mx:,} {symbol}".replace(",", " ")

        # Legacy string price
        price_str = answers.get("price")
        if price_str:
            return str(price_str)

        return None

    def _escape(self, text: str) -> str:
        """HTML escape user content."""
        return html.escape(text, quote=True)
