"""章节进度管理 Mapper 层

通过 PostgreSQL 物化视图 mv_chapter_progress 查询章节进度聚合数据。
物化视图由 edu_student_resource_progress 自动聚合，Service 层负责刷新。
"""

from collections.abc import Sequence
from datetime import datetime, time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.educationv2.stats import ChapterProgressQueryDTO

_MV = "mv_chapter_progress"

# 物化视图行字段映射（用于将 Row 转换为 dict）
_MV_COLUMNS = (
    "student_id",
    "course_id",
    "chapter_id",
    "completion_rate",
    "is_completed",
    "first_visit_time",
    "last_visit_time",
    "complete_time",
)


def _row_to_dict(row: Any) -> dict[str, Any]:
    """将 SQLAlchemy Row 转换为 dict。"""
    return dict(zip(_MV_COLUMNS, row, strict=True))


class ChapterProgressMapper:
    """章节进度数据访问层（物化视图查询）"""

    @staticmethod
    async def get_by_student_and_chapter(
        student_id: int, chapter_id: int, db_session: AsyncSession
    ) -> dict[str, Any] | None:
        """根据学生ID和章节ID查询进度

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param chapter_id: 章节ID
        :return: 进度字典或 None
        """
        stmt = text(
            f"SELECT {', '.join(_MV_COLUMNS)} FROM {_MV} WHERE student_id = :student_id AND chapter_id = :chapter_id"
        )
        result = await db_session.execute(stmt, {"student_id": student_id, "chapter_id": chapter_id})
        row = result.first()
        return _row_to_dict(row) if row else None

    @staticmethod
    async def get_progress_list(
        db: AsyncSession, query_object: ChapterProgressQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[dict[str, Any]], int]:
        """根据查询参数获取章节进度列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组
        """
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if query_object.student_id is not None:
            conditions.append("student_id = :student_id")
            params["student_id"] = query_object.student_id
        if query_object.chapter_id is not None:
            conditions.append("chapter_id = :chapter_id")
            params["chapter_id"] = query_object.chapter_id
        if query_object.is_completed:
            conditions.append("is_completed = :is_completed")
            params["is_completed"] = query_object.is_completed
        if query_object.begin_time and query_object.end_time:
            conditions.append("first_visit_time BETWEEN :begin_time AND :end_time")
            params["begin_time"] = datetime.combine(query_object.begin_time, time(0, 0, 0))
            params["end_time"] = datetime.combine(query_object.end_time, time(23, 59, 59))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 获取总数
        count_sql = f"SELECT COUNT(*) FROM {_MV} {where_clause}"
        total_result = await db.execute(text(count_sql), params)
        total = total_result.scalar() or 0

        # 获取数据
        data_sql = f"SELECT {', '.join(_MV_COLUMNS)} FROM {_MV} {where_clause} ORDER BY last_visit_time DESC"
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            data_sql += " LIMIT :limit OFFSET :offset"
            params["limit"] = query_object.size
            params["offset"] = offset

        result = await db.execute(text(data_sql), params)
        rows = [_row_to_dict(row) for row in result.all()]

        return rows, total

    @staticmethod
    async def get_progresses_by_student_id(student_id: int, db_session: AsyncSession) -> list[dict[str, Any]]:
        """根据学生ID获取所有进度列表

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :return: 进度字典列表
        """
        stmt = text(
            f"SELECT {', '.join(_MV_COLUMNS)} FROM {_MV} WHERE student_id = :student_id ORDER BY last_visit_time DESC"
        )
        result = await db_session.execute(stmt, {"student_id": student_id})
        return [_row_to_dict(row) for row in result.all()]

    @staticmethod
    async def get_progresses_by_chapter_id(chapter_id: int, db_session: AsyncSession) -> list[dict[str, Any]]:
        """根据章节ID获取所有进度列表

        :param db_session: 数据库会话
        :param chapter_id: 章节ID
        :return: 进度字典列表
        """
        stmt = text(
            f"SELECT {', '.join(_MV_COLUMNS)} FROM {_MV} WHERE chapter_id = :chapter_id ORDER BY completion_rate DESC"
        )
        result = await db_session.execute(stmt, {"chapter_id": chapter_id})
        return [_row_to_dict(row) for row in result.all()]

    @staticmethod
    async def calculate_course_progress(student_id: int, course_id: int, db_session: AsyncSession) -> int:
        """计算学生课程的整体学习进度（课程完成百分比）

        公式：SUM(已读资料的 completion_rate) / 课程资料总数 * 100
        未打开的资料不进入分子，但计入分母，从而反映真实完成比例。

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param course_id: 课程ID
        :return: 整体进度（0-100）
        """
        stmt = text("""
            SELECT COALESCE(FLOOR(
                COALESCE(SUM(rp.completion_rate), 0)::NUMERIC /
                NULLIF((
                    SELECT COUNT(*)
                    FROM edu_resource r
                    JOIN edu_chapter ch ON ch.chapter_id = r.chapter_id
                    WHERE ch.course_id = :course_id AND r.status != '2' AND ch.status != '2'
                ), 0)
            ), 0)::INT
            FROM edu_student_resource_progress rp
            WHERE rp.student_id = :student_id
              AND rp.course_id = :course_id
              AND rp.status != '2'
        """)
        result = await db_session.execute(stmt, {"student_id": student_id, "course_id": course_id})
        return result.scalar() or 0
