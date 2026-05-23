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
    def test_structured_output(self, capsys) -> None:
        log = logger("test_mod")
        log.info("hello", key="value")
        err = capsys.readouterr().err
        data = json.loads(err)
        assert data["level"] == "info"
        assert data["msg"] == "hello"
        assert data["module"] == "test_mod"
        assert data["key"] == "value"
