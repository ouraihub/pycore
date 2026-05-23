"""Concurrency utilities — thread pool and async helpers."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from pycore.log import logger

log = logger("concurrent")

T = TypeVar("T")


@dataclass
class TaskResult:
    """Result of a single concurrent task."""

    key: str
    success: bool
    value: Any = None
    error: str = ""


def run_parallel(
    tasks: dict[str, Callable[[], T]],
    *,
    max_workers: int = 5,
) -> list[TaskResult]:
    """Run multiple tasks in parallel using threads.

    Args:
        tasks: dict of {name: callable}
        max_workers: thread pool size

    Returns:
        List of TaskResult in completion order.

    Usage:
        results = run_parallel({
            "site_a": lambda: fetch("https://a.com"),
            "site_b": lambda: fetch("https://b.com"),
        }, max_workers=3)
    """
    results: list[TaskResult] = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_key = {pool.submit(fn): key for key, fn in tasks.items()}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                value = future.result()
                results.append(TaskResult(key=key, success=True, value=value))
            except Exception as e:
                log.error("Parallel task failed", task=key, error=str(e))
                results.append(TaskResult(key=key, success=False, error=str(e)))

    return results


def run_batch(
    items: list[T],
    fn: Callable[[T], Any],
    *,
    max_workers: int = 5,
    label: str = "batch",
) -> list[TaskResult]:
    """Run the same function over a list of items in parallel.

    Usage:
        results = run_batch(urls, fetch_url, max_workers=3, label="fetch")
    """
    tasks = {f"{label}_{i}": (lambda item=item: fn(item)) for i, item in enumerate(items)}
    return run_parallel(tasks, max_workers=max_workers)


async def run_async(
    tasks: dict[str, Callable[[], Any]],
) -> list[TaskResult]:
    """Run tasks concurrently using asyncio (for async-native code).

    Wraps sync callables in executor. For truly async functions,
    use gather_async() instead.

    Usage:
        results = asyncio.run(run_async({"a": fn_a, "b": fn_b}))
    """
    loop = asyncio.get_event_loop()
    results: list[TaskResult] = []

    async def _run(key: str, fn: Callable[[], Any]) -> TaskResult:
        try:
            value = await loop.run_in_executor(None, fn)
            return TaskResult(key=key, success=True, value=value)
        except Exception as e:
            log.error("Async task failed", task=key, error=str(e))
            return TaskResult(key=key, success=False, error=str(e))

    completed = await asyncio.gather(*[_run(k, fn) for k, fn in tasks.items()])
    return list(completed)


async def gather_async(
    tasks: dict[str, Any],  # dict[str, Coroutine]
) -> list[TaskResult]:
    """Gather multiple coroutines with error handling.

    Usage:
        async def fetch(url): ...
        results = await gather_async({"a": fetch("http://a"), "b": fetch("http://b")})
    """
    results: list[TaskResult] = []

    async def _wrap(key: str, coro: Any) -> TaskResult:
        try:
            value = await coro
            return TaskResult(key=key, success=True, value=value)
        except Exception as e:
            log.error("Gather task failed", task=key, error=str(e))
            return TaskResult(key=key, success=False, error=str(e))

    completed = await asyncio.gather(*[_wrap(k, c) for k, c in tasks.items()])
    return list(completed)
