"""
Standalone DB health check for Docker and smoke tests.
Runnable as: python -m src.bot.health
Uses Settings from env; does not depend on init_db() or the main bot process.
"""
import asyncio
import sys

from sqlalchemy import text

from src.bot.config import Settings
from src.bot.database.session import get_engine


async def check_db() -> bool:
    settings = Settings()
    engine = get_engine(settings)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    finally:
        await engine.dispose()


def main() -> None:
    try:
        ok = asyncio.run(check_db())
        if ok:
            print("OK")
            sys.exit(0)
    except Exception as e:
        print(f"health check failed: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
