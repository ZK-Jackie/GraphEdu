"""Service 后端服务启动命令模块

本模块提供 GraphEdu 后端 API 服务的启动和管理功能。

后端服务基于 FastAPI 框架构建，提供 RESTful API 接口。
支持多种运行模式：标准模式、开发模式、生产模式。

服务功能:
    - 用户认证与授权（JWT + RBAC）
    - 业务 CRUD 接口
    - 文件上传下载
    - 日志管理
    - 系统配置管理
    - 知识图谱相关接口（通过 Neo4j）

技术栈:
    - Web 框架: FastAPI
    - ASGI 服务器: Uvicorn
    - 数据库 ORM: SQLAlchemy (async)
    - 缓存: Redis
    - 图数据库: Neo4j
    - 对象存储: S3 兼容接口

主要命令:
    start   标准模式启动服务
    dev     开发模式启动（热重载 + 详细日志）
    prod    生产模式启动（多进程，无热重载）

配置文件:
    - dev.config.yaml   开发环境配置
    - prod.config.yaml  生产环境配置

配置包含:
    - log: 日志配置（级别、输出、轮转）
    - database: 数据库连接（PostgreSQL, Redis, Neo4j）
    - service: 服务配置（token、JWT）
    - distribute: 分布式配置（OSS、队列）
    - model.llm: LLM 模型配置

常用示例:
    # 标准模式启动
    graphedu service start                         # 默认配置（8000 端口）
    graphedu service start --port 9000             # 指定端口
    graphedu service start --config prod.config.yaml  # 指定配置文件
    graphedu service start -w 4                    # 4 个工作进程

    # 开发模式启动（推荐）
    graphedu service dev                           # 热重载 + debug 日志
    graphedu service dev --port 9000               # 指定端口

    # 生产模式启动
    graphedu service prod                          # 多进程模式
    graphedu service prod -w 8                     # 8 个工作进程
    graphedu service prod --port 80                # 监听 80 端口

运行模式对比:
    ┌─────────┬──────────┬─────────┬──────────┐
    │ 模式    │ 热重载   │ 工作进程│ 适用场景 │
    ├─────────┼──────────┼─────────┼──────────┤
    │ start   │ 可选     │ 可选    │ 灵活配置 │
    │ dev     │ 是       │ 1       │ 开发调试 │
    │ prod    │ 否       │ 4       │ 生产部署 │
    └─────────┴──────────┴─────────┴──────────┘

事件循环:
    - Linux/macOS: uvloop (高性能)
    - Windows: asyncio:SelectorEventLoop
    - 可通过 --loop 参数覆盖

环境变量:
    可通过环境变量覆盖配置:
    export GRAPHEDU_DATABASE__HOST=localhost
    export GRAPHEDU_SERVICE__PORT=8000

API 文档:
    启动服务后访问:
    - Swagger UI:  http://localhost:8000/docs
    - ReDoc:       http://localhost:8000/redoc
    - OpenAPI:     http://localhost:8000/openapi.json

退出码:
    0    正常停止（Ctrl+C）
    1    启动失败或运行错误

See Also:
    - FastAPI 文档: https://fastapi.tiangolo.com/
    - Uvicorn 文档: https://www.uvicorn.org/
"""

import logging
import os
import sys

import typer
import uvicorn

from graphedu.common import get_config

service_app = typer.Typer(help="启动后端 API 服务")
logger = logging.getLogger(__name__)


def _default_loop() -> str:
    """根据平台选择默认事件循环。

    不使用 uvloop：graphrag_llm 的依赖 nest_asyncio2 不兼容 uvloop.Loop。
    Windows 需要 SelectorEventLoop（ProactorEventLoop 不支持某些 asyncio 操作）。
    """
    return "asyncio:SelectorEventLoop" if sys.platform in ("win32", "cygwin", "cli") else "asyncio"


@service_app.command("start")
def start_service(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="绑定的主机地址"),
    port: int = typer.Option(8000, "--port", "-p", help="绑定的端口号"),
    workers: int = typer.Option(1, "--workers", "-w", help="工作进程数"),
    reload: bool = typer.Option(False, "--reload", "-r", help="启用热重载（开发模式）"),
    log_level: str = typer.Option(
        "info", "--log-level", "-l", help="日志级别 (debug/info/warning/error)", case_sensitive=False
    ),
    loop: str = typer.Option(
        _default_loop(),
        "--loop",
        help="事件循环实现（默认：Linux/macOS=uvloop, Windows=Selector）",
        case_sensitive=True,
    ),
):
    """启动后端 API 服务

    示例:
        graphedu service start                    # 使用默认配置启动
        graphedu service start --port 9000        # 指定端口启动
        graphedu service start --reload           # 开发模式启动（热重载）
        graphedu service start -w 4               # 多进程模式启动
        graphedu service start --config prod.config.yaml  # 使用指定配置文件
    """
    # 启动补充逻辑：关闭 litellm 日志
    os.environ["LITELLM_LOG"] = "ERROR"

    config = get_config()

    try:
        # reload/workers 模式必须使用字符串路径，否则使用 app 对象（支持断点调试）
        if reload or workers > 1:
            # 热重载或多进程模式：使用字符串路径（不支持断点调试）
            app_target = "graphedu.api.service:app"
        else:
            # 单进程模式：直接导入 app 对象（支持 PyCharm 断点调试）
            from graphedu.api.service import app

            app_target = app

        uvicorn.run(
            app_target,
            host=host,
            port=port,
            workers=workers if not reload else 1,  # reload 模式不支持多进程
            reload=reload,
            log_level=log_level,
            log_config=config.logging.model_dump(),
            loop=loop,
        )
    except KeyboardInterrupt:
        logger.info("服务已停止")
        raise typer.Exit(code=0) from None
    except Exception as e:
        logger.error(f"服务启动失败: {e}", exc_info=True)
        raise typer.Exit(code=1) from None


@service_app.command("dev")
def dev_service(
    port: int = typer.Option(8000, "--port", "-p", help="绑定的端口号"),
):
    """开发模式启动（自动启用热重载和详细日志）

    示例:
        graphedu service dev             # 使用默认端口 8000
        graphedu service dev --port 9000 # 使用端口 9000
    """
    start_service(
        host="127.0.0.1",
        port=port,
        workers=0,
        reload=False,
        log_level="debug",
        loop=_default_loop(),
    )


@service_app.command("prod")
def prod_service(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="绑定的主机地址"),
    port: int = typer.Option(8000, "--port", "-p", help="绑定的端口号"),
    workers: int = typer.Option(4, "--workers", "-w", help="工作进程数"),
):
    """生产模式启动（多进程，无热重载）

    示例:
        graphedu service prod                        # 使用默认配置
        graphedu service prod -w 8                   # 8 个工作进程
        graphedu service prod --port 9000            # 指定端口
    """
    start_service(
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_level="info",
        loop=_default_loop(),
    )
