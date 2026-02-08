"""V2 repo: admin action audit log."""
import uuid

from src.bot.database import session as db_session
from src.bot.database.models import AdminAction, AdminActionType


async def log_admin_action(
    admin_id: int,
    action: AdminActionType,
    *,
    target_project_id: uuid.UUID | None = None,
    target_submission_id: uuid.UUID | None = None,
    comment: str | None = None,
) -> AdminAction:
    """Append admin action to audit log. At least one of target_project_id or target_submission_id should be set."""
    if db_session.async_session_maker is None:
        db_session.init_db()
    async with db_session.async_session_maker() as session:
        row = AdminAction(
            admin_id=admin_id,
            action=action,
            target_project_id=target_project_id,
            target_submission_id=target_submission_id,
            comment=comment,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row
