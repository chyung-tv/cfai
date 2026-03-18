from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core import defaults


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


def _as_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


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
    app_env: str = os.getenv("APP_ENV", defaults.APP_ENV)
    app_log_level: str = os.getenv("APP_LOG_LEVEL", defaults.APP_LOG_LEVEL)
    database_url: str = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    database_url_direct: str = _normalize_database_url(os.getenv("DATABASE_URL_DIRECT", ""))
    frontend_url: str = os.getenv("FRONTEND_URL", defaults.FRONTEND_URL)
    fmp_api_key: str = os.getenv("FMP_API_KEY", "")
    fmp_base_url: str = os.getenv("FMP_BASE_URL", defaults.FMP_BASE_URL)
    fmp_timeout_seconds: int = _as_int("FMP_TIMEOUT_SECONDS", defaults.FMP_TIMEOUT_SECONDS)
    maintenance_seed_target_count: int = _as_int(
        "MAINTENANCE_SEED_TARGET_COUNT", defaults.MAINTENANCE_SEED_TARGET_COUNT
    )
    maintenance_seed_min_market_cap: int = _as_int(
        "MAINTENANCE_SEED_MIN_MARKET_CAP", defaults.MAINTENANCE_SEED_MIN_MARKET_CAP
    )
    workflow_node_heartbeat_interval_seconds: int = _as_int(
        "WORKFLOW_NODE_HEARTBEAT_INTERVAL_SECONDS", defaults.WORKFLOW_NODE_HEARTBEAT_INTERVAL_SECONDS
    )
    workflow_stale_progress_threshold_seconds: int = _as_int(
        "WORKFLOW_STALE_PROGRESS_THRESHOLD_SECONDS", defaults.WORKFLOW_STALE_PROGRESS_THRESHOLD_SECONDS
    )
    workflow_stall_monitor_interval_seconds: int = _as_int(
        "WORKFLOW_STALL_MONITOR_INTERVAL_SECONDS", defaults.WORKFLOW_STALL_MONITOR_INTERVAL_SECONDS
    )
    workflow_stall_signal_cooldown_seconds: int = _as_int(
        "WORKFLOW_STALL_SIGNAL_COOLDOWN_SECONDS", defaults.WORKFLOW_STALL_SIGNAL_COOLDOWN_SECONDS
    )
    vertex_ai_project_id: str = os.getenv("VERTEX_AI_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    vertex_ai_api_key: str = os.getenv("VERTEX_AI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    vertex_ai_location: str = os.getenv(
        "VERTEX_AI_LOCATION", os.getenv("GOOGLE_CLOUD_LOCATION", defaults.VERTEX_AI_LOCATION)
    )
    google_genai_use_vertexai: bool = _as_bool("GOOGLE_GENAI_USE_VERTEXAI", defaults.GOOGLE_GENAI_USE_VERTEXAI)
    deep_research_agent: str = os.getenv(
        "DEEP_RESEARCH_AGENT",
        defaults.DEEP_RESEARCH_AGENT,
    )
    llm_flash_lite_model: str = os.getenv("LLM_FLASH_LITE_MODEL", defaults.LLM_FLASH_LITE_MODEL)
    structured_output_model: str = os.getenv(
        "STRUCTURED_OUTPUT_MODEL",
        os.getenv("LLM_FLASH_LITE_MODEL", defaults.STRUCTURED_OUTPUT_MODEL),
    )
    deep_research_dev_model: str = os.getenv(
        "DEEP_RESEARCH_DEV_MODEL",
        os.getenv("LLM_FLASH_LITE_MODEL", defaults.DEEP_RESEARCH_DEV_MODEL),
    )
    deep_research_dev_grounding_enabled: bool = _as_bool(
        "DEEP_RESEARCH_DEV_GROUNDING_ENABLED",
        defaults.DEEP_RESEARCH_DEV_GROUNDING_ENABLED,
    )
    deep_research_use_endpoint_in_production: bool = _as_bool(
        "DEEP_RESEARCH_USE_ENDPOINT_IN_PRODUCTION",
        defaults.DEEP_RESEARCH_USE_ENDPOINT_IN_PRODUCTION,
    )
    deep_research_poll_interval_seconds: int = _as_int(
        "DEEP_RESEARCH_POLL_INTERVAL_SECONDS", defaults.DEEP_RESEARCH_POLL_INTERVAL_SECONDS
    )
    deep_research_max_wait_seconds: int = _as_int(
        "DEEP_RESEARCH_MAX_WAIT_SECONDS", defaults.DEEP_RESEARCH_MAX_WAIT_SECONDS
    )
    deep_research_enable_live_calls: bool = _as_bool(
        "DEEP_RESEARCH_ENABLE_LIVE_CALLS", defaults.DEEP_RESEARCH_ENABLE_LIVE_CALLS
    )
    chat_enable_live_calls: bool = _as_bool("CHAT_ENABLE_LIVE_CALLS", defaults.CHAT_ENABLE_LIVE_CALLS)
    skip_deep_research_in_tests: bool = _as_bool("SKIP_DEEP_RESEARCH_IN_TESTS", defaults.SKIP_DEEP_RESEARCH_IN_TESTS)
    memory_default_user_id: str = os.getenv("MEMORY_DEFAULT_USER_ID", defaults.MEMORY_DEFAULT_USER_ID)
    memory_recall_max_candidates: int = _as_int("MEMORY_RECALL_MAX_CANDIDATES", defaults.MEMORY_RECALL_MAX_CANDIDATES)
    memory_prompt_topk: int = _as_int("MEMORY_PROMPT_TOPK", defaults.MEMORY_PROMPT_TOPK)
    memory_summary_max_chars: int = _as_int("MEMORY_SUMMARY_MAX_CHARS", defaults.MEMORY_SUMMARY_MAX_CHARS)
    memory_write_confidence_threshold: float = _as_float(
        "MEMORY_WRITE_CONFIDENCE_THRESHOLD", defaults.MEMORY_WRITE_CONFIDENCE_THRESHOLD
    )
    memory_job_max_retries: int = _as_int("MEMORY_JOB_MAX_RETRIES", defaults.MEMORY_JOB_MAX_RETRIES)
    memory_compression_min_writes: int = _as_int("MEMORY_COMPRESSION_MIN_WRITES", defaults.MEMORY_COMPRESSION_MIN_WRITES)
    memory_compression_injected_char_limit: int = _as_int(
        "MEMORY_COMPRESSION_INJECTED_CHAR_LIMIT", defaults.MEMORY_COMPRESSION_INJECTED_CHAR_LIMIT
    )
    memory_compression_max_summary_age_hours: int = _as_int(
        "MEMORY_COMPRESSION_MAX_SUMMARY_AGE_HOURS", defaults.MEMORY_COMPRESSION_MAX_SUMMARY_AGE_HOURS
    )
    memory_compression_cooldown_minutes: int = _as_int(
        "MEMORY_COMPRESSION_COOLDOWN_MINUTES", defaults.MEMORY_COMPRESSION_COOLDOWN_MINUTES
    )
    turn_structured_output_enabled: bool = _as_bool(
        "TURN_STRUCTURED_OUTPUT_ENABLED", defaults.TURN_STRUCTURED_OUTPUT_ENABLED
    )
    turn_schema_retry_max: int = _as_int("TURN_SCHEMA_RETRY_MAX", defaults.TURN_SCHEMA_RETRY_MAX)
    turn_schema_repair_enabled: bool = _as_bool("TURN_SCHEMA_REPAIR_ENABLED", defaults.TURN_SCHEMA_REPAIR_ENABLED)
    memory_suggestion_fallback_mode: str = os.getenv(
        "MEMORY_SUGGESTION_FALLBACK_MODE",
        defaults.MEMORY_SUGGESTION_FALLBACK_MODE,
    )
    memory_suggestion_max_candidates: int = _as_int(
        "MEMORY_SUGGESTION_MAX_CANDIDATES",
        defaults.MEMORY_SUGGESTION_MAX_CANDIDATES,
    )


settings = Settings()
