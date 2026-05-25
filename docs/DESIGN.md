# pycore 设计文档 v3 — 最终方案

## 定位

Python 项目的共享基础库。提供：CLI 骨架、结构化日志、配置加载、HTTP 客户端、通知。

**不包含**业务逻辑（AI 调用、Playwright、fetcher 实现等留在各项目）。

## 设计决策

| 决策点 | 方案 |
|--------|------|
| CLI 框架 | Typer（类型注解自动生成 CLI） |
| 任务发现 | 自动扫描 `tasks/` 目录 |
| 结果输出 | stdout + 可选 `RESULT_FILE` 环境变量 |
| 包管理 | uv + 独立 git 仓库 |
| 日志 | 结构化 JSON，输出到 stderr |
| 配置 | 环境变量 + .env，类型安全 |
| HTTP | urllib 封装（零额外依赖），重试+超时 |
| 通知 | Telegram/飞书，通过环境变量选择通道 |

## 模块结构

```
src/pycore/
├── __init__.py         # 公共 API 导出
├── cli.py              # CLI 骨架（基于 Typer + 自动扫描）
├── log.py              # 结构化 JSON 日志
├── config.py           # 环境变量加载 + 类型转换
├── http.py             # HTTP 客户端（重试、超时）
├── notify.py           # 通知发送（Telegram/飞书）
└── result.py           # Result 数据类
```

## 各模块 API

### cli.py — CLI 骨架

```python
from pycore.cli import create_app

# 自动扫描 tasks/ 目录下所有带 @app.command() 的模块
app = create_app("msgflow", tasks_package="tasks")

# 或手动传入 Typer app
if __name__ == "__main__":
    app()
```

下游项目的 `__main__.py`：

```python
from pycore.cli import create_app
app = create_app("msgflow", tasks_package="tasks")
app()
```

下游项目的 `tasks/fetch.py`：

```python
import typer
from pycore.result import Result, output_result

app = typer.Typer()

@app.command()
def fetch(url: str):
    """抓取 URL 为 Markdown"""
    content = ...
    output_result(Result.ok(content))
```

### result.py — 统一结果

```python
import os
from dataclasses import dataclass

@dataclass
class Result:
    success: bool
    output: str
    error: str = ""

    @classmethod
    def ok(cls, output: str) -> "Result": ...

    @classmethod
    def fail(cls, error: str) -> "Result": ...

def output_result(result: Result) -> None:
    """输出结果到 stdout，可选写文件。"""
    print(result.output if result.success else f"ERROR: {result.error}")
    result_file = os.environ.get("RESULT_FILE")
    if result_file:
        Path(result_file).write_text(result.output or result.error)
```

### log.py — 结构化日志

```python
from pycore.log import get_logger

log = get_logger("fetch")
log.info("Fetching URL", url="https://example.com")
# stderr: {"ts":"...","level":"info","module":"fetch","msg":"Fetching URL","url":"https://example.com"}
```

### config.py — 配置加载

```python
from pycore.config import env, require_env

# 带默认值
timeout = env("TIMEOUT", default=30, cast=int)

# 必填（缺失时抛 ConfigError）
api_key = require_env("API_KEY")

# 布尔
debug = env("DEBUG", default=False, cast=bool)
```

### http.py — HTTP 客户端

```python
from pycore.http import http

# GET
resp = http.get("https://r.jina.ai/https://example.com", timeout=30)

# POST JSON
resp = http.post("https://api.example.com/data", json={"key": "value"})

# 自动重试（默认 3 次，指数退避）
resp = http.get(url, retries=3)
```

### notify.py — 通知

```python
from pycore.notify import notify

# 根据环境变量自动选择通道（NOTIFY_CHANNEL=telegram|feishu）
notify("✅ 任务完成：文章已改写")
```

## 下游项目使用

### 安装

```toml
# pyproject.toml
[project]
dependencies = [
    "pycore @ git+https://github.com/ouraihub/pycore.git",
    "typer>=0.12",
]
```

### 项目结构

```
msgflow/python/
├── pyproject.toml
├── src/
│   ├── __main__.py      # 3 行：create_app + app()
│   └── tasks/
│       ├── __init__.py
│       ├── fetch.py     # @app.command()
│       ├── rewrite.py
│       └── publish.py
```

### 本地运行

```bash
uv run python -m msgflow fetch "https://example.com"
uv run python -m msgflow rewrite "https://example.com" --style lu-xun
uv run python -m msgflow --help
```

### GitHub Actions

```yaml
- uses: astral-sh/setup-uv@v4
- run: uv sync
- run: |
    RESULT_FILE=/tmp/result.txt \
    uv run python -m msgflow ${{ inputs.action }} "${{ inputs.target }}" ${{ inputs.extra_args }}
```

## 实施计划

| Phase | 内容 | 文件数 |
|-------|------|--------|
| 1 | result.py + log.py + config.py | 3 |
| 2 | http.py + notify.py | 2 |
| 3 | cli.py（Typer + 自动扫描） | 1 |
| 4 | 测试 + 文档 + 发布到 GitHub | - |

总代码量预估：~300 行。

## 工具链

- **包管理**：uv
- **构建**：hatchling
- **lint**：ruff
- **测试**：pytest
- **类型检查**：pyright
- **CLI**：typer

## pyproject.toml

```toml
[project]
name = "pycore"
version = "0.1.0"
description = "Shared Python foundation — CLI, logging, config, HTTP, notify"
requires-python = ">=3.11"
dependencies = ["typer>=0.12"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "pyright>=1.1"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pycore"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "ANN", "B", "SIM"]
ignore = ["ANN101", "ANN102"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## 下游项目集成规划

### msgflow（ohwiki/msgflow）

| 步骤 | 状态 | 说明 |
|------|------|------|
| 分支 `feat/python-use-pycore` 已引入 pycore | ✅ 完成 | log/config/http/Result 已在用 |
| 替换本地 `lib/registry.py` 为 `pycore.Registry` | ⏳ 待做 | 合并分支后执行 |
| GitHub Actions workflow 适配 | ⏳ 待做 | `feishu-task.yml` 改用 `uv run python src/run_task.py` |
| 删除 `python-legacy/` | ⏳ 待做 | 新版全部验证通过后 |

### wucurcheck（augmentcodehub/wucurcheck）

| 步骤 | 状态 | 说明 |
|------|------|------|
| 替换 `utils/logger.py` 为 `pycore.logger` | ⏳ 待做 | |
| 替换 `utils/notify.py` 为 `pycore.notify` | ⏳ 待做 | |
| 替换 `utils/config.py` 为 `pycore.config` | ⏳ 待做 | |

### 未来新项目

直接按 `docs/COMPONENTS.md` 的模板搭建，不再重复造轮子。
