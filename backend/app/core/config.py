from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


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


def _normalize_database_url(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if value.startswith("postgresql://"):
        value = "postgresql+asyncpg://" + value[len("postgresql://") :]

    parts = urlsplit(value)
    query_items = dict(parse_qsl(parts.query, keep_blank_values=True))
    sslmode = query_items.pop("sslmode", None)
    query_items.pop("channel_binding", None)
    if sslmode and "ssl" not in query_items:
        query_items["ssl"] = "require" if sslmode.lower() in {"require", "verify-full"} else sslmode
    normalized_query = urlencode(query_items)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, normalized_query, parts.fragment))


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    database_url_direct: str = _normalize_database_url(os.getenv("DATABASE_URL_DIRECT", ""))
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
    llm_flash_lite_model: str = os.getenv("LLM_FLASH_LITE_MODEL", "gemini3.1-flash-lite")
    structured_output_model: str = os.getenv(
        "STRUCTURED_OUTPUT_MODEL",
        os.getenv("LLM_FLASH_LITE_MODEL", "gemini3.1-flash-lite"),
    )
    deep_research_dev_model: str = os.getenv(
        "DEEP_RESEARCH_DEV_MODEL",
        os.getenv("LLM_FLASH_LITE_MODEL", "gemini3.1-flash-lite"),
    )
    deep_research_dev_grounding_enabled: bool = _as_bool(
        "DEEP_RESEARCH_DEV_GROUNDING_ENABLED",
        True,
    )
    deep_research_use_endpoint_in_production: bool = _as_bool(
        "DEEP_RESEARCH_USE_ENDPOINT_IN_PRODUCTION",
        True,
    )
    deep_research_poll_interval_seconds: int = _as_int("DEEP_RESEARCH_POLL_INTERVAL_SECONDS", 10)
    deep_research_max_wait_seconds: int = _as_int("DEEP_RESEARCH_MAX_WAIT_SECONDS", 1200)
    deep_research_enable_live_calls: bool = _as_bool("DEEP_RESEARCH_ENABLE_LIVE_CALLS", False)
    skip_deep_research_in_tests: bool = _as_bool("SKIP_DEEP_RESEARCH_IN_TESTS", False)


settings = Settings()
