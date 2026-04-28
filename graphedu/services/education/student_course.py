"""选课管理服务模块

该模块提供选课信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import date, datetime, timedelta
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.course import CourseNotFoundException
from graphedu.common.exceptions.services.education.student import StudentNotFoundException
from graphedu.common.exceptions.services.education.student_course import (
    CourseNotAvailableException,
    StudentCourseAlreadyExistsException,
    StudentCourseNotFoundException,
)
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.course import StudentCourseQueryDTO, StudentCourseUpdateDTO
from graphedu.common.models.orm.education import EduCourse, EduStudentCourse
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.educationv2.course import (
    CourseListVO,
    CourseStudentStatsVO,
    StudentCourseDetailVO,
    StudentCourseListVO,
)
from graphedu.common.models.vo.educationv2.stats import (
    StudentChapterProgressVO,
    StudentCourseOverviewVO,
    StudentDailyActiveItemVO,
    StudentKnowledgeProfileVO,
    StudentResourceProgressItemVO,
    StudentWeakPointVO,
)
from graphedu.common.resource import AioS3Client
from graphedu.mapper.education.course import CourseMapper
from graphedu.mapper.education.student import StudentMapper
from graphedu.mapper.education.student_course import StudentCourseMapper
from graphedu.mapper.education.study_analytics import StudyAnalyticsMapper
from graphedu.services.system.upload import UploadService

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_course_orm_to_list_vo(course_orm) -> CourseListVO:
    """将课程 ORM 对象转换为 CourseListVO。

    Args:
        course_orm: 课程 ORM 对象。

    Returns:
        CourseListVO: 课程列表项 VO。
    """
    return CourseListVO(
        course_id=course_orm.course_id,
        course_code=course_orm.course_code,
        course_name=course_orm.course_name,
        faculty=course_orm.faculty,
        cover_file_id=course_orm.cover_file_id,
        cover_url=None,  # 如果需要封面URL，需要额外查询
        status=course_orm.status,
        is_public=course_orm.is_public,
        student_count=course_orm.student_count,
        view_count=course_orm.view_count,
        create_time=course_orm.create_time,
        teacher_id=None,  # 如果需要教师信息，需要额外查询
        teacher_name=None,
    )


def _convert_student_course_orm_to_list_vo(
    enrollment_orm: EduStudentCourse, course_orm: EduCourse = None
) -> StudentCourseListVO:
    """将选课 ORM 对象转换为 StudentCourseListVO。

    Args:
        enrollment_orm: 选课 ORM 对象。
        course_orm: 课程 ORM 对象（可选）。

    Returns:
        StudentCourseListVO: 选课列表项 VO。
    """
    # 从课程 ORM 获取课程信息
    course_name = course_orm.course_name if course_orm else None
    course_code = course_orm.course_code if course_orm else None
    cover_file_id = course_orm.cover_file_id if course_orm else None

    return StudentCourseListVO(
        id=enrollment_orm.id,
        student_id=enrollment_orm.student_id,
        course_id=enrollment_orm.course_id,
        enroll_time=enrollment_orm.enroll_time,
        progress=enrollment_orm.progress,
        last_study_time=enrollment_orm.last_study_time,
        course_name=course_name,
        course_code=course_code,
        cover_file_id=cover_file_id,
        cover_url=None,  # 由 Service 层通过 UploadService 填充
    )


def _convert_student_course_orm_to_detail_vo(
    enrollment_orm: EduStudentCourse, course_vo: CourseListVO | None = None
) -> StudentCourseDetailVO:
    """将选课 ORM 对象转换为 StudentCourseDetailVO。

    Args:
        enrollment_orm: 选课 ORM 对象。
        course_vo: 课程列表 VO（可选）。

    Returns:
        StudentCourseDetailVO: 选课详细信息 VO。
    """
    return StudentCourseDetailVO(
        id=enrollment_orm.id,
        student_id=enrollment_orm.student_id,
        course_id=enrollment_orm.course_id,
        enroll_time=enrollment_orm.enroll_time,
        progress=enrollment_orm.progress,
        last_study_time=enrollment_orm.last_study_time,
        course=course_vo,
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_course_available(course_id: int, query_db: AsyncSession):
    """检查课程是否可选（状态正常且公开）。

    Args:
        course_id: 课程ID。
        query_db: 数据库会话。

    Returns:
        EduCourse: 课程对象。

    Raises:
        CourseNotFoundException: 课程不存在。
        CourseNotAvailableException: 课程不可选。
    """
    course = await CourseMapper.get_by_id(course_id, query_db)
    if not course:
        raise CourseNotFoundException(course_id)

    if course.status != "0":
        raise CourseNotAvailableException(course_id, message=f"课程 {course_id} 已停用")

    if course.is_public != "Y":
        raise CourseNotAvailableException(course_id, message=f"课程 {course_id} 未公开")

    return course


async def _check_already_enrolled(student_id: int, course_id: int, query_db: AsyncSession):
    """检查是否已选过该课程。

    Args:
        student_id: 学生ID。
        course_id: 课程ID。
        query_db: 数据库会话。

    Raises:
        StudentCourseAlreadyExistsException: 学生已选过该课程。
    """
    existing = await StudentCourseMapper.get_student_course(student_id, course_id, query_db)
    if existing:
        raise StudentCourseAlreadyExistsException(student_id=student_id, course_id=course_id)


async def _check_enrollment_exists(enrollment_id: int, query_db: AsyncSession):
    """检查选课记录是否存在。

    Args:
        enrollment_id: 选课记录ID。
        query_db: 数据库会话。

    Returns:
        EduStudentCourse: 选课记录对象。

    Raises:
        StudentCourseNotFoundException: 选课记录不存在。
    """
    enrollment = await StudentCourseMapper.get_by_id(enrollment_id, query_db)
    if not enrollment:
        raise StudentCourseNotFoundException(enrollment_id=enrollment_id)
    return enrollment


# ============================================================================
# StudentCourseService 类
# ============================================================================


class StudentCourseService:
    """选课管理服务类

    提供选课的增删改查功能。
    """

    @staticmethod
    async def assign_course_to_student(
        query_db: AsyncSession,
        student_id: int,
        course_id: int,
        current_user: CurrentUser | None,
        s3_client: AioS3Client | None = None,
    ) -> StudentCourseDetailVO:
        """为学生派发课程（管理员操作）。

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。
            current_user: 当前登录用户。
            s3_client: S3 客户端（可选）。

        Returns:
            StudentCourseDetailVO: 创建成功的选课 VO。

        Raises:
            CourseNotFoundException: 课程不存在。
            CourseNotAvailableException: 课程不可选。
            StudentCourseAlreadyExistsException: 学生已选过该课程。
            Exception: 其他异常。
        """
        # 1. 检查学生是否存在
        student = await StudentMapper.get_by_id(student_id, query_db)
        if not student:
            raise StudentNotFoundException(student_id=student_id)

        # 2. 检查课程是否可用
        course = await _check_course_available(course_id, query_db)

        # 3. 检查是否已派发过
        await _check_already_enrolled(student_id, course_id, query_db)

        # 4. 创建选课记录
        new_enrollment = EduStudentCourse(
            student_id=student_id,
            course_id=course_id,
            enroll_time=datetime.now(),
            progress=0,
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
        )
        await StudentCourseMapper.enroll_course(new_enrollment, query_db)

        # 5. 更新课程的学生计数
        course.student_count = (course.student_count or 0) + 1
        await CourseMapper.update(course, query_db)

        # 6. 更新学生的课程计数
        student.course_count = (student.course_count or 0) + 1
        await StudentMapper.update(student, query_db)

        logger.info(f"为学生 {student_id} 派发课程 {course_id} 成功")

        # 7. 返回选课详情
        course_vo = _convert_course_orm_to_list_vo(course)

        # 获取封面 URL
        if s3_client and course_vo.cover_file_id:
            course_vo.cover_url = await UploadService.get_file_url(course_vo.cover_file_id, query_db, s3_client)

        return _convert_student_course_orm_to_detail_vo(new_enrollment, course_vo)

    @staticmethod
    async def batch_assign_courses(
        query_db: AsyncSession, student_ids: list[int], course_id: int, current_user: CurrentUser | None
    ) -> dict:
        """批量派发课程（管理员操作，部分成功模式）。

        Args:
            query_db: 数据库会话。
            student_ids: 学生ID列表。
            course_id: 课程ID。
            current_user: 当前登录用户。

        Returns:
            dict: 包含 success_count, fail_count, results 的字典
        """
        from typing import TypedDict

        class BatchResultItem(TypedDict):
            student_id: int
            success: bool
            error: str | None

        results: list[BatchResultItem] = []
        success_count = 0
        fail_count = 0

        for student_id in student_ids:
            try:
                # 检查学生是否存在
                student = await StudentMapper.get_by_id(student_id, query_db)
                if not student:
                    results.append({"student_id": student_id, "success": False, "error": f"学生 {student_id} 不存在"})
                    fail_count += 1
                    continue

                # 检查是否已派发过
                existing = await StudentCourseMapper.get_student_course(student_id, course_id, query_db)
                if existing:
                    results.append(
                        {"student_id": student_id, "success": False, "error": f"学生 {student_id} 已选过该课程"}
                    )
                    fail_count += 1
                    continue

                # 创建选课记录
                new_enrollment = EduStudentCourse(
                    student_id=student_id,
                    course_id=course_id,
                    enroll_time=datetime.now(),
                    progress=0,
                    create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
                )
                await StudentCourseMapper.enroll_course(new_enrollment, query_db)

                results.append({"student_id": student_id, "success": True, "error": None})
                success_count += 1

            except Exception as e:
                results.append({"student_id": student_id, "success": False, "error": str(e)})
                fail_count += 1

        # 更新课程的学生计数（只统计成功的）
        if success_count > 0:
            course = await CourseMapper.get_by_id(course_id, query_db)
            if course:
                course.student_count = (course.student_count or 0) + success_count
                await CourseMapper.update(course, query_db)

            # 更新学生的课程计数（只统计成功的）
            for student_id in [r["student_id"] for r in results if r["success"]]:
                student = await StudentMapper.get_by_id(student_id, query_db)
                if student:
                    student.course_count = (student.course_count or 0) + 1
                    await StudentMapper.update(student, query_db)

        logger.info(f"批量派发课程 {course_id} 完成: 成功 {success_count}, 失败 {fail_count}")

        return {"success_count": success_count, "fail_count": fail_count, "results": results}

    @staticmethod
    async def revoke_course_from_student(query_db: AsyncSession, enrollment_id: int, current_user: CurrentUser) -> None:
        """撤销学生的课程（管理员操作）。

        Args:
            query_db: 数据库会话。
            enrollment_id: 选课记录ID。
            current_user: 当前用户。

        Raises:
            StudentCourseNotFoundException: 选课记录不存在。
        """
        # 1. 检查选课记录是否存在
        enrollment = await _check_enrollment_exists(enrollment_id, query_db)

        # 2. 删除选课记录
        await StudentCourseMapper.drop_course(enrollment_id, query_db)

        # 3. 更新课程的学生计数
        course = await CourseMapper.get_by_id(enrollment.course_id, query_db)
        if course and course.student_count and course.student_count > 0:
            course.student_count -= 1
            await CourseMapper.update(course, query_db)

        # 4. 更新学生的课程计数
        student = await StudentMapper.get_by_id(enrollment.student_id, query_db)
        if student and student.course_count and student.course_count > 0:
            student.course_count -= 1
            await StudentMapper.update(student, query_db)

        logger.info(f"撤销选课记录 {enrollment_id} 成功")

    @staticmethod
    async def get_student_course_list(
        query_db: AsyncSession, query_object: StudentCourseQueryDTO, s3_client: AioS3Client | None = None
    ) -> PageResponse[StudentCourseListVO]:
        """查询学生的选课列表。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。
            s3_client: S3 客户端（可选）。

        Returns:
            PageResponse[StudentCourseListVO]: 分页结果。
        """
        rows, total = await StudentCourseMapper.get_student_course_list(query_db, query_object, is_page=True)

        # 将 ORM 对象转换为 StudentCourseListVO
        enrollment_list = []
        for row in rows:
            enrollment_orm = row[0]
            course_orm = row[1]
            enrollment_list.append(_convert_student_course_orm_to_list_vo(enrollment_orm, course_orm))

        # 批量获取封面 URL
        if s3_client:
            cover_file_ids = [item.cover_file_id for item in enrollment_list if item.cover_file_id]
            if cover_file_ids:
                url_map = await UploadService.get_file_url_map(cover_file_ids, query_db, s3_client)
                for item in enrollment_list:
                    if item.cover_file_id:
                        item.cover_url = url_map.get(item.cover_file_id)

        return PageResponse(rows=enrollment_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def update_learning_progress(
        query_db: AsyncSession, student_id: int, update_data: StudentCourseUpdateDTO
    ) -> None:
        """更新学习进度（0-100）。

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            update_data: 更新数据 DTO。

        Raises:
            StudentCourseNotFoundException: 选课记录不存在。
        """
        # 1. 获取选课记录
        enrollment = await StudentCourseMapper.get_student_course(student_id, update_data.course_id, query_db)
        if not enrollment:
            raise StudentCourseNotFoundException

        # 2. 更新进度和最后学习时间
        enrollment.progress = update_data.progress
        enrollment.last_study_time = datetime.now()
        await StudentCourseMapper.update_progress(enrollment, query_db)

        logger.info(f"更新学习进度成功: 学生 {student_id}, 课程 {update_data.course_id}, 进度 {update_data.progress}%")

    @staticmethod
    async def get_enrollment_detail(
        query_db: AsyncSession, enrollment_id: int, s3_client: AioS3Client | None = None
    ) -> StudentCourseDetailVO | None:
        """获取选课详细信息。

        Args:
            query_db: 数据库会话。
            enrollment_id: 选课记录ID。
            s3_client: S3 客户端（可选）。

        Returns:
            StudentCourseDetailVO | None: 选课详细信息 VO。
        """
        enrollment = await StudentCourseMapper.get_by_id(enrollment_id, query_db)
        if not enrollment:
            return None

        # 获取课程信息
        course = await CourseMapper.get_by_id(enrollment.course_id, query_db)
        course_vo = _convert_course_orm_to_list_vo(course) if course else None

        # 获取封面 URL
        if s3_client and course_vo and course_vo.cover_file_id:
            course_vo.cover_url = await UploadService.get_file_url(course_vo.cover_file_id, query_db, s3_client)

        return _convert_student_course_orm_to_detail_vo(enrollment, course_vo)

    @staticmethod
    async def join_course(
        query_db: AsyncSession,
        student_id: int,
        course_id: int,
        current_user: CurrentUser | None,
        s3_client: AioS3Client | None = None,
    ) -> StudentCourseDetailVO:
        """学生自主选课。

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。
            current_user: 当前登录用户。
            s3_client: S3 客户端（可选）。

        Returns:
            StudentCourseDetailVO: 创建成功的选课 VO。

        Raises:
            StudentNotFoundException: 学生不存在。
            CourseNotFoundException: 课程不存在。
            CourseNotAvailableException: 课程不可选（未公开或已停用）。
            StudentCourseAlreadyExistsException: 学生已选过该课程。
        """
        # 1. 检查学生是否存在
        student = await StudentMapper.get_by_id(student_id, query_db)
        if not student:
            raise StudentNotFoundException(student_id=student_id)

        # 2. 检查课程是否可用（必须公开且状态正常）
        course = await _check_course_available(course_id, query_db)

        # 3. 检查是否已选过
        await _check_already_enrolled(student_id, course_id, query_db)

        # 4. 创建选课记录
        new_enrollment = EduStudentCourse(
            student_id=student_id,
            course_id=course_id,
            enroll_time=datetime.now(),
            progress=0,
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
        )
        await StudentCourseMapper.enroll_course(new_enrollment, query_db)

        # 5. 更新课程的学生计数
        course.student_count = (course.student_count or 0) + 1
        await CourseMapper.update(course, query_db)

        # 6. 更新学生的课程计数
        student.course_count = (student.course_count or 0) + 1
        await StudentMapper.update(student, query_db)

        logger.info(f"学生 {student_id} 自主选课 {course_id} 成功")

        # 7. 返回选课详情
        course_vo = _convert_course_orm_to_list_vo(course)

        # 获取封面 URL
        if s3_client and course_vo.cover_file_id:
            course_vo.cover_url = await UploadService.get_file_url(course_vo.cover_file_id, query_db, s3_client)

        return _convert_student_course_orm_to_detail_vo(new_enrollment, course_vo)

    @staticmethod
    async def leave_course(query_db: AsyncSession, student_id: int, course_id: int) -> None:
        """学生退出课程。

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。

        Raises:
            StudentCourseNotFoundException: 选课记录不存在。
        """
        # 1. 获取选课记录
        enrollment = await StudentCourseMapper.get_student_course(student_id, course_id, query_db)
        if not enrollment:
            raise StudentCourseNotFoundException

        enrollment_id = enrollment.id

        # 2. 删除选课记录
        await StudentCourseMapper.drop_course(enrollment_id, query_db)

        # 3. 更新课程的学生计数
        course = await CourseMapper.get_by_id(course_id, query_db)
        if course and course.student_count and course.student_count > 0:
            course.student_count -= 1
            await CourseMapper.update(course, query_db)

        # 4. 更新学生的课程计数
        student = await StudentMapper.get_by_id(student_id, query_db)
        if student and student.course_count and student.course_count > 0:
            student.course_count -= 1
            await StudentMapper.update(student, query_db)

        logger.info(f"学生 {student_id} 退出课程 {course_id} 成功")

    @staticmethod
    async def get_course_overview(
        query_db: AsyncSession,
        student_id: int,
        course_id: int,
        week_start: datetime | None = None,
    ) -> StudentCourseOverviewVO:
        """获取学生课程学习概览（消费 SQL 视图）

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。
            week_start: 周一日期（可选，默认本周一）。

        Returns:
            StudentCourseOverviewVO: 学生课程学习概览。
        """
        # 顺序查询聚合数据（AsyncSession 不支持并发操作）
        course_progress = await StudyAnalyticsMapper.get_my_course_progress(student_id, course_id, query_db)
        streak = await StudyAnalyticsMapper.get_my_study_streak(student_id, course_id, query_db)
        ranking = await StudyAnalyticsMapper.get_my_ranking(student_id, course_id, query_db)

        # 从选课记录获取进度（三层 rollup 维护的字段）
        enrollment = await StudentCourseMapper.get_student_course(student_id, course_id, query_db)
        progress = enrollment.progress if enrollment else 0

        # 章节进度统计（从物化视图获取真正完成的章节数）
        completed_chapters, total_chapters = await StudentCourseMapper.get_student_chapter_progress(
            student_id, course_id, query_db
        )

        # 累计学习时长（分钟） — Mapper 返回 dict
        total_study_seconds = course_progress.get("total_study_seconds", 0) if course_progress else 0
        total_study_time = round((total_study_seconds or 0) / 60)

        # 连续学习天数 — Mapper 返回 dict 或 None
        consecutive_days = streak.get("current_streak", 0) if streak else 0

        # 排名百分位 — Mapper 返回 dict 或 None
        rank_percentile = None
        if ranking and ranking.get("mastery_percentile") is not None:
            pct = float(ranking["mastery_percentile"]) * 100
            if pct <= 5:
                rank_percentile = "Top 5%"
            elif pct <= 10:
                rank_percentile = "Top 10%"
            elif pct <= 20:
                rank_percentile = "Top 20%"
            elif pct <= 30:
                rank_percentile = "Top 30%"
            elif pct <= 50:
                rank_percentile = "Top 50%"
            else:
                rank_percentile = f"Top {int(pct)}%"

        # 最后学习时间
        last_study_time = course_progress.get("last_event_time") if course_progress else None

        # 课程整体统计（从 edu_student_course 实时聚合）
        course_stats_raw = await StudentCourseMapper.get_course_stats(course_id, query_db)
        course_stats = CourseStudentStatsVO(
            total_students=course_stats_raw["total_students"],
            average_progress=course_stats_raw["average_progress"],
            completed_students=course_stats_raw.get("completed_students", 0),
            today_active=course_stats_raw["today_active"],
        )

        # 每日学习活跃度（按指定周补齐7天） — Mapper 返回 dict 列表
        if week_start is not None:
            monday = week_start.date() if isinstance(week_start, datetime) else week_start
        else:
            today = date.today()
            monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        days_range = (sunday - monday).days + 1
        daily_summary = await StudyAnalyticsMapper.get_my_daily_summary(
            student_id, course_id, query_db, days=days_range + 7
        )
        summary_map: dict[str, int] = {}
        for row in daily_summary:
            row_date = row["study_date"]
            row_date_val = row_date.date() if hasattr(row_date, "date") else row_date
            if monday <= row_date_val <= sunday:
                active_minutes = round((row.get("total_study_seconds") or 0) / 60)
                date_key = row_date_val.strftime("%m-%d")
                summary_map[date_key] = active_minutes

        daily_active = []
        for i in range(7):
            current_date = monday + timedelta(days=i)
            date_str = current_date.strftime("%m-%d")
            daily_active.append(
                StudentDailyActiveItemVO(
                    date=date_str,
                    active_minutes=summary_map.get(date_str, 0),
                )
            )

        return StudentCourseOverviewVO(
            course_id=course_id,
            student_id=student_id,
            progress=progress or 0,
            completed_chapters=completed_chapters or 0,
            total_chapters=total_chapters or 0,
            total_study_time=total_study_time,
            last_study_time=last_study_time,
            consecutive_days=consecutive_days or 0,
            rank_percentile=rank_percentile,
            course_stats=course_stats,
            daily_active=daily_active,
        )

    @staticmethod
    async def _calculate_rank_percentile(student_progress: int, course_id: int, query_db: AsyncSession) -> str | None:
        """计算学生在课程中的排名百分位

        Args:
            student_progress: 学生的学习进度。
            course_id: 课程ID。
            query_db: 数据库会话。

        Returns:
            str | None: 排名百分位（如 'Top 5%'），如果无法计算则返回 None。
        """
        # 查询课程中进度大于等于当前学生的学生数
        better_or_equal_count_query = select(func.count(EduStudentCourse.id)).where(
            EduStudentCourse.course_id == course_id, EduStudentCourse.progress >= student_progress
        )
        better_or_equal_count_result = await query_db.execute(better_or_equal_count_query)
        better_or_equal_count = better_or_equal_count_result.scalar() or 0

        # 查询课程总学生数
        total_count_query = select(func.count(EduStudentCourse.id)).where(EduStudentCourse.course_id == course_id)
        total_count_result = await query_db.execute(total_count_query)
        total_count = total_count_result.scalar() or 1  # 避免除以0

        if total_count == 0:
            return None

        # 计算排名百分位（进度越高，百分位越靠前）
        percentile = (better_or_equal_count / total_count) * 100

        # 格式化为 "Top X%" 的形式
        if percentile <= 5:
            return "Top 5%"
        if percentile <= 10:
            return "Top 10%"
        if percentile <= 20:
            return "Top 20%"
        if percentile <= 30:
            return "Top 30%"
        if percentile <= 50:
            return "Top 50%"
        return f"Top {int(percentile)}%"

    @staticmethod
    async def get_chapter_progress(
        query_db: AsyncSession, student_id: int, course_id: int
    ) -> list[StudentChapterProgressVO]:
        """获取学生在课程下的章节+资源学习进度

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。

        Returns:
            list[StudentChapterProgressVO]: 章节进度列表。
        """
        raw = await StudentCourseMapper.get_student_chapter_detail_progress(student_id, course_id, query_db)
        result = []
        for item in raw:
            resources = [
                StudentResourceProgressItemVO(**rp) for rp in item["resources"]
            ]
            result.append(
                StudentChapterProgressVO(
                    chapter_id=item["chapter_id"],
                    chapter_name=item["chapter_name"],
                    chapter_no=item["chapter_no"],
                    parent_id=item["parent_id"],
                    completion_rate=item["completion_rate"],
                    is_completed=item["is_completed"],
                    resource_count=item["resource_count"],
                    completed_resource_count=item["completed_resource_count"],
                    last_visit_time=item["last_visit_time"],
                    resources=resources,
                )
            )
        return result

    @staticmethod
    async def get_knowledge_profile(
        query_db: AsyncSession, student_id: int, course_id: int
    ) -> list[StudentKnowledgeProfileVO]:
        """获取学生知识点掌握度画像

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。

        Returns:
            list[StudentKnowledgeProfileVO]: 知识点画像列表。
        """
        rows = await StudyAnalyticsMapper.get_my_node_profile(student_id, course_id, query_db)

        # 批量查询知识点名称 — Mapper 返回 dict 列表
        uuids = [row["node_uuid"] for row in rows]
        node_name_map: dict[str, str] = {}
        if uuids:
            from graphedu.common.models.orm.education import EduKnowledgePointEmbedding

            stmt = select(
                EduKnowledgePointEmbedding.node_uuid, EduKnowledgePointEmbedding.title
            ).where(EduKnowledgePointEmbedding.node_uuid.in_(uuids))
            cr = await query_db.execute(stmt)
            node_name_map = {str(r[0]): r[1] for r in cr.all()}

        return [
            StudentKnowledgeProfileVO(
                node_uuid=str(row["node_uuid"]),
                node_name=node_name_map.get(str(row["node_uuid"]), ""),
                first_interaction_at=row.get("first_interaction_at"),
                last_interaction_at=row.get("last_interaction_at"),
                total_interaction_count=row.get("total_interaction_count", 0) or 0,
                total_question_count=row.get("total_question_count", 0) or 0,
                total_interest_count=row.get("total_interest_count", 0) or 0,
                total_explain_request_count=row.get("total_explain_request_count", 0) or 0,
                total_study_seconds=row.get("total_study_seconds", 0) or 0,
                latest_mastery_level=row.get("latest_mastery_level", "") or "",
                latest_mastery_score=float(row["latest_mastery_score"]) if row.get("latest_mastery_score") else None,
                latest_assessed_at=row.get("latest_assessed_at"),
                latest_assessment_reason=row.get("latest_assessment_reason"),
            )
            for row in rows
        ]

    @staticmethod
    async def get_weak_points(query_db: AsyncSession, student_id: int, course_id: int) -> list[StudentWeakPointVO]:
        """获取学生薄弱知识点

        Args:
            query_db: 数据库会话。
            student_id: 学生ID。
            course_id: 课程ID。

        Returns:
            list[StudentWeakPointVO]: 薄弱知识点列表。
        """
        rows = await StudyAnalyticsMapper.get_my_weak_points(student_id, course_id, query_db)

        # 批量查询知识点名称 — Mapper 返回 dict 列表
        uuids = [row["node_uuid"] for row in rows]
        node_name_map: dict[str, str] = {}
        if uuids:
            from graphedu.common.models.orm.education import EduKnowledgePointEmbedding

            stmt = select(
                EduKnowledgePointEmbedding.node_uuid, EduKnowledgePointEmbedding.title
            ).where(EduKnowledgePointEmbedding.node_uuid.in_(uuids))
            cr = await query_db.execute(stmt)
            node_name_map = {str(r[0]): r[1] for r in cr.all()}

        return [
            StudentWeakPointVO(
                node_uuid=str(row["node_uuid"]),
                node_name=node_name_map.get(str(row["node_uuid"]), ""),
                total_interaction_count=row.get("total_interaction_count", 0) or 0,
                total_question_count=row.get("total_question_count", 0) or 0,
                total_study_seconds=row.get("total_study_seconds", 0) or 0,
                latest_mastery_level=row.get("latest_mastery_level", "") or "",
                latest_mastery_score=float(row["latest_mastery_score"]) if row.get("latest_mastery_score") else None,
                latest_assessed_at=row.get("latest_assessed_at"),
                effort_ratio=round(float(row.get("effort_ratio", 0) or 0), 2),
            )
            for row in rows
        ]
