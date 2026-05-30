"""pycore init — generate a new project from template."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def init_project(name: str, directory: Path | None = None) -> Path:
    """Generate a new pycore-based project structure."""
    root = directory or Path.cwd() / name
    root.mkdir(parents=True, exist_ok=True)

    src = root / "src"
    tasks = src / "tasks"
    tests = root / "tests"
    workflows = root / ".github" / "workflows"

    for d in [tasks, tests, workflows]:
        d.mkdir(parents=True, exist_ok=True)

    _write(src / "__main__.py", _MAIN_PY.format(name=name))
    _write(tasks / "__init__.py", "")
    _write(tasks / "hello.py", _HELLO_TASK)
    _write(tests / "test_hello.py", _TEST_HELLO.format(name=name))
    _write(root / "pyproject.toml", _PYPROJECT.format(name=name))
    _write(root / ".env.example", _ENV_EXAMPLE)
    _write(root / ".gitignore", _GITIGNORE)
    _write(root / "AGENTS.md", _AGENTS.format(name=name))
    _write(root / "README.md", _README.format(name=name))
    _write(workflows / "run.yml", _WORKFLOW.format(name=name))

    return root


def _write(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


_MAIN_PY = dedent('''\
    from pycore import create_app
    app = create_app("{name}", tasks_package="tasks")

    if __name__ == "__main__":
        app()
''')

_HELLO_TASK = dedent('''\
    """Example task."""
    import typer
    from pycore import logger

    log = logger("hello")


    def run(target: str = typer.Argument("world", help="Who to greet")):
        """Say hello."""
        log.info("Hello", target=target)
        typer.echo(f"Hello, {{target}}!")
''')

_TEST_HELLO = dedent('''\
    """Smoke test."""
    import subprocess


    def test_hello():
        result = subprocess.run(
            ["uv", "run", "python", "-m", "{name}", "hello", "test"],
            capture_output=True, text=True,
        )
        assert "Hello, test!" in result.stdout
''')

_PYPROJECT = dedent('''\
    [project]
    name = "{name}"
    version = "0.1.0"
    requires-python = ">=3.11"
    dependencies = [
        "pycore @ git+https://github.com/ouraihub/pycore.git",
    ]

    [build-system]
    requires = ["setuptools>=68"]
    build-backend = "setuptools.build_meta"

    [tool.setuptools.packages.find]
    where = ["src"]

    [tool.uv]
    package = true

    [dependency-groups]
    dev = ["pytest>=8.0", "ruff>=0.5"]

    [tool.pytest.ini_options]
    testpaths = ["tests"]

    [tool.ruff]
    line-length = 120
    fix = true

    [tool.ruff.format]
    quote-style = "double"
''')

_ENV_EXAMPLE = dedent('''\
    CALLBACK_URL=https://your-worker.workers.dev/callback
    CALLBACK_SECRET=your_secret
''')

_GITIGNORE = dedent('''\
    .venv/
    __pycache__/
    *.egg-info/
    dist/
    .env
    results.json
''')

_AGENTS = dedent('''\
    # {name}

    ## 项目结构

    - `src/tasks/` — 业务命令（每个文件一个命令）
    - `src/__main__.py` — CLI 入口（pycore create_app 自动扫描 tasks/）
    - `.github/workflows/run.yml` — CI 执行模板

    ## 运行

    ```bash
    uv sync
    uv run python -m {name} --help
    uv run python -m {name} hello world
    ```

    ## 添加新命令

    在 `src/tasks/` 下创建新文件，定义 `run()` 函数即可自动注册：

    ```python
    # src/tasks/fetch.py
    import typer
    from pycore import logger
    log = logger("fetch")

    def run(url: str = typer.Argument(...)):
        log.info("Fetching", url=url)
        ...
    ```

    ## 回调

    所有项目内置 `callback` 命令：
    ```bash
    CALLBACK_URL=... CALLBACK_SECRET=... uv run python -m {name} callback --file results.json
    ```
''')

_README = dedent('''\
    # {name}

    基于 [pycore](https://github.com/ouraihub/pycore) 的自动化项目。

    ## 快速开始

    ```bash
    uv sync
    uv run python -m {name} --help
    ```

    ## 开发

    ```bash
    uv run pytest -v
    uv run ruff check src/
    ```
''')

_WORKFLOW = dedent('''\
    name: Run Task
    on:
      workflow_dispatch:
        inputs:
          action:
            description: "命令名"
            required: true
            type: string
          target:
            description: "目标参数"
            required: false
            default: ""
            type: string
          callback_url:
            description: "回调地址"
            required: false
            default: ""
            type: string

    jobs:
      run:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: "3.11"
          - uses: astral-sh/setup-uv@v4
          - run: uv sync

          - name: Execute
            run: |
              uv run python -m {name} ${{{{ inputs.action }}}} "${{{{ inputs.target }}}}" --output results.json
            env:
              CALLBACK_URL: ${{{{ inputs.callback_url || secrets.CALLBACK_URL }}}}
              CALLBACK_SECRET: ${{{{ secrets.CALLBACK_SECRET }}}}

          - name: Callback
            if: always()
            run: uv run python -m {name} callback --file results.json
            env:
              CALLBACK_URL: ${{{{ inputs.callback_url || secrets.CALLBACK_URL }}}}
              CALLBACK_SECRET: ${{{{ secrets.CALLBACK_SECRET }}}}
''')
