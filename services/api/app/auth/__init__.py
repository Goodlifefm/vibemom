"""
Authentication module for Telegram Mini App.

Provides:
- Telegram WebApp initData validation
- JWT token generation and validation
- FastAPI dependencies for authentication
"""

from app.auth.telegram_webapp import TelegramUser, validate_init_data
from app.auth.jwt import create_access_token, decode_access_token, TokenPayload
from app.auth.deps import get_current_user, CurrentUser

__all__ = [
    "TelegramUser",
    "validate_init_data",
    "create_access_token",
    "decode_access_token",
    "TokenPayload",
    "get_current_user",
    "CurrentUser",
]
