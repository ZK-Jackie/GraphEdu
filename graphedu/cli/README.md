# GraphEdu CLI 模块文档

> GraphEdu 命令行工具（CLI）是项目的核心管理接口，提供服务启动、代码生成、测试运行、代码检查等功能。

## 目录

- [概述](#概述)
- [安装与使用](#安装与使用)
- [命令结构](#命令结构)
- [全局参数](#全局参数)
- [核心命令](#核心命令)
  - [service](#service---后端服务管理)
  - [builder](#builder---数据构建服务)
  - [generate](#generate---代码生成工具)
  - [clean](#clean---清理工具)
- [配置文件](#配置文件)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

---

## 概述

GraphEdu CLI 基于 **Typer** 框架构建，提供了一套完整的命令行工具用于项目的日常开发和管理。

### 技术栈

- **CLI 框架**: Typer
- **Web 服务器**: Uvicorn
- **测试框架**: Pytest
- **代码检查**: Ruff
- **代码生成**: Jinja2

### 设计原则

1. **异步优先**: 所有服务命令默认使用 async 模式
2. **分层严格**: 遵循项目的 Controller → Service → Mapper 分层架构
3. **配置驱动**: 通过 YAML 配置文件管理环境差异
4. **开发友好**: 提供开发模式（热重载、详细日志）和生产模式

---

## 安装与使用

### 前置要求

- Python 3.13+
- uv (推荐) 或 pip

### 基本用法

```bash
# 使用 uv 运行（推荐）
uv run -m graphedu <command> <subcommand> [options]

# 或使用项目入口点
graphedu <command> <subcommand> [options]

# 查看帮助
graphedu --help
graphedu <command> --help
graphedu <command> <subcommand> --help
```

---

## 命令结构

```
graphedu
├── service        # 后端 API 服务管理
│   ├── start      # 标准模式启动
│   ├── dev        # 开发模式启动
│   └── prod       # 生产模式启动
├── builder        # 数据构建服务管理
│   ├── start      # 标准模式启动
│   └── dev        # 开发模式启动
├── generate       # 代码生成工具
│   ├── code       # 从数据库生成代码
│   │   ├── model  # 生成 ORM 模型
│   │   ├── crud   # 生成完整 CRUD
│   │   └── list   # 列出可用模板
│   ├── env        # 生成环境变量文件
│   └── schema     # 生成 JSON Schema
├── lint           # 代码静态检查
│   ├── check      # 运行 lint 检查
│   ├── format     # 代码格式化
│   ├── all        # 同时运行 lint 和 format
│   ├── rules      # 列出可用规则
│   ├── clean      # 清理缓存
│   └── show-config # 显示配置
├── test           # 测试运行工具
│   ├── run        # 运行测试
│   ├── config     # 管理模块映射
│   ├── coverage   # 生成覆盖率报告
│   ├── markers    # 列出可用标记
│   └── info       # 显示测试信息
└── clean          # 清理工具
    ├── pycache    # 清理 Python 缓存
    ├── logs       # 清理日志文件
    ├── pytest     # 清理 pytest 缓存
    ├── all        # 清理所有
    └── info       # 显示统计信息
```

---

## 全局参数

所有命令都支持以下全局参数：

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `--config` | `-c` | 配置文件路径 | `dev.config.yaml` |
| `--verbose` | `-v` | 启用详细输出 | `false` |

---

## 核心命令

### service - 后端服务管理

启动和管理 GraphEdu 后端 API 服务。

#### 命令

| 命令 | 说明 |
|------|------|
| `start` | 标准模式启动服务 |
| `dev` | 开发模式启动（热重载 + 详细日志） |
| `prod` | 生产模式启动（多进程） |

#### 通用参数

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `--host` | `-h` | 绑定的主机地址 | `0.0.0.0` |
| `--port` | `-p` | 绑定的端口号 | `8000` |
| `--workers` | `-w` | 工作进程数 | `1` |
| `--reload` | `-r` | 启用热重载 | `false` |
| `--log-level` | `-l` | 日志级别 | `info` |
| `--loop` | - | 事件循环实现 | `auto` |

#### 运行模式对比

| 模式 | 热重载 | 工作进程 | 适用场景 |
|------|--------|----------|----------|
| `start` | 可选 | 可选 | 灵活配置 |
| `dev` | 是 | 1 | 开发调试 |
| `prod` | 否 | 4 | 生产部署 |

#### 使用示例

```bash
# 开发模式（推荐日常开发）
uv run -m graphedu service dev

# 指定端口
uv run -m graphedu service dev --port 9000

# 生产模式
uv run -m graphedu service prod
uv run -m graphedu service prod -w 8 --port 80

# 标准模式
uv run -m graphedu service start --reload -w 2
```

#### API 文档

服务启动后可访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

---

### builder - 数据构建服务

启动和管理分布式数据构建服务（知识图谱构建等）。

#### 命令

| 命令 | 说明 |
|------|------|
| `start` | 标准模式启动服务 |
| `dev` | 开发模式启动 |

#### 服务功能

- 知识图谱数据构建（GraphRAG）
- 课程数据预处理和清洗
- 文档向量化处理
- 实体关系提取

#### 使用示例

```bash
# 开发模式
uv run -m graphedu builder dev

# 指定端口（默认 8001）
uv run -m graphedu builder dev --port 9001

# 生产模式
uv run -m graphedu builder start -w 2
```

---

### generate - 代码生成工具

#### generate code - 从数据库生成代码

**命令**

| 命令 | 说明 |
|------|------|
| `model` | 生成 ORM 实体模型 |
| `crud` | 生成完整 CRUD 代码 |
| `list` | 列出可用代码模板 |

**generate code model - 生成 ORM 模型**

```bash
# 基本用法
uv run -m graphedu generate code model edu_course

# 指定模块名
uv run -m graphedu generate code model edu_course -m course

# 覆盖已存在文件
uv run -m graphedu generate code model edu_course --overwrite
```

参数：
| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `table_name` | - | 数据库表名 | 必填 |
| `--module` | `-m` | 模块名 | 从表名提取 |
| `--output` | `-o` | 输出目录 | 当前目录 |
| `--overwrite` | - | 覆盖已存在文件 | false |

**generate code crud - 生成完整 CRUD**

```bash
# 基本用法（表名默认为 edu_{module}）
uv run -m graphedu generate code crud course

# 指定表名
uv run -m graphedu generate code crud student --table edu_student

# 不生成 API 层
uv run -m graphedu generate code crud teacher --no-api

# 覆盖已存在文件
uv run -m graphedu generate code crud course --overwrite
```

参数：
| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `module_name` | - | 模块名称 | 必填 |
| `--table` | `-t` | 数据库表名 | `edu_{module}` |
| `--api/--no-api` | - | 是否生成 API 层 | true |
| `--service/--no-service` | - | 是否生成 Service 层 | true |
| `--mapper/--no-mapper` | - | 是否生成 Mapper 层 | true |
| `--overwrite` | - | 覆盖已存在文件 | false |

**生成代码结构**

```
graphedu/
├── api/services/{domain}/
│   └── {module}.py            # FastAPI 路由
├── services/{domain}/
│   └── {module}.py            # Service 类
├── mapper/
│   └── {module}.py            # Mapper 类
└── common/models/
    ├── orm/{domain}.py        # ORM 实体（需手动合并）
    ├── dto/{module}.py        # DTO 模型
    └── vo/{module}.py         # VO 模型
```

#### generate env - 生成环境变量文件

基于模板从 YAML 配置生成 .env 文件。

```bash
# 使用默认模板生成
uv run -m graphedu generate env

# 使用自定义模板
uv run -m graphedu generate env --template .env.custom

# 脱敏生成（用于分享）
uv run -m graphedu generate env --mask > .env.example

# 列出模板变量
uv run -m graphedu generate env --list
```

参数：
| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `--config` | `-c` | 配置文件路径 | `dev.config.yaml` |
| `--template` | `-t` | 模板文件路径 | 内置模板 |
| `--output` | `-o` | 输出文件路径 | `.env` |
| `--mask` | - | 脱敏敏感信息 | false |
| `--list` | `-l` | 列出模板变量 | false |

**模板语法**

```bash
# 引用配置值
POSTGRES_DSN=${database.postgresql.dsn}

# 带默认值
LOG_LEVEL=${log.level:INFO}
```

#### generate schema - 生成 JSON Schema

为 Pydantic 模型生成 JSON Schema。

```bash
# 使用快捷方式
uv run -m graphedu generate schema service

# 指定输出路径
uv run -m graphedu generate schema service --output ./schemas/

# 列出快捷方式
uv run -m graphedu generate schema --list
```

参数：
| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `class_path` | - | Pydantic 类路径或快捷方式 | 必填 |
| `--output` | `-o` | 输出路径 | `.generated` |
| `--pretty/--no-pretty` | - | 是否格式化 JSON | true |
| `--list` | `-l` | 列出快捷方式 | false |

---

### lint - 代码检查工具

基于 Ruff 的代码静态检查和格式化工具。

#### 命令

| 命令 | 说明 |
|------|------|
| `check` | 运行 lint 检查 |
| `format` | 代码格式化 |
| `all` | 同时运行 lint 和 format |
| `rules` | 列出可用规则 |
| `clean` | 清理 Ruff 缓存 |
| `show-config` | 显示配置 |

#### 使用示例

```bash
# 基本检查
uv run -m graphedu lint check

# 自动修复
uv run -m graphedu lint check --fix

# 代码格式化
uv run -m graphedu lint format

# 一键检查和修复
uv run -m graphedu lint all

# 只检查不修复
uv run -m graphedu lint all --check-only

# 查看规则
uv run -m graphedu lint rules
uv run -m graphedu lint rules 'F*'
```

#### lint check 参数

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `paths` | - | 检查路径 | 整个项目 |
| `--fix` | `-f` | 自动修复 | false |
| `--select` | `-s` | 启用的检查代码 | - |
| `--ignore` | `-i` | 忽略的错误代码 | - |
| `--output-format` | `-o` | 输出格式 | `concise` |
| `--statistics` | - | 显示统计信息 | false |

#### Ruff 规则配置

项目配置的规则集：`F`, `E`, `W`, `I`, `UP`, `B`, `C4`, `SIM`, `ASYNC`, `RET`, `RSE`, `ERA`, `N`, `D`, `RUF`

详见 `pyproject.toml` 中的 `[tool.ruff]` 配置。

---

### test - 测试运行工具

基于 Pytest 的测试运行和管理工具。

#### 命令

| 命令 | 说明 |
|------|------|
| `run` | 运行测试 |
| `config` | 管理模块映射 |
| `coverage` | 生成覆盖率报告 |
| `markers` | 列出可用标记 |
| `info` | 显示测试信息 |

#### 使用示例

```bash
# 运行所有测试
uv run -m graphedu test run

# 按模块运行
uv run -m graphedu test run unit
uv run -m graphedu test run integration

# 按 marker 过滤
uv run -m graphedu test run -m unit
uv run -m graphedu test run -m "not slow"

# 并行运行
uv run -m graphedu test run -n 4
uv run -m graphedu test run -n auto

# 覆盖率报告
uv run -m graphedu test coverage
uv run -m graphedu test coverage --report html --open

# 调试模式
uv run -m graphedu test run -x --pdb
```

#### test run 参数

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `module` | - | 模块名称或路径 | 运行全部 |
| `--marker` | `-m` | 按 marker 过滤 | - |
| `--function` | `-k` | 运行匹配的测试函数 | - |
| `--parallel` | `-n` | 并行进程数 | 0 |
| `--exitfirst` | `-x` | 第一个失败后停止 | false |
| `--coverage` | `-c` | 生成覆盖率报告 | false |
| `--pdb` | - | 失败时进入调试器 | false |

#### 测试标记（Markers）

- `unit`: 单元测试
- `integration`: 集成测试
- `e2e`: 端到端测试
- `slow`: 慢速测试
- `asyncio`: 异步测试

#### 模块映射配置

模块映射保存在 `tests/module_mapping.json`：

```json
{
  "common": "tests/common",
  "unit": "tests/unit",
  "integration": "tests/integration",
  "e2e": "tests/e2e"
}
```

管理命令：

```bash
# 列出所有映射
uv run -m graphedu test config --list

# 添加映射
uv run -m graphedu test config --add "api=tests/api"

# 删除映射
uv run -m graphedu test config --remove "api"
```

---

### clean - 清理工具

清理项目临时文件和缓存。

#### 命令

| 命令 | 说明 |
|------|------|
| `pycache` | 清理 Python 缓存 |
| `logs` | 清理日志文件 |
| `pytest` | 清理 pytest 缓存 |
| `all` | 清理所有 |
| `info` | 显示统计信息 |

#### 使用示例

```bash
# 清理 Python 缓存
uv run -m graphedu clean pycache

# 清理日志（保留 7 天）
uv run -m graphedu clean logs --keep-days 7

# 清理所有
uv run -m graphedu clean all

# 查看统计信息
uv run -m graphedu clean info
```

#### clean logs 参数

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|--------|
| `--keep-days` | `-k` | 保留天数 | 0（全部清理） |
| `--dry-run` | - | 模拟运行 | false |

---

## 配置文件

### 配置文件结构

```
项目根目录/
├── dev.config.yaml      # 开发环境配置
├── prod.config.yaml     # 生产环境配置
└── example.config.yaml  # 配置模板
```

### 配置节

| 节 | 说明 |
|----|------|
| `log` | 日志配置 |
| `database` | 数据库连接配置 |
| `service` | 服务配置 |
| `distribute` | 分布式配置 |
| `model.llm` | LLM 模型配置 |

### 环境变量覆盖

可通过环境变量覆盖配置：

```bash
export GRAPHEDU_DATABASE__HOST=localhost
export GRAPHEDU_SERVICE__PORT=8000
export GRAPHEDU_LOG__LEVEL=DEBUG
```

格式：`GRAPHEDU_<节>__<子节>__<键>`

---

## 开发指南

### 添加新命令

1. 在 `graphedu/cli/` 下创建新模块文件
2. 使用 Typer 定义命令
3. 在 `graphedu/cli/__init__.py` 中注册

示例：

```python
# graphedu/cli/mycmd.py
import typer

mycmd_app = typer.Typer(help="我的命令")

@mycmd_app.command("hello")
def hello(name: str = typer.Option("world", "--name")):
    """打招呼"""
    typer.echo(f"Hello, {name}!")

# graphedu/cli/__init__.py
from graphedu.cli.mycmd import mycmd_app
cli.add_typer(mycmd_app, name="mycmd")
```

### 命令最佳实践

1. **使用类型提示**: 所有参数都应有类型注解
2. **提供帮助文本**: 为命令和参数添加 `help` 文档
3. **统一错误处理**: 使用 `typer.Exit(code=1)` 退出
4. **日志记录**: 使用 `logging` 模块记录操作
5. **配置驱动**: 通过配置文件管理环境差异

---

## 常见问题

### Q: 如何在开发时启用断点调试？

使用 `service dev` 或单进程模式启动服务：

```bash
# 方式 1：使用 dev 命令
uv run -m graphedu service dev

# 方式 2：单进程模式
uv run -m graphedu service start
```

多进程模式不支持断点调试。

### Q: 如何指定不同的配置文件？

```bash
uv run -m graphedu -c prod.config.yaml service start
```

### Q: 代码生成后需要手动做什么？

1. 将 ORM 实体合并到对应领域文件（如 `graphedu/common/models/orm/education.py`）
2. 在 `graphedu/api/service.py` 中注册路由
3. 添加权限菜单 SQL（`sys_function` 表）

### Q: 测试运行很慢怎么办？

```bash
# 只运行单元测试
uv run -m graphedu test run -m unit

# 排除慢速测试
uv run -m graphedu test run -m "not slow"

# 并行运行
uv run -m graphedu test run -n auto
```

---

## 参考链接

- [Typer 文档](https://typer.tiangolo.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Uvicorn 文档](https://www.uvicorn.org/)
- [Pytest 文档](https://docs.pytest.org/)
- [Ruff 文档](https://docs.astral.sh/ruff/)
