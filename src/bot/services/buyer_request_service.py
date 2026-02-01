from src.bot.database import session as db_session
from src.bot.database.models import BuyerRequest


async def create_buyer_request(
    buyer_id: int,
    what: str,
    budget: str,
    contact: str,
) -> BuyerRequest:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        req = BuyerRequest(
            buyer_id=buyer_id,
            what=what,
            budget=budget,
            contact=contact,
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)
        return req
