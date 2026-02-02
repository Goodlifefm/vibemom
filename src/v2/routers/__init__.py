"""V2 routers: start (cabinet), form (steps + back/skip), preview, moderation. Wired when V2_ENABLED=true."""
from aiogram import Router

from src.v2.routers import start as v2_start
from src.v2.routers import form as v2_form
from src.v2.routers import preview as v2_preview
from src.v2.routers import moderation as v2_moderation


def setup_v2_routers() -> Router:
    root = Router()
    root.include_router(v2_start.router)
    root.include_router(v2_form.router)
    root.include_router(v2_preview.router)
    root.include_router(v2_moderation.router)
    return root
