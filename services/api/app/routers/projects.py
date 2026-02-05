"""
Projects endpoints.

Endpoints:
- GET /projects/my - Get current user's projects
- POST /projects/create_draft - Create new draft project
- GET /projects/{id} - Get project details
- POST /projects/{id}/preview - Generate preview
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.db import get_session
from app.dto.models import PreviewDTO, ProjectDetailsDTO, ProjectListItemDTO
from app.logging_config import get_logger
from app.services.projects_service import ProjectsService

logger = get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "/my",
    response_model=list[ProjectListItemDTO],
    summary="Get my projects",
    description="Get list of all projects for the current user.",
)
async def get_my_projects(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProjectListItemDTO]:
    """
    Get all projects (submissions) for the current authenticated user.

    Returns list of ProjectListItemDTO with:
    - Basic info: id, status, revision
    - Progress: completion_percent, missing_fields
    - Action hints: next_action, can_* flags
    - Timestamps and moderation info
    """
    if current_user.db_id is None:
        # User doesn't exist in DB yet, no projects
        return []

    service = ProjectsService(session)
    projects = await service.get_user_projects(current_user.db_id)

    logger.debug(
        f"Retrieved {len(projects)} projects for user",
        extra={"telegram_id": current_user.telegram_id}
    )

    return projects


@router.post(
    "/create_draft",
    response_model=ProjectDetailsDTO,
    summary="Create draft project",
    description="Create a new draft project for the current user.",
    status_code=status.HTTP_201_CREATED,
)
async def create_draft_project(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    """
    Create a new draft project for the current user.

    Returns ProjectDetailsDTO with the new project details.
    """
    service = ProjectsService(session)

    # Ensure user exists in DB
    user = await service.get_or_create_user(
        telegram_id=current_user.telegram_id,
        username=current_user.username,
        full_name=current_user.full_name,
    )

    # Create draft submission
    project = await service.create_draft(user.id)

    logger.info(
        f"Created draft project",
        extra={
            "project_id": project.id,
            "telegram_id": current_user.telegram_id,
        }
    )

    return project


@router.get(
    "/{project_id}",
    response_model=ProjectDetailsDTO,
    summary="Get project details",
    description="Get full project details by ID. User must be owner or admin.",
    responses={
        404: {"description": "Project not found or access denied"},
    },
)
async def get_project(
    project_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    """
    Get full project details by ID.

    Access control:
    - Owner can view their own projects
    - Admin can view any project

    Returns ProjectDetailsDTO with:
    - Full project info and normalized fields
    - Raw answers (for editing)
    - Rendered preview HTML
    - Progress and action hints
    """
    service = ProjectsService(session)

    project = await service.get_project_by_id(
        project_id=project_id,
        user_id=current_user.db_id,
        is_admin=current_user.is_admin,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    logger.debug(
        f"Retrieved project details",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
        }
    )

    return project


@router.post(
    "/{project_id}/preview",
    response_model=PreviewDTO,
    summary="Generate preview",
    description="Generate HTML preview for a project. User must be owner or admin.",
    responses={
        404: {"description": "Project not found or access denied"},
    },
)
async def generate_preview(
    project_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PreviewDTO:
    """
    Generate preview HTML for a project.

    Uses the same renderer as GET /projects/{id}, ensuring
    preview == published consistency.

    Returns PreviewDTO with:
    - preview_html: HTML-escaped project post
    """
    service = ProjectsService(session)

    project = await service.get_project_by_id(
        project_id=project_id,
        user_id=current_user.db_id,
        is_admin=current_user.is_admin,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    # Generate preview using answers
    preview_html = service.render_preview(project.answers)

    logger.debug(
        f"Generated preview",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
        }
    )

    return PreviewDTO(preview_html=preview_html)
