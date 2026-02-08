"""
Public storefront endpoints (no-auth).

Endpoints:
- GET /public/projects - list published projects
- GET /public/projects/{id_or_slug} - get published project card
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dto.models import PublicProjectDTO, PublicProjectListItemDTO
from app.logging_config import get_logger
from app.services.projects_service import ProjectsService

logger = get_logger(__name__)

router = APIRouter(prefix="/public", tags=["Public"])


@router.get(
    "/projects",
    response_model=list[PublicProjectListItemDTO],
    summary="List published projects",
    description="Public storefront listing. Returns only published projects.",
)
async def list_public_projects(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> list[PublicProjectListItemDTO]:
    service = ProjectsService(session)
    items = await service.list_public_projects(limit=limit, offset=offset)
    logger.debug("Listed public projects", extra={"limit": limit, "offset": offset, "count": len(items)})
    return items


@router.get(
    "/projects/{id_or_slug}",
    response_model=PublicProjectDTO,
    summary="Get published project",
    description="Public project page data. Accepts UUID or public_slug.",
    responses={
        404: {"description": "Project not found"},
    },
)
async def get_public_project(
    id_or_slug: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublicProjectDTO:
    service = ProjectsService(session)
    project = await service.get_public_project_by_identifier(id_or_slug)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
