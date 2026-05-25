# pycore 组件参考 & GitHub Actions 集成指南

## 组件一览

| 模块 | 导入方式 | 用途 |
|------|---------|------|
| Registry | `from pycore import Registry` | 泛型注册表（装饰器注册 + 按名查找 + 分发） |
| Result | `from pycore import Result, output_result` | 统一任务结果 + RESULT_FILE 输出 |
| Logger | `from pycore import logger` | 结构化 JSON 日志（kwargs 即字段） |
| Config | `from pycore import env, require_env, load_dotenv` | 环境变量加载 + 类型转换 |
| HTTP | `from pycore.http import get, post, HttpError` | HTTP 客户端（重试 + 超时） |
| Notify | `from pycore.notify import notify` | 通知发送（Telegram/飞书） |
| Retry | `from pycore.retry import retry` | 通用重试装饰器（指数退避） |
| Concurrent | `from pycore import run_parallel, run_batch, TaskResult` | 多线程 + 异步 |
| Errors | `from pycore import AppError, ExternalServiceError, ...` | 统一异常层级 |
| Constants | `from pycore import constants` | 通用常量 |
| CLI | `from pycore import create_app` | Typer + 自动扫描 tasks/ |

## 各组件用法

### Registry

```python
from pycore import Registry

fetchers = Registry("fetcher")

@fetchers.register
class JinaFetcher:
    name = "jina"
    def can_handle(self, url: str) -> bool:
        return url.startswith("http")
    def fetch(self, url: str) -> str: ...

# 使用
fetchers.get("jina")                          # 按名获取
fetchers.find(lambda f: f.can_handle(url))    # 按条件查找
fetchers.all()                                # 所有实例
fetchers.names()                              # ["jina", ...]
"jina" in fetchers                            # True
len(fetchers)                                 # 1
```

### Result

```python
from pycore import Result, output_result

result = Result.ok("内容", artifacts=["path/to/file.md"])
result = Result.fail("错误信息")

output_result(result)  # 打印到 stdout，如果设了 RESULT_FILE 也写文件
```

### Logger

```python
from pycore import logger

log = logger("my_module")
log.info("Fetching", url="https://...", timeout=30)
log.error("Failed", error=str(e), status=500)
# 输出到 stderr: {"ts":"...","level":"info","module":"my_module","msg":"Fetching","url":"...","timeout":30}
```

### Config

```python
from pycore import env, require_env, load_dotenv

load_dotenv()                                    # 加载 .env 文件
api_key = require_env("API_KEY")                 # 必填，缺失抛 ConfigError
timeout = env("TIMEOUT", default=30, cast=int)   # 可选，带类型转换
debug = env("DEBUG", default=False, cast=bool)
```

### HTTP

```python
from pycore.http import get, post, HttpError

resp = get("https://api.example.com/data", timeout=10, retries=3)
data = resp.json()

resp = post("https://api.example.com/submit", json={"key": "value"})

try:
    resp = get(url)
except HttpError as e:
    print(f"HTTP {e.status}: {e.body}")
```

### Notify

```python
from pycore.notify import notify

# 根据 NOTIFY_CHANNEL 环境变量自动选通道
notify("✅ 任务完成")
```

环境变量：`NOTIFY_CHANNEL=telegram|feishu`，`TELEGRAM_BOT_TOKEN`，`TELEGRAM_CHAT_ID`，`FEISHU_WEBHOOK_URL`

### Retry

```python
from pycore.retry import retry

@retry(max_attempts=3, delay=1.0, exceptions=(TimeoutError, ConnectionError))
def flaky_call():
    ...
```

### Concurrent

```python
from pycore import run_parallel, run_batch

# 多个不同任务并行
results = run_parallel({
    "a": lambda: fetch("https://a.com"),
    "b": lambda: fetch("https://b.com"),
}, max_workers=3)

# 同一函数批量执行
results = run_batch(urls, fetch_url, max_workers=5)

# 每个 result: TaskResult(key, success, value, error)
for r in results:
    if r.success:
        print(f"{r.key}: {r.value}")
```

### Errors

```python
from pycore import ValidationError, ExternalServiceError

raise ValidationError("Invalid URL", url=url)
raise ExternalServiceError("API failed", service="feishu", status=403)

# 异常层级：
# AppError → ConfigError / ValidationError / NotFoundError /
#            AuthError / ExternalServiceError / TimeoutError / RateLimitError
```

### CLI

```python
# __main__.py（3 行）
from pycore import create_app
app = create_app("myproject", tasks_package="tasks")
app()
```

自动扫描 `tasks/` 目录下的模块，每个模块导出 `app = typer.Typer()` 或 `def run()` 函数。

---

## GitHub Actions 集成

### 安装 pycore

```yaml
# .github/workflows/task.yml
jobs:
  run-task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync
        working-directory: python

      - name: Run task
        env:
          FEISHU_APP_ID: ${{ secrets.FEISHU_APP_ID }}
          FEISHU_APP_SECRET: ${{ secrets.FEISHU_APP_SECRET }}
          RESULT_FILE: /tmp/result.txt
        run: uv run python -m myproject ${{ inputs.action }} "${{ inputs.target }}"
        working-directory: python/src
```

### pyproject.toml 配置

```toml
[project]
name = "myproject"
dependencies = [
    "pycore @ git+https://github.com/ouraihub/pycore.git",
    "typer>=0.12",
]

[tool.hatch.metadata]
allow-direct-references = true
```

### 带 Playwright 的任务（微信抓取）

```yaml
      - name: Install Playwright
        run: |
          uv pip install playwright
          uv run python -m playwright install chromium --with-deps
        working-directory: python
```

### 读取结果并回调

```yaml
      - name: Callback with result
        if: always()
        run: |
          RESULT=$(cat /tmp/result.txt 2>/dev/null || echo "no output")
          curl -s -X POST "${{ secrets.CALLBACK_URL }}" \
            -H "Content-Type: application/json" \
            -d "{\"result\": $(echo "$RESULT" | jq -Rs .), \"action\": \"${{ inputs.action }}\"}"
```

### 完整 workflow 示例

```yaml
name: Run Task
on:
  workflow_dispatch:
    inputs:
      action:
        required: true
        type: string
      target:
        required: true
        type: string
      style:
        required: false
        type: string
        default: ""

jobs:
  task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - run: uv sync
        working-directory: python

      - name: Install Playwright (if needed)
        if: contains(inputs.target, 'mp.weixin.qq.com')
        run: |
          uv pip install playwright beautifulsoup4 lxml markdownify
          uv run python -m playwright install chromium --with-deps
        working-directory: python

      - name: Execute
        env:
          FEISHU_APP_ID: ${{ secrets.FEISHU_APP_ID }}
          FEISHU_APP_SECRET: ${{ secrets.FEISHU_APP_SECRET }}
          RESULT_FILE: /tmp/result.txt
          NOTIFY_CHANNEL: telegram
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          EXTRA_ARGS=""
          if [ -n "${{ inputs.style }}" ]; then
            EXTRA_ARGS="--style ${{ inputs.style }}"
          fi
          uv run python src/run_task.py ${{ inputs.action }} "${{ inputs.target }}" $EXTRA_ARGS
        working-directory: python
```
