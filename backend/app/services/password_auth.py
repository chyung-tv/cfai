from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.security import hash_password, verify_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def signup_with_password(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str | None = None,
) -> User:
    normalized_email = normalize_email(email)
    existing = await db.execute(select(User).where(User.email == normalized_email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("email already in use")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")

    user = User(
        email=normalized_email,
        display_name=display_name.strip() if display_name else None,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_with_password(db: AsyncSession, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user is None or not user.password_hash:
        raise ValueError("invalid credentials")
    if not verify_password(password, user.password_hash):
        raise ValueError("invalid credentials")
    if not user.is_active:
        raise ValueError("account disabled")
    return user
