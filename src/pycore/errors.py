"""Unified exception hierarchy for all projects."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base exception. All project exceptions inherit from this."""

    code: str = "APP_ERROR"

    def __init__(self, message: str, **context: Any) -> None:
        self.message = message
        self.context = context
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, **self.context}


class ConfigError(AppError):
    """Configuration missing or invalid."""
    code = "CONFIG_ERROR"


class ValidationError(AppError):
    """Input validation failed."""
    code = "VALIDATION_ERROR"


class NotFoundError(AppError):
    """Resource not found."""
    code = "NOT_FOUND"


class AuthError(AppError):
    """Authentication or authorization failed."""
    code = "AUTH_ERROR"


class ExternalServiceError(AppError):
    """External API/service call failed."""
    code = "EXTERNAL_SERVICE_ERROR"

    def __init__(self, message: str, *, service: str = "", status: int = 0, **context: Any) -> None:
        super().__init__(message, service=service, status=status, **context)


class OperationTimeoutError(AppError):
    """Operation timed out."""
    code = "TIMEOUT"


class RateLimitError(AppError):
    """Rate limit exceeded."""
    code = "RATE_LIMIT"
