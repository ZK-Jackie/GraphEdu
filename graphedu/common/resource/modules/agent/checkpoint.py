"""LangGraph 检查点资源模块。"""

from collections.abc import AsyncGenerator
import logging
from typing import Any, LiteralString

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import psycopg
from psycopg_pool import AsyncConnectionPool

from graphedu.common.config.modules.agent import AgentConfig

logger = logging.getLogger(__name__)


async def init_langgraph_checkpointer(
    config: AgentConfig,
) -> AsyncGenerator[AsyncPostgresSaver, Any]:
    """初始化 LangGraph 检查点保存器。

    Args:
        config: Agent 配置对象。

    Yields:
        AsyncPostgresSaver: LangGraph 检查点保存器实例。
    """
    # 查询表信息需要提供 schema 名称，否则会默认查询当前连接用户的 search_path 中的表，导致查询结果不准确
    CHECKPOINT_TABLES: list[LiteralString] = [  # noqa: N806
        "public.checkpoint_blobs",
        "public.checkpoint_migrations",
        "public.checkpoint_writes",
        "public.checkpoints",
    ]
    do_setup = False

    async with (
        await psycopg.AsyncConnection.connect(str(config.dsn), connect_timeout=10) as conn,
        conn.cursor() as cursor,
    ):
        query: LiteralString = """SELECT t.name, to_regclass(t.name) FROM unnest(%s::text[]) AS t(name);"""
        await cursor.execute(query, (CHECKPOINT_TABLES,))
        results = await cursor.fetchall()
        do_setup = any(oid is None for _, oid in results)
    # https://github.com/langchain-ai/langgraph/issues/3716#issuecomment-3055087468
    if do_setup:
        logger.info("LangGraph checkpointer tables not found, performing setup.")
        async with AsyncConnectionPool(
            str(config.dsn),
            min_size=1,
            max_size=10,
            max_idle=300,
            kwargs={
                "autocommit": True,
                "prepare_threshold": None,
                "sslmode": "disable",
                "sslcert": None,
                "sslkey": None,
                "sslrootcert": None,
                "sslcrl": None,
            },
            open=False,
        ) as pool:
            _init_checkpointer = AsyncPostgresSaver(pool)
            await _init_checkpointer.setup()
    else:
        logger.info("LangGraph checkpointer tables found, skipping setup.")
    async with AsyncConnectionPool(
        str(config.dsn),
        min_size=1,
        max_size=10,
        max_idle=300,
        kwargs={
            "prepare_threshold": None,
            "sslmode": "disable",
            "sslcert": None,
            "sslkey": None,
            "sslrootcert": None,
            "sslcrl": None,
        },
        open=False,
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        logger.info("LangGraph checkpointer initialized.")
        yield checkpointer
