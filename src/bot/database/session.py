from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bot.config import Settings


def get_engine(settings: Settings | None = None):
    from src.bot.config import Settings as S
    s = settings or S()
    url = s.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=False)


def get_session_factory(settings: Settings | None = None):
    engine = get_engine(settings)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async_session_maker = None


def init_db(settings: Settings | None = None) -> None:
    global async_session_maker
    async_session_maker = get_session_factory(settings)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_maker is None:
        init_db()
    async with async_session_maker() as session:
        yield session
