# 使用 pycore 初始化新项目

> 本文档供 AI agent 直接执行。

## 前置条件

- pycore 已 clone 到本地：`/home/administrator/workspace/open-source/pycore`
- 已安装 uv

## 初始化步骤

```bash
# 1. 创建项目
cd /home/administrator/workspace/open-source
uv run --directory /home/administrator/workspace/open-source/pycore pycore <项目名>

# 2. 进入项目
cd <项目名>

# 3. 初始化 git
git init && git add -A && git commit -m "init: pycore scaffold"

# 4. 安装依赖
uv sync

# 5. 验证
uv run python -m <项目名> --help
uv run python -m <项目名> hello world
```

## 生成的目录结构

```
<项目名>/
├── src/
│   ├── __main__.py         # CLI 入口（自动扫描 tasks/）
│   └── tasks/
│       ├── __init__.py
│       └── hello.py        # 示例命令（可删）
├── tests/
│   └── test_hello.py
├── .github/
│   └── workflows/
│       └── run.yml         # GitHub Actions: 触发→执行→回调
├── pyproject.toml          # 依赖 pycore，配好 uv + ruff + pytest
├── .env.example            # CALLBACK_URL / CALLBACK_SECRET
├── .gitignore
├── AGENTS.md               # AI agent 上下文文档
└── README.md
```

## 添加新命令

在 `src/tasks/` 下创建 Python 文件，定义 `run()` 函数：

```python
# src/tasks/checkin.py
import typer
from pycore import logger, require_env
from pycore.http import post

log = logger("checkin")


def run(
    username: str = typer.Option(..., help="账号"),
    output: str = typer.Option("results.json", help="输出文件"),
):
    """执行签到"""
    log.info("Checkin start", username=username)
    # ... 业务逻辑 ...
    typer.echo(f"Done → {output}")
```

自动注册为命令：

```bash
uv run python -m <项目名> checkin --username test@qq.com
```

## 内置命令

### callback

所有项目自动拥有，无需手写：

```bash
CALLBACK_URL=https://worker.dev/callback \
CALLBACK_SECRET=xxx \
uv run python -m <项目名> callback --file results.json
```

读取 results.json → POST 到 CALLBACK_URL，payload 格式：

```json
{"secret": "xxx", "action": "batch_result", "data": {"results": [...]}}
```

## GitHub Actions workflow

生成的 `.github/workflows/run.yml` 已包含完整闭环：

1. `workflow_dispatch` 接收 `action` + `target` + `callback_url`
2. 执行命令：`python -m <项目名> <action> "<target>" --output results.json`
3. 回调：`python -m <项目名> callback --file results.json`

Worker/Dashboard 只需触发 workflow_dispatch 即可。

## 可用的 pycore 模块

```python
from pycore import logger                    # 结构化日志: log.info("msg", key=val)
from pycore import env, require_env          # 环境变量（带类型转换）
from pycore import Result, output_result     # 统一结果类型
from pycore import Registry                  # 装饰器注册表
from pycore import run_parallel, run_batch   # 并发执行
from pycore import AppError, ExternalServiceError, ConfigError  # 异常层级
from pycore.http import get, post, HttpError # HTTP 请求（带重试）
from pycore.retry import retry               # 重试装饰器
from pycore.notify import notify             # 通知（Telegram/飞书）
```

## 示例：完整的签到项目

```bash
# 初始化
pycore daily-checkin
cd daily-checkin

# 删除示例，写业务
rm src/tasks/hello.py tests/test_hello.py
```

```python
# src/tasks/checkin.py
import json
import typer
from pathlib import Path
from pycore import logger, require_env
from pycore.http import post, HttpError

log = logger("checkin")


def run(
    username: str = typer.Option(..., help="账号"),
    password: str = typer.Option(..., help="密码"),
    output: Path = typer.Option("results.json", help="输出路径"),
):
    """签到"""
    log.info("Start", username=username)
    try:
        resp = post("https://api.example.com/checkin", json={"u": username, "p": password})
        result = {"username": username, "status": "active", "last_result": "签到成功"}
    except HttpError as e:
        result = {"username": username, "status": "active", "last_result": f"失败: HTTP {e.status}"}
        log.error("Failed", username=username, status=e.status)

    output.write_text(json.dumps([result], ensure_ascii=False, indent=2))
    log.info("Done", username=username)
    typer.echo(f"→ {output}")
```

```bash
# 运行
uv run python -m daily-checkin checkin --username test@qq.com --password xxx

# 回调
CALLBACK_URL=https://worker.dev/callback CALLBACK_SECRET=s \
uv run python -m daily-checkin callback --file results.json
```
