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


async def list_projects_by_seller(seller_id: int, limit: int = 5) -> list[Project]:
    """Last N projects by seller (any status). For V2 cabinet."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(Project)
            .where(Project.seller_id == seller_id)
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )
        return list(r.scalars().all())


async def get_project(project_id: uuid.UUID) -> Project | None:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Project).where(Project.id == project_id))
        return r.scalar_one_or_none()


async def update_project_fields(
    project_id: uuid.UUID,
    *,
    title: str | None = None,
    description: str | None = None,
    stack: str | None = None,
    link: str | None = None,
    price: str | None = None,
    contact: str | None = None,
    status: ProjectStatus | None = None,
) -> Project | None:
    """Update project fields (for V2 draft edits). Only non-None args are updated."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Project).where(Project.id == project_id))
        p = r.scalar_one_or_none()
        if not p:
            return None
        if title is not None:
            p.title = title
        if description is not None:
            p.description = description
        if stack is not None:
            p.stack = stack
        if link is not None:
            p.link = link
        if price is not None:
            p.price = price
        if contact is not None:
            p.contact = contact
        if status is not None:
            p.status = status
        await session.commit()
        await session.refresh(p)
        return p


async def create_draft_project(seller_id: int) -> Project:
    """Create a new draft project (V2). Uses placeholders for required columns."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        project = Project(
            seller_id=seller_id,
            title="—",
            description="{}",
            stack="—",
            link="—",
            price="—",
            contact="—",
            status=ProjectStatus.draft,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project
