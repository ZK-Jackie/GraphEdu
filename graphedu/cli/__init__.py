"""GraphEdu CLI"""

import typer

from graphedu.cli._ctx import global_param
from graphedu.cli.beat import beat_app
from graphedu.cli.clean import clean_app
from graphedu.cli.generate import generate_app
from graphedu.cli.service import service_app
from graphedu.cli.worker import worker_app

cli = typer.Typer(name="graphedu", help="GraphEdu 项目命令行工具", add_completion=False, callback=global_param)


cli.add_typer(service_app, name="service", help="后端 API 服务")
cli.add_typer(generate_app, name="generate", help="代码生成工具（code/env/schema）")
cli.add_typer(clean_app, name="clean", help="清理工具")
cli.add_typer(worker_app, name="worker", help="Celery Worker 服务")
cli.add_typer(beat_app, name="beat", help="Celery Beat 定时调度服务")
