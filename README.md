# pycore

Python 项目共享基础库 — CLI 骨架、日志、配置、HTTP、通知、并发、异常。

## 安装

```bash
uv add "pycore @ git+https://github.com/ouraihub/pycore.git"
```

## 快速上手

### 定义任务（下游项目）

```python
# tasks/fetch.py
import typer
from pycore import Result, output_result, logger
from pycore.http import get

app = typer.Typer()
log = logger("fetch")

@app.command()
def fetch(url: str):
    """抓取 URL 为 Markdown"""
    log.info("Fetching", url=url)
    resp = get(f"https://r.jina.ai/{url}", headers={"Accept": "text/markdown"})
    output_result(Result.ok(resp.body))
```

### CLI 入口

```python
# __main__.py
from pycore import create_app
app = create_app("myproject", tasks_package="tasks")
app()
```

### 运行

```bash
uv run python -m myproject fetch "https://example.com"
uv run python -m myproject --help
```

## 模块一览

| 模块 | 导入 | 用途 |
|------|------|------|
| CLI | `from pycore import create_app` | Typer + 自动扫描 tasks/ |
| 日志 | `from pycore import logger` | 结构化 JSON 日志 |
| 配置 | `from pycore import env, require_env, load_dotenv` | 环境变量 + .env |
| HTTP | `from pycore.http import get, post` | 请求 + 重试 + 超时 |
| 通知 | `from pycore.notify import notify` | Telegram/飞书 |
| 并发 | `from pycore import run_parallel, run_batch` | 多线程/异步 |
| 异常 | `from pycore import AppError, ExternalServiceError, ...` | 统一异常层级 |
| 常量 | `from pycore import constants` | 通用常量 |
| 结果 | `from pycore import Result, output_result` | 统一输出 |
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

load_dotenv()  # 加载 .env 文件
api_key = require_env("API_KEY")  # 缺失则抛 ConfigError
timeout = env("TIMEOUT", default=30, cast=int)
debug = env("DEBUG", default=False, cast=bool)
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

# 多个不同任务并行
results = run_parallel({
    "site_a": lambda: get("https://a.com").body,
    "site_b": lambda: get("https://b.com").body,
}, max_workers=3)

# 同一函数批量执行
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

```yaml
- uses: astral-sh/setup-uv@v4
- run: uv sync
- run: |
    RESULT_FILE=/tmp/result.txt \
    uv run python -m myproject ${{ inputs.action }} "${{ inputs.target }}"
```

## 开发

```bash
git clone https://github.com/ouraihub/pycore.git
cd pycore
uv sync --dev
uv run pytest -v
uv run ruff check src/
```

## 规范文档

- [CONVENTIONS.md](./docs/CONVENTIONS.md) — 日志规范 + 异常处理规范
- [DESIGN.md](./docs/DESIGN.md) — 架构设计
