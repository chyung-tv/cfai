from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.session_service import resolve_session_user_id


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    raw_token = request.cookies.get(settings.session_cookie_name)
    user_id = await resolve_session_user_id(db, raw_token)
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def require_auth(
    current_user: User | None = Depends(get_current_user),
) -> User:
    if current_user is None:
        raise HTTPException(status_code=401, detail="authentication required")
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="account disabled")
    return current_user


def require_role(*allowed_roles: str):
    async def _guard(current_user: User = Depends(require_auth)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="insufficient role")
        return current_user

    return _guard
