"""题库查询 Mapper 层。

提供基于章节向量匹配的题目查询功能。
"""

import logging

from sqlalchemy import func, select

from graphedu.common.models import SystemConstants
from graphedu.common.models.orm.education import EduChapter, EduCourseExercise
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 1024  # EduChapter.embedding 向量维度


class ExerciseQueryMapper:
    """题库查询数据访问层"""

    @staticmethod
    async def match_chapters_by_embedding(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        query_embedding: list[float],
        limit: int = 3,
        max_distance: float = 0.5,
    ) -> list[int]:
        """基于向量相似度匹配章节，返回 chapter_id 列表。

        :param pg_client: PostgreSQL 异步客户端实例
        :param course_id: 课程ID
        :param query_embedding: 查询文本的 embedding 向量
        :param limit: 返回章节数量上限
        :param max_distance: cosine 距离阈值，超过此值的章节将被排除
        :return: 按 cosine 距离排序的 chapter_id 列表
        """
        if not query_embedding or len(query_embedding) != _EMBEDDING_DIM:
            logger.warning(
                "Invalid embedding dimension: expected %d, got %s",
                _EMBEDDING_DIM,
                len(query_embedding) if query_embedding else 0,
            )
            return []

        async with pg_client.session_context() as session:
            chapter_distance = EduChapter.embedding.cosine_distance(query_embedding)

            stmt = (
                select(EduChapter.chapter_id)
                .where(
                    EduChapter.course_id == course_id,
                    EduChapter.status == SystemConstants.Status.NORMAL,
                    EduChapter.embedding.is_not(None),
                    chapter_distance <= max_distance,
                )
                .order_by(chapter_distance.asc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_exercises_by_ids(
        pg_client: AsyncPostgresqlClient,
        exercise_ids: list[int],
    ) -> list[EduCourseExercise]:
        """根据题目ID列表查询题目。

        :param pg_client: PostgreSQL 异步客户端实例
        :param exercise_ids: 题目 ID 列表
        :return: 题目列表
        """
        if not exercise_ids:
            return []

        async with pg_client.session_context() as session:
            stmt = select(EduCourseExercise).where(
                EduCourseExercise.exercise_id.in_(exercise_ids),
                EduCourseExercise.status == SystemConstants.Status.NORMAL,
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_random_exercise(
        pg_client: AsyncPostgresqlClient,
        chapter_id: int,
        limit: int = 1,
    ) -> list[EduCourseExercise]:
        """从指定章节的题库中随机选取题目。

        :param pg_client: PostgreSQL 异步客户端实例
        :param chapter_id: 章节ID
        :param limit: 返回题目数量上限
        :return: 随机选取的题目列表
        """
        async with pg_client.session_context() as session:
            stmt = (
                select(EduCourseExercise)
                .where(
                    EduCourseExercise.chapter_id == chapter_id,
                    EduCourseExercise.status == SystemConstants.Status.NORMAL,
                )
                .order_by(func.random())
                .limit(limit)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())
