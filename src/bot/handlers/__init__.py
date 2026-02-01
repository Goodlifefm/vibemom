from aiogram import Router

from src.bot.handlers import admin, catalog, leads, request, start, submit

def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(submit.router)
    root.include_router(request.router)
    root.include_router(catalog.router)
    root.include_router(leads.router)
    root.include_router(admin.router)
    return root
