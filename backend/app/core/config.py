from __future__ import annotations

import os
from dataclasses import dataclass


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cfai:cfai@localhost:5432/cfai",
    )
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    google_oauth_client_id: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    google_oauth_client_secret: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    google_oauth_redirect_uri: str = os.getenv(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:3001/auth/oauth/google/callback",
    )
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "cfai_session")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    session_ttl_seconds: int = _as_int("SESSION_TTL_SECONDS", 60 * 60 * 24 * 7)
    password_reset_ttl_seconds: int = _as_int("PASSWORD_RESET_TTL_SECONDS", 60 * 30)


settings = Settings()
