"""Unified result type for task output."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Result:
    """Generic task result — supports both string output and structured data."""

    success: bool
    output: str = ""
    data: dict[str, Any] | None = None
    message: str = ""
    error: str = ""
    artifacts: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls, output: str | dict | None = None, *, message: str = "", artifacts: list[str] | None = None) -> Result:
        if isinstance(output, dict):
            return cls(success=True, data=output, message=message, artifacts=artifacts or [])
        return cls(success=True, output=output or "", message=message, artifacts=artifacts or [])

    @classmethod
    def fail(cls, error: str, data: dict[str, Any] | None = None) -> Result:
        return cls(success=False, error=error, message=error, data=data)


def output_result(result: Result) -> None:
    """Print result to stdout. Optionally write to RESULT_FILE."""
    text = result.output or result.message if result.success else f"ERROR: {result.error}"
    print(text)
    result_file = os.environ.get("RESULT_FILE")
    if result_file:
        Path(result_file).write_text(text, encoding="utf-8")
