from sqlalchemy import select

from src.bot.database import session as db_session
from src.bot.database.models import Project, ProjectStatus
from src.bot.matching import filter_and_sort_matches


async def match_request_to_projects(request_what: str, request_budget: str) -> list[dict]:
    """Return list of project dicts (id, title, description, price) with score >= threshold."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Project).where(Project.status == ProjectStatus.approved))
        projects = r.scalars().all()
    proj_dicts = [
        {"id": str(p.id), "title": p.title, "description": p.description, "price": p.price}
        for p in projects
    ]
    return filter_and_sort_matches(request_what, request_budget, proj_dicts)
