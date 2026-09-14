"""知识图谱自动生成 Celery 任务

由 KnowledgeGraphService.submit_auto_generate 派发。
submit 方法先创建 edu_knowledge_graph 记录（task_status=pending），
本任务接收 graph_id 后执行重量级操作（GraphRAG 调用、AGE 写入）并更新状态。
"""

import asyncio
import logging
import sys

from graphedu.common.resource import ContainerMode, try_get_container
from graphedu.workers.celery import celery_app
from graphedu.workers.runtime import categorize_exception, raise_if_cancelled

logger = logging.getLogger(__name__)


async def _update_task_status(graph_id: int, task_status: str, db) -> None:
    """更新 edu_knowledge_graph.task_status 字段（委托 Mapper，不在 worker 层写裸 SQL）。"""
    from graphedu.mapper.education.knowledge_graph import KnowledgeGraphMapper

    await KnowledgeGraphMapper.update_task_status(graph_id, task_status, db)


def _report_progress(graph_id: int, percent: int, step: str) -> None:
    """向 Celery Redis backend 上报进度。

    与 CeleryWorkflowCallbacks 使用相同的 celery_app.backend.store_result 模式，
    task_id 使用 str(graph_id)，前端通过 AsyncResult(str(graph_id)) 读取。
    """
    try:
        celery_app.backend.store_result(
            task_id=str(graph_id),
            result={"percent": percent, "step": step},
            state="PROGRESS",
        )
    except Exception:
        logger.warning("[知识图谱生成] 上报进度失败: graph_id=%d", graph_id, exc_info=True)


async def _persist_status(pg_client, graph_id: int, task_status: str) -> None:
    """持久化任务状态（独立短事务，失败仅记录不抛出，避免掩盖原异常）。"""
    try:
        async with pg_client.session_context() as db:
            await _update_task_status(graph_id, task_status, db)
    except Exception:
        logger.exception("更新 task_status=%s 失败: graph_id=%d", task_status, graph_id)


@celery_app.task(
    bind=True,
    name="graphedu.workers.auto_generate_knowledge_graph",
    max_retries=1,
    # 知识图谱生成含 GraphRAG 调用，可能持续数小时，覆盖全局 task_time_limit(3600s)。
    # 软超时抛 SoftTimeLimitExceeded（由下方分类逻辑标记 failed，不再重试）。
    soft_time_limit=7200,
    time_limit=7500,
)
def auto_generate_knowledge_graph(
    self,
    course_id: int,
    graph_id: int,
    graph_name: str | None = None,
    user_id: int | None = None,
):
    """异步执行知识图谱自动生成。

    由 submit_auto_generate 预创建记录后派发。本任务负责：
    1. 更新 task_status → processing
    2. 调用 GraphRAG 生成图谱（重量级操作）
    3. 写入 AGE 图数据库
    4. 更新 task_status → success / failed / cancelled

    异常按 ``runtime.categorize_exception`` 分类：取消/超时不重试，业务异常可重试。
    在 GraphRAG 调用等重量级步骤前后调用 ``raise_if_cancelled`` 实现协作式中断。
    """

    async def _process(pg_client):
        from uuid import UUID

        from graphedu.common.models.bo.user import CurrentUser, UserDetail
        from graphedu.common.models.orm import SysUser
        from graphedu.mapper.education.chapter import ChapterMapper
        from graphedu.mapper.education.chapter_knowledge_point import ChapterKnowledgePointMapper
        from graphedu.mapper.education.graphrag_task import GraphRAGTaskMapper
        from graphedu.services.education.dependency_inference import KnowledgeRelationshipBO
        from graphedu.services.education.knowledge_extraction import KnowledgePointBO
        from graphedu.services.education.syllabus_graph import SyllabusGraphService
        from graphedu.services.external.graphrag import GraphRAGService

        # 构造最小化 CurrentUser（仅填充 user_id）
        current_user = CurrentUser(
            permissions=[],
            role_keys=[],
            detail=UserDetail(user=SysUser(user_id=user_id)) if user_id else None,
        )

        async with pg_client.session_context() as db:
            await _update_task_status(graph_id, "processing", db)
        _report_progress(graph_id, 5, "初始化任务")

        # 2. 查找启用的 GraphRAG 任务
        raise_if_cancelled(self)
        async with pg_client.session_context() as db:
            enabled_task = await GraphRAGTaskMapper.get_enabled_task_for_course(course_id, db)
        if enabled_task is None:
            raise RuntimeError(f"课程 {course_id} 没有启用的 GraphRAG 索引任务")
        _report_progress(graph_id, 10, "查找索引任务")

        # 3. 获取章节列表（含 ID 和名称）
        async with pg_client.session_context() as db:
            chapters = await ChapterMapper.get_chapters_by_course_id(course_id, db)
        chapter_names = [ch.chapter_name for ch in chapters if ch.chapter_name]
        _report_progress(graph_id, 15, "获取章节列表")

        # 4. 调用 GraphRAG 生成可视化图谱（重量级操作）
        raise_if_cancelled(self)
        _report_progress(graph_id, 20, "GraphRAG 知识提炼（耗时较长）")
        graph_data = await GraphRAGService.generate_visual_graph(
            graphrag_task_id=enabled_task.task_id,
            chapter_names=chapter_names,
        )
        _report_progress(graph_id, 75, "构建图谱数据")

        # 5. 构建 BO 并直接调用 save_graph_from_extraction
        raise_if_cancelled(self)
        operator_id = (
            current_user.detail.user.user_id
            if current_user and current_user.detail and current_user.detail.user
            else None
        )

        points_bo = [
            KnowledgePointBO(
                title=node.label,
                description=node.description or node.label,
                importance=3,
                confidence=1.0,
                source="ai",
            )
            for node in graph_data.nodes
        ]

        node_id_to_label = {node.id: node.label for node in graph_data.nodes}
        rels_bo = [
            KnowledgeRelationshipBO(
                source_title=node_id_to_label.get(edge.source, str(edge.source)),
                target_title=node_id_to_label.get(edge.target, str(edge.target)),
                relation_type=edge.type,
                confidence=1.0,
                description=edge.description,
            )
            for edge in graph_data.edges
        ]

        # 6. 写入 AGE
        _report_progress(graph_id, 80, "写入图数据库")
        result = await SyllabusGraphService.save_graph_from_extraction(
            pg_client, course_id, points_bo, rels_bo, operator_id=operator_id, graph_id=graph_id
        )
        title_to_uuid = result.title_to_uuid

        # 6.1 写入节点-章节关联（edu_knowledge_node_chapter）
        raise_if_cancelled(self)
        _report_progress(graph_id, 90, "写入章节关联")
        async with pg_client.session_context() as db:
            for node in graph_data.nodes:
                node_uuid_str = title_to_uuid.get(node.label)
                if not node_uuid_str or not node.chapter_indices:
                    continue
                node_uuid = UUID(node_uuid_str)
                for ch_idx in node.chapter_indices:
                    if ch_idx < len(chapters):
                        await ChapterKnowledgePointMapper.add_link(chapters[ch_idx].chapter_id, node_uuid, db)

        # 7. 更新状态为 success
        async with pg_client.session_context() as db:
            await _update_task_status(graph_id, "success", db)
        _report_progress(graph_id, 100, "完成")

        # 8. 触发知识点 / 章节 embedding 填充（异步派发，不阻塞图谱生成任务返回）
        # populate 任务为「增量 + 幂等」：仅处理缺失向量的节点，已填充的直接跳过，
        # 故即时触发与 Celery Beat 每小时兜底并存，不会重复向量化。派发失败不阻断主流程，
        # 由 Beat 定时任务补偿。
        try:
            from graphedu.workers.chapter_embedding_tasks import populate_chapter_embeddings
            from graphedu.workers.knowledge_point_embedding_tasks import populate_knowledge_point_embeddings

            populate_knowledge_point_embeddings.apply_async(args=[course_id])
            populate_chapter_embeddings.apply_async(args=[course_id])
        except Exception:
            logger.exception(
                "派发 embedding 填充任务失败: course_id=%s（将由 Beat 定时任务兜底）", course_id
            )

        logger.info(
            "知识图谱异步生成完成: graph_id=%d, course_id=%d, nodes=%d, edges=%d",
            graph_id,
            course_id,
            len(graph_data.nodes),
            len(graph_data.edges),
        )

        return {
            "graph_id": graph_id,
            "graph_name": graph_name,
            "task_status": "success",
            "total_nodes": len(graph_data.nodes),
            "total_edges": len(graph_data.edges),
        }

    async def _run():
        container = await try_get_container(ContainerMode.WORKER)
        pg_client = await container.postgresql_client()
        try:
            return await _process(pg_client)
        except Exception as e:
            category = categorize_exception(e)
            if category == "cancelled":
                logger.info("知识图谱生成被取消: graph_id=%d", graph_id)
                await _persist_status(pg_client, graph_id, "cancelled")
                return {"graph_id": graph_id, "task_status": "cancelled"}
            if category == "timeout":
                logger.error("知识图谱生成超时: graph_id=%d, error=%s", graph_id, e)
                await _persist_status(pg_client, graph_id, "failed")
                return {"graph_id": graph_id, "task_status": "failed", "message": str(e)}
            # 业务异常：标记 failed 并重试
            logger.exception(
                "知识图谱自动生成失败: graph_id=%d, course_id=%d, error=%s",
                graph_id,
                course_id,
                e,
            )
            await _persist_status(pg_client, graph_id, "failed")
            raise self.retry(exc=e, countdown=120) from e

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_run(), **asyncio_run_kwargs)
