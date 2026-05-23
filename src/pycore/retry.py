"""Generic retry decorator with exponential backoff."""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from pycore.log import logger

log = logger("retry")

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: float = 30.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Total attempts (including first try).
        delay: Initial delay between retries (seconds).
        backoff: Multiplier for delay after each retry.
        max_delay: Maximum delay cap.
        exceptions: Tuple of exception types to catch and retry.

    Usage:
        @retry(max_attempts=3, delay=1.0, exceptions=(TimeoutError, ConnectionError))
        def flaky_call():
            ...
    """

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: BaseException | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        log.error(
                            "All retries exhausted",
                            func=fn.__name__,
                            attempt=attempt,
                            error=str(e),
                        )
                        raise
                    log.warning(
                        "Retrying",
                        func=fn.__name__,
                        attempt=attempt,
                        next_delay=current_delay,
                        error=str(e),
                    )
                    time.sleep(current_delay)
                    current_delay = min(current_delay * backoff, max_delay)

            raise last_exception  # type: ignore[misc]  # unreachable

        return wrapper  # type: ignore[return-value]

    return decorator
