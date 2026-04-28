"""教师工作台分析服务模块

提供教师查看课程学生数据、学习分析等功能。

职责：
1. 验证教师对课程的访问权限。
2. 聚合多个 Mapper 的查询结果。
3. 将 ORM 数据转换为 VO 返回。
"""

import logging
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.orm.education import EduStudent
from graphedu.common.models.vo.educationv2.chapter import ChapterCompletionItemVO
from graphedu.common.models.vo.educationv2.course import CourseStudentsResultVO, CourseStudentStatsVO, CourseStudentVO
from graphedu.common.models.vo.educationv2.stats import (
    CourseAnalyticsVO,
    ProgressDistributionItemVO,
    StudentChapterDetailResultVO,
    StudentChapterExerciseDetailVO,
    StudentChapterLearningItemVO,
    StudentChapterLearningResultVO,
    StudentChapterMasteryDetailVO,
    StudentChapterResourceDetailVO,
    StudentRankingItemVO,
)
from graphedu.mapper.education.teach_analytics import TeachAnalyticsMapper
from graphedu.services.education.course import _check_course_permission

logger = logging.getLogger(__name__)

_RANGE_LABELS = ["0-20%", "21-40%", "41-60%", "61-80%", "81-100%"]


class TeachAnalyticsService:
    """教师工作台分析服务"""

    @staticmethod
    async def get_course_students(
        query_db: AsyncSession,
        course_id: int,
        current_user: CurrentUser,
        page: int = 1,
        size: int = 20,
    ) -> CourseStudentsResultVO:
        """获取课程学生列表及汇总统计数据。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            current_user: 当前用户（需为该课程教师）。
            page: 页码。
            size: 每页数量。

        Returns:
            CourseStudentsResultVO: 学生列表 + 统计数据 + 总数。
        """
        await _check_course_permission(course_id, current_user, query_db)

        rows, total = await TeachAnalyticsMapper.get_course_students(course_id, query_db, page, size)

        students: list[CourseStudentVO] = []
        for enrollment, student in rows:
            students.append(
                CourseStudentVO(
                    enrollment_id=enrollment.id,
                    student_id=student.student_id,
                    real_name=student.real_name,
                    student_no=student.student_no,
                    class_name=student.class_name,
                    faculty=student.faculty,
                    gender=student.gender,
                    avatar_url=None,
                    enroll_time=enrollment.enroll_time,
                    progress=enrollment.progress or 0,
                    last_study_time=enrollment.last_study_time,
                    status=student.status,
                )
            )

        raw_stats = await TeachAnalyticsMapper.get_course_student_stats(course_id, query_db)
        stats = CourseStudentStatsVO(
            total_students=raw_stats.get("total_students", 0),
            average_progress=round(raw_stats.get("average_progress") or 0, 1),
            completed_students=raw_stats.get("completed_students", 0),
            today_active=raw_stats.get("today_active", 0),
        )
        return CourseStudentsResultVO(students=students, stats=stats, total=total)

    @staticmethod
    async def get_course_analytics(
        query_db: AsyncSession,
        course_id: int,
        current_user: CurrentUser,
        time_range: Literal["week", "month", "all"] = "month",
    ) -> CourseAnalyticsVO:
        """获取课程综合数据分析（消费 SQL 视图）。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            current_user: 当前用户（需为该课程教师）。
            time_range: 时间范围（week/month/all）。

        Returns:
            CourseAnalyticsVO: 综合分析数据。
        """
        await _check_course_permission(course_id, current_user, query_db)

        # 顺序查询：课程概览 + 章节统计 + 进度分布
        # 注意：AsyncSession 不支持并发查询，必须顺序执行
        overview = await TeachAnalyticsMapper.get_course_learning_overview(course_id, query_db)
        chapter_stats_list = await TeachAnalyticsMapper.get_course_chapter_stats(course_id, query_db)
        dist_rows = await TeachAnalyticsMapper.get_progress_distribution(course_id, query_db)

        # 章节完成率 — Mapper 返回 dict 列表
        if chapter_stats_list:
            chapter_completion = [
                ChapterCompletionItemVO(
                    chapter_id=stat["chapter_id"],
                    chapter=stat.get("chapter_name") or f"章节 {stat['chapter_id']}",
                    completion=round(float(stat.get("avg_mastery_score") or 0), 1),
                    students=stat.get("student_count", 0) or 0,
                )
                for stat in chapter_stats_list
            ]
        else:
            chapter_rows = await TeachAnalyticsMapper.get_chapter_completion(course_id, query_db)
            chapter_completion = [
                ChapterCompletionItemVO(
                    chapter_id=row[0],
                    chapter=row[1] or f"章节 {row[0]}",
                    completion=round(row[2] or 0, 1),
                    students=row[3] or 0,
                )
                for row in chapter_rows
            ]

        # 进度分布
        progress_distribution = [
            ProgressDistributionItemVO(
                range=_RANGE_LABELS[i],
                count=row.get("count", 0) if isinstance(row, dict) else (getattr(row, "count", 0) or 0),
            )
            for i, row in enumerate(dist_rows)
        ]

        # 从聚合数据填充扩展字段 — Mapper 返回 dict
        if overview:
            total_study_minutes = round((overview.get("total_study_seconds") or 0) / 60)
            return CourseAnalyticsVO(
                total_students=overview.get("total_student_count", 0) or 0,
                active_students=overview.get("active_student_count_30d", 0) or 0,
                average_progress=0,
                total_study_time=total_study_minutes,
                chapter_completion=chapter_completion,
                daily_active=[],
                progress_distribution=progress_distribution,
                total_event_count=overview.get("total_event_count", 0) or 0,
                total_question_count=overview.get("total_question_count", 0) or 0,
                total_quiz_count=overview.get("total_quiz_count", 0) or 0,
                quiz_correct_rate=round(float(overview.get("quiz_correct_rate") or 0), 1),
                avg_mastery_score=(
                    float(overview["avg_mastery_score"])
                    if overview.get("avg_mastery_score") is not None
                    else None
                ),
                high_mastery_count=overview.get("high_mastery_count", 0) or 0,
                medium_mastery_count=overview.get("medium_mastery_count", 0) or 0,
                low_mastery_count=overview.get("low_mastery_count", 0) or 0,
                nodes_touched=overview.get("nodes_touched", 0) or 0,
            )

        # 无数据时回退
        return CourseAnalyticsVO(
            chapter_completion=chapter_completion,
            progress_distribution=progress_distribution,
        )

    @staticmethod
    async def get_course_rankings(
        query_db: AsyncSession,
        course_id: int,
        current_user: CurrentUser,
    ) -> list[StudentRankingItemVO]:
        """获取课程学生排名列表。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            current_user: 当前用户（需为该课程教师）。

        Returns:
            list[StudentRankingItemVO]: 学生排名列表。
        """
        await _check_course_permission(course_id, current_user, query_db)

        ranking_rows = await TeachAnalyticsMapper.get_course_student_rankings(course_id, query_db)

        # 批量查询学生姓名 — Mapper 返回 dict 列表
        student_ids = list({row["student_id"] for row in ranking_rows})
        student_name_map: dict[int, str] = {}
        if student_ids:
            stmt = select(EduStudent.student_id, EduStudent.real_name).where(
                EduStudent.student_id.in_(student_ids)
            )
            cr = await query_db.execute(stmt)
            student_name_map = {r[0]: r[1] for r in cr.all()}

        return [
            StudentRankingItemVO(
                student_id=row["student_id"],
                student_name=student_name_map.get(row["student_id"], ""),
                total_event_count=row.get("total_event_count", 0) or 0,
                question_count=row.get("question_count", 0) or 0,
                quiz_count=row.get("quiz_count", 0) or 0,
                quiz_correct_rate=float(row["quiz_correct_rate"]) if row.get("quiz_correct_rate") is not None else None,
                avg_mastery_score=float(row["avg_mastery_score"]) if row.get("avg_mastery_score") is not None else None,
                chapters_touched=row.get("chapters_touched", 0) or 0,
                chapter_coverage_rate=round(float(row.get("chapter_coverage_rate") or 0), 2),
                nodes_touched=row.get("nodes_touched", 0) or 0,
                node_coverage_rate=round(float(row.get("node_coverage_rate") or 0), 2),
                total_study_seconds=row.get("total_study_seconds", 0) or 0,
                study_days=row.get("study_days", 0) or 0,
                mastery_percentile=round(float(row.get("mastery_percentile") or 0), 4),
            )
            for row in ranking_rows
        ]

    @staticmethod
    async def get_student_chapter_learning(
        db: AsyncSession,
        course_id: int,
        student_id: int,
        current_user: CurrentUser,
    ) -> StudentChapterLearningResultVO:
        """获取学生在课程中的章节学习汇总。

        复用 StudentCourseMapper 的物化视图查询，确保与学生端一致的数据源。

        :param db: 数据库会话
        :param course_id: 课程ID
        :param student_id: 学生ID
        :param current_user: 当前用户
        :return: 章节学习汇总结果
        """
        from graphedu.mapper.education.student_course import StudentCourseMapper

        await _check_course_permission(course_id, current_user, db)

        raw = await StudentCourseMapper.get_student_chapter_detail_progress(student_id, course_id, db)

        total_chapters = len(raw)
        completed_chapters = sum(1 for r in raw if r.get("is_completed") == "Y")

        chapters = [
            StudentChapterLearningItemVO(
                chapter_id=r["chapter_id"],
                chapter_name=r["chapter_name"],
                chapter_no=r["chapter_no"],
                parent_id=r["parent_id"],
                completion_rate=r.get("completion_rate", 0),
                is_completed=r.get("is_completed", "N"),
                last_study_time=r.get("last_visit_time"),
            )
            for r in raw
        ]

        return StudentChapterLearningResultVO(
            student_id=student_id,
            course_id=course_id,
            chapters=chapters,
            total_chapters=total_chapters,
            completed_chapters=completed_chapters,
        )

    @staticmethod
    async def get_student_chapter_detail(
        db: AsyncSession,
        course_id: int,
        student_id: int,
        chapter_id: int,
        detail_type: str,
        current_user: CurrentUser,
        page: int = 1,
        size: int = 20,
    ) -> StudentChapterDetailResultVO:
        """获取学生在某章节的可展开详情（资料/答题/知识点掌握）。

        :param db: 数据库会话
        :param course_id: 课程ID
        :param student_id: 学生ID
        :param chapter_id: 章节ID
        :param detail_type: 详情类型 (resources/exercises/mastery)
        :param current_user: 当前用户
        :param page: 页码
        :param size: 每页数量
        :return: 详情结果
        """
        await _check_course_permission(course_id, current_user, db)

        if detail_type == "resources":
            rows, total = await TeachAnalyticsMapper.get_student_chapter_resources(
                student_id, chapter_id, db, page, size
            )
            items = [
                StudentChapterResourceDetailVO(
                    progress_id=row.progress_id,
                    resource_id=row.resource_id,
                    resource_name=row.resource_name,
                    resource_type=row.resource_type,
                    completion_rate=row.completion_rate,
                    is_completed=row.is_completed,
                    view_count=row.view_count,
                    total_duration=row.total_duration,
                    last_view_time=row.last_view_time,
                )
                for row in rows
            ]
        elif detail_type == "exercises":
            rows, total = await TeachAnalyticsMapper.get_student_chapter_exercises(
                student_id, course_id, chapter_id, db, page, size
            )
            items = [
                StudentChapterExerciseDetailVO(
                    attempt_id=row.attempt_id,
                    exercise_id=row.exercise_id,
                    student_answer=row.student_answer,
                    is_correct=row.is_correct,
                    time_spent=row.time_spent,
                    attempt_time=row.attempt_time,
                )
                for row in rows
            ]
        elif detail_type == "mastery":
            rows, total = await TeachAnalyticsMapper.get_student_chapter_mastery(
                student_id, course_id, chapter_id, db, page, size
            )
            items = [
                StudentChapterMasteryDetailVO(
                    mastery_id=row.mastery_id,
                    node_uuid=str(row.node_uuid),
                    node_title=row.node_title,
                    mastery_score=float(row.mastery_score) if row.mastery_score else None,
                    mastery_level=row.mastery_level,
                    assessed_at=row.assessed_at,
                )
                for row in rows
            ]
        else:
            return StudentChapterDetailResultVO(detail_type=detail_type, items=[], total=0)

        return StudentChapterDetailResultVO(detail_type=detail_type, items=items, total=total)
