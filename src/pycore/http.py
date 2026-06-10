"""HTTP client with retry and timeout."""

from __future__ import annotations

import json as json_lib
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class Response:
    status: int
    body: str
    headers: dict[str, str]

    def json(self) -> Any:
        return json_lib.loads(self.body)


class HttpError(Exception):
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body[:200]}")


def get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 0,
) -> Response:
    """HTTP GET with optional retries."""
    return _request("GET", url, headers=headers, timeout=timeout, retries=retries)


def post(
    url: str,
    *,
    json: Any = None,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 0,
) -> Response:
    """HTTP POST with JSON or raw data."""
    h = dict(headers or {})
    body = data
    if json is not None:
        body = json_lib.dumps(json).encode()
        h.setdefault("Content-Type", "application/json")
    return _request("POST", url, body=body, headers=h, timeout=timeout, retries=retries)


def _request(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 0,
) -> Response:
    last_error: Exception | None = None
    h = dict(headers or {})
    h.setdefault("User-Agent", "Mozilla/5.0 (compatible; WucurBot/1.0)")
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=h, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return Response(
                    status=resp.status,
                    body=resp.read().decode("utf-8"),
                    headers=dict(resp.headers),
                )
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == retries:
                raise HttpError(e.code, e.read().decode("utf-8", errors="replace")) from e
            last_error = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries:
                raise HttpError(0, str(e)) from e
            last_error = e

        # Exponential backoff
        time.sleep(min(2**attempt, 10))

    raise HttpError(0, str(last_error))  # Should not reach here
