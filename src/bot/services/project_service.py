import uuid
from sqlalchemy import select

from src.bot.database import session as db_session
from src.bot.database.models import Project, ProjectStatus


async def create_project(
    seller_id: int,
    title: str,
    description: str,
    stack: str,
    link: str,
    price: str,
    contact: str,
) -> Project:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        project = Project(
            seller_id=seller_id,
            title=title,
            description=description,
            stack=stack,
            link=link,
            price=price,
            contact=contact,
            status=ProjectStatus.pending,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project


async def list_approved_projects() -> list[Project]:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Project).where(Project.status == ProjectStatus.approved).order_by(Project.created_at.desc())
        )
        return list(r.scalars().all())


async def list_pending_projects() -> list[Project]:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Project).where(Project.status == ProjectStatus.pending).order_by(Project.created_at.asc())
        )
        return list(r.scalars().all())


async def update_project_status(project_id: uuid.UUID, status: ProjectStatus) -> None:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Project).where(Project.id == project_id))
        p = r.scalar_one_or_none()
        if p:
            p.status = status
            await session.commit()
