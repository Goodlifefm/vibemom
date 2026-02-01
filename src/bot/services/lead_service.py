import uuid
from sqlalchemy import select

from src.bot.database import session as db_session
from src.bot.database.models import Lead, LeadType, Project, BuyerRequest, ProjectStatus


async def create_leads_for_request(
    buyer_request_id: uuid.UUID,
    project_ids: list[uuid.UUID],
) -> None:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        for pid in project_ids:
            lead = Lead(
                project_id=pid,
                buyer_request_id=buyer_request_id,
                lead_type=LeadType.REQUEST_OFFER,
            )
            session.add(lead)
        await session.commit()


async def list_leads_for_seller(user_id: int) -> tuple[list[Project], list[Lead]]:
    """Return (my_projects, leads for those projects)."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(Project).where(Project.seller_id == user_id))
        my_projects = list(r.scalars().all())
        project_ids = [p.id for p in my_projects]
        if not project_ids:
            return my_projects, []
        r2 = await session.execute(
            select(Lead).where(Lead.project_id.in_(project_ids)).order_by(Lead.created_at.desc())
        )
        leads_list = list(r2.scalars().all())
    return my_projects, leads_list


async def list_my_requests_with_projects(
    user_id: int,
) -> tuple[list[BuyerRequest], list[Lead], dict[uuid.UUID, Project]]:
    """Return (buyer_requests, leads for them, project_id -> Project for approved)."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(
            select(BuyerRequest).where(BuyerRequest.buyer_id == user_id).order_by(BuyerRequest.created_at.desc())
        )
        requests_list = list(r.scalars().all())
        if not requests_list:
            return requests_list, [], {}
        r2 = await session.execute(
            select(Lead).where(Lead.buyer_request_id.in_([req.id for req in requests_list]))
        )
        leads_list = list(r2.scalars().all())
        r3 = await session.execute(select(Project).where(Project.status == ProjectStatus.approved))
        all_projects = {p.id: p for p in r3.scalars().all()}
    return requests_list, leads_list, all_projects
