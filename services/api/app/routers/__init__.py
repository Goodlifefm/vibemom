"""
API Routers.
"""

from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.me import router as me_router
from app.routers.projects import router as projects_router
from app.routers.public import router as public_router
from app.routers.debug import router as debug_router

__all__ = [
    "health_router",
    "auth_router",
    "me_router",
    "projects_router",
    "public_router",
    "debug_router",
]
