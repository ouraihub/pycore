"""pycore — shared Python foundation for OurAIHub projects."""

from pycore.result import Result, output_result
from pycore.log import logger
from pycore.config import env, require_env, load_dotenv
from pycore.cli import create_app
from pycore.errors import (
    AppError,
    ConfigError,
    ValidationError,
    NotFoundError,
    AuthError,
    ExternalServiceError,
    TimeoutError,
    RateLimitError,
)

__all__ = [
    "Result",
    "output_result",
    "logger",
    "env",
    "require_env",
    "load_dotenv",
    "create_app",
    "AppError",
    "ConfigError",
    "ValidationError",
    "NotFoundError",
    "AuthError",
    "ExternalServiceError",
    "TimeoutError",
    "RateLimitError",
]
