"""Tests for pycore."""

import os
import json
import logging
from unittest.mock import patch

from pycore.result import Result, output_result
from pycore.config import env, require_env, ConfigError, load_dotenv
from pycore.log import logger


class TestResult:
    def test_ok(self) -> None:
        r = Result.ok("hello")
        assert r.success is True
        assert r.output == "hello"
        assert r.error == ""

    def test_fail(self) -> None:
        r = Result.fail("boom")
        assert r.success is False
        assert r.output == ""
        assert r.error == "boom"

    def test_output_result_stdout(self, capsys) -> None:
        output_result(Result.ok("test output"))
        assert "test output" in capsys.readouterr().out

    def test_output_result_file(self, tmp_path) -> None:
        f = tmp_path / "result.txt"
        with patch.dict(os.environ, {"RESULT_FILE": str(f)}):
            output_result(Result.ok("file content"))
        assert f.read_text() == "file content"


class TestConfig:
    def test_env_default(self) -> None:
        assert env("NONEXISTENT_KEY_XYZ", default="fallback") == "fallback"

    def test_env_cast_int(self) -> None:
        with patch.dict(os.environ, {"TEST_PORT": "8080"}):
            assert env("TEST_PORT", default=0, cast=int) == 8080

    def test_env_cast_bool(self) -> None:
        with patch.dict(os.environ, {"TEST_DEBUG": "true"}):
            assert env("TEST_DEBUG", default=False, cast=bool) is True

    def test_require_env_missing(self) -> None:
        import pytest
        with pytest.raises(ConfigError):
            require_env("DEFINITELY_NOT_SET_XYZ")

    def test_require_env_present(self) -> None:
        with patch.dict(os.environ, {"MY_KEY": "val"}):
            assert require_env("MY_KEY") == "val"

    def test_load_dotenv(self, tmp_path) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text('FOO_TEST=bar\n# comment\nBAZ_TEST="quoted"')
        load_dotenv(str(dotenv))
        assert os.environ.get("FOO_TEST") == "bar"
        assert os.environ.get("BAZ_TEST") == "quoted"
        # Cleanup
        del os.environ["FOO_TEST"]
        del os.environ["BAZ_TEST"]


class TestLogger:
    def test_structured_output(self) -> None:
        import io
        log = logger("test_mod2")
        # Capture by adding a temporary handler
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        handler.setFormatter(logging.getLogger("pycore").handlers[0].formatter)
        logging.getLogger("pycore").addHandler(handler)
        try:
            log.info("hello", key="value")
            output = buf.getvalue()
            data = json.loads(output.strip())
            assert data["level"] == "info"
            assert data["msg"] == "hello"
            assert data["module"] == "test_mod2"
            assert data["key"] == "value"
        finally:
            logging.getLogger("pycore").removeHandler(handler)

from pycore.errors import AppError, ExternalServiceError, ValidationError


class TestErrors:
    def test_app_error_context(self) -> None:
        e = ValidationError("bad input", field="email", value="xxx")
        assert e.code == "VALIDATION_ERROR"
        assert e.message == "bad input"
        assert e.context == {"field": "email", "value": "xxx"}

    def test_to_dict(self) -> None:
        e = ExternalServiceError("API down", service="feishu", status=502)
        d = e.to_dict()
        assert d["code"] == "EXTERNAL_SERVICE_ERROR"
        assert d["service"] == "feishu"
        assert d["status"] == 502

    def test_inheritance(self) -> None:
        e = ValidationError("x")
        assert isinstance(e, AppError)
        assert isinstance(e, Exception)

import asyncio
import time
from pycore.concurrent import run_parallel, run_batch, run_async, gather_async, TaskResult


class TestConcurrent:
    def test_run_parallel(self) -> None:
        results = run_parallel({
            "a": lambda: "hello",
            "b": lambda: 42,
        })
        assert len(results) == 2
        values = {r.key: r.value for r in results}
        assert values["a"] == "hello"
        assert values["b"] == 42

    def test_run_parallel_error(self) -> None:
        def fail():
            raise ValueError("boom")

        results = run_parallel({"ok": lambda: 1, "bad": fail})
        by_key = {r.key: r for r in results}
        assert by_key["ok"].success is True
        assert by_key["bad"].success is False
        assert "boom" in by_key["bad"].error

    def test_run_batch(self) -> None:
        results = run_batch([1, 2, 3], lambda x: x * 2, label="double")
        assert all(r.success for r in results)
        assert sorted(r.value for r in results) == [2, 4, 6]

    def test_run_parallel_actually_parallel(self) -> None:
        def slow():
            time.sleep(0.1)
            return True

        start = time.time()
        results = run_parallel({f"t{i}": slow for i in range(5)}, max_workers=5)
        elapsed = time.time() - start
        assert elapsed < 0.3  # 5 tasks × 0.1s should finish in ~0.1s with 5 workers
        assert all(r.success for r in results)

    def test_run_async(self) -> None:
        results = asyncio.run(run_async({"x": lambda: "async_val"}))
        assert results[0].success is True
        assert results[0].value == "async_val"

    def test_gather_async(self) -> None:
        async def double(n):
            return n * 2

        async def main():
            return await gather_async({"a": double(3), "b": double(5)})

        results = asyncio.run(main())
        values = {r.key: r.value for r in results}
        assert values["a"] == 6
        assert values["b"] == 10
