# pycore 日志规范 & 异常处理规范

## 日志规范

### 使用方式

```python
from pycore import logger

log = logger("module_name")

log.info("Action description", key="value", count=42)
log.warning("Something unexpected", url=url, status=404)
log.error("Operation failed", error=str(e), user_id=uid)
```

### 输出格式

JSON Lines，输出到 stderr：

```json
{"ts":"2026-05-23T18:00:00","level":"info","module":"fetch","msg":"Fetching URL","url":"https://..."}
```

### 规则

| 规则 | 说明 |
|------|------|
| **不用 print** | 所有输出走 logger，print 只用于 Result 最终输出 |
| **msg 用英文动词短语** | `"Fetching URL"` 不是 `"开始抓取"` |
| **不记录敏感值** | API Key、密码、token 不出现在日志里 |
| **失败必须 log** | 每个 except 块必须有 log.error 或 log.warning |
| **成功可选 log** | 关键操作 log.info，高频操作不 log |
| **带上下文** | kwargs 传结构化字段，不要拼字符串 |

### 级别使用

| 级别 | 场景 |
|------|------|
| `error` | 操作失败，需要关注（外部服务挂了、配置缺失） |
| `warning` | 非预期但可恢复（重试成功、降级处理） |
| `info` | 关键业务动作（任务开始/完成、发布成功） |
| `debug` | 开发调试（默认不输出，设 `LOG_LEVEL=DEBUG` 开启） |

### 反模式

```python
# ❌ 拼字符串
log.info(f"Fetched {url} in {elapsed}ms")

# ✅ 结构化字段
log.info("Fetched", url=url, elapsed_ms=elapsed)

# ❌ 吞异常
try:
    do_something()
except Exception:
    pass

# ✅ 记录后处理
try:
    do_something()
except Exception as e:
    log.error("do_something failed", error=str(e))
    raise
```

---

## 异常处理规范

### 异常层级

```
AppError (base)
├── ConfigError          # 配置缺失或无效
├── ValidationError      # 输入校验失败
├── NotFoundError        # 资源不存在
├── AuthError            # 认证/授权失败
├── ExternalServiceError # 外部服务调用失败（带 service + status）
├── TimeoutError         # 操作超时
└── RateLimitError       # 限流
```

### 使用方式

```python
from pycore import ExternalServiceError, ConfigError, require_env

# 配置缺失
api_key = require_env("API_KEY")  # 自动抛 ConfigError

# 外部服务失败
try:
    resp = http.post(url, json=data)
except HttpError as e:
    raise ExternalServiceError(
        "Feishu API failed",
        service="feishu",
        status=e.status,
    ) from e

# 输入校验
if not url.startswith("http"):
    raise ValidationError("Invalid URL", url=url)
```

### 规则

| 规则 | 说明 |
|------|------|
| **不吞异常** | 每个 except 必须 log + re-raise 或返回明确错误 |
| **用具体异常** | 不要 `except Exception`，用具体的 `ExternalServiceError` 等 |
| **带上下文** | 异常构造时传 kwargs，方便日志和调试 |
| **边界处转换** | 在模块边界把第三方异常转成 pycore 异常 |
| **CLI 入口兜底** | 只在最外层（run_task / __main__）catch AppError 并输出 |

### 边界处转换示例

```python
# adapters/feishu.py — 模块边界
from pycore import ExternalServiceError
from pycore.http import post, HttpError

def publish_to_feishu(title: str, content: str) -> str:
    try:
        resp = post(FEISHU_API, json={"title": title, "content": content})
        return resp.json()["data"]["url"]
    except HttpError as e:
        raise ExternalServiceError(
            "Failed to publish to Feishu",
            service="feishu",
            status=e.status,
        ) from e
```

### CLI 入口兜底

```python
# __main__.py
from pycore import AppError, logger

log = logger("main")

try:
    app()
except AppError as e:
    log.error("Task failed", code=e.code, **e.context)
    output_result(Result.fail(e.message))
    sys.exit(1)
except Exception as e:
    log.error("Unexpected error", error=str(e))
    output_result(Result.fail(f"Unexpected: {e}"))
    sys.exit(2)
```
