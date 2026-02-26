from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.oauth_account import OauthAccount
from app.models.user import User
from app.services.password_auth import normalize_email

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_google_start_url(state: str) -> str:
    query = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)


async def _exchange_code_for_access_token(code: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    response.raise_for_status()
    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise ValueError("google token exchange failed")
    return access_token


async def _fetch_google_profile(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    response.raise_for_status()
    profile = response.json()
    if not profile.get("sub") or not profile.get("email"):
        raise ValueError("google profile missing required fields")
    return profile


async def upsert_user_from_google_callback(db: AsyncSession, code: str) -> User:
    access_token = await _exchange_code_for_access_token(code)
    profile = await _fetch_google_profile(access_token)
    provider_user_id = str(profile["sub"])
    email = normalize_email(str(profile["email"]))
    display_name = profile.get("name")

    oauth_result = await db.execute(
        select(OauthAccount).where(
            OauthAccount.provider == "google",
            OauthAccount.provider_user_id == provider_user_id,
        )
    )
    oauth_account = oauth_result.scalar_one_or_none()
    if oauth_account is not None:
        user_result = await db.execute(select(User).where(User.id == oauth_account.user_id))
        user = user_result.scalar_one()
        return user

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if user is None:
        user = User(email=email, display_name=display_name)
        db.add(user)
        await db.flush()

    db.add(
        OauthAccount(
            user_id=user.id,
            provider="google",
            provider_user_id=provider_user_id,
        )
    )
    await db.commit()
    await db.refresh(user)
    return user
