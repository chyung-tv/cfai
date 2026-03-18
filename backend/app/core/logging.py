from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any


class PrettyTextLogFormatter(logging.Formatter):
    _LEVEL_COLORS = {
        "DEBUG": "\x1b[36m",  # cyan
        "INFO": "\x1b[32m",  # green
        "WARNING": "\x1b[33m",  # yellow
        "ERROR": "\x1b[31m",  # red
        "CRITICAL": "\x1b[35m",  # magenta
    }
    _RESET_COLOR = "\x1b[0m"
    _reserved = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }
    _field_order = ("trace_id", "symbol", "event_type", "substate", "duration_ms", "error_code")

    def __init__(self) -> None:
        super().__init__()
        self._enable_color = self._resolve_color_mode()

    def _resolve_color_mode(self) -> bool:
        env = os.getenv("APP_LOG_COLOR", "auto").strip().lower()
        if env in {"0", "false", "off", "no"}:
            return False
        if env in {"1", "true", "on", "yes"}:
            return True
        return sys.stderr.isatty()

    def _compact_logger_name(self, name: str) -> str:
        for prefix in ("app.", "uvicorn.", "fastapi."):
            if name.startswith(prefix):
                return name[len(prefix) :]
        return name

    @staticmethod
    def _fmt_value(value: Any) -> str:
        return str(value).replace("\n", "\\n")

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        level = f"{record.levelname:<8}"
        if self._enable_color:
            color = self._LEVEL_COLORS.get(record.levelname, "")
            if color:
                level = f"{color}{level}{self._RESET_COLOR}"
        logger_name = self._compact_logger_name(record.name)
        parts: list[str] = [f"{ts} {level} {logger_name} - {record.getMessage()}"]

        fields = []
        for key in self._field_order:
            value = getattr(record, key, None)
            if value is not None:
                if key == "trace_id":
                    fields.append(f"trace={self._fmt_value(value)}")
                elif key == "duration_ms":
                    fields.append(f"ms={self._fmt_value(value)}")
                else:
                    fields.append(f"{key}={self._fmt_value(value)}")
        if fields:
            parts.append(" | " + " ".join(fields))
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._reserved and not key.startswith("_")
        }
        if extras:
            extras_text = " ".join(
                f"{key}={self._fmt_value(extras[key])}" for key in sorted(extras.keys())
            )
            parts.append(f" | extra: {extras_text}")
        if record.exc_info:
            parts.append("\n" + self.formatException(record.exc_info))
        return "".join(parts)


def configure_app_logging(*, level: str = "INFO") -> None:
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(PrettyTextLogFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = True

