from sqlalchemy import select

from src.bot.database import session as db_session
from src.bot.database.models import User


async def get_or_create_user(
    telegram_id: int,
    username: str | None,
    full_name: str | None,
) -> User:
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        r = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = r.scalar_one_or_none()
        if user:
            user.username = username
            user.full_name = full_name
            await session.commit()
            await session.refresh(user)
            return user
        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
