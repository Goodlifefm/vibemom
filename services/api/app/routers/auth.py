"""
Authentication endpoints.

Endpoints:
- POST /auth/telegram - Authenticate with Telegram initData
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.telegram_webapp import InitDataValidationError, validate_init_data
from app.config import get_settings
from app.db import get_session
from app.dto.models import AuthRequestDTO, AuthResponseDTO, UserDTO
from app.logging_config import get_logger
from app.services.projects_service import ProjectsService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/telegram",
    response_model=AuthResponseDTO,
    summary="Authenticate with Telegram",
    description="Validate Telegram WebApp initData and return JWT token.",
    responses={
        401: {"description": "Invalid initData"},
        500: {"description": "Server error"},
    },
)
async def auth_telegram(
    body: AuthRequestDTO,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponseDTO:
    """
    Authenticate user with Telegram WebApp initData.

    1. Validates initData using Telegram's HMAC algorithm
    2. Creates or updates user in database
    3. Returns JWT access token

    The token should be used in Authorization header for subsequent requests:
    `Authorization: Bearer <token>`
    """
    try:
        # Validate initData
        tg_user = validate_init_data(body.init_data)
    except InitDataValidationError as e:
        logger.warning(f"Auth failed: {e.message}", extra={"details": e.details})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid initData: {e.message}",
        )

    # Get or create user in database
    service = ProjectsService(session)
    db_user = await service.get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )

    # Check admin status
    settings = get_settings()
    admin_ids = settings.get_admin_ids()
    is_admin = db_user.is_admin or tg_user.id in admin_ids

    # Create JWT token
    access_token = create_access_token(
        telegram_id=tg_user.id,
        username=tg_user.username,
    )

    # Calculate expiration time in seconds
    expires_in = settings.api_jwt_ttl_min * 60

    logger.info(
        "User authenticated",
        extra={"telegram_id": tg_user.id, "username": tg_user.username}
    )

    return AuthResponseDTO(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserDTO(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
            is_admin=is_admin,
        ),
    )
