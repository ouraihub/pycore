"""Unified result type for task output."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Result:
    """Generic task result."""

    success: bool
    output: str
    error: str = ""
    artifacts: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls, output: str, artifacts: list[str] | None = None) -> Result:
        return cls(success=True, output=output, artifacts=artifacts or [])

    @classmethod
    def fail(cls, error: str) -> Result:
        return cls(success=False, output="", error=error)


def output_result(result: Result) -> None:
    """Print result to stdout. Optionally write to RESULT_FILE."""
    text = result.output if result.success else f"ERROR: {result.error}"
    print(text)
    result_file = os.environ.get("RESULT_FILE")
    if result_file:
        Path(result_file).write_text(text, encoding="utf-8")
