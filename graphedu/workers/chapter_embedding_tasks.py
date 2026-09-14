"""章节向量嵌入填充 Celery 任务。

遍历课程的叶子章节（parent_id != 0），生成 embedding 写入 edu_chapter.embedding
字段（Vector(1024)）。供知识点图谱按章节向量检索（visualize_graph_query）与
按章节向量匹配题目（exercise_query）使用。

包含存量回填（按课程）和定时增量同步（扫描所有课程）两种任务，结构与
populate_knowledge_point_embeddings 保持一致。
"""

import asyncio
import logging
import sys

from graphedu.common.resource import ContainerMode, try_get_container
from graphedu.workers.celery import celery_app

logger = logging.getLogger(__name__)

_BATCH_SIZE = 32
_MAX_COURSES_PER_RUN = 50
"""sync_all 每轮最多派发的课程数，避免瞬间堆积压垮 worker / 触发 embedding API 限流。
超出部分由下轮 beat 补偿（populate 幂等，重复执行无害）。"""


@celery_app.task(name="graphedu.workers.populate_chapter_embeddings")
def populate_chapter_embeddings(course_id: int):
    """为指定课程的叶子章节生成 embedding 并写入 edu_chapter.embedding。

    Args:
        course_id: 课程 ID
    """

    async def _process():
        from graphedu.mapper.education.chapter import ChapterMapper
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        container = await try_get_container(ContainerMode.WORKER)
        pg_client = await container.postgresql_client()

        # 1. 获取未生成 embedding 的叶子章节
        async with pg_client.session_context() as db_session:
            pending = await ChapterMapper.get_leaf_chapters_without_embedding(course_id, db_session)

        if not pending:
            logger.info("课程 %s 章节无 embedding 待填充，跳过", course_id)
            return {"course_id": course_id, "status": "skipped", "reason": "全部已填充"}

        # 2. 批量生成 embedding 并写入
        embedding_llm = SyllabusGraphService._get_embedding_llm()
        texts = [f"{c.chapter_name}\n{c.description or ''}".strip() for c in pending]
        updated = 0

        for i in range(0, len(texts), _BATCH_SIZE):
            batch_texts = texts[i : i + _BATCH_SIZE]
            batch_chapters = pending[i : i + _BATCH_SIZE]

            try:
                embeddings = await embedding_llm.aembed_documents(batch_texts)
            except Exception as e:
                logger.exception(
                    "生成章节 embedding 失败: course_id=%s, batch=%d-%d", course_id, i, i + len(batch_texts)
                )
                logger.error("错误: %s", e)
                continue

            async with pg_client.session_context() as db_session:
                for chapter, embedding in zip(batch_chapters, embeddings, strict=True):
                    try:
                        await ChapterMapper.update_embedding(chapter.chapter_id, embedding, db_session)
                        updated += 1
                    except Exception as e:
                        logger.exception("写入章节 embedding 失败: chapter_id=%s", chapter.chapter_id)
                        logger.error("错误: %s", e)
                await db_session.commit()

        logger.info("课程 %s 章节 embedding 填充完成: 待填充 %d, 成功 %d", course_id, len(pending), updated)
        return {"course_id": course_id, "status": "ok", "total": len(pending), "updated": updated}

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_process(), **asyncio_run_kwargs)


@celery_app.task(name="graphedu.workers.sync_all_chapter_embeddings")
def sync_all_chapter_embeddings():
    """定时扫描所有课程，为缺失 embedding 的叶子章节自动补全。

    由 Celery Beat 触发。对每个课程派发 populate_chapter_embeddings 子任务。
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
            logger.info("无活跃课程，跳过章节 embedding 同步")
            return {"status": "skipped", "reason": "无活跃课程", "dispatched": 0}

        # 限流：每轮最多派发 _MAX_COURSES_PER_RUN 个，超出下轮 beat 补偿。
        to_dispatch = course_ids[:_MAX_COURSES_PER_RUN]
        skipped = len(course_ids) - len(to_dispatch)
        for cid in to_dispatch:
            populate_chapter_embeddings.apply_async(args=[cid])

        logger.info(
            "章节 embedding 定时同步: 扫描 %d 个课程, 派发 %d 个任务, 跳过 %d 个(下轮补偿)",
            len(course_ids),
            len(to_dispatch),
            skipped,
        )
        return {
            "status": "ok",
            "total_courses": len(course_ids),
            "dispatched": len(to_dispatch),
            "skipped": skipped,
        }

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_scan(), **asyncio_run_kwargs)
