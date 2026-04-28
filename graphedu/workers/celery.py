"""Celery 应用实例"""

import logging

from celery import Celery

from graphedu.common.config.manager import get_config

logger = logging.getLogger(__name__)

celery_config = get_config().celery

celery_app = Celery("graphedu")
# celery 配置，文档：https://docs.celeryq.dev/en/stable/userguide/configuration.html
celery_app.conf.update(
    broker_url=celery_config.broker_url,
    result_backend=celery_config.result_backend,
    task_serializer=celery_config.task_serializer,
    result_serializer=celery_config.result_serializer,
    accept_content=celery_config.accept_content,
    timezone=celery_config.timezone,
    task_track_started=celery_config.task_track_started,
    task_time_limit=celery_config.task_time_limit,
    task_soft_time_limit=celery_config.task_soft_time_limit,
    result_expires=celery_config.result_expires,
    worker_prefetch_multiplier=celery_config.worker_prefetch_multiplier,
    redis_backend_health_check_interval=celery_config.redis_backend_health_check_interval,
    redis_max_connections=celery_config.redis_max_connections,
    redis_socket_connect_timeout=celery_config.redis_socket_connect_timeout,
    redis_socket_keepalive=celery_config.redis_socket_keepalive,
)

# 显式注册任务模块
celery_app.conf.update(
    include=[
        "graphedu.workers.graphrag_tasks",
        "graphedu.workers.study_assessment_tasks",
        "graphedu.workers.knowledge_point_embedding_tasks",
        "graphedu.workers.knowledge_graph_tasks",
        "graphedu.workers.course_exercise_tasks",
    ],
)

# Celery Beat 定时调度
celery_app.conf.update(
    beat_schedule={
        "sync-all-pending-embeddings": {
            "task": "graphedu.workers.sync_all_pending_embeddings",
            "schedule": celery_config.beat_sync_embeddings_interval,
        },
    },
)

# @worker_process_init.connect
# def _on_worker_process_init(**_kwargs) -> None:
#     """子进程 fork 后重置全局容器，确保每个进程拥有独立的数据库连接池。
#
#     Celery prefork 模式下，子进程通过 fork 创建，会继承父进程的全部内存状态。
#     如果父进程已经初始化了数据库连接池，子进程会共享同一批 TCP 连接，
#     导致 PostgreSQL 检测到协议异常后主动断开连接（OperationalError）。
#     通过重置全局容器，让每个子进程在首次执行任务时创建自己的连接池。
#     """
#     from graphedu.common.resource.manager import set_container
#
#     set_container(None)
#     logger.debug("Worker 子进程已重置全局容器，将在首次任务时创建独立连接池")
