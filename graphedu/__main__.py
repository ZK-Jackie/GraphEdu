"""GraphEdu 命令行工具主入口模块

本模块是 GraphEdu 项目的主入口点，提供统一的命令行接口（CLI）来管理项目的各个方面。

使用方式:
    使用 Python 模块方式运行:
    >>> python -m graphedu [OPTIONS] COMMAND [ARGS]...

    或使用 uv 运行（推荐）:
    >>> uv run -m graphedu [OPTIONS] COMMAND [ARGS]...

    或安装后使用 graphedu 命令:
    >>> graphedu [OPTIONS] COMMAND [ARGS]...

可用命令:
    ========== 服务管理 ==========
    service          启动后端 API 服务（FastAPI）
                     - start: 标准模式启动
                     - dev: 开发模式启动（热重载 + 详细日志）
                     - prod: 生产模式启动（多进程）

    builder          启动分布式数据构建服务
                     - 用于构建知识图谱数据、课程数据预处理等

    pdf-converter    启动分布式 PDF 转换服务
                     - 处理 PDF 转图片、文本提取等任务

    ========== 代码生成 ==========
    generate         生成业务 CRUD 代码
                     - crud: 生成完整 CRUD 代码
                     - model: 仅生成 PO 模型
                     - list: 列出可用模板

    generate-schema  生成 Pydantic 模型 JSON Schema
                     - schema: 生成指定类的 JSON Schema
                     - 支持快捷方式（如 'service'）

    ========== 代码质量 ==========
    lint             代码静态检查工具（基于 Ruff）
                     - check: 运行 lint 检查
                     - format: 代码格式化
                     - all: 同时运行 lint 和 format
                     - rules: 列出所有可用规则
                     - clean: 清理 ruff 缓存
                     - show-config: 显示 ruff 配置

    ========== 项目维护 ==========
    clean            清理临时文件和缓存
                     - pycache: 清理 Python 缓存
                     - logs: 清理日志文件
                     - pytest: 清理 pytest 缓存
                     - all: 清理所有
                     - info: 显示清理信息

    ========== 测试运行 ==========
    test             运行单元测试和集成测试（基于 pytest）
                     - run: 运行测试
                     - config: 管理模块映射配置
                     - coverage: 生成覆盖率报告
                     - markers: 列出可用 markers
                     - info: 显示测试信息

全局选项:
    --help           显示帮助信息并退出
    --version        显示版本信息并退出

常用示例:
    # ===== 开发模式启动服务 =====
    uv run -m graphedu service dev                 # 开发模式（端口 8000）
    uv run -m graphedu service dev --port 9000     # 指定端口

    # ===== 生产模式启动服务 =====
    uv run -m graphedu service prod                # 生产模式（4 进程）
    uv run -m graphedu service prod -w 8           # 8 个工作进程

    # ===== 代码检查和格式化 =====
    uv run -m graphedu lint check                  # 检查代码
    uv run -m graphedu lint check --fix            # 检查并自动修复
    uv run -m graphedu lint all                    # 同时 lint 和 format
    uv run -m graphedu lint rules 'F*'             # 列出 Pyflakes 规则

    # ===== 清理缓存 =====
    uv run -m graphedu clean all                   # 清理所有缓存
    uv run -m graphedu clean logs --keep-days 7    # 保留 7 天日志
    uv run -m graphedu clean info                  # 查看清理信息

    # ===== 运行测试 =====
    uv run -m graphedu test run                    # 运行所有测试
    uv run -m graphedu test run unit               # 运行单元测试
    uv run -m graphedu test run -m unit -n 4       # 4 进程并行运行
    uv run -m graphedu test coverage --report html # 生成 HTML 覆盖率报告

    # ===== 代码生成 =====
    uv run -m graphedu generate crud course        # 生成 course 模块代码
    uv run -m graphedu generate list               # 列出可用模板

配置文件:
    - dev.config.yaml   开发环境配置
    - prod.config.yaml  生产环境配置

环境变量:
    可以通过环境变量覆盖配置文件中的设置，格式为:
    GRAPHEDU_SECTION__KEY=value

退出码:
    0    成功
    1    错误或失败

Module Attributes:
    cli (typer.Typer): 主 Typer 应用实例，包含所有子命令

See Also:
    - graphedu.cli: CLI 命令实现模块
    - graphedu.api.service: FastAPI 应用定义
    - graphedu.common.config: 配置管理模块
"""

import sys

from graphedu.cli import cli

sys.stdout.reconfigure(encoding="utf-8")
if __name__ == "__main__":
    cli()
