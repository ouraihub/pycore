# AGENTS.md

AI 编码助手的行为准则。本项目由 AI 维护和开发。

## 项目概览

pycore 是 Python 共享基础库，为所有 OurAIHub Python 项目提供：CLI 骨架、结构化日志、配置加载、HTTP 客户端、通知、并发、异常体系、重试。

**定位**：纯通用工具，不含业务逻辑。下游项目通过 `uv add` 引入。

## 开发环境

```bash
uv sync --dev          # 安装依赖
uv run pytest -v       # 跑测试
uv run ruff check src/ # lint
```

## 架构约束

- **零业务逻辑** — 不放 AI 调用、Playwright、fetcher 实现等业务代码
- **最少依赖** — 运行时只依赖 typer，其余用标准库
- **每个模块一个文件** — 不拆子目录（除非模块超过 200 行）
- **所有公共 API 从 `__init__.py` 导出** — 用户只需 `from pycore import xxx`

## 代码规范

### 必须遵守

- 所有函数有类型注解（参数 + 返回值）
- 所有模块有 docstring
- 用 `from __future__ import annotations`
- 日志用 `pycore.log.logger()`，不用 print
- 异常用 `pycore.errors` 层级，不裸抛 Exception
- 新功能必须有测试

### 风格

- ruff 规则：`E, F, I, N, UP, ANN, B, SIM`（ANN401 忽略）
- 行宽 100
- 用 dataclass 而不是 dict 传递结构化数据
- 用 `|` 语法而不是 `Optional[]`（Python 3.11+）

## 修改代码时

### 新增模块

1. 在 `src/pycore/` 下创建 `xxx.py`
2. 在 `__init__.py` 中导出公共 API
3. 在 `tests/test_core.py` 中添加测试类 `TestXxx`
4. 在 `README.md` 模块一览表中添加一行
5. 跑 `uv run ruff check src/ && uv run pytest` 确认通过

### 修改已有模块

- 不改公共 API 签名（除非明确要求）
- 不删已有测试
- 改完跑 lint + 测试

### 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
refactor: 重构（不改行为）
test: 测试
```

## 测试

```bash
uv run pytest -v              # 全部
uv run pytest -k "TestRetry"  # 单个类
uv run pytest --tb=short      # 简短错误
```

所有测试在 `tests/test_core.py`，按模块分 class：
- `TestResult`
- `TestConfig`
- `TestLogger`
- `TestErrors`
- `TestConcurrent`
- `TestRetry`

## 文件结构

```
src/pycore/
├── __init__.py      # 公共 API（所有导出在这里）
├── py.typed         # PEP 561 类型标记
├── cli.py           # Typer + tasks/ 自动扫描
├── concurrent.py    # run_parallel / run_batch / run_async
├── config.py        # env() / require_env() / load_dotenv()
├── constants.py     # 通用常量
├── errors.py        # AppError 异常层级
├── http.py          # get() / post() + 重试 + 超时
├── log.py           # 结构化 JSON 日志
├── notify.py        # Telegram / 飞书通知
├── result.py        # Result 数据类 + output_result()
└── retry.py         # @retry 装饰器
tests/
└── test_core.py     # 所有测试
```

## 关键设计决策

| 决策 | 原因 |
|------|------|
| Typer 做 CLI | 类型注解自动生成参数，不用写 argparse |
| 装饰器注册 | 下游项目加任务只需 `@app.command()`，不改入口 |
| JSON 日志到 stderr | stdout 留给 Result 输出，GitHub Actions 能解析 JSON |
| RESULT_FILE 环境变量 | Actions 读文件回调，本地不写文件 |
| urllib 不用 requests | 零额外依赖 |
| errors 带 context kwargs | 异常可序列化为 JSON，方便日志和回调 |

## 规范文档

- `docs/CONVENTIONS.md` — 日志规则 + 异常处理规则（必读）
- `docs/DESIGN.md` — 架构设计 + 下游项目使用方式
