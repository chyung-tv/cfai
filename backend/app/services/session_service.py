from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user_session import UserSession
from app.services.security import generate_token, hash_token


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def create_session(
    db: AsyncSession,
    user_id: int,
    request: Request,
) -> str:
    token = generate_token()
    expires_at = _now_utc() + timedelta(seconds=settings.session_ttl_seconds)
    row = UserSession(
        user_id=user_id,
        token_hash=hash_token(token),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        expires_at=expires_at,
    )
    db.add(row)
    await db.commit()
    return token


async def resolve_session_user_id(db: AsyncSession, raw_token: str | None) -> int | None:
    if not raw_token:
        return None

    result = await db.execute(
        select(UserSession).where(UserSession.token_hash == hash_token(raw_token))
    )
    session_row = result.scalar_one_or_none()
    if session_row is None:
        return None
    if session_row.revoked_at is not None:
        return None
    if session_row.expires_at <= _now_utc():
        return None
    return session_row.user_id


async def revoke_session(db: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    result = await db.execute(
        select(UserSession).where(UserSession.token_hash == hash_token(raw_token))
    )
    session_row = result.scalar_one_or_none()
    if session_row is None or session_row.revoked_at is not None:
        return
    session_row.revoked_at = _now_utc()
    await db.commit()


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
