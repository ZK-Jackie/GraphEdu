"""Beat CLI 命令模块

提供 Celery Beat 定时调度服务的启动命令。
"""

import logging

import typer

beat_app = typer.Typer(help="Celery Beat 定时调度命令")
logger = logging.getLogger(__name__)


@beat_app.command("start")
def start_beat(
    log_level: str = typer.Option("info", "--log-level", "-l", help="日志级别"),
    schedule: str = typer.Option(
        "data/celerybeat-schedule", "--schedule", "-s", help="调度数据库文件路径"
    ),
):
    """启动 Celery Beat 定时调度服务

    Beat 作为独立进程运行，负责将定时任务推送到消息队列，
    由 Worker 进程实际执行。

    Examples:
        graphedu beat start                              # 使用默认配置启动
        graphedu beat start --log-level debug            # 调试日志
        graphedu beat start --schedule /tmp/celerybeat   # 指定调度数据库路径
    See Also:
        https://docs.celeryq.dev/en/stable/userguide/beat.html
    """
    from graphedu.workers.celery import celery_app

    logger.info("启动 Celery Beat，日志级别: %s，调度数据库: %s", log_level, schedule)

    try:
        celery_app.start(
            argv=[
                "beat",
                f"--loglevel={log_level}",
                f"--schedule={schedule}",
            ]
        )
    except SystemExit:
        raise typer.Exit(code=0) from None
