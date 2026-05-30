# pycore

Python 项目共享基础库 + 微框架 — 一条命令创建项目，内置 CLI 骨架、回调、日志、配置、HTTP、并发、异常。

## 安装

```bash
uv add "pycore @ git+https://github.com/ouraihub/pycore.git"
```

## 创建新项目

```bash
pycore myproject
cd myproject
uv sync
uv run python -m myproject --help
```

生成标准结构：

```
myproject/
├── src/
│   ├── __main__.py       # CLI 入口（自动扫描 tasks/）
│   └── tasks/
│       └── hello.py      # 示例命令
├── tests/
├── .github/workflows/
│   └── run.yml           # 触发→执行→回调 workflow 模板
├── pyproject.toml        # 已配好 pycore 依赖
├── .env.example
└── AGENTS.md
```

## 快速上手

### 添加命令

在 `src/tasks/` 下创建文件，定义 `run()` 函数即可自动注册：

```python
# src/tasks/fetch.py
import typer
from pycore import logger
from pycore.http import get

log = logger("fetch")

def run(url: str = typer.Argument(..., help="URL to fetch")):
    """抓取 URL"""
    log.info("Fetching", url=url)
    resp = get(f"https://r.jina.ai/{url}", headers={"Accept": "text/markdown"})
    typer.echo(resp.body)
```

运行：

```bash
uv run python -m myproject fetch "https://example.com"
```

### 内置 callback 命令

所有项目自动拥有 `callback` 命令，无需手写：

```bash
CALLBACK_URL=https://worker.dev/callback CALLBACK_SECRET=xxx \
uv run python -m myproject callback --file results.json
```

## 模块一览

| 模块 | 导入 | 用途 |
|------|------|------|
| 脚手架 | `pycore init` | 生成新项目 |
| CLI | `from pycore import create_app` | Typer + 自动扫描 tasks/ + 内置 callback |
| 回调 | 内置 | `callback --file results.json` POST 到 Worker |
| 日志 | `from pycore import logger` | 结构化 JSON 日志 |
| 配置 | `from pycore import env, require_env, load_dotenv` | 环境变量 + .env |
| HTTP | `from pycore.http import get, post` | 请求 + 重试 + 超时 |
| 通知 | `from pycore.notify import notify` | Telegram/飞书 |
| 并发 | `from pycore import run_parallel, run_batch` | 多线程/异步 |
| 异常 | `from pycore import AppError, ExternalServiceError, ...` | 统一异常层级 |
| 结果 | `from pycore import Result, output_result` | 统一输出（str 或 dict） |
| 注册表 | `from pycore import Registry` | 装饰器自动注册 + 按名查找 |
| 重试 | `from pycore.retry import retry` | 通用重试装饰器 |

## 日志

```python
from pycore import logger
log = logger("my_module")

log.info("User created", user_id="123", provider="github")
# stderr: {"ts":"...","level":"info","module":"my_module","msg":"User created","user_id":"123","provider":"github"}
```

## 配置

```python
from pycore import env, require_env, load_dotenv

load_dotenv()
api_key = require_env("API_KEY")  # 缺失则抛 ConfigError
timeout = env("TIMEOUT", default=30, cast=int)
```

## Result

支持字符串输出和结构化数据两种模式：

```python
from pycore import Result, output_result

# CLI 输出模式
result = Result.ok("操作完成", artifacts=["output.md"])

# 结构化数据模式（provider 间传递）
result = Result.ok({"user_id": "123", "balance": "9.24"}, message="登录成功")

# 失败
result = Result.fail("连接超时")

# 输出到 stdout + RESULT_FILE
output_result(result)
```

## HTTP

```python
from pycore.http import get, post, HttpError

resp = get("https://api.example.com/data", timeout=10, retries=3)
data = resp.json()

resp = post("https://api.example.com/submit", json={"key": "value"})
```

## 并发

```python
from pycore import run_parallel, run_batch

results = run_parallel({
    "site_a": lambda: get("https://a.com").body,
    "site_b": lambda: get("https://b.com").body,
}, max_workers=3)

results = run_batch(urls, fetch_url, max_workers=5)
```

## 异常

```python
from pycore import ExternalServiceError, ValidationError

if not url.startswith("http"):
    raise ValidationError("Invalid URL", url=url)

try:
    resp = post(api_url, json=data)
except HttpError as e:
    raise ExternalServiceError("API failed", service="feishu", status=e.status) from e
```

## 重试

```python
from pycore.retry import retry

@retry(max_attempts=3, delay=1.0, exceptions=(TimeoutError, ConnectionError))
def flaky_operation():
    ...
```

## GitHub Actions 集成

`pycore init` 生成的 workflow 模板：

```yaml
jobs:
  run:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run python -m myproject ${{ inputs.action }} "${{ inputs.target }}" --output results.json
      - if: always()
        run: uv run python -m myproject callback --file results.json
        env:
          CALLBACK_URL: ${{ inputs.callback_url || secrets.CALLBACK_URL }}
          CALLBACK_SECRET: ${{ secrets.CALLBACK_SECRET }}
```

## 开发

```bash
git clone https://github.com/ouraihub/pycore.git
cd pycore
uv sync --all-extras
uv run pytest -v
uv run ruff check src/
```

## 规范文档

- [CONVENTIONS.md](./docs/CONVENTIONS.md) — 日志规范 + 异常处理规范
- [DESIGN.md](./docs/DESIGN.md) — 架构设计
- [COMPONENTS.md](./docs/COMPONENTS.md) — 模块详细说明
