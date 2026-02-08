import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, Text, VARCHAR
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    rejected = "rejected"
    published = "published"

    # Backward-compatible aliases (stored as the canonical values above).
    pending = "submitted"
    needs_fix = "rejected"
    approved = "published"
    published_to_tg = "published"


class LeadType(str, enum.Enum):
    PROJECT_INTEREST = "PROJECT_INTEREST"
    REQUEST_OFFER = "REQUEST_OFFER"


class AdminActionType(str, enum.Enum):
    """V2: admin moderation action for audit log."""
    approve = "approve"
    needs_fix = "needs_fix"
    reject = "reject"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="seller")
    buyer_requests: Mapped[list["BuyerRequest"]] = relationship("BuyerRequest", back_populates="buyer")


class Project(Base):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    stack: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    link: Mapped[str] = mapped_column(VARCHAR(1000), nullable=False)
    price: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    contact: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.draft, nullable=False
    )
    moderation_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    seller: Mapped["User"] = relationship("User", back_populates="projects")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="project")


class BuyerRequest(Base):
    __tablename__ = "buyer_request"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    what: Mapped[str] = mapped_column(Text, nullable=False)
    budget: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    contact: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer: Mapped["User"] = relationship("User", back_populates="buyer_requests")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="buyer_request")


class Lead(Base):
    __tablename__ = "lead"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    buyer_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("buyer_request.id"), nullable=True)
    lead_type: Mapped[LeadType] = mapped_column(Enum(LeadType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="leads")
    buyer_request: Mapped["BuyerRequest | None"] = relationship("BuyerRequest", back_populates="leads")


# --- V2 forward-compatible tables (Step 2). V1 does not use these. ---


class Submission(Base):
    """Submission lifecycle (draft -> submitted -> rejected/published)."""
    __tablename__ = "submission"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.draft, nullable=False
    )
    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rendered_post: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_step: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    # Mini App public publishing (MVP).
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public_slug: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True, index=True)
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
    # Legacy moderation metadata (kept for backward compatibility / old rows).
    fix_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminAction(Base):
    """V2: audit log of admin moderation actions (approve / needs_fix / reject)."""
    __tablename__ = "admin_action"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    target_project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=True)
    target_submission_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("submission.id"), nullable=True)
    action: Mapped[AdminActionType] = mapped_column(Enum(AdminActionType), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
