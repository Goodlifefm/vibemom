from aiogram import Router

from src.bot.handlers import admin, catalog, start, submit
from src.bot.config import Settings


def setup_routers() -> Router:
    root = Router()
    settings = Settings()
    if getattr(settings, "v2_enabled", False):
        from src.v2.routers import setup_v2_routers
        root.include_router(setup_v2_routers())
    root.include_router(start.router)
    root.include_router(submit.router)
    root.include_router(catalog.router)
    root.include_router(admin.router)
    return root
