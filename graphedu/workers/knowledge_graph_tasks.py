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

logger = logging.getLogger(__name__)


async def _update_task_status(graph_id: int, task_status: str, db) -> None:
    """更新 edu_knowledge_graph.task_status 字段。"""
    from sqlalchemy import update as sql_update

    from graphedu.common.models.orm.education import EduKnowledgeGraph

    stmt = (
        sql_update(EduKnowledgeGraph)
        .where(EduKnowledgeGraph.graph_id == graph_id)
        .values(task_status=task_status)
    )
    await db.execute(stmt)
    await db.flush()


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


@celery_app.task(bind=True, name="graphedu.workers.auto_generate_knowledge_graph", max_retries=1)
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
    4. 更新 task_status → success / failed

    Args:
        self: Celery 任务实例（bind=True）。
        course_id: 课程 ID。
        graph_id: 已创建的知识图谱记录 ID。
        graph_name: 图谱名称。
        user_id: 操作用户 ID。
    """

    async def _process():
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

        container = await try_get_container(ContainerMode.WORKER)
        pg_client = await container.postgresql_client()

        # 构造最小化 CurrentUser（仅填充 user_id）
        current_user = CurrentUser(
            permissions=[],
            role_keys=[],
            detail=UserDetail(user=SysUser(user_id=user_id)) if user_id else None,
        )

        async with pg_client.session_context() as db:
            await _update_task_status(graph_id, "processing", db)
        _report_progress(graph_id, 5, "初始化任务")

        try:
            # 2. 查找启用的 GraphRAG 任务
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
            _report_progress(graph_id, 20, "GraphRAG 知识提炼（耗时较长）")
            graph_data = await GraphRAGService.generate_visual_graph(
                graphrag_task_id=enabled_task.task_id,
                chapter_names=chapter_names,
            )
            _report_progress(graph_id, 75, "构建图谱数据")

            # 5. 构建 BO 并直接调用 save_graph_from_extraction
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
            _report_progress(graph_id, 90, "写入章节关联")
            async with pg_client.session_context() as db:
                for node in graph_data.nodes:
                    node_uuid_str = title_to_uuid.get(node.label)
                    if not node_uuid_str or not node.chapter_indices:
                        continue
                    node_uuid = UUID(node_uuid_str)
                    for ch_idx in node.chapter_indices:
                        if ch_idx < len(chapters):
                            await ChapterKnowledgePointMapper.add_link(
                                chapters[ch_idx].chapter_id, node_uuid, db
                            )

            # 7. 更新状态为 success
            async with pg_client.session_context() as db:
                await _update_task_status(graph_id, "success", db)
            _report_progress(graph_id, 100, "完成")

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

        except Exception:
            # 更新状态为 failed
            try:
                async with pg_client.session_context() as db:
                    await _update_task_status(graph_id, "failed", db)
            except Exception:
                logger.exception("更新 task_status=failed 也失败: graph_id=%d", graph_id)
            raise

    try:
        asyncio_run_kwargs = {}
        if sys.platform == "win32":
            asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
        return asyncio.run(_process(), **asyncio_run_kwargs)
    except Exception as e:
        logger.exception(
            "知识图谱自动生成失败: graph_id=%d, course_id=%d, error=%s",
            graph_id,
            course_id,
            e,
        )
        raise self.retry(exc=e, countdown=120) from e
