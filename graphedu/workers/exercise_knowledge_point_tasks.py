"""习题-知识点候选推荐 Celery 任务。

题目生成后异步触发，为每道题用混合检索推荐候选知识点，写入
edu_exercise_knowledge_point_suggestion（不绑定）。已有 manual 绑定的题跳过，
不覆盖教师决策。教师确认后由 API 写入 edu_exercise_knowledge_point。
"""

import asyncio
import logging
import sys

from graphedu.common.resource import ContainerMode, try_get_container
from graphedu.workers.celery import celery_app

logger = logging.getLogger(__name__)

# 每题推荐的候选知识点数量
_TOP_K = 3


@celery_app.task(name="graphedu.workers.recommend_exercise_knowledge_points")
def recommend_exercise_knowledge_points(exercise_ids: list[int]):
    """为指定题目推荐候选知识点（仅写候选表，不绑定）。

    对每道题：
    1. 若已有 manual 绑定 → 跳过（尊重教师决策）；
    2. 否则取题干文本，混合检索 top-K 知识点，覆盖写入候选表。

    Args:
        exercise_ids: 习题 ID 列表
    """

    async def _process():
        from uuid import UUID

        from sqlalchemy import select

        from graphedu.common.models.orm.education import EduCourseExercise
        from graphedu.mapper.education.exercise_knowledge_point import ExerciseKnowledgePointMapper
        from graphedu.mapper.education.exercise_knowledge_point_suggestion import (
            ExerciseKnowledgePointSuggestionMapper,
        )
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        container = await try_get_container(ContainerMode.WORKER)
        pg_client = await container.postgresql_client()

        recommended = 0
        skipped = 0
        for exercise_id in exercise_ids:
            try:
                # 1. 查题目（取 course_id + 题干文本）
                async with pg_client.session_context() as db:
                    stmt = select(EduCourseExercise).where(EduCourseExercise.exercise_id == exercise_id)
                    exercise = (await db.execute(stmt)).scalars().first()

                if not exercise:
                    logger.warning("推荐跳过：题目不存在 exercise_id=%s", exercise_id)
                    skipped += 1
                    continue

                # 2. 已有 manual 绑定 → 跳过，不覆盖教师决策
                async with pg_client.session_context() as db:
                    if await ExerciseKnowledgePointMapper.has_manual_association(exercise_id, db):
                        logger.info("推荐跳过：题目已有手动绑定 exercise_id=%s", exercise_id)
                        skipped += 1
                        continue

                # 3. 提取题干文本
                text = _extract_exercise_text(exercise)
                if not text:
                    logger.info("推荐跳过：题目无可用文本 exercise_id=%s", exercise_id)
                    skipped += 1
                    continue

                # 4. 混合检索候选知识点
                merged_nodes, _, _ = await SyllabusGraphService.search_nodes_hybrid(
                    pg_client=pg_client,
                    course_id=exercise.course_id,
                    keyword=text[:200],  # 截断避免检索输入过长
                    keyword_limit=_TOP_K,
                    vector_limit=_TOP_K,
                )
                if not merged_nodes:
                    logger.info("推荐跳过：未检索到候选知识点 exercise_id=%s", exercise_id)
                    skipped += 1
                    continue

                # 5. 覆盖写入候选（relevance_score 用检索排名归一化，越靠前越高）
                items: list[tuple[UUID, float]] = []
                for idx, node in enumerate(merged_nodes[:_TOP_K]):
                    try:
                        uuid_obj = UUID(node.uuid) if isinstance(node.uuid, str) else node.uuid
                    except (ValueError, AttributeError, TypeError):
                        continue
                    score = round(1.0 - idx * (1.0 / _TOP_K), 4)
                    items.append((uuid_obj, max(score, 0.0)))

                if items:
                    async with pg_client.session_context() as db:
                        await ExerciseKnowledgePointSuggestionMapper.replace_suggestions(exercise_id, items, db)
                        await db.commit()
                    recommended += 1
                else:
                    skipped += 1
            except Exception:
                logger.exception("推荐候选知识点失败: exercise_id=%s", exercise_id)
                continue

        logger.info(
            "题目知识点推荐完成: 共 %d 题, 推荐 %d, 跳过 %d",
            len(exercise_ids),
            recommended,
            skipped,
        )
        return {"total": len(exercise_ids), "recommended": recommended, "skipped": skipped}

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_process(), **asyncio_run_kwargs)


def _extract_exercise_text(exercise) -> str:
    """从 EduCourseExercise.exercise（JSONB）提取用于检索的文本。"""
    content = exercise.exercise
    if not isinstance(content, dict):
        return ""
    parts = [str(content.get("title") or ""), str(content.get("content") or "")]
    return "\n".join(p for p in parts if p).strip()
