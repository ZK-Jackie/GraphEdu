"""首页仪表盘服务模块

提供学生端和教师端首页仪表盘的业务逻辑。
"""

from datetime import date
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.orm.education import EduStudent
from graphedu.common.models.vo.educationv2.stats import (
    DailyActiveItemVO,
    DashboardCalendarItemVO,
    DashboardCourseItemVO,
    DashboardWeakPointVO,
    StudentDailyActiveItemVO,
    StudentDashboardSummaryVO,
    TeacherDashboardCourseVO,
    TeacherDashboardRankingVO,
    TeacherDashboardSummaryVO,
)
from graphedu.common.resource.modules.database.oss import AioS3Client
from graphedu.mapper.education.dashboard import DashboardMapper
from graphedu.services.system.upload import UploadService

logger = logging.getLogger(__name__)


class DashboardService:
    """首页仪表盘服务类"""

    # ========================================================================
    # 学生端
    # ========================================================================

    @staticmethod
    async def get_student_summary(query_db: AsyncSession, student_id: int) -> StudentDashboardSummaryVO:
        """获取学生仪表盘总览统计

        :param query_db: 数据库会话
        :param student_id: 学生ID
        :return: 学生仪表盘总览 VO
        """
        total_study_days = await DashboardMapper.get_student_total_study_days(student_id, query_db)
        total_study_minutes = await DashboardMapper.get_student_total_study_minutes(student_id, query_db)
        effective_study_minutes = await DashboardMapper.get_student_effective_study_minutes(student_id, query_db)
        review_study_minutes = await DashboardMapper.get_student_review_study_minutes(student_id, query_db)
        active_course_count = await DashboardMapper.get_student_active_course_count(student_id, query_db)
        consecutive_days = await DashboardMapper.get_student_current_streak(student_id, query_db)

        return StudentDashboardSummaryVO(
            total_study_days=total_study_days,
            total_study_minutes=total_study_minutes,
            effective_study_minutes=effective_study_minutes,
            review_study_minutes=review_study_minutes,
            active_course_count=active_course_count,
            consecutive_days=consecutive_days,
        )

    @staticmethod
    async def get_student_calendar(query_db: AsyncSession, student_id: int, year: int) -> list[DashboardCalendarItemVO]:
        """获取学生学习日历数据

        :param query_db: 数据库会话
        :param student_id: 学生ID
        :param year: 查询年份
        :return: 日历数据列表
        """
        raw_data = await DashboardMapper.get_student_calendar_data(student_id, query_db, year)
        return [DashboardCalendarItemVO(date=row[0][:10], minutes=row[1]) for row in raw_data]

    @staticmethod
    async def get_student_trend(
        query_db: AsyncSession, student_id: int, start_date: date, end_date: date
    ) -> list[StudentDailyActiveItemVO]:
        """获取学生学习趋势数据

        :param query_db: 数据库会话
        :param student_id: 学生ID
        :param start_date: 起始日期
        :param end_date: 结束日期
        :return: 每日活跃数据列表
        """
        raw_data = await DashboardMapper.get_student_trend_data(student_id, query_db, start_date, end_date)
        return [
            StudentDailyActiveItemVO(
                date=row[0][5:10] if len(row[0]) >= 10 else row[0],
                active_minutes=row[1],
            )
            for row in raw_data
        ]

    @staticmethod
    async def get_student_recent_courses(
        query_db: AsyncSession, student_id: int, limit: int, s3_client: AioS3Client
    ) -> list[DashboardCourseItemVO]:
        """获取学生最近学习的课程

        :param query_db: 数据库会话
        :param student_id: 学生ID
        :param limit: 返回数量
        :param s3_client: S3 客户端
        :return: 课程列表
        """
        rows = await DashboardMapper.get_student_recent_courses(student_id, query_db, limit)

        # 批量获取课程封面 URL
        cover_file_ids = [course.cover_file_id for _, course in rows if course.cover_file_id]
        cover_url_map: dict[int, str] = {}
        if cover_file_ids:
            cover_url_map = await UploadService.get_file_url_map(cover_file_ids, query_db, s3_client)

        result = []
        for enrollment, course in rows:
            result.append(
                DashboardCourseItemVO(
                    course_id=course.course_id,
                    course_name=course.course_name,
                    cover_url=cover_url_map.get(course.cover_file_id) if course.cover_file_id else None,
                    progress=enrollment.progress or 0,
                    last_study_time=enrollment.last_study_time,
                )
            )
        return result

    @staticmethod
    async def get_student_weak_points(
        query_db: AsyncSession, student_id: int, limit: int = 5
    ) -> list[DashboardWeakPointVO]:
        """获取学生跨课程薄弱知识点

        :param query_db: 数据库会话
        :param student_id: 学生ID
        :param limit: 返回数量
        :return: 薄弱知识点列表
        """
        rows = await DashboardMapper.get_student_cross_course_weak_points(student_id, query_db, limit)

        # 获取知识点对应的课程名称
        course_ids = list({row.course_id for row in rows if hasattr(row, "course_id")})
        course_name_map: dict[int, str] = {}
        if course_ids:
            from graphedu.common.models.orm.education import EduCourse

            stmt = select(EduCourse.course_id, EduCourse.course_name).where(EduCourse.course_id.in_(course_ids))
            cr = await query_db.execute(stmt)
            course_name_map = {r[0]: r[1] for r in cr.all()}

        # 获取知识点名称
        uuids = [row.node_uuid for row in rows]
        node_name_map: dict[str, str] = {}
        if uuids:
            from graphedu.common.models.orm.education import EduKnowledgePointEmbedding

            stmt = select(EduKnowledgePointEmbedding.node_uuid, EduKnowledgePointEmbedding.title).where(
                EduKnowledgePointEmbedding.node_uuid.in_(uuids)
            )
            cr = await query_db.execute(stmt)
            node_name_map = {str(r[0]): r[1] for r in cr.all()}

        return [
            DashboardWeakPointVO(
                node_uuid=str(row.node_uuid),
                node_name=node_name_map.get(str(row.node_uuid), ""),
                course_name=course_name_map.get(row.course_id, ""),
                total_interaction_count=row.total_interaction_count or 0,
                total_question_count=row.total_question_count or 0,
                total_study_seconds=row.total_study_seconds or 0,
                latest_mastery_level=row.latest_mastery_level or "",
                latest_mastery_score=float(row.latest_mastery_score) if row.latest_mastery_score else None,
                latest_assessed_at=row.latest_assessed_at,
            )
            for row in rows
        ]

    # ========================================================================
    # 教师端
    # ========================================================================

    @staticmethod
    async def _get_student_name_map(student_ids: list[int], query_db: AsyncSession) -> dict[int, str]:
        """批量查询学生姓名映射

        :param student_ids: 学生ID列表
        :param query_db: 数据库会话
        :return: {student_id: real_name} 映射
        """
        if not student_ids:
            return {}
        stmt = select(EduStudent.student_id, EduStudent.real_name).where(EduStudent.student_id.in_(student_ids))
        result = await query_db.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def _get_teacher_course_ids(query_db: AsyncSession, current_user: CurrentUser) -> list[int]:
        """获取教师的课程ID列表（优先关联表，备选 create_by）

        :param query_db: 数据库会话
        :param current_user: 当前用户
        :return: 课程ID列表
        """
        teacher_id = current_user.detail.teacher_info.teacher_id
        course_ids = await DashboardMapper.get_teacher_course_ids(teacher_id, query_db)
        if not course_ids:
            # 回退到 create_by
            user_id = current_user.detail.user.user_id if current_user.detail.user else None
            if user_id:
                course_ids = await DashboardMapper.get_teacher_course_ids_by_create(user_id, query_db)
        return course_ids

    @staticmethod
    async def get_teacher_summary(query_db: AsyncSession, current_user: CurrentUser) -> TeacherDashboardSummaryVO:
        """获取教师仪表盘总览统计

        :param query_db: 数据库会话
        :param current_user: 当前用户
        :return: 教师仪表盘总览 VO
        """
        course_ids = await DashboardService._get_teacher_course_ids(query_db, current_user)
        total_courses = len(course_ids)
        total_students = await DashboardMapper.get_teacher_total_students(course_ids, query_db)
        today_active = await DashboardMapper.get_teacher_today_active_students(course_ids, query_db)
        avg_mastery = await DashboardMapper.get_teacher_avg_mastery(course_ids, query_db)

        return TeacherDashboardSummaryVO(
            total_courses=total_courses,
            total_students=total_students,
            today_active_students=today_active,
            avg_mastery_score=round(avg_mastery, 1) if avg_mastery else None,
        )

    @staticmethod
    async def get_teacher_courses(query_db: AsyncSession, current_user: CurrentUser) -> list[TeacherDashboardCourseVO]:
        """获取教师各课程概览

        :param query_db: 数据库会话
        :param current_user: 当前用户
        :return: 课程概览列表
        """
        course_ids = await DashboardService._get_teacher_course_ids(query_db, current_user)
        overviews = await DashboardMapper.get_teacher_course_overviews(course_ids, query_db)

        return [
            TeacherDashboardCourseVO(
                course_id=ov.course_id,
                course_name=ov.course_name or "",
                student_count=ov.total_student_count or 0,
                avg_mastery_score=round(float(ov.avg_mastery_score or 0), 1),
                quiz_correct_rate=round(float(ov.quiz_correct_rate), 1) if ov.quiz_correct_rate else None,
            )
            for ov in overviews
        ]

    @staticmethod
    async def get_teacher_rankings(
        query_db: AsyncSession, current_user: CurrentUser, limit: int = 10
    ) -> list[TeacherDashboardRankingVO]:
        """获取教师跨课程学生排名

        :param query_db: 数据库会话
        :param current_user: 当前用户
        :param limit: 返回数量
        :return: 学生排名列表
        """
        course_ids = await DashboardService._get_teacher_course_ids(query_db, current_user)
        rankings = await DashboardMapper.get_teacher_cross_course_rankings(course_ids, query_db, limit)

        # 批量查询学生姓名
        student_ids = list({r.student_id for r in rankings})
        student_name_map = await DashboardService._get_student_name_map(student_ids, query_db)

        return [
            TeacherDashboardRankingVO(
                student_id=r.student_id,
                student_name=student_name_map.get(r.student_id, ""),
                course_name=r.course_name or "",
                mastery_percentile=float(r.mastery_percentile),
                avg_mastery_score=float(r.avg_mastery_score) if r.avg_mastery_score else None,
            )
            for r in rankings
        ]

    @staticmethod
    async def get_teacher_trend(
        query_db: AsyncSession,
        current_user: CurrentUser,
        days: int = 30,
        start_date: date | None = None,
        end_date: date | None = None,
        course_id: int | None = None,
    ) -> list[DailyActiveItemVO]:
        """获取教师课程互动趋势数据

        :param query_db: 数据库会话
        :param current_user: 当前用户
        :param days: 查询天数（当 start_date/end_date 未提供时使用）
        :param start_date: 起始日期（可选，优先于 days）
        :param end_date: 结束日期（可选，优先于 days）
        :param course_id: 课程ID（可选，不传则查全部课程）
        :return: 每日活跃数据列表
        """
        if course_id is not None:
            course_ids = [course_id]
        else:
            course_ids = await DashboardService._get_teacher_course_ids(query_db, current_user)
        raw_data = await DashboardMapper.get_teacher_trend_data(course_ids, query_db, days, start_date, end_date)
        return [
            DailyActiveItemVO(
                date=row[0][5:10] if len(row[0]) >= 10 else row[0],
                count=row[1],
            )
            for row in raw_data
        ]
