"""
JWT token handling for API authentication.

Uses HS256 algorithm with configurable secret and expiration.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# JWT algorithm
ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    """JWT token payload."""

    telegram_id: int
    username: str | None = None
    exp: datetime
    iat: datetime


class TokenError(Exception):
    """Base exception for token errors."""

    pass


class TokenExpiredError(TokenError):
    """Raised when token has expired."""

    pass


class TokenInvalidError(TokenError):
    """Raised when token is invalid."""

    pass


def create_access_token(
    telegram_id: int,
    username: str | None = None,
    *,
    secret: str | None = None,
    ttl_minutes: int | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        telegram_id: User's Telegram ID
        username: User's Telegram username
        secret: JWT secret (uses settings if not provided)
        ttl_minutes: Token TTL in minutes (uses settings if not provided)

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()

    if secret is None:
        secret = settings.api_jwt_secret
    if ttl_minutes is None:
        ttl_minutes = settings.api_jwt_ttl_min

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ttl_minutes)

    payload: dict[str, Any] = {
        "telegram_id": telegram_id,
        "username": username,
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(payload, secret, algorithm=ALGORITHM)

    logger.debug(
        "Created access token",
        extra={"telegram_id": telegram_id, "expires": expire.isoformat()}
    )

    return token


def decode_access_token(
    token: str,
    *,
    secret: str | None = None,
) -> TokenPayload:
    """
    Decode and validate a JWT access token.

    Args:
        token: Encoded JWT token string
        secret: JWT secret (uses settings if not provided)

    Returns:
        TokenPayload with decoded data

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    settings = get_settings()

    if secret is None:
        secret = settings.api_jwt_secret

    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

        # Convert timestamps to datetime
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        return TokenPayload(
            telegram_id=payload["telegram_id"],
            username=payload.get("username"),
            exp=exp,
            iat=iat,
        )

    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        raise TokenExpiredError("Token has expired")

    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise TokenInvalidError(f"Invalid token: {e}")

    except (KeyError, ValueError) as e:
        logger.warning(f"Malformed token payload: {e}")
        raise TokenInvalidError(f"Malformed token payload: {e}")
