import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Text, VARCHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    needs_fix = "needs_fix"
    approved = "approved"
    rejected = "rejected"


class LeadType(str, enum.Enum):
    PROJECT_INTEREST = "PROJECT_INTEREST"
    REQUEST_OFFER = "REQUEST_OFFER"


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
        Enum(ProjectStatus), default=ProjectStatus.pending, nullable=False
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
