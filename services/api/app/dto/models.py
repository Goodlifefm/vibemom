"""
Pydantic models for API DTOs.

Following docs/MINIAPP_DATA_CONTRACT.md specifications.
All user-supplied content is HTML-escaped when rendered.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums
# =============================================================================


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    draft = "draft"
    pending = "pending"
    needs_fix = "needs_fix"
    approved = "approved"
    rejected = "rejected"


class NextActionType(str, Enum):
    """Next action type for project."""

    continue_form = "continue"
    fix = "fix"
    wait = "wait"
    view = "view"
    archived = "archived"


# =============================================================================
# User DTOs
# =============================================================================


class UserPublicDTO(BaseModel):
    """Public user information (external API)."""

    model_config = ConfigDict(from_attributes=True)

    telegram_id: int
    username: str | None = None
    full_name: str | None = None


class UserDTO(UserPublicDTO):
    """User DTO with admin flag."""

    is_admin: bool = False


# =============================================================================
# Auth DTOs
# =============================================================================


class AuthRequestDTO(BaseModel):
    """Request body for /auth/telegram endpoint."""

    init_data: str = Field(..., alias="initData", description="Telegram WebApp initData string")

    model_config = ConfigDict(populate_by_name=True)


class TokenDTO(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class AuthResponseDTO(BaseModel):
    """Response from /auth/telegram endpoint."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserDTO


# =============================================================================
# Project DTOs
# =============================================================================


class NextActionDTO(BaseModel):
    """Next action hint for project UI."""

    action: NextActionType
    label: str
    cta_enabled: bool


class ProjectListItemDTO(BaseModel):
    """Project item for list view (My Projects)."""

    model_config = ConfigDict(from_attributes=True)

    # Identity
    id: str  # UUID as string
    status: ProjectStatus
    revision: int

    # Display
    title_short: str  # Truncated to 50 chars
    completion_percent: int  # 0-100

    # Action
    next_action: NextActionDTO

    # Access control flags
    can_edit: bool
    can_submit: bool
    can_archive: bool
    can_delete: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None

    # Moderation
    has_fix_request: bool
    fix_request_preview: str | None = None  # First 100 chars

    # Derived
    current_step: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class ProjectFieldsDTO(BaseModel):
    """Normalized project fields for rendering."""

    # Author
    author_name: str | None = None
    author_contact: str | None = None
    author_role: str | None = None

    # Project
    project_title: str | None = None
    project_subtitle: str | None = None
    problem: str | None = None
    audience_type: str | None = None
    niche: str | None = None
    what_done: str | None = None
    project_status: str | None = None

    # Stack
    stack_ai: str | None = None
    stack_tech: str | None = None
    stack_infra: str | None = None
    stack_reason: str | None = None

    # Economics
    dev_time: str | None = None
    price_display: str | None = None
    monetization: str | None = None
    potential: str | None = None

    # Goals
    goal: str | None = None
    inbound_ready: str | None = None

    # Links
    links: list[str] = Field(default_factory=list)

    # Highlights
    cool_part: str | None = None
    hardest_part: str | None = None


class ProjectDetailsDTO(BaseModel):
    """Full project details for detail/edit view."""

    model_config = ConfigDict(from_attributes=True)

    # Identity
    id: str  # UUID as string
    status: ProjectStatus
    revision: int
    current_step: str | None = None

    # Content
    answers: dict[str, Any] | None = None  # Raw answers (for admin/debug)
    fields: ProjectFieldsDTO  # Normalized fields

    # Rendered
    preview_html: str | None = None

    # Progress
    completion_percent: int
    missing_fields: list[str] = Field(default_factory=list)
    filled_fields: list[str] = Field(default_factory=list)

    # Action
    next_action: NextActionDTO

    # Access control
    can_edit: bool
    can_submit: bool
    can_archive: bool
    can_delete: bool

    # Moderation
    fix_request: str | None = None
    moderated_at: datetime | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None


class PreviewDTO(BaseModel):
    """Preview response."""

    preview_html: str


# =============================================================================
# API Response Wrappers
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    database: str = "ok"


class VersionResponse(BaseModel):
    """Version info response."""

    version: str
    git_sha: str
    git_branch: str
    build_time: str
    env: str
    webapp_url: str
    api_public_url: str


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    code: str | None = None
