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


def _as_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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
    fmp_api_key: str = os.getenv("FMP_API_KEY", "")
    fmp_base_url: str = os.getenv("FMP_BASE_URL", "https://financialmodelingprep.com")
    fmp_timeout_seconds: int = _as_int("FMP_TIMEOUT_SECONDS", 30)
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    deep_research_agent: str = os.getenv(
        "DEEP_RESEARCH_AGENT",
        "deep-research-pro-preview-12-2025",
    )
    structured_output_model: str = os.getenv("STRUCTURED_OUTPUT_MODEL", "gemini-2.5-flash")
    deep_research_poll_interval_seconds: int = _as_int("DEEP_RESEARCH_POLL_INTERVAL_SECONDS", 10)
    deep_research_max_wait_seconds: int = _as_int("DEEP_RESEARCH_MAX_WAIT_SECONDS", 1200)
    deep_research_enable_live_calls: bool = _as_bool("DEEP_RESEARCH_ENABLE_LIVE_CALLS", False)
    skip_deep_research_in_tests: bool = _as_bool("SKIP_DEEP_RESEARCH_IN_TESTS", False)


settings = Settings()
