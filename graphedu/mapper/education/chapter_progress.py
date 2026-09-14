"""章节进度管理 Mapper 层

提供课程整体学习进度计算（基于 edu_student_resource_progress 实时聚合）。

注意：章节维度的进度聚合由物化视图 mv_chapter_progress 提供，相关查询见
StudentCourseMapper（学生课程概览 / 章节进度）与 TeachAnalyticsMapper（教师端
学生章节学习汇总）；本类仅负责课程级整体进度计算。
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ChapterProgressMapper:
    """章节进度数据访问层"""

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
