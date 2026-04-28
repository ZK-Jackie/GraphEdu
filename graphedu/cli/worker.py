"""Worker CLI 命令模块

提供 Celery Worker 启动命令。
"""

import logging
import os
from pathlib import Path

import typer

worker_app = typer.Typer(help="Celery Worker 命令")
logger = logging.getLogger(__name__)


@worker_app.command("start")
def start_worker(
    log_level: str = typer.Option("info", "--log-level", "-l", help="日志级别"),
    concurrency: int = typer.Option(2, "--concurrency", "-c", help="工作进程数"),
    pool: str = typer.Option("prefork", "--pool", "-p", help="进程池类型"),
):
    """启动 Celery Worker

    Examples:
        graphedu worker start                      # 使用默认配置启动
        graphedu worker start --concurrency 4     # 4 个工作进程
        graphedu worker start --pool gevent       # 使用 gevent 池
    See Also:
        https://docs.celeryq.dev/en/stable/reference/cli.html#cmdoption-celery-worker-c
    """
    from graphedu.workers.celery import celery_app

    logger.info("Starting Celery Worker with log level: %s, concurrency: %d, pool: %s", log_level, concurrency, pool)
    preheat_worker()

    try:
        celery_app.worker_main(
            argv=[
                "worker",
                f"--loglevel={log_level}",
                f"--concurrency={concurrency}",
                f"--pool={pool}",
            ]
        )
    except SystemExit:
        raise typer.Exit(code=0) from None


def preheat_worker():
    """预热 Celery Worker，确保相关模块和配置被加载
    1. tiktoken 编码器预热：提前下载 tiktoken 编码器，确保后续文本 chunking 的快速响应（https://zhuanlan.zhihu.com/p/678582399）
    2. nltk_data 预热：加载 nltk_data 资源，确保文本处理相关功能的快速响应（https://docs.pingcode.com/ask/ask-ask/1100501.html）
    """
    # 项目根目录（worker.py 位于 graphedu/cli/ 下，向上两级即为项目根目录）
    Path(__file__).resolve().parents[2]

    # 1. 关闭 litellm 日志
    os.environ["LITELLM_LOG"] = "ERROR"

    # 2. 下载 tiktoken 编码器，确保后续文本 chunking 的快速响应
    # tiktoken_cache_dir = project_root / "data" / "cache" / "tiktoken"
    # tiktoken_cache_dir.mkdir(parents=True, exist_ok=True)
    # os.environ["TIKTOKEN_CACHE_DIR"] = str(tiktoken_cache_dir)
    # try:
    #     tiktoken.get_encoding("cl100k_base")
    # except Exception:
    #     logger.warning("tiktoken 编码器下载失败，将在首次使用时重试", exc_info=True)
    #
    # # 3. 下载 nltk_data 资源，确保文本处理相关功能的快速响应
    # nltk_cache_dir = project_root / "data" / "cache" / "nltk"
    # nltk_cache_dir.mkdir(parents=True, exist_ok=True)
    # nltk.data.path.append(str(nltk_cache_dir))
    # nltk_resources = [
    #     "punkt",
    #     "punkt_tab",
    #     "averaged_perceptron_tagger",
    #     "averaged_perceptron_tagger_eng",
    #     "maxent_ne_chunker",
    #     "maxent_ne_chunker_tab",
    #     "words",
    #     "wordnet",
    # ]
    # for resource in nltk_resources:
    #     try:
    #         nltk.download(resource, quiet=True, download_dir=str(nltk_cache_dir))
    #     except Exception:
    #         logger.warning("nltk 资源 %s 下载失败", resource, exc_info=True)

    logger.info("GraphEdu Worker preheated successfully")
