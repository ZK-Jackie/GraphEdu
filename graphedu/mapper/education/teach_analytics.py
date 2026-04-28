"""教师端课程分析 Mapper 层

提供教师工作台课程学生列表及学习数据统计查询。
优先使用 SQLAlchemy Core 聚合查询基础表，保留原表查询作为兼容。
"""

from collections.abc import Sequence

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.orm.education import (
    EduChapter,
    EduChapterResource,
    EduCourseExercise,
    EduExerciseAttempt,
    EduKnowledgeNodeChapter,
    EduKnowledgePointEmbedding,
    EduStudent,
    EduStudentCourse,
    EduStudentLearningEvent,
    EduStudentMastery,
    EduStudentResourceProgress,
)
from graphedu.mapper.education.study_analytics import StudyAnalyticsMapper


class TeachAnalyticsMapper:
    """教师端课程分析数据访问层"""

    # ========================================================================
    # 聚合查询（替代原 SQL 视图）
    # ========================================================================

    @staticmethod
    async def get_course_learning_overview(course_id: int, db: AsyncSession) -> dict | None:
        """获取课程整体学习概览（聚合基础表）

        委托给 StudyAnalyticsMapper.get_course_overview。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 统计字典
        """
        return await StudyAnalyticsMapper.get_course_overview(course_id, db)

    @staticmethod
    async def get_course_chapter_stats(course_id: int, db: AsyncSession) -> list[dict]:
        """获取课程各章节学习统计（聚合基础表）

        委托给 StudyAnalyticsMapper.get_chapter_stats。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 章节统计字典列表
        """
        return await StudyAnalyticsMapper.get_chapter_stats(course_id, db)

    @staticmethod
    async def get_course_student_rankings(course_id: int, db: AsyncSession) -> list[dict]:
        """获取课程学生排名（聚合基础表）

        委托给 StudyAnalyticsMapper.get_student_rankings。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 学生排名字典列表
        """
        return await StudyAnalyticsMapper.get_student_rankings(course_id, db)

    # ========================================================================
    # 原有方法（保留兼容）
    # ========================================================================

    @staticmethod
    async def get_course_students(
        course_id: int,
        db: AsyncSession,
        page: int = 1,
        size: int = 50,
    ) -> tuple[Sequence[tuple], int]:
        """查询课程所有选课学生（含进度和最后学习时间）

        :param course_id: 课程ID
        :param db: 数据库会话
        :param page: 页码
        :param size: 每页数量
        :return: (rows, total)，rows 为 (EduStudentCourse, EduStudent) 元组列表
        """
        base_conditions = [
            EduStudentCourse.course_id == course_id,
            EduStudent.status != SystemConstants.Status.DELETED,
        ]

        query = (
            select(EduStudentCourse, EduStudent)
            .join(
                EduStudent,
                and_(
                    EduStudentCourse.student_id == EduStudent.student_id,
                    EduStudent.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(and_(*base_conditions))
            .order_by(EduStudentCourse.enroll_time.desc())
        )

        count_query = (
            select(func.count(EduStudentCourse.id))
            .select_from(EduStudentCourse)
            .join(
                EduStudent,
                and_(
                    EduStudentCourse.student_id == EduStudent.student_id,
                    EduStudent.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(and_(*base_conditions))
        )
        total = (await db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        rows = (await db.execute(query)).all()
        return rows, total

    @staticmethod
    async def get_course_student_stats(
        course_id: int,
        db: AsyncSession,
    ) -> dict:
        """获取课程学生统计汇总（总数、平均进度、完成数）

        从基础表聚合。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 统计字典
        """
        agg_stmt = select(
            func.count(EduStudentCourse.id).label("total"),
            func.avg(EduStudentCourse.progress).label("avg_progress"),
            func.sum(case((EduStudentCourse.progress == 100, 1), else_=0)).label("completed"),
        ).where(EduStudentCourse.course_id == course_id)
        agg_row = (await db.execute(agg_stmt)).first()

        total = agg_row.total or 0 if agg_row else 0
        avg_progress = round(agg_row.avg_progress or 0) if agg_row else 0
        completed = int(agg_row.completed or 0) if agg_row else 0

        # 今日活跃
        from datetime import date

        today = date.today()
        from sqlalchemy import Date as SaDate, cast as sa_cast

        active_stmt = select(func.count(func.distinct(EduStudentLearningEvent.student_id))).where(
            EduStudentLearningEvent.course_id == course_id,
            sa_cast(EduStudentLearningEvent.event_time, SaDate) >= today,
            EduStudentLearningEvent.status == "0",
        )
        today_active = (await db.execute(active_stmt)).scalar() or 0

        return {
            "total_students": total,
            "average_progress": avg_progress,
            "completed_students": completed,
            "today_active": today_active,
        }

    @staticmethod
    async def get_chapter_completion(
        course_id: int,
        db: AsyncSession,
    ) -> Sequence[tuple]:
        """获取各章节的平均完成率和已学习人数

        使用 StudyAnalyticsMapper 的章节数据。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 每行含 (chapter_id, chapter_name, avg_completion, student_count) 的列表
        """
        chapter_stats = await StudyAnalyticsMapper.get_chapter_stats(course_id, db)
        return [
            (
                stat["chapter_id"],
                stat["chapter_name"],
                stat.get("avg_mastery_score", 0) or 0,
                stat.get("student_count", 0) or 0,
            )
            for stat in chapter_stats
        ]

    @staticmethod
    async def get_progress_distribution(
        course_id: int,
        db: AsyncSession,
    ) -> list[dict]:
        """获取学生进度分布（5 个区间）

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: [{"range": "0-20%", "count": n}, ...]
        """
        ranges = [
            ("0-20%", 0, 20),
            ("21-40%", 21, 40),
            ("41-60%", 41, 60),
            ("61-80%", 61, 80),
            ("81-100%", 81, 100),
        ]
        result = []
        for label, lo, hi in ranges:
            stmt = select(func.count(EduStudentCourse.id)).where(
                EduStudentCourse.course_id == course_id,
                EduStudentCourse.progress >= lo,
                EduStudentCourse.progress <= hi,
            )
            count = (await db.execute(stmt)).scalar() or 0
            result.append({"range": label, "count": count})
        return result

    # ========================================================================
    # 学生章节学习详情
    # ========================================================================

    @staticmethod
    async def get_student_chapter_learning_summary(
        student_id: int,
        course_id: int,
        db: AsyncSession,
    ) -> list[dict]:
        """获取学生在课程中每章节的学习摘要。

        聚合 learning_event 表按 chapter_id 分组，合并章节进度和掌握度数据。

        :param student_id: 学生ID
        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 章节学习摘要字典列表
        """
        # 1. 获取课程所有章节（叶子节点）
        chapter_stmt = (
            select(
                EduChapter.chapter_id,
                EduChapter.chapter_name,
                EduChapter.chapter_no,
                EduChapter.parent_id,
            )
            .where(
                EduChapter.course_id == course_id,
                EduChapter.status == "0",
                EduChapter.parent_id != 0,
            )
            .order_by(EduChapter.chapter_no)
        )
        chapters = (await db.execute(chapter_stmt)).all()

        # 2. 聚合学习事件按 chapter_id
        event_stmt = (
            select(
                EduStudentLearningEvent.chapter_id,
                func.count(EduStudentLearningEvent.event_id).label("total_events"),
                func.sum(
                    case(
                        (EduStudentLearningEvent.event_type == "chapter_progress", 1),
                        else_=0,
                    )
                ).label("quiz_count"),
                func.sum(EduStudentLearningEvent.duration_seconds).label("total_seconds"),
                func.max(EduStudentLearningEvent.event_time).label("last_study_time"),
            )
            .where(
                EduStudentLearningEvent.student_id == student_id,
                EduStudentLearningEvent.course_id == course_id,
                EduStudentLearningEvent.chapter_id.isnot(None),
                EduStudentLearningEvent.status == "0",
            )
            .group_by(EduStudentLearningEvent.chapter_id)
        )
        event_rows = (await db.execute(event_stmt)).all()
        event_map: dict[int, dict] = {}
        for row in event_rows:
            event_map[row.chapter_id] = {
                "total_events": row.total_events or 0,
                "quiz_count": row.quiz_count or 0,
                "total_seconds": row.total_seconds or 0,
                "last_study_time": row.last_study_time,
            }

        # 3. 获取该学生在本课程的掌握度（按 node_uuid 取最新记录）
        mastery_subq = (
            select(
                EduStudentMastery.node_uuid,
                func.max(EduStudentMastery.mastery_score).label("score"),
            )
            .where(
                EduStudentMastery.student_id == student_id,
                EduStudentMastery.course_id == course_id,
                EduStudentMastery.status == "0",
            )
            .group_by(EduStudentMastery.node_uuid)
            .subquery()
        )
        # 按 chapter_id 聚合掌握度
        chapter_mastery_stmt = (
            select(
                EduKnowledgeNodeChapter.chapter_id,
                func.avg(mastery_subq.c.score).label("avg_score"),
            )
            .join(
                mastery_subq,
                EduKnowledgeNodeChapter.node_uuid == mastery_subq.c.node_uuid,
            )
            .where(
                EduKnowledgeNodeChapter.chapter_id.in_([c.chapter_id for c in chapters]),
                EduKnowledgeNodeChapter.status == "0",
            )
            .group_by(EduKnowledgeNodeChapter.chapter_id)
        )
        mastery_rows = (await db.execute(chapter_mastery_stmt)).all()
        mastery_map: dict[int, float] = {}
        for row in mastery_rows:
            mastery_map[row.chapter_id] = float(row.avg_score or 0)

        # 4. 获取每个章节的资源完成情况
        chapter_ids = [c.chapter_id for c in chapters]
        resource_completion_stmt = (
            select(
                EduChapterResource.chapter_id,
                func.count(EduChapterResource.resource_id).label("total_count"),
                func.count(EduStudentResourceProgress.progress_id).label("completed_count"),
                func.avg(
                    func.coalesce(EduStudentResourceProgress.completion_rate, 0)
                ).label("avg_completion"),
            )
            .outerjoin(
                EduStudentResourceProgress,
                and_(
                    EduChapterResource.resource_id == EduStudentResourceProgress.resource_id,
                    EduStudentResourceProgress.student_id == student_id,
                    EduStudentResourceProgress.is_completed == "Y",
                    EduStudentResourceProgress.status == "0",
                ),
            )
            .where(
                EduChapterResource.chapter_id.in_(chapter_ids),
                EduChapterResource.status == "0",
            )
            .group_by(EduChapterResource.chapter_id)
        )
        resource_rows = (await db.execute(resource_completion_stmt)).all()
        resource_map: dict[int, dict] = {}
        for row in resource_rows:
            resource_map[row.chapter_id] = {
                "total": row.total_count or 0,
                "completed": row.completed_count or 0,
                "avg_completion": float(row.avg_completion or 0),
            }

        # 4. 获取答题统计（通过 exercise_attempt JOIN course_exercise 获取 chapter_id）
        quiz_stmt = (
            select(
                EduCourseExercise.chapter_id,
                func.count(EduExerciseAttempt.attempt_id).label("total"),
                func.sum(case((EduExerciseAttempt.is_correct.is_(True), 1), else_=0)).label(
                    "correct"
                ),
            )
            .join(
                EduExerciseAttempt,
                EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id,
            )
            .where(
                EduExerciseAttempt.student_id == student_id,
                EduCourseExercise.course_id == course_id,
                EduCourseExercise.chapter_id.isnot(None),
                EduCourseExercise.status == "0",
            )
            .group_by(EduCourseExercise.chapter_id)
        )
        quiz_rows = (await db.execute(quiz_stmt)).all()
        quiz_map: dict[int, dict] = {}
        for row in quiz_rows:
            quiz_map[row.chapter_id] = {
                "total": row.total or 0,
                "correct": row.correct or 0,
            }

        # 6. 合并数据
        result = []
        for ch in chapters:
            event_data = event_map.get(ch.chapter_id, {})
            quiz_data = quiz_map.get(ch.chapter_id, {"total": 0, "correct": 0})
            res_data = resource_map.get(ch.chapter_id, {"total": 0, "completed": 0, "avg_completion": 0})
            total_res = res_data["total"]
            completed_res = res_data["completed"]
            completion_rate = round(completed_res / total_res * 100, 1) if total_res > 0 else 0
            result.append({
                "chapter_id": ch.chapter_id,
                "chapter_name": ch.chapter_name,
                "chapter_no": ch.chapter_no,
                "parent_id": ch.parent_id,
                "completion_rate": completion_rate,
                "is_completed": "Y" if total_res > 0 and completed_res >= total_res else "N",
                "total_events": event_data.get("total_events", 0),
                "total_study_seconds": event_data.get("total_seconds", 0),
                "last_study_time": event_data.get("last_study_time"),
                "quiz_total": quiz_data["total"],
                "quiz_correct": quiz_data["correct"],
                "quiz_correct_rate": (
                    round(quiz_data["correct"] / quiz_data["total"] * 100, 1)
                    if quiz_data["total"] > 0
                    else None
                ),
                "avg_mastery_score": (
                    round(mastery_map.get(ch.chapter_id, 0), 1)
                    if ch.chapter_id in mastery_map
                    else None
                ),
            })

        return result

    @staticmethod
    async def get_student_chapter_resources(
        student_id: int,
        chapter_id: int,
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[tuple], int]:
        """获取学生在某章节的资料阅读进度明细。

        :param student_id: 学生ID
        :param chapter_id: 章节ID
        :param db: 数据库会话
        :param page: 页码
        :param size: 每页数量
        :return: (rows, total)
        """
        conditions = [
            EduStudentResourceProgress.student_id == student_id,
            EduStudentResourceProgress.chapter_id == chapter_id,
            EduStudentResourceProgress.status == "0",
        ]

        count_stmt = select(func.count(EduStudentResourceProgress.progress_id)).where(*conditions)
        total = (await db.execute(count_stmt)).scalar() or 0

        query = (
            select(
                EduStudentResourceProgress.progress_id,
                EduStudentResourceProgress.resource_id,
                EduChapterResource.resource_name,
                EduStudentResourceProgress.resource_type,
                EduStudentResourceProgress.completion_rate,
                EduStudentResourceProgress.is_completed,
                EduStudentResourceProgress.view_count,
                EduStudentResourceProgress.total_duration,
                EduStudentResourceProgress.last_view_time,
            )
            .outerjoin(
                EduChapterResource,
                EduStudentResourceProgress.resource_id == EduChapterResource.resource_id,
            )
            .where(*conditions)
            .order_by(EduStudentResourceProgress.last_view_time.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await db.execute(query)).all()
        return rows, total

    @staticmethod
    async def get_student_chapter_exercises(
        student_id: int,
        course_id: int,
        chapter_id: int,
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[tuple], int]:
        """获取学生在某章节的答题记录明细。

        :param student_id: 学生ID
        :param course_id: 课程ID
        :param chapter_id: 章节ID
        :param db: 数据库会话
        :param page: 页码
        :param size: 每页数量
        :return: (rows, total)
        """
        conditions = [
            EduExerciseAttempt.student_id == student_id,
            EduCourseExercise.course_id == course_id,
            EduCourseExercise.chapter_id == chapter_id,
            EduCourseExercise.status == "0",
        ]

        count_stmt = (
            select(func.count(EduExerciseAttempt.attempt_id))
            .join(EduCourseExercise, EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id)
            .where(*conditions)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        query = (
            select(
                EduExerciseAttempt.attempt_id,
                EduExerciseAttempt.exercise_id,
                EduExerciseAttempt.student_answer,
                EduExerciseAttempt.is_correct,
                EduExerciseAttempt.time_spent,
                EduExerciseAttempt.attempt_time,
            )
            .join(EduCourseExercise, EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id)
            .where(*conditions)
            .order_by(EduExerciseAttempt.attempt_time.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await db.execute(query)).all()
        return rows, total

    @staticmethod
    async def get_student_chapter_mastery(
        student_id: int,
        course_id: int,
        chapter_id: int,
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[tuple], int]:
        """获取学生在某章节的知识点掌握明细。

        :param student_id: 学生ID
        :param course_id: 课程ID
        :param chapter_id: 章节ID
        :param db: 数据库会话
        :param page: 页码
        :param size: 每页数量
        :return: (rows, total)
        """
        # 子查询：每个 node_uuid 取最新一条评估记录
        latest_mastery = (
            select(
                EduStudentMastery.mastery_id,
                EduStudentMastery.node_uuid,
                EduStudentMastery.mastery_score,
                EduStudentMastery.mastery_level,
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
                EduStudentMastery.course_id == course_id,
                EduStudentMastery.status == "0",
            )
            .subquery()
        )

        # JOIN 知识点-章节关联表 + 知识点嵌入表（获取标题）
        conditions = [
            EduKnowledgeNodeChapter.chapter_id == chapter_id,
            EduKnowledgeNodeChapter.status == "0",
            latest_mastery.c.rn == 1,
        ]

        count_stmt = (
            select(func.count())
            .select_from(latest_mastery)
            .join(
                EduKnowledgeNodeChapter,
                latest_mastery.c.node_uuid == EduKnowledgeNodeChapter.node_uuid,
            )
            .where(*conditions)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        query = (
            select(
                latest_mastery.c.mastery_id,
                latest_mastery.c.node_uuid,
                EduKnowledgePointEmbedding.title.label("node_title"),
                latest_mastery.c.mastery_score,
                latest_mastery.c.mastery_level,
                latest_mastery.c.assessed_at,
            )
            .select_from(latest_mastery)
            .join(
                EduKnowledgeNodeChapter,
                latest_mastery.c.node_uuid == EduKnowledgeNodeChapter.node_uuid,
            )
            .outerjoin(
                EduKnowledgePointEmbedding,
                latest_mastery.c.node_uuid == EduKnowledgePointEmbedding.node_uuid,
            )
            .where(*conditions)
            .order_by(latest_mastery.c.assessed_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await db.execute(query)).all()
        return rows, total
