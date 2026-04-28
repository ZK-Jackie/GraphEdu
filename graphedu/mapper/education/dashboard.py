"""首页仪表盘 Mapper 层

查询基础表进行聚合统计，为首页仪表盘提供数据。
替代原 SQL 视图查询，使用 SQLAlchemy Core 直接聚合。
"""

from datetime import date, timedelta
from types import SimpleNamespace

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import (
    EduCourse,
    EduCourseExercise,
    EduCourseTeacher,
    EduExerciseAttempt,
    EduStudentCourse,
    EduStudentLearningEvent,
    EduStudentMastery,
)


def _compute_streaks(study_dates: list[date]) -> tuple[int, int]:
    """从学习日期列表计算当前连续天数和最长连续天数。

    :param study_dates: 去重后的学习日期列表
    :return: (current_streak, longest_streak)
    """
    if not study_dates:
        return 0, 0
    sorted_dates = sorted(set(study_dates))
    current = longest = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    # 当前连续仅当最后日期是今天或昨天时有效
    today = date.today()
    if sorted_dates[-1] < today - timedelta(days=1):
        current = 0
    return current, longest


class DashboardMapper:
    """首页仪表盘数据访问层"""

    # ========================================================================
    # 学生端
    # ========================================================================

    @staticmethod
    async def get_student_total_study_days(student_id: int, db: AsyncSession) -> int:
        """获取学生跨课程总学习天数（按日期去重）"""
        stmt = select(func.count(func.distinct(cast(EduStudentLearningEvent.event_time, Date)))).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.status == "0",
        )
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_student_total_study_minutes(student_id: int, db: AsyncSession) -> int:
        """获取学生跨课程总学习时长（分钟）"""
        stmt = select(func.coalesce(func.sum(EduStudentLearningEvent.duration_seconds), 0)).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.status == "0",
        )
        total_seconds = (await db.execute(stmt)).scalar() or 0
        return round(total_seconds / 60)

    @staticmethod
    async def get_student_effective_study_minutes(student_id: int, db: AsyncSession) -> int:
        """获取学生跨课程有效学习时长（分钟），优先使用 effective_duration_seconds"""
        stmt = select(
            func.coalesce(
                func.sum(
                    func.coalesce(
                        EduStudentLearningEvent.effective_duration_seconds, EduStudentLearningEvent.duration_seconds
                    )
                ),
                0,
            )
        ).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.status == "0",
        )
        total_seconds = (await db.execute(stmt)).scalar() or 0
        return round(total_seconds / 60)

    @staticmethod
    async def get_student_review_study_minutes(student_id: int, db: AsyncSession) -> int:
        """获取学生跨课程复习时长（分钟）"""
        stmt = select(
            func.coalesce(
                func.sum(
                    func.coalesce(
                        EduStudentLearningEvent.effective_duration_seconds, EduStudentLearningEvent.duration_seconds
                    )
                ),
                0,
            )
        ).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.is_review == True,  # noqa: E712
            EduStudentLearningEvent.status == "0",
        )
        total_seconds = (await db.execute(stmt)).scalar() or 0
        return round(total_seconds / 60)

    @staticmethod
    async def get_student_active_course_count(student_id: int, db: AsyncSession) -> int:
        """获取学生在修课程数"""
        stmt = select(func.count()).where(EduStudentCourse.student_id == student_id)
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def _get_student_study_dates(student_id: int, db: AsyncSession) -> list[date]:
        """获取学生所有去重学习日期（用于连续天数计算）"""
        stmt = select(func.distinct(cast(EduStudentLearningEvent.event_time, Date))).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.status == "0",
        )
        return [row[0] for row in (await db.execute(stmt)).all()]

    @staticmethod
    async def get_student_max_streak(student_id: int, db: AsyncSession) -> int:
        """获取学生跨课程最长连续学习天数"""
        dates = await DashboardMapper._get_student_study_dates(student_id, db)
        _, longest = _compute_streaks(dates)
        return longest

    @staticmethod
    async def get_student_current_streak(student_id: int, db: AsyncSession) -> int:
        """获取学生跨课程当前连续学习天数"""
        dates = await DashboardMapper._get_student_study_dates(student_id, db)
        current, _ = _compute_streaks(dates)
        return current

    @staticmethod
    async def get_student_calendar_data(student_id: int, db: AsyncSession, year: int) -> list[tuple[str, int]]:
        """获取学生日历热力图数据（跨课程按日期聚合）"""
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        stmt = (
            select(
                cast(EduStudentLearningEvent.event_time, Date).label("study_date"),
                func.coalesce(func.sum(EduStudentLearningEvent.duration_seconds), 0),
            )
            .where(
                EduStudentLearningEvent.student_id == student_id,
                EduStudentLearningEvent.event_time >= start,
                EduStudentLearningEvent.event_time <= end,
                EduStudentLearningEvent.status == "0",
            )
            .group_by(cast(EduStudentLearningEvent.event_time, Date))
            .order_by(cast(EduStudentLearningEvent.event_time, Date))
        )
        return [(str(row[0]), round(row[1] / 60)) for row in (await db.execute(stmt)).all()]

    @staticmethod
    async def get_student_trend_data(
        student_id: int, db: AsyncSession, start_date: date, end_date: date
    ) -> list[tuple[str, int]]:
        """获取学生指定日期范围每日学习活跃分钟（跨课程）"""
        stmt = (
            select(
                cast(EduStudentLearningEvent.event_time, Date).label("study_date"),
                func.coalesce(func.sum(EduStudentLearningEvent.duration_seconds), 0),
            )
            .where(
                EduStudentLearningEvent.student_id == student_id,
                EduStudentLearningEvent.event_time >= start_date,
                EduStudentLearningEvent.event_time <= end_date,
                EduStudentLearningEvent.status == "0",
            )
            .group_by(cast(EduStudentLearningEvent.event_time, Date))
            .order_by(cast(EduStudentLearningEvent.event_time, Date))
        )
        return [(str(row[0]), round(row[1] / 60)) for row in (await db.execute(stmt)).all()]

    @staticmethod
    async def get_student_recent_courses(student_id: int, db: AsyncSession, limit: int = 6) -> list[tuple]:
        """获取学生最近学习的课程"""
        stmt = (
            select(EduStudentCourse, EduCourse)
            .join(EduCourse, EduStudentCourse.course_id == EduCourse.course_id)
            .where(EduStudentCourse.student_id == student_id)
            .order_by(EduStudentCourse.last_study_time.desc().nullslast())
            .limit(limit)
        )
        return list((await db.execute(stmt)).all())

    @staticmethod
    async def get_student_cross_course_weak_points(student_id: int, db: AsyncSession, limit: int = 5) -> list:
        """获取学生跨课程薄弱知识点

        替代原 VStudentWeakPoints 视图查询，使用事件聚合 + 最新掌握度 JOIN。
        返回 Row 对象，支持 .node_uuid, .course_id 等属性访问。
        """
        # Step 1: 聚合事件按 node_uuid, course_id
        event_agg = (
            select(
                EduStudentLearningEvent.node_uuid,
                EduStudentLearningEvent.course_id,
                func.count(EduStudentLearningEvent.event_id).label("total_interaction_count"),
                func.count(EduStudentLearningEvent.event_id)
                .filter(EduStudentLearningEvent.event_type == "question")
                .label("total_question_count"),
                func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label("total_study_seconds"),
            )
            .where(
                EduStudentLearningEvent.student_id == student_id,
                EduStudentLearningEvent.node_uuid.isnot(None),
                EduStudentLearningEvent.status == "0",
            )
            .group_by(EduStudentLearningEvent.node_uuid, EduStudentLearningEvent.course_id)
            .subquery()
        )

        # Step 2: 每个 node_uuid 的最新掌握度
        mastery_ranked = (
            select(
                EduStudentMastery.node_uuid,
                EduStudentMastery.mastery_level,
                EduStudentMastery.mastery_score,
                EduStudentMastery.assessed_at,
                func.row_number()
                .over(
                    partition_by=EduStudentMastery.node_uuid,
                    order_by=EduStudentMastery.assessed_at.desc(),
                )
                .label("rn"),
            )
            .where(
                EduStudentMastery.student_id == student_id,
                EduStudentMastery.status == "0",
            )
            .subquery()
        )

        # Step 3: JOIN 并筛选薄弱点（低掌握度 + 一定交互量）
        stmt = (
            select(
                event_agg.c.node_uuid,
                event_agg.c.course_id,
                event_agg.c.total_interaction_count,
                event_agg.c.total_question_count,
                event_agg.c.total_study_seconds,
                mastery_ranked.c.mastery_level.label("latest_mastery_level"),
                mastery_ranked.c.mastery_score.label("latest_mastery_score"),
                mastery_ranked.c.assessed_at.label("latest_assessed_at"),
            )
            .join(mastery_ranked, event_agg.c.node_uuid == mastery_ranked.c.node_uuid)
            .where(
                mastery_ranked.c.rn == 1,
                mastery_ranked.c.mastery_level.in_(["low", "medium"]),
                event_agg.c.total_interaction_count > 2,
            )
            .order_by(event_agg.c.total_interaction_count.desc())
            .limit(limit)
        )
        return list((await db.execute(stmt)).all())

    # ========================================================================
    # 教师端
    # ========================================================================

    @staticmethod
    async def get_teacher_course_ids(teacher_id: int, db: AsyncSession) -> list[int]:
        """获取教师教授的课程ID列表"""
        stmt = select(EduCourseTeacher.course_id).where(EduCourseTeacher.teacher_id == teacher_id)
        return [row[0] for row in (await db.execute(stmt)).all()]

    @staticmethod
    async def get_teacher_course_ids_by_create(teacher_id: int, db: AsyncSession) -> list[int]:
        """获取教师创建的课程ID列表（作为备选）"""
        stmt = select(EduCourse.course_id).where(EduCourse.create_by == teacher_id)
        return [row[0] for row in (await db.execute(stmt)).all()]

    @staticmethod
    async def get_teacher_total_students(course_ids: list[int], db: AsyncSession) -> int:
        """获取教师所有课程的总学生数"""
        if not course_ids:
            return 0
        stmt = select(func.coalesce(func.sum(EduCourse.student_count), 0)).where(EduCourse.course_id.in_(course_ids))
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_teacher_today_active_students(course_ids: list[int], db: AsyncSession) -> int:
        """获取教师课程今日活跃学生数"""
        if not course_ids:
            return 0
        today = date.today()
        stmt = select(func.count(func.distinct(EduStudentLearningEvent.student_id))).where(
            EduStudentLearningEvent.course_id.in_(course_ids),
            cast(EduStudentLearningEvent.event_time, Date) >= today,
            EduStudentLearningEvent.status == "0",
        )
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_teacher_avg_mastery(course_ids: list[int], db: AsyncSession) -> float | None:
        """获取教师课程平均掌握度"""
        if not course_ids:
            return None
        stmt = select(func.avg(EduStudentMastery.mastery_score)).where(
            EduStudentMastery.course_id.in_(course_ids),
            EduStudentMastery.status == "0",
        )
        return (await db.execute(stmt)).scalar()

    @staticmethod
    async def get_teacher_course_overviews(course_ids: list[int], db: AsyncSession) -> list:
        """获取教师各课程概览

        替代原 VCourseLearningOverview 视图查询。
        返回 SimpleNamespace 对象，支持 .course_id, .course_name 等属性访问。
        """
        if not course_ids:
            return []

        # 学生数：按课程聚合
        student_count_subq = (
            select(
                EduStudentCourse.course_id,
                func.count(EduStudentCourse.id).label("student_count"),
            )
            .group_by(EduStudentCourse.course_id)
            .subquery()
        )

        # 平均掌握度：按课程聚合
        mastery_subq = (
            select(
                EduStudentMastery.course_id,
                func.avg(EduStudentMastery.mastery_score).label("avg_mastery_score"),
            )
            .where(EduStudentMastery.status == "0")
            .group_by(EduStudentMastery.course_id)
            .subquery()
        )

        # 答题正确率：按课程聚合
        quiz_subq = (
            select(
                EduCourseExercise.course_id,
                func.avg(case((EduExerciseAttempt.is_correct.is_(True), 100.0), else_=0.0)).label("quiz_correct_rate"),
            )
            .join(EduExerciseAttempt, EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id)
            .where(EduCourseExercise.status == "0")
            .group_by(EduCourseExercise.course_id)
            .subquery()
        )

        # 主查询
        stmt = (
            select(
                EduCourse.course_id,
                EduCourse.course_name,
                func.coalesce(student_count_subq.c.student_count, 0).label("total_student_count"),
                mastery_subq.c.avg_mastery_score,
                quiz_subq.c.quiz_correct_rate,
            )
            .outerjoin(student_count_subq, EduCourse.course_id == student_count_subq.c.course_id)
            .outerjoin(mastery_subq, EduCourse.course_id == mastery_subq.c.course_id)
            .outerjoin(quiz_subq, EduCourse.course_id == quiz_subq.c.course_id)
            .where(EduCourse.course_id.in_(course_ids))
        )

        rows = (await db.execute(stmt)).all()
        return [
            SimpleNamespace(
                course_id=row.course_id,
                course_name=row.course_name,
                total_student_count=row.total_student_count or 0,
                avg_mastery_score=row.avg_mastery_score,
                quiz_correct_rate=row.quiz_correct_rate,
            )
            for row in rows
        ]

    @staticmethod
    async def get_teacher_cross_course_rankings(course_ids: list[int], db: AsyncSession, limit: int = 10) -> list:
        """获取教师跨课程综合排名

        替代原 VCourseStudentRanking 视图查询。
        使用 Python 计算 PERCENT_RANK，返回 SimpleNamespace 列表。
        """
        if not course_ids:
            return []

        # 获取每个学生在每个课程的平均掌握度
        stmt = (
            select(
                EduStudentMastery.student_id,
                EduStudentMastery.course_id,
                func.avg(EduStudentMastery.mastery_score).label("avg_mastery_score"),
            )
            .where(
                EduStudentMastery.course_id.in_(course_ids),
                EduStudentMastery.status == "0",
            )
            .group_by(EduStudentMastery.student_id, EduStudentMastery.course_id)
        )
        rows = (await db.execute(stmt)).all()

        # 按课程分组计算百分位
        from collections import defaultdict

        course_scores: dict[int, list[tuple[int, float]]] = defaultdict(list)
        for row in rows:
            if row.avg_mastery_score is not None:
                course_scores[row.course_id].append((row.student_id, float(row.avg_mastery_score)))

        # 获取课程名称映射
        course_stmt = select(EduCourse.course_id, EduCourse.course_name).where(EduCourse.course_id.in_(course_ids))
        course_name_map = {r[0]: r[1] for r in (await db.execute(course_stmt)).all()}

        # 计算百分位并生成结果
        results = []
        for cid, scores in course_scores.items():
            sorted_scores = sorted(s[1] for s in scores)
            n = len(sorted_scores)
            for student_id, score in scores:
                # PERCENT_RANK: (rank - 1) / (n - 1)
                rank = sum(1 for s in sorted_scores if s <= score)
                percentile = (rank - 1) / max(n - 1, 1) if n > 1 else 1.0
                results.append(
                    SimpleNamespace(
                        student_id=student_id,
                        course_id=cid,
                        course_name=course_name_map.get(cid, ""),
                        avg_mastery_score=score,
                        mastery_percentile=percentile,
                    )
                )

        results.sort(key=lambda x: x.mastery_percentile, reverse=True)
        return results[:limit]

    @staticmethod
    async def get_teacher_trend_data(
        course_ids: list[int],
        db: AsyncSession,
        days: int = 30,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[tuple[str, int]]:
        """获取教师课程每日活跃学生数

        支持两种模式：
        1. 按 days 天数回溯（默认）
        2. 按 start_date / end_date 日期范围查询
        """
        if not course_ids:
            return []

        if start_date and end_date:
            since = start_date
            before = end_date
        else:
            since = date.today() - timedelta(days=days)
            before = None

        conditions = [
            EduStudentLearningEvent.course_id.in_(course_ids),
            EduStudentLearningEvent.event_time >= since,
            EduStudentLearningEvent.status == "0",
        ]
        if before is not None:
            conditions.append(EduStudentLearningEvent.event_time <= before)

        stmt = (
            select(
                cast(EduStudentLearningEvent.event_time, Date).label("study_date"),
                func.count(func.distinct(EduStudentLearningEvent.student_id)),
            )
            .where(*conditions)
            .group_by(cast(EduStudentLearningEvent.event_time, Date))
            .order_by(cast(EduStudentLearningEvent.event_time, Date))
        )
        return [(str(row[0]), row[1]) for row in (await db.execute(stmt)).all()]
