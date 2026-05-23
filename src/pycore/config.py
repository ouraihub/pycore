"""Environment-based configuration with type safety."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypeVar, overload

T = TypeVar("T")


class ConfigError(Exception):
    """Raised when a required config value is missing."""


def load_dotenv(path: str = ".env") -> None:
    """Load .env file into os.environ. No-op if file doesn't exist."""
    env_path = Path(path)
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:  # Don't override existing
            os.environ[key] = value


@overload
def env(key: str, *, default: str = ...) -> str: ...
@overload
def env(key: str, *, default: int, cast: type[int]) -> int: ...
@overload
def env(key: str, *, default: bool, cast: type[bool]) -> bool: ...
@overload
def env(key: str, *, default: T, cast: type[T]) -> T: ...


def env(key: str, *, default: T | None = None, cast: type[T] | None = None) -> T | str:  # type: ignore[assignment]
    """Get an environment variable with optional type casting."""
    value = os.environ.get(key)
    if value is None:
        if default is not None:
            return default
        return ""

    if cast is None:
        return value
    if cast is bool:
        return value.lower() in ("1", "true", "yes")  # type: ignore[return-value]
    return cast(value)  # type: ignore[return-value]


def require_env(key: str) -> str:
    """Get a required environment variable. Raises ConfigError if missing."""
    value = os.environ.get(key)
    if not value:
        raise ConfigError(f"Required environment variable '{key}' is not set")
    return value
