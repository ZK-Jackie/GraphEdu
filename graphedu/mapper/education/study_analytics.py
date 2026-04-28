"""学情分析 Mapper 层

查询基础表进行聚合统计，提供教师端和学生端的学情分析数据。
替代原 SQL 视图查询，使用 SQLAlchemy Core 直接聚合。
"""

from datetime import date, timedelta

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import (
    EduChapter,
    EduCourseExercise,
    EduExerciseAttempt,
    EduKnowledgeNodeChapter,
    EduStudentLearningEvent,
    EduStudentMastery,
)


class StudyAnalyticsMapper:
    """学情分析数据访问层（查询基础表聚合）"""

    # ========================================================================
    # 教师端
    # ========================================================================

    @staticmethod
    async def get_course_overview(course_id: int, db: AsyncSession) -> dict | None:
        """获取课程整体学习概览

        替代原 VCourseLearningOverview 视图查询。
        返回字典，包含课程聚合统计数据。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 统计字典，无数据返回 None
        """
        # 事件聚合
        event_stmt = select(
            func.count(EduStudentLearningEvent.event_id).label("total_event_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "question")
            .label("total_question_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "interest")
            .label("total_interest_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "explain_request")
            .label("total_explain_request_count"),
            func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label(
                "total_study_seconds"
            ),
            func.count(func.distinct(EduStudentLearningEvent.student_id)).label(
                "total_student_count"
            ),
            func.count(func.distinct(EduStudentLearningEvent.chapter_id)).label("chapters_touched"),
            func.count(func.distinct(EduStudentLearningEvent.node_uuid)).label("nodes_touched"),
            func.min(EduStudentLearningEvent.event_time).label("first_event_time"),
            func.max(EduStudentLearningEvent.event_time).label("last_event_time"),
        ).where(
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.status == "0",
        )
        event_row = (await db.execute(event_stmt)).first()

        if not event_row or event_row.total_event_count == 0:
            return None

        # 近7天/30天活跃
        today = date.today()
        active_7d_stmt = select(func.count(func.distinct(EduStudentLearningEvent.student_id))).where(
            EduStudentLearningEvent.course_id == course_id,
            cast(EduStudentLearningEvent.event_time, Date) >= today - timedelta(days=7),
            EduStudentLearningEvent.status == "0",
        )
        active_7d = (await db.execute(active_7d_stmt)).scalar() or 0

        active_30d_stmt = select(func.count(func.distinct(EduStudentLearningEvent.student_id))).where(
            EduStudentLearningEvent.course_id == course_id,
            cast(EduStudentLearningEvent.event_time, Date) >= today - timedelta(days=30),
            EduStudentLearningEvent.status == "0",
        )
        active_30d = (await db.execute(active_30d_stmt)).scalar() or 0

        # 掌握度分布
        mastery_stmt = select(
            func.count(EduStudentMastery.mastery_id)
            .filter(EduStudentMastery.mastery_level == "high")
            .label("high"),
            func.count(EduStudentMastery.mastery_id)
            .filter(EduStudentMastery.mastery_level == "medium")
            .label("medium"),
            func.count(EduStudentMastery.mastery_id)
            .filter(EduStudentMastery.mastery_level == "low")
            .label("low"),
            func.avg(EduStudentMastery.mastery_score).label("avg_score"),
        ).where(
            EduStudentMastery.course_id == course_id,
            EduStudentMastery.status == "0",
        )
        mastery_row = (await db.execute(mastery_stmt)).first()

        # 答题统计
        quiz_stmt = select(
            func.count(EduExerciseAttempt.attempt_id).label("total_quiz"),
            func.sum(case((EduExerciseAttempt.is_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        ).join(
            EduCourseExercise, EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id
        ).where(
            EduCourseExercise.course_id == course_id,
            EduCourseExercise.status == "0",
        )
        quiz_row = (await db.execute(quiz_stmt)).first()

        total_quiz = quiz_row.total_quiz or 0 if quiz_row else 0
        correct = quiz_row.correct or 0 if quiz_row else 0

        return {
            "course_id": course_id,
            "total_student_count": event_row.total_student_count or 0,
            "active_student_count_7d": active_7d,
            "active_student_count_30d": active_30d,
            "total_event_count": event_row.total_event_count or 0,
            "total_question_count": event_row.total_question_count or 0,
            "total_interest_count": event_row.total_interest_count or 0,
            "total_explain_request_count": event_row.total_explain_request_count or 0,
            "total_quiz_count": total_quiz,
            "total_quiz_correct_count": correct,
            "quiz_correct_rate": round(correct / total_quiz * 100, 1) if total_quiz > 0 else None,
            "avg_mastery_score": round(float(mastery_row.avg_score), 1)
            if mastery_row and mastery_row.avg_score is not None
            else None,
            "high_mastery_count": mastery_row.high or 0 if mastery_row else 0,
            "medium_mastery_count": mastery_row.medium or 0 if mastery_row else 0,
            "low_mastery_count": mastery_row.low or 0 if mastery_row else 0,
            "chapters_touched": event_row.chapters_touched or 0,
            "nodes_touched": event_row.nodes_touched or 0,
            "total_study_seconds": event_row.total_study_seconds or 0,
            "first_event_time": event_row.first_event_time,
            "last_event_time": event_row.last_event_time,
        }

    @staticmethod
    async def get_chapter_stats(course_id: int, db: AsyncSession) -> list[dict]:
        """获取课程各章节学习统计

        替代原 VCourseChapterStats 视图查询。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 章节统计字典列表
        """
        # 获取课程章节
        chapters = (
            select(EduChapter.chapter_id, EduChapter.chapter_name)
            .where(EduChapter.course_id == course_id, EduChapter.status == "0", EduChapter.parent_id != 0)
            .order_by(EduChapter.chapter_no)
        )
        chapter_rows = (await db.execute(chapters)).all()
        if not chapter_rows:
            return []

        chapter_ids = [r.chapter_id for r in chapter_rows]

        # 事件按章节聚合
        event_stmt = select(
            EduStudentLearningEvent.chapter_id,
            func.count(EduStudentLearningEvent.event_id).label("total_events"),
            func.count(func.distinct(EduStudentLearningEvent.student_id)).label("student_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "question")
            .label("question_count"),
            func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label(
                "total_seconds"
            ),
            func.count(func.distinct(EduStudentLearningEvent.node_uuid)).label("nodes_touched"),
        ).where(
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.chapter_id.in_(chapter_ids),
            EduStudentLearningEvent.status == "0",
        ).group_by(EduStudentLearningEvent.chapter_id)
        event_map = {r.chapter_id: r for r in (await db.execute(event_stmt)).all()}

        # 章节知识点总数
        node_count_stmt = select(
            EduKnowledgeNodeChapter.chapter_id,
            func.count(func.distinct(EduKnowledgeNodeChapter.node_uuid)).label("total_nodes"),
        ).where(
            EduKnowledgeNodeChapter.chapter_id.in_(chapter_ids),
            EduKnowledgeNodeChapter.status == "0",
        ).group_by(EduKnowledgeNodeChapter.chapter_id)
        node_count_map = {r.chapter_id: r.total_nodes for r in (await db.execute(node_count_stmt)).all()}

        # 章节答题统计
        quiz_stmt = select(
            EduCourseExercise.chapter_id,
            func.count(EduExerciseAttempt.attempt_id).label("quiz_count"),
            func.sum(case((EduExerciseAttempt.is_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        ).join(
            EduExerciseAttempt, EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id
        ).where(
            EduCourseExercise.course_id == course_id,
            EduCourseExercise.chapter_id.in_(chapter_ids),
            EduCourseExercise.status == "0",
        ).group_by(EduCourseExercise.chapter_id)
        quiz_map = {r.chapter_id: r for r in (await db.execute(quiz_stmt)).all()}

        # 组装结果
        results = []
        for ch in chapter_rows:
            evt = event_map.get(ch.chapter_id)
            quiz = quiz_map.get(ch.chapter_id)
            total_nodes = node_count_map.get(ch.chapter_id, 0)
            nodes_touched = evt.nodes_touched if evt else 0

            results.append({
                "course_id": course_id,
                "chapter_id": ch.chapter_id,
                "chapter_name": ch.chapter_name,
                "student_count": evt.student_count if evt else 0,
                "total_event_count": evt.total_events if evt else 0,
                "question_count": evt.question_count if evt else 0,
                "quiz_count": quiz.quiz_count if quiz else 0,
                "quiz_correct_count": quiz.correct if quiz else 0,
                "quiz_correct_rate": round(quiz.correct / quiz.quiz_count * 100, 1)
                if quiz and quiz.quiz_count and quiz.quiz_count > 0
                else None,
                "nodes_touched": nodes_touched,
                "total_node_count": total_nodes,
                "node_coverage_rate": round(nodes_touched / total_nodes * 100, 1)
                if total_nodes > 0
                else 0,
                "total_study_seconds": evt.total_seconds if evt else 0,
            })
        return results

    @staticmethod
    async def get_student_rankings(course_id: int, db: AsyncSession) -> list[dict]:
        """获取课程学生排名（按掌握度百分位降序）

        替代原 VCourseStudentRanking 视图查询。
        使用 Python 计算 PERCENT_RANK。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 学生排名字典列表
        """
        # 获取每个学生的聚合数据
        event_stmt = select(
            EduStudentLearningEvent.student_id,
            func.count(EduStudentLearningEvent.event_id).label("total_events"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "question")
            .label("question_count"),
            func.count(func.distinct(EduStudentLearningEvent.chapter_id)).label("chapters_touched"),
            func.count(func.distinct(EduStudentLearningEvent.node_uuid)).label("nodes_touched"),
            func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label(
                "total_seconds"
            ),
            func.count(func.distinct(cast(EduStudentLearningEvent.event_time, Date))).label(
                "study_days"
            ),
        ).where(
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.status == "0",
        ).group_by(EduStudentLearningEvent.student_id)
        event_rows = (await db.execute(event_stmt)).all()

        if not event_rows:
            return []

        # 获取课程章节数和知识点数
        total_chapters = (
            await db.execute(
                select(func.count()).where(
                    EduChapter.course_id == course_id,
                    EduChapter.status == "0",
                    EduChapter.parent_id != 0,
                )
            )
        ).scalar() or 0

        total_nodes = (
            await db.execute(
                select(func.count(func.distinct(EduKnowledgeNodeChapter.node_uuid))).where(
                    EduKnowledgeNodeChapter.chapter_id.in_(
                        select(EduChapter.chapter_id).where(
                            EduChapter.course_id == course_id,
                            EduChapter.status == "0",
                            EduChapter.parent_id != 0,
                        )
                    ),
                    EduKnowledgeNodeChapter.status == "0",
                )
            )
        ).scalar() or 0

        # 掌握度评分
        mastery_stmt = select(
            EduStudentMastery.student_id,
            func.avg(EduStudentMastery.mastery_score).label("avg_score"),
        ).where(
            EduStudentMastery.course_id == course_id,
            EduStudentMastery.status == "0",
        ).group_by(EduStudentMastery.student_id)
        mastery_map = {r.student_id: r.avg_score for r in (await db.execute(mastery_stmt)).all()}

        # 答题统计
        quiz_stmt = select(
            EduExerciseAttempt.student_id,
            func.count(EduExerciseAttempt.attempt_id).label("quiz_count"),
            func.sum(case((EduExerciseAttempt.is_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        ).join(
            EduCourseExercise, EduExerciseAttempt.exercise_id == EduCourseExercise.exercise_id
        ).where(
            EduCourseExercise.course_id == course_id,
            EduCourseExercise.status == "0",
        ).group_by(EduExerciseAttempt.student_id)
        quiz_map = {r.student_id: r for r in (await db.execute(quiz_stmt)).all()}

        # 计算百分位
        all_scores = [float(mastery_map.get(r.student_id, 0) or 0) for r in event_rows]
        sorted_scores = sorted(all_scores)
        n = len(sorted_scores)

        results = []
        for row in event_rows:
            score = float(mastery_map.get(row.student_id, 0) or 0)
            rank = sum(1 for s in sorted_scores if s <= score)
            percentile = (rank - 1) / max(n - 1, 1) if n > 1 else 1.0

            quiz = quiz_map.get(row.student_id)
            chapters_touched = row.chapters_touched or 0
            nodes_touched = row.nodes_touched or 0

            results.append({
                "student_id": row.student_id,
                "course_id": course_id,
                "total_event_count": row.total_events or 0,
                "question_count": row.question_count or 0,
                "quiz_count": quiz.quiz_count if quiz else 0,
                "quiz_correct_rate": round(quiz.correct / quiz.quiz_count * 100, 1)
                if quiz and quiz.quiz_count and quiz.quiz_count > 0
                else None,
                "avg_mastery_score": score if score > 0 else None,
                "chapters_touched": chapters_touched,
                "chapter_coverage_rate": round(chapters_touched / total_chapters * 100, 1)
                if total_chapters > 0
                else 0,
                "nodes_touched": nodes_touched,
                "node_coverage_rate": round(nodes_touched / total_nodes * 100, 1)
                if total_nodes > 0
                else 0,
                "total_study_seconds": row.total_seconds or 0,
                "study_days": row.study_days or 0,
                "mastery_percentile": percentile,
            })

        results.sort(key=lambda x: x["mastery_percentile"], reverse=True)
        return results

    @staticmethod
    async def get_student_course_progress_list(course_id: int, db: AsyncSession) -> list[dict]:
        """获取课程所有学生的学习进度

        替代原 VStudentCourseProgress 视图查询。

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: 学生进度字典列表
        """
        # 复用 get_student_rankings 的逻辑
        return await StudyAnalyticsMapper.get_student_rankings(course_id, db)

    # ========================================================================
    # 学生端
    # ========================================================================

    @staticmethod
    async def get_my_course_progress(
        student_id: int, course_id: int, db: AsyncSession
    ) -> dict | None:
        """获取学生在某课程的学习进度

        :return: 进度字典，不存在则 None
        """
        rankings = await StudyAnalyticsMapper.get_student_rankings(course_id, db)
        for r in rankings:
            if r["student_id"] == student_id:
                return r
        return None

    @staticmethod
    async def get_my_daily_summary(
        student_id: int, course_id: int, db: AsyncSession, days: int = 30
    ) -> list[dict]:
        """获取学生最近 N 天的每日学习统计

        替代原 VStudentDailySummary 视图查询。

        :return: 每日统计字典列表
        """
        since = date.today() - timedelta(days=days)
        stmt = select(
            cast(EduStudentLearningEvent.event_time, Date).label("study_date"),
            func.count(EduStudentLearningEvent.event_id).label("total_event_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "question")
            .label("question_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "interest")
            .label("interest_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "explain_request")
            .label("explain_request_count"),
            func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label(
                "total_study_seconds"
            ),
            func.count(func.distinct(EduStudentLearningEvent.node_uuid)).label("nodes_touched"),
        ).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.event_time >= since,
            EduStudentLearningEvent.status == "0",
        ).group_by(cast(EduStudentLearningEvent.event_time, Date)).order_by(
            cast(EduStudentLearningEvent.event_time, Date)
        )
        return [
            {
                "study_date": row.study_date,
                "total_event_count": row.total_event_count or 0,
                "question_count": row.question_count or 0,
                "interest_count": row.interest_count or 0,
                "explain_request_count": row.explain_request_count or 0,
                "total_study_seconds": row.total_study_seconds or 0,
                "nodes_touched": row.nodes_touched or 0,
            }
            for row in (await db.execute(stmt)).all()
        ]

    @staticmethod
    async def get_my_node_profile(
        student_id: int, course_id: int, db: AsyncSession
    ) -> list[dict]:
        """获取学生知识点画像

        替代原 VStudentNodeProfile 视图查询。

        :return: 知识点画像字典列表
        """
        # 事件按 node_uuid 聚合
        event_stmt = select(
            EduStudentLearningEvent.node_uuid,
            func.count(EduStudentLearningEvent.event_id).label("total_interaction_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "question")
            .label("total_question_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "interest")
            .label("total_interest_count"),
            func.count(EduStudentLearningEvent.event_id)
            .filter(EduStudentLearningEvent.event_type == "explain_request")
            .label("total_explain_request_count"),
            func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label(
                "total_study_seconds"
            ),
            func.min(EduStudentLearningEvent.event_time).label("first_interaction_at"),
            func.max(EduStudentLearningEvent.event_time).label("last_interaction_at"),
        ).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.node_uuid.isnot(None),
            EduStudentLearningEvent.status == "0",
        ).group_by(EduStudentLearningEvent.node_uuid)
        event_rows = (await db.execute(event_stmt)).all()

        if not event_rows:
            return []

        # 每个 node_uuid 的最新掌握度
        mastery_ranked = (
            select(
                EduStudentMastery.node_uuid,
                EduStudentMastery.mastery_level,
                EduStudentMastery.mastery_score,
                EduStudentMastery.reason,
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

        latest_stmt = select(
            mastery_ranked.c.node_uuid,
            mastery_ranked.c.mastery_level,
            mastery_ranked.c.mastery_score,
            mastery_ranked.c.reason,
            mastery_ranked.c.assessed_at,
        ).where(mastery_ranked.c.rn == 1)
        mastery_map = {
            str(r.node_uuid): r for r in (await db.execute(latest_stmt)).all()
        }

        # 组装结果
        results = []
        for row in event_rows:
            uuid_str = str(row.node_uuid)
            m = mastery_map.get(uuid_str)
            results.append({
                "node_uuid": uuid_str,
                "total_interaction_count": row.total_interaction_count or 0,
                "total_question_count": row.total_question_count or 0,
                "total_interest_count": row.total_interest_count or 0,
                "total_explain_request_count": row.total_explain_request_count or 0,
                "total_study_seconds": row.total_study_seconds or 0,
                "first_interaction_at": row.first_interaction_at,
                "last_interaction_at": row.last_interaction_at,
                "latest_mastery_level": m.mastery_level or "" if m else "",
                "latest_mastery_score": float(m.mastery_score) if m and m.mastery_score else None,
                "latest_assessed_at": m.assessed_at if m else None,
                "latest_assessment_reason": m.reason if m else None,
            })

        results.sort(key=lambda x: x["last_interaction_at"] or date.min, reverse=True)
        return results

    @staticmethod
    async def get_my_weak_points(
        student_id: int, course_id: int, db: AsyncSession
    ) -> list[dict]:
        """获取学生薄弱知识点

        替代原 VStudentWeakPoints 视图查询。
        从 node_profile 数据中过滤低掌握度 + 高投入的知识点。

        :return: 薄弱知识点字典列表
        """
        profiles = await StudyAnalyticsMapper.get_my_node_profile(student_id, course_id, db)

        # 过滤薄弱点：低/中掌握度 + 有一定交互量
        weak_points = []
        for p in profiles:
            mastery = p["latest_mastery_score"] or 0
            interactions = p["total_interaction_count"] + p["total_question_count"]
            if p["latest_mastery_level"] in ("low", "medium") and interactions > 2:
                effort_ratio = round(interactions / max(mastery, 0.1), 1)
                weak_points.append({**p, "effort_ratio": effort_ratio})

        weak_points.sort(key=lambda x: x["effort_ratio"], reverse=True)
        return weak_points

    @staticmethod
    async def get_my_study_streak(
        student_id: int, course_id: int, db: AsyncSession
    ) -> dict | None:
        """获取学生学习连续性

        替代原 VStudentStudyStreak 视图查询。
        使用 Python 从日级数据计算连续天数。

        :return: 连续性字典，不存在则 None
        """
        stmt = select(func.distinct(cast(EduStudentLearningEvent.event_time, Date))).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.status == "0",
        )
        dates = [row[0] for row in (await db.execute(stmt)).all()]

        if not dates:
            return None

        sorted_dates = sorted(set(dates))
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

        return {
            "student_id": student_id,
            "course_id": course_id,
            "total_study_days": len(sorted_dates),
            "last_study_date": sorted_dates[-1],
            "current_streak": current,
            "longest_streak": longest,
        }

    @staticmethod
    async def get_my_ranking(
        student_id: int, course_id: int, db: AsyncSession
    ) -> dict | None:
        """获取学生在课程中的排名数据

        :return: 排名字典，不存在则 None
        """
        rankings = await StudyAnalyticsMapper.get_student_rankings(course_id, db)
        for r in rankings:
            if r["student_id"] == student_id:
                return r
        return None

    @staticmethod
    async def get_student_global_stats(student_id: int, db: AsyncSession) -> dict | None:
        """获取学生全局学习统计（跨所有课程）

        从 EduStudentLearningEvent 实时聚合，替代 edu_student 表中的冗余字段。

        :param student_id: 学生ID
        :param db: 数据库会话
        :return: 统计字典 {"total_study_seconds": int, "course_count": int}，无数据返回 None
        """
        stmt = select(
            func.sum(func.coalesce(EduStudentLearningEvent.duration_seconds, 0)).label("total_study_seconds"),
            func.count(func.distinct(EduStudentLearningEvent.course_id)).label("course_count"),
        ).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.status == "0",
        )
        row = (await db.execute(stmt)).first()
        if not row or (row.total_study_seconds == 0 and row.course_count == 0):
            return None
        return {
            "total_study_seconds": row.total_study_seconds or 0,
            "course_count": row.course_count or 0,
        }
