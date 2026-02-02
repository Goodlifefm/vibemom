#!/usr/bin/env python3
"""
Step 3 verification: run inside bot container to exercise V2 repo against real DB.
  docker compose exec bot python -m scripts.v2_repo_smoke
Expected: prints OK and exit 0.
"""
import asyncio
import sys

from src.bot.config import Settings
from src.bot.database.session import init_db
from src.bot.database.models import ProjectStatus
from src.bot.database.models import AdminActionType
from src.v2.repo import (
    get_or_create_user,
    get_active_submission,
    create_submission,
    update_answers_step,
    set_status,
    log_admin_action,
)


async def main() -> None:
    settings = Settings()
    init_db(settings)

    user = await get_or_create_user(telegram_id=999999999, username=None, full_name="V2 smoke test")
    assert user.id is not None

    sub = await create_submission(user_id=user.id)
    assert sub.id is not None
    assert sub.status == ProjectStatus.draft

    updated = await update_answers_step(sub.id, {"step1": "value1"})
    assert updated is not None
    assert updated.answers == {"step1": "value1"}

    await set_status(sub.id, ProjectStatus.pending)
    active = await get_active_submission(user.id)
    assert active is None  # pending is not "active" (draft/needs_fix)

    action = await log_admin_action(
        admin_id=user.id,
        action=AdminActionType.approve,
        target_submission_id=sub.id,
        comment="smoke test",
    )
    assert action.id is not None

    print("OK")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"v2_repo_smoke failed: {e}", file=sys.stderr)
        sys.exit(1)
