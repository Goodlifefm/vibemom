"""
Current user endpoints.

Endpoints:
- GET /me - Get current user info
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.deps import CurrentUser, get_current_user
from app.dto.models import UserDTO

router = APIRouter(tags=["User"])


@router.get(
    "/me",
    response_model=UserDTO,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UserDTO:
    """
    Get current authenticated user's information.

    Returns:
        UserDTO with telegram_id, username, full_name, and is_admin flag.
    """
    return UserDTO(
        telegram_id=current_user.telegram_id,
        username=current_user.username,
        full_name=current_user.full_name,
        is_admin=current_user.is_admin,
    )
