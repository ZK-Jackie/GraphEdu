"""选课管理 Mapper 层

负责选课数据的访问操作，包括选课记录的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import date, datetime, time

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.course import StudentCourseQueryDTO
from graphedu.common.models.orm.education import (
    EduCourse,
    EduStudent,
    EduStudentCourse,
    EduStudentLearningEvent,
)


class StudentCourseMapper:
    """选课数据访问层

    提供选课信息的 CRUD 操作。
    """

    @staticmethod
    async def enroll_course(enrollment: EduStudentCourse, db_session: AsyncSession) -> EduStudentCourse:
        """创建选课记录

        :param db_session: 数据库会话
        :param enrollment: 选课记录信息
        :return: 选课记录对象
        """
        db_session.add(enrollment)
        await db_session.flush()
        return enrollment

    @staticmethod
    async def batch_get_student_count(course_ids: list[int], db_session: AsyncSession) -> dict[int, int]:
        """批量查询课程的实际学生数量（从 edu_student_course 表动态统计）。

        :param course_ids: 课程 ID 列表。
        :param db_session: 数据库会话。
        :return: {course_id: student_count} 映射。
        """
        if not course_ids:
            return {}
        stmt = (
            select(EduStudentCourse.course_id, func.count())
            .where(EduStudentCourse.course_id.in_(course_ids))
            .group_by(EduStudentCourse.course_id)
        )
        result = await db_session.execute(stmt)
        return dict(result.all())

    @staticmethod
    async def drop_course(enrollment_id: int, db_session: AsyncSession) -> None:
        """删除选课记录（物理删除）

        :param db_session: 数据库会话
        :param enrollment_id: 选课记录ID
        :return: None
        """
        stmt = delete(EduStudentCourse).where(EduStudentCourse.id == enrollment_id)
        await db_session.execute(stmt)
        await db_session.flush()

    @staticmethod
    async def get_by_id(enrollment_id: int, db_session: AsyncSession) -> EduStudentCourse | None:
        """根据选课记录ID查询

        :param db_session: 数据库会话
        :param enrollment_id: 选课记录ID
        :return: 选课记录对象
        """
        stmt = select(EduStudentCourse).where(EduStudentCourse.id == enrollment_id)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_student_course(student_id: int, course_id: int, db_session: AsyncSession) -> EduStudentCourse | None:
        """根据学生ID和课程ID查询（唯一性检查）

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param course_id: 课程ID
        :return: 选课记录对象
        """
        stmt = select(EduStudentCourse).where(
            EduStudentCourse.student_id == student_id, EduStudentCourse.course_id == course_id
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_student_course_list(
        db: AsyncSession, query_object: StudentCourseQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[tuple[EduStudentCourse, EduCourse | None]], int]:
        """查询学生的选课列表（联表查询课程信息）

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为选课列表，total为总数
        """
        # 构建基础查询条件
        base_conditions = []

        if query_object.student_id:
            base_conditions.append(EduStudentCourse.student_id == query_object.student_id)
        if query_object.course_id:
            base_conditions.append(EduStudentCourse.course_id == query_object.course_id)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduStudentCourse.enroll_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建主查询（关联 edu_course 表）
        query = (
            select(EduStudentCourse, EduCourse)
            .join(
                EduCourse,
                and_(
                    EduStudentCourse.course_id == EduCourse.course_id,
                    EduCourse.status != SystemConstants.Status.DELETED,
                ),
                isouter=True,
            )
            .where(and_(*base_conditions))
            .order_by(EduStudentCourse.enroll_time.desc())
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count(func.distinct(EduStudentCourse.id)))
            .select_from(EduStudentCourse)
            .join(
                EduCourse,
                and_(
                    EduStudentCourse.course_id == EduCourse.course_id,
                    EduCourse.status != SystemConstants.Status.DELETED,
                ),
                isouter=True,
            )
            .where(and_(*base_conditions))
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.all()

        return rows, total

    @staticmethod
    async def get_course_student_list(
        db: AsyncSession, course_id: int, is_page: bool = False, page: int = 1, size: int = 10
    ) -> tuple[Sequence[tuple[EduStudentCourse, EduStudent | None]], int]:
        """查询课程的学生列表（联表查询学生信息）

        :param db: 数据库会话
        :param course_id: 课程ID
        :param is_page: 是否开启分页
        :param page: 页码
        :param size: 每页数量
        :return: (rows, total) 元组，rows为学生列表，total为总数
        """
        # 构建基础查询条件
        base_conditions = [
            EduStudentCourse.course_id == course_id,
            EduStudent.status != SystemConstants.Status.DELETED,
        ]

        # 构建主查询（关联 edu_student 表）
        query = (
            select(EduStudentCourse, EduStudent)
            .join(
                EduStudent,
                and_(
                    EduStudentCourse.student_id == EduStudent.student_id,
                    EduStudent.status != SystemConstants.Status.DELETED,
                ),
                isouter=True,
            )
            .where(and_(*base_conditions))
            .order_by(EduStudentCourse.enroll_time.desc())
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count(func.distinct(EduStudentCourse.id)))
            .select_from(EduStudentCourse)
            .join(
                EduStudent,
                and_(
                    EduStudentCourse.student_id == EduStudent.student_id,
                    EduStudent.status != SystemConstants.Status.DELETED,
                ),
                isouter=True,
            )
            .where(and_(*base_conditions))
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and page and size:
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

        result = await db.execute(query)
        rows = result.all()

        return rows, total

    @staticmethod
    async def update_progress(enrollment: EduStudentCourse, db_session: AsyncSession) -> None:
        """更新选课记录（包括学习进度和最后学习时间）

        :param db_session: 数据库会话
        :param enrollment: 选课记录信息
        :return: None
        """
        await db_session.merge(enrollment)
        await db_session.flush()

    @staticmethod
    async def get_student_course_overview(
        student_id: int, course_id: int, db_session: AsyncSession
    ) -> tuple[EduStudentCourse | None, dict, list]:
        """查询学生课程学习概览数据

        :param student_id: 学生ID
        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: (选课记录, 课程统计, 每日活跃度) 元组
        """
        # 1. 获取选课记录
        enrollment = await StudentCourseMapper.get_student_course(student_id, course_id, db_session)

        # 2. 课程整体统计（总学生数、平均进度、今日活跃）
        today = datetime.now().date()

        # 查询课程总学生数和平均进度
        course_stats_query = select(
            func.count(EduStudentCourse.id).label("total_students"),
            func.avg(EduStudentCourse.progress).label("average_progress"),
        ).where(EduStudentCourse.course_id == course_id)
        course_stats_result = await db_session.execute(course_stats_query)
        course_stats_row = course_stats_result.first()

        # 查询今日活跃学生数（今日有学习记录的学生数）
        # today_active_query = (
        #     select(func.count(func.distinct(EduStudentRecord.student_id)))
        #     .join(
        #         EduStudentCourse,
        #         EduStudentRecord.student_id == EduStudentCourse.student_id,
        #     )
        #     .where(EduStudentCourse.course_id == course_id, EduStudentRecord.study_date == today)
        # )
        # today_active_result = await db_session.execute(today_active_query)
        # today_active = today_active_result.scalar() or 0

        course_stats = {
            "total_students": course_stats_row.total_students or 0,
            "average_progress": int(course_stats_row.average_progress or 0),
            "today_active": 0,  # TODO: 实现今日活跃统计
        }

        # 3. 查询最近7天学习活跃度
        from datetime import timedelta

        seven_days_ago = today - timedelta(days=6)

        # daily_active_query = (
        #     select(
        #         EduStudentRecord.study_date.label("date"),
        #         func.sum(EduStudentRecord.study_duration).label("active_minutes"),
        #     )
        #     .where(EduStudentRecord.student_id == student_id, EduStudentRecord.course_id == course_id)
        #     .where(EduStudentRecord.study_date >= seven_days_ago)
        #     .group_by(EduStudentRecord.study_date)
        #     .order_by(EduStudentRecord.study_date)
        # )
        # daily_active_result = await db_session.execute(daily_active_query)
        # daily_active_rows = daily_active_result.all()

        # daily_active = [
        #     {"date": row.date.strftime("%m-%d"), "active_minutes": row.active_minutes or 0}
        #     for row in daily_active_rows
        # ]

        # 补充缺失的日期（确保7天数据完整）
        # date_map = {item["date"]: item["active_minutes"] for item in daily_active}
        complete_daily_active = []
        for i in range(7):
            current_date = seven_days_ago + timedelta(days=i)
            date_str = current_date.strftime("%m-%d")
            complete_daily_active.append(
                {
                    "date": date_str,
                    "active_minutes": 0,  # TODO: 实现每日活跃统计
                }
            )

        return enrollment, course_stats, complete_daily_active

    @staticmethod
    async def get_student_chapter_progress(
        student_id: int, course_id: int, db_session: AsyncSession
    ) -> tuple[int, int]:
        """查询学生章节学习进度统计

        :param student_id: 学生ID
        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: (已完成章节数, 总章节数) 元组
        """
        from sqlalchemy import text

        from graphedu.common.models.orm.education import EduChapter

        # 查询课程的总章节数
        total_chapters_query = select(func.count(EduChapter.chapter_id)).where(
            EduChapter.course_id == course_id, EduChapter.status != SystemConstants.Status.DELETED
        )
        total_chapters_result = await db_session.execute(total_chapters_query)
        total_chapters = total_chapters_result.scalar() or 0

        # 查询学生已完成的章节数（通过物化视图）
        completed_chapters_query = text(
            "SELECT COUNT(*) FROM public.mv_chapter_progress mv "
            "JOIN public.edu_chapter c ON c.chapter_id = mv.chapter_id "
            "WHERE mv.student_id = :student_id AND c.course_id = :course_id "
            "AND mv.is_completed = 'Y' AND c.status != '2'"
        )
        completed_chapters_result = await db_session.execute(
            completed_chapters_query, {"student_id": student_id, "course_id": course_id}
        )
        completed_chapters = completed_chapters_result.scalar() or 0

        return completed_chapters, total_chapters

    @staticmethod
    async def get_course_stats(course_id: int, db_session: AsyncSession) -> dict[str, int]:
        """查询课程整体统计数据（平均进度、今日活跃、总学生数）

        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: 包含 total_students, average_progress, today_active 的字典
        """
        today = date.today()

        # 总学生数 + 平均进度
        stats_query = select(
            func.count(EduStudentCourse.id).label("total_students"),
            func.avg(EduStudentCourse.progress).label("average_progress"),
        ).where(EduStudentCourse.course_id == course_id)
        stats_result = await db_session.execute(stats_query)
        stats_row = stats_result.first()

        # 今日活跃学生数（今日有学习事件的不同学生数）
        today_start = datetime.combine(today, time(0, 0, 0))
        today_active_query = select(func.count(func.distinct(EduStudentLearningEvent.student_id))).where(
            EduStudentLearningEvent.course_id == course_id,
            EduStudentLearningEvent.create_time >= today_start,
        )
        today_active_result = await db_session.execute(today_active_query)
        today_active = today_active_result.scalar() or 0

        return {
            "total_students": stats_row.total_students or 0,
            "average_progress": int(stats_row.average_progress or 0),
            "today_active": today_active,
        }

    @staticmethod
    async def get_student_chapter_detail_progress(
        student_id: int, course_id: int, db_session: AsyncSession
    ) -> list[dict]:
        """查询学生在课程下的章节+资源详细进度

        :param student_id: 学生ID
        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: 章节进度列表（含资源进度）
        """
        from sqlalchemy import text as sa_text

        from graphedu.common.models.orm.education import (
            EduChapter,
            EduChapterResource,
            EduStudentResourceProgress,
        )

        # 1. 查询课程所有章节
        chapters_query = (
            select(EduChapter)
            .where(EduChapter.course_id == course_id, EduChapter.status != SystemConstants.Status.DELETED)
            .order_by(EduChapter.chapter_no)
        )
        chapters_result = await db_session.execute(chapters_query)
        chapters = list(chapters_result.scalars().all())

        # 2. 查询学生章节完成进度（从物化视图）
        chapter_progress_map: dict[int, dict] = {}
        if chapters:
            chapter_ids = [c.chapter_id for c in chapters]
            mv_query = sa_text(
                "SELECT chapter_id, completion_rate, is_completed, last_visit_time "
                "FROM public.mv_chapter_progress WHERE student_id = :sid AND chapter_id = ANY(:cids)"
            )
            mv_result = await db_session.execute(mv_query, {"sid": student_id, "cids": chapter_ids})
            for row in mv_result:
                chapter_progress_map[row.chapter_id] = {
                    "completion_rate": row.completion_rate or 0,
                    "is_completed": row.is_completed or "N",
                    "last_visit_time": row.last_visit_time,
                }

        # 3. 查询学生资源阅读进度
        resource_progress_map: dict[int, dict] = {}
        rp_query = (
            select(EduStudentResourceProgress, EduChapterResource.resource_name)
            .join(
                EduChapterResource,
                EduStudentResourceProgress.resource_id == EduChapterResource.resource_id,
            )
            .where(
                EduStudentResourceProgress.student_id == student_id,
                EduStudentResourceProgress.course_id == course_id,
            )
        )
        rp_result = await db_session.execute(rp_query)
        for rp, res_name in rp_result:
            resource_progress_map[rp.resource_id] = {
                "resource_name": res_name,
                "resource_type": rp.resource_type,
                "completion_rate": rp.completion_rate or 0,
                "is_completed": rp.is_completed or "N",
                "view_count": rp.view_count or 0,
                "total_duration": rp.total_duration or 0,
                "last_view_time": rp.last_view_time,
            }

        # 4. 查询每章节下所有资料
        chapter_resources_map: dict[int, list] = {}
        if chapters:
            resources_query = (
                select(EduChapterResource)
                .where(EduChapterResource.chapter_id.in_(chapter_ids))
                .order_by(EduChapterResource.resource_id)
            )
            resources_result = await db_session.execute(resources_query)
            for res in resources_result.scalars().all():
                if res.chapter_id not in chapter_resources_map:
                    chapter_resources_map[res.chapter_id] = []
                chapter_resources_map[res.chapter_id].append(res)

        # 5. 组装结果
        result = []
        for ch in chapters:
            cp = chapter_progress_map.get(ch.chapter_id, {})
            all_resources = chapter_resources_map.get(ch.chapter_id, [])
            completed_count = sum(
                1
                for r in all_resources
                if resource_progress_map.get(r.resource_id, {}).get("is_completed") == "Y"
            )

            resources_vo = []
            for r in all_resources:
                rp = resource_progress_map.get(r.resource_id)
                if rp:
                    resources_vo.append({
                        "resource_id": r.resource_id,
                        "resource_name": rp["resource_name"],
                        "resource_type": rp["resource_type"],
                        "completion_rate": rp["completion_rate"],
                        "is_completed": rp["is_completed"],
                        "view_count": rp["view_count"],
                        "total_duration": rp["total_duration"],
                        "last_view_time": rp["last_view_time"],
                    })
                else:
                    resources_vo.append({
                        "resource_id": r.resource_id,
                        "resource_name": r.resource_name,
                        "resource_type": r.resource_type,
                        "completion_rate": 0,
                        "is_completed": "N",
                        "view_count": 0,
                        "total_duration": 0,
                        "last_view_time": None,
                    })

            result.append({
                "chapter_id": ch.chapter_id,
                "chapter_name": ch.chapter_name,
                "chapter_no": ch.chapter_no or 0,
                "parent_id": ch.parent_id or 0,
                "completion_rate": cp.get("completion_rate", 0),
                "is_completed": cp.get("is_completed", "N"),
                "resource_count": len(all_resources),
                "completed_resource_count": completed_count,
                "last_visit_time": cp.get("last_visit_time"),
                "resources": resources_vo,
            })

        return result
