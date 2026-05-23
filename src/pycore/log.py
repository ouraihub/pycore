"""Structured JSON logging."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname.lower(),
            "module": record.name.removeprefix("pycore."),
            "msg": record.getMessage(),
        }
        # Merge extra kwargs
        for key, value in record.__dict__.items():
            if key.startswith("_extra_"):
                entry[key[7:]] = value
        if record.exc_info and record.exc_info[0]:
            entry["error"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


_initialized = False


def get_logger(name: str) -> logging.Logger:
    """Get a structured logger. Extra kwargs in log calls become JSON fields."""
    global _initialized
    if not _initialized:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JsonFormatter())
        root = logging.getLogger("pycore")
        root.addHandler(handler)
        root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        root.propagate = False
        _initialized = True

    return logging.getLogger(f"pycore.{name}")


class _LoggerAdapter(logging.LoggerAdapter):
    """Adapter that passes kwargs as extra fields."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        extra = kwargs.get("extra", {})
        for k, v in kwargs.items():
            if k not in ("extra", "exc_info", "stack_info", "stacklevel"):
                extra[f"_extra_{k}"] = v
        kwargs = {"extra": extra}
        return msg, kwargs


def logger(name: str) -> _LoggerAdapter:
    """Get a logger that accepts kwargs as structured fields.

    Usage:
        log = logger("fetch")
        log.info("Fetching", url="https://...", timeout=30)
    """
    return _LoggerAdapter(get_logger(name), {})
