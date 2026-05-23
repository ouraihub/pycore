"""Shared constants across projects."""

from __future__ import annotations

# --- Exit Codes ---
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_UNEXPECTED = 2
EXIT_CONFIG_ERROR = 3

# --- HTTP ---
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
USER_AGENT = "pycore/0.1"

# --- File Paths ---
RESULT_FILE_DEFAULT = "/tmp/result.txt"

# --- Limits ---
MAX_CONTENT_LENGTH = 500_000  # 500KB max for fetched content
MAX_WORKERS_DEFAULT = 5

# --- Time (seconds) ---
ONE_MINUTE = 60
ONE_HOUR = 3600
ONE_DAY = 86400

# --- Status ---
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_PENDING = "pending"
STATUS_TIMEOUT = "timeout"
