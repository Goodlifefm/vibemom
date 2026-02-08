"""
Projects endpoints.

Endpoints:
- GET /projects/my - Get current user's projects
- POST /projects/create_draft - Create new draft project
- GET /projects/{id} - Get project details
- POST /projects/{id}/submit - Submit project for moderation
- POST /projects/{id}/withdraw - Withdraw project from moderation
- PATCH /projects/{id} - Update project (allowed only for draft/rejected)
- DELETE /projects/{id} - Delete project (allowed only for draft/rejected)
- POST /projects/{id}/approve - Approve and publish (admin-only)
- POST /projects/{id}/reject - Reject with reason (admin-only)
- POST /projects/{id}/preview - Generate preview (rendering)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.db import get_session
from app.dto.models import (
    PreviewDTO,
    ProjectDetailsDTO,
    ProjectListItemDTO,
    ProjectPatchDTO,
    RejectProjectRequestDTO,
    SubmitProjectRequestDTO,
)
from app.logging_config import get_logger
from app.services.projects_service import ProjectsService, ProjectStatusConflictError, TelegramPublishError

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
    service = ProjectsService(session)
    user_id = current_user.db_id

    # Ensure user exists in DB even if auth dependency couldn't resolve db_id
    # (e.g. first run after fresh DB, or transient DB lookup error recovery).
    if user_id is None:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    projects = await service.get_user_projects(user_id)
    if len(projects) == 0:
        # Auto-seed "Первый проект" to avoid dead-end empty UX.
        await service.create_seed_draft(user_id)
        projects = await service.get_user_projects(user_id)

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
        "Created draft project",
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

    user_id = current_user.db_id
    if user_id is None and not current_user.is_admin:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    project = await service.get_project_by_id(
        project_id=project_id,
        user_id=user_id,
        is_admin=current_user.is_admin,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    logger.debug(
        "Retrieved project details",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
        }
    )

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectDetailsDTO,
    summary="Update project (partial)",
    description="Partially update project answers by ID. Allowed only for author projects in draft/rejected.",
    responses={
        400: {"description": "Invalid payload"},
        404: {"description": "Project not found or access denied"},
        409: {"description": "In moderation"},
    },
)
async def patch_project(
    project_id: str,
    payload: ProjectPatchDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    service = ProjectsService(session)

    user_id = current_user.db_id
    if user_id is None:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    try:
        updated = await service.patch_project_answers(
            project_id=project_id,
            user_id=user_id,
            is_admin=False,  # Author-only for PATCH in the Mini App
            patch=payload,
        )
    except ProjectStatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    logger.info(
        "Patched project answers",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
            "keys": list(payload.model_dump(exclude_unset=True).keys()),
        },
    )

    return updated


@router.post(
    "/{project_id}/submit",
    response_model=ProjectDetailsDTO,
    summary="Submit project for moderation",
    description="Submit a project for moderation (MVP fields required). User must be owner.",
    responses={
        400: {"description": "Project is not ready for submit (missing required fields)"},
        404: {"description": "Project not found or access denied"},
        409: {"description": "In moderation"},
    },
)
async def submit_project(
    project_id: str,
    payload: SubmitProjectRequestDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    service = ProjectsService(session)

    # Ensure user exists in DB
    user_id = current_user.db_id
    if user_id is None:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    try:
        submitted = await service.submit_project(
            project_id=project_id,
            user_id=user_id,
            show_contacts=payload.show_contacts,
        )
    except ProjectStatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if submitted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    logger.info(
        "Submitted project (Mini App)",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
            "show_contacts": payload.show_contacts,
        },
    )

    return submitted


@router.post(
    "/{project_id}/withdraw",
    response_model=ProjectDetailsDTO,
    summary="Withdraw project from moderation",
    description="Withdraw a submitted project back to draft. User must be owner.",
    responses={
        404: {"description": "Project not found or access denied"},
        409: {"description": "Not in submitted status"},
    },
)
async def withdraw_project(
    project_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    service = ProjectsService(session)

    # Ensure user exists in DB
    user_id = current_user.db_id
    if user_id is None:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    try:
        updated = await service.withdraw_project(project_id=project_id, user_id=user_id)
    except ProjectStatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    logger.info(
        "Withdrew project (Mini App)",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
        },
    )

    return updated


@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Delete a project. Allowed only for draft/rejected. User must be owner.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Project not found or access denied"},
        409: {"description": "In moderation"},
    },
)
async def delete_project(
    project_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    service = ProjectsService(session)

    # Ensure user exists in DB
    user_id = current_user.db_id
    if user_id is None:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    try:
        ok = await service.delete_project(project_id=project_id, user_id=user_id)
    except ProjectStatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    logger.info(
        "Deleted project (Mini App)",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
        },
    )


@router.post(
    "/{project_id}/approve",
    response_model=ProjectDetailsDTO,
    summary="Approve project (admin-only)",
    description="Approve a submitted project, publish it to the Telegram channel, and mark it as published.",
    responses={
        403: {"description": "Admin only"},
        404: {"description": "Project not found"},
        409: {"description": "Invalid status transition"},
        502: {"description": "Telegram publish failed"},
    },
)
async def approve_project(
    project_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    service = ProjectsService(session)

    try:
        updated = await service.approve_project(project_id=project_id)
    except ProjectStatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TelegramPublishError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    logger.info(
        "Approved project (admin)",
        extra={"project_id": project_id, "telegram_id": current_user.telegram_id},
    )

    return updated


@router.post(
    "/{project_id}/reject",
    response_model=ProjectDetailsDTO,
    summary="Reject project (admin-only)",
    description="Reject a submitted project with a required reason.",
    responses={
        400: {"description": "Reason required"},
        403: {"description": "Admin only"},
        404: {"description": "Project not found"},
        409: {"description": "Invalid status transition"},
    },
)
async def reject_project(
    project_id: str,
    payload: RejectProjectRequestDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectDetailsDTO:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    service = ProjectsService(session)

    try:
        updated = await service.reject_project(project_id=project_id, reason=payload.reason)
    except ProjectStatusConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    logger.info(
        "Rejected project (admin)",
        extra={"project_id": project_id, "telegram_id": current_user.telegram_id},
    )

    return updated


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

    user_id = current_user.db_id
    if user_id is None and not current_user.is_admin:
        user = await service.get_or_create_user(
            telegram_id=current_user.telegram_id,
            username=current_user.username,
            full_name=current_user.full_name,
        )
        user_id = user.id

    project = await service.get_project_by_id(
        project_id=project_id,
        user_id=user_id,
        is_admin=current_user.is_admin,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    # Generate preview using answers
    preview_html = service.render_preview(project.answers, show_contacts=bool(project.show_contacts))

    logger.debug(
        "Generated preview",
        extra={
            "project_id": project_id,
            "telegram_id": current_user.telegram_id,
        }
    )

    return PreviewDTO(preview_html=preview_html)
