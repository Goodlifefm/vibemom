"""
Telegram WebApp initData validation.

Implements HMAC validation as per Telegram Bot API documentation:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, unquote

from pydantic import BaseModel

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class TelegramUser(BaseModel):
    """Telegram user data from initData."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    photo_url: str | None = None

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class InitDataValidationError(Exception):
    """Raised when initData validation fails."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


def validate_init_data(
    init_data: str,
    bot_token: str | None = None,
    max_age_seconds: int = 86400,  # 24 hours
) -> TelegramUser:
    """
    Validate Telegram WebApp initData and extract user information.

    The validation follows Telegram's algorithm:
    1. Parse init_data as URL query string
    2. Extract hash from the data
    3. Create data-check-string from remaining fields
    4. Create secret key: HMAC-SHA256(bot_token, "WebAppData")
    5. Calculate HMAC-SHA256(data_check_string, secret_key)
    6. Compare with provided hash

    Args:
        init_data: The initData string from Telegram WebApp
        bot_token: Bot token for validation (uses settings if not provided)
        max_age_seconds: Maximum age of auth_date in seconds (default 24h)

    Returns:
        TelegramUser object with user data

    Raises:
        InitDataValidationError: If validation fails
    """
    if not init_data:
        raise InitDataValidationError("Empty initData")

    # Get bot token
    if not bot_token:
        settings = get_settings()
        bot_token = settings.bot_token

    if not bot_token:
        raise InitDataValidationError("Bot token not configured")

    try:
        # Parse query string
        parsed = parse_qs(init_data, keep_blank_values=True)
        data_dict: dict[str, Any] = {}

        for key, values in parsed.items():
            if values:
                # URL decode the value
                data_dict[key] = unquote(values[0])

        # Extract and validate hash
        received_hash = data_dict.pop("hash", None)
        if not received_hash:
            raise InitDataValidationError("Missing hash in initData")

        # Validate auth_date (prevent replay attacks)
        auth_date_str = data_dict.get("auth_date")
        if not auth_date_str:
            raise InitDataValidationError("Missing auth_date in initData")

        try:
            auth_date = int(auth_date_str)
            now = int(datetime.now(timezone.utc).timestamp())
            age = now - auth_date

            if age > max_age_seconds:
                raise InitDataValidationError(
                    "initData expired",
                    f"age={age}s, max={max_age_seconds}s"
                )
            if age < -60:  # Allow 1 minute clock skew
                raise InitDataValidationError(
                    "initData from future",
                    f"age={age}s"
                )
        except ValueError:
            raise InitDataValidationError("Invalid auth_date format")

        # Create data-check-string: sort keys alphabetically, format as "key=value"
        data_check_pairs = sorted(
            [f"{k}={v}" for k, v in data_dict.items()],
            key=lambda x: x.split("=")[0]
        )
        data_check_string = "\n".join(data_check_pairs)

        # Create secret key: HMAC-SHA256("WebAppData", bot_token)
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        # Calculate HMAC-SHA256(data_check_string, secret_key)
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Compare hashes (constant time comparison)
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning(
                "initData hash mismatch",
                extra={"calculated": calculated_hash[:16], "received": received_hash[:16]}
            )
            raise InitDataValidationError("Invalid hash signature")

        # Extract user data
        user_str = data_dict.get("user")
        if not user_str:
            raise InitDataValidationError("Missing user in initData")

        try:
            user_data = json.loads(user_str)
            user = TelegramUser(**user_data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise InitDataValidationError(f"Invalid user data: {e}")

        logger.info(
            "initData validated successfully",
            extra={"telegram_id": user.id, "username": user.username}
        )

        return user

    except InitDataValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error validating initData: {e}")
        raise InitDataValidationError(f"Validation failed: {e}")
