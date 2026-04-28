"""知识点向量嵌入填充 Celery 任务。

遍历 AGE 图谱中的 KnowledgePoint 节点，生成 embedding 并写入 edu_knowledge_point_embedding 表。
包含存量回填（按课程）和定时增量同步（扫描所有课程）两种任务。
"""

import asyncio
import logging
import sys
from uuid import UUID

from graphedu.common.resource import ContainerMode, try_get_container
from graphedu.workers.celery import celery_app

logger = logging.getLogger(__name__)

_BATCH_SIZE = 32


@celery_app.task(bind=True, name="graphedu.workers.populate_knowledge_point_embeddings", max_retries=1)
def populate_knowledge_point_embeddings(self, course_id: int):
    """为指定课程的知识点生成 embedding 并写入 edu_knowledge_point_embedding 表。

    Args:
        self: Celery 任务实例
        course_id: 课程 ID
    """

    async def _process():
        from graphedu.mapper.education.knowledge_point_embedding import KnowledgePointEmbeddingMapper
        from graphedu.mapper.education.syllabus_graph import SyllabusGraphMapper
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        container = await try_get_container(ContainerMode.WORKER)
        pg_client = await container.postgresql_client()

        # 1. 获取课程所有知识点
        nodes = await SyllabusGraphMapper.get_graph_nodes(pg_client, course_id)
        if not nodes:
            logger.info("课程 %s 无知识点，跳过", course_id)
            return {"course_id": course_id, "status": "skipped", "reason": "无知识点"}

        # 2. 过滤已有 embedding 的知识点
        async with pg_client.session_context() as db_session:
            existing_uuids = await KnowledgePointEmbeddingMapper.get_existing_node_uuids(course_id, db_session)

        pending = [n for n in nodes if n.uuid and n.uuid not in existing_uuids]
        if not pending:
            logger.info("课程 %s 知识点 embedding 已全部填充，跳过", course_id)
            return {"course_id": course_id, "status": "skipped", "reason": "全部已填充"}

        # 3. 批量生成 embedding 并写入
        embedding_llm = SyllabusGraphService._get_embedding_llm()
        texts = [f"{n.title}\n{n.description or ''}".strip() for n in pending]
        inserted = 0

        for i in range(0, len(texts), _BATCH_SIZE):
            batch_texts = texts[i : i + _BATCH_SIZE]
            batch_nodes = pending[i : i + _BATCH_SIZE]

            try:
                embeddings = await embedding_llm.aembed_documents(batch_texts)
            except Exception as e:
                logger.exception("生成 embedding 失败: course_id=%s, batch=%d-%d", course_id, i, i + len(batch_texts))
                logger.error("错误: %s", e)
                continue

            async with pg_client.session_context() as db_session:
                for node, embedding in zip(batch_nodes, embeddings, strict=True):
                    try:
                        await KnowledgePointEmbeddingMapper.upsert_embedding(
                            node_uuid=UUID(node.uuid),
                            course_id=course_id,
                            title=node.title,
                            embedding=embedding,
                            db_session=db_session,
                        )
                        inserted += 1
                    except Exception as e:
                        logger.exception("写入 embedding 失败: node_uuid=%s", node.uuid)
                        logger.error("错误: %s", e)
                await db_session.commit()

        logger.info("课程 %s embedding 填充完成: 总计 %d, 新增 %d", course_id, len(nodes), inserted)
        return {"course_id": course_id, "status": "ok", "total": len(nodes), "inserted": inserted}

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_process(), **asyncio_run_kwargs)


@celery_app.task(name="graphedu.workers.sync_all_pending_embeddings")
def sync_all_pending_embeddings():
    """定时扫描所有课程，为缺失 embedding 的知识点自动补全。

    由 Celery Beat 每小时触发。对每个课程派发 populate_knowledge_point_embeddings 子任务。
    """

    async def _scan():
        from sqlalchemy import select

        from graphedu.common.models.orm.education import EduCourse

        container = await try_get_container(ContainerMode.WORKER)
        pg_client = await container.postgresql_client()

        async with pg_client.session_context() as db_session:
            stmt = select(EduCourse.course_id).where(EduCourse.status == "0")
            result = await db_session.execute(stmt)
            course_ids = [row[0] for row in result.all()]

        if not course_ids:
            logger.info("无活跃课程，跳过 embedding 同步")
            return {"status": "skipped", "reason": "无活跃课程", "dispatched": 0}

        dispatched = 0
        for cid in course_ids:
            populate_knowledge_point_embeddings.apply_async(args=[cid])
            dispatched += 1

        logger.info("Embedding 定时同步: 扫描 %d 个课程, 派发 %d 个任务", len(course_ids), dispatched)
        return {"status": "ok", "total_courses": len(course_ids), "dispatched": dispatched}

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_scan(), **asyncio_run_kwargs)
