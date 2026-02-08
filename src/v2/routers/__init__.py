"""V2 routers: menu (global), start (cabinet), form (steps + back/skip), preview, moderation, fallback. Wired when V2_ENABLED=true."""
from aiogram import Router

from src.v2.routers import menu as v2_menu
from src.v2.routers import start as v2_start
from src.v2.routers import form as v2_form
from src.v2.routers import preview as v2_preview
from src.v2.routers import moderation as v2_moderation
from src.v2.routers import fallback as v2_fallback


def setup_v2_routers() -> Router:
    root = Router()
    root.include_router(v2_menu.router)  # first: catch 🏠 Меню / /menu from any state
    root.include_router(v2_start.router)
    root.include_router(v2_form.router)
    root.include_router(v2_preview.router)
    root.include_router(v2_moderation.router)
    root.include_router(v2_fallback.router)  # last: unknown callback_data -> "Открой меню: 🏠 Меню"
    return root
