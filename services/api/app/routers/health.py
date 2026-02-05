"""
Health check and version endpoints.

Endpoints:
- GET /healthz - Health check
- GET /version - Version information
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app import __version__
from app.config import get_settings
from app.db import check_db_connection
from app.dto.models import HealthResponse, VersionResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service and database are healthy.",
)
async def healthz() -> HealthResponse | JSONResponse:
    """
    Health check endpoint.

    Returns 200 if service is healthy, 503 if database is unavailable.
    """
    db_ok = await check_db_connection()

    if db_ok:
        return HealthResponse(status="ok", database="ok")
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "unavailable"},
        )


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Version information",
    description="Get service version and build information.",
)
async def version() -> VersionResponse:
    """
    Version information endpoint.

    Returns version, git SHA, branch, build time, and Mini App URLs.
    """
    settings = get_settings()

    return VersionResponse(
        version=__version__,
        git_sha=settings.git_sha,
        git_branch=settings.git_branch,
        build_time=settings.build_time,
        env=settings.app_env,
        webapp_url=settings.webapp_url or "(not set)",
        api_public_url=settings.api_public_url or "(not set)",
    )
