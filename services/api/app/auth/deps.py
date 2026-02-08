"""
FastAPI authentication dependencies.

Provides dependency injection for authenticated routes.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenError, TokenPayload, decode_access_token
from app.config import get_settings
from app.db import get_session
from app.logging_config import get_logger

logger = get_logger(__name__)

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Current authenticated user information."""

    telegram_id: int
    username: str | None = None
    full_name: str | None = None
    is_admin: bool = False
    db_id: int | None = None  # Internal DB ID (not exposed in APIs)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    """
    FastAPI dependency to get the current authenticated user.

    Validates JWT token from Authorization header and looks up user in database.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        session: Database session

    Returns:
        CurrentUser object with user information

    Raises:
        HTTPException: 401 if authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload: TokenPayload = decode_access_token(token)
    except TokenError as e:
        logger.warning(f"Auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    admin_ids = settings.get_admin_ids()

    # Look up user in database
    # Import here to avoid circular imports
    try:
        # Try to import the shared User model from bot
        from sqlalchemy import BigInteger, Boolean, VARCHAR
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

        class Base(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"

            id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
            telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
            username: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
            full_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
            is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

        result = await session.execute(
            select(User).where(User.telegram_id == payload.telegram_id)
        )
        db_user = result.scalar_one_or_none()

        if db_user:
            return CurrentUser(
                telegram_id=db_user.telegram_id,
                username=db_user.username,
                full_name=db_user.full_name,
                is_admin=db_user.is_admin or payload.telegram_id in admin_ids,
                db_id=db_user.id,
            )

    except Exception as e:
        logger.warning(f"Failed to look up user in DB: {e}")

    # User not in DB yet, return basic info from token
    return CurrentUser(
        telegram_id=payload.telegram_id,
        username=payload.username,
        is_admin=payload.telegram_id in admin_ids,
    )


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser | None:
    """
    Optional authentication dependency.

    Returns None if no valid token is provided instead of raising an exception.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
