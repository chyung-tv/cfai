from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.services.password_auth import normalize_email
from app.services.security import generate_token, hash_password, hash_token


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def create_reset_token(db: AsyncSession, email: str) -> str | None:
    normalized_email = normalize_email(email)
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    token = generate_token()
    user.reset_token_hash = hash_token(token)
    user.reset_token_expires_at = _now_utc() + timedelta(
        seconds=settings.password_reset_ttl_seconds
    )
    await db.commit()
    return token


async def consume_reset_token(db: AsyncSession, token: str, new_password: str) -> bool:
    if len(new_password) < 8:
        raise ValueError("password must be at least 8 characters")

    token_digest = hash_token(token)
    result = await db.execute(select(User).where(User.reset_token_hash == token_digest))
    user = result.scalar_one_or_none()
    if user is None:
        return False
    if user.reset_token_expires_at is None or user.reset_token_expires_at <= _now_utc():
        return False

    user.password_hash = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    await db.commit()
    return True
