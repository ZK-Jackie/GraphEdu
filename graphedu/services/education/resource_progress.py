"""学生资料阅读进度服务模块

职责：
1. 处理前端进度上报（upsert 资料→章节→课程 三层汇总）
2. 提供学生端断点续学查询
"""

from datetime import datetime, timedelta
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education import ChapterNotFoundException
from graphedu.common.exceptions.services.education.chapter_resource import ChapterResourceNotFoundException
from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.event import ResourceProgressReportDTO
from graphedu.common.models.orm.education import (
    EduStudentLearningEvent,
    EduStudentResourceProgress,
)
from graphedu.common.models.vo.educationv2.student_learning_event import StudentResourceProgressDetailVO
from graphedu.mapper.education.chapter import ChapterMapper
from graphedu.mapper.education.chapter_progress import ChapterProgressMapper
from graphedu.mapper.education.chapter_resource import ChapterResourceMapper
from graphedu.mapper.education.resource_progress import ResourceProgressMapper

logger = logging.getLogger(__name__)

# 距上次查阅超过此间隔视为新一次阅读（分钟）
_NEW_VIEW_THRESHOLD_MINUTES = 30


# ============================================================================
# completion_rate 自动计算
# ============================================================================


def _calculate_completion_rate(position: dict | None, resource_type: str) -> int | None:
    """根据 position 和 resource_type 自动计算 completion_rate

    :param position: 前端上报的位置数据
    :param resource_type: 资料类型
    :return: 完成度 0-100，无法计算时返回 None
    """
    if not position:
        return None

    match resource_type:
        case "pdf" | "document":
            page = position.get("page")
            total_pages = position.get("total_pages")
            if page is not None and total_pages and int(total_pages) > 0:
                return min(int(page / total_pages * 100), 100)
        case "video":
            video_second = position.get("video_second")
            duration = position.get("duration")
            if video_second is not None and duration and int(duration) > 0:
                return min(int(video_second / duration * 100), 100)
        case "text":
            scroll_percent = position.get("scroll_percent")
            if scroll_percent is not None:
                return min(int(scroll_percent), 100)
        case "image" | "audio":
            return 100

    return None


# ============================================================================
# ORM → VO 转换
# ============================================================================


def _convert_to_detail_vo(orm: EduStudentResourceProgress) -> StudentResourceProgressDetailVO:
    """ORM → DetailVO"""
    return StudentResourceProgressDetailVO.model_validate(orm)


# ============================================================================
# Service
# ============================================================================


class ResourceProgressService:
    """学生资料阅读进度服务类"""

    @staticmethod
    async def report_progress(
        db: AsyncSession,
        report_dto: ResourceProgressReportDTO,
        student_id: int,
    ) -> StudentResourceProgressDetailVO:
        """处理前端进度上报（核心方法：upsert + 双写事件 + 三层汇总）

        :param db: 数据库会话
        :param report_dto: 上报 DTO
        :param student_id: 当前学生ID（从 JWT 获取）
        :return: 更新后的进度详情
        """
        now = datetime.now()

        # 1. 查询资料信息以获取 chapter_id、course_id、resource_type
        resource = await ChapterResourceMapper.get_by_id(report_dto.resource_id, db)
        if not resource:
            raise ChapterResourceNotFoundException(resource_id=report_dto.resource_id)

        chapter_id = resource.chapter_id
        resource_type = resource.resource_type

        chapter = await ChapterMapper.get_by_id(chapter_id, db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)
        course_id = chapter.course_id

        # 2. 计算 completion_rate
        completion_rate = report_dto.completion_rate
        if completion_rate is None or completion_rate == 0:
            completion_rate = _calculate_completion_rate(report_dto.position, resource_type) or 0

        # 3. Upsert 资料级进度
        existing = await ResourceProgressMapper.get_by_student_and_resource(student_id, report_dto.resource_id, db)

        if existing:
            # 更新已有记录
            # 先记录旧的 last_view_time，用于判断是否为新一次阅读
            old_last_view_time = existing.last_view_time
            was_already_completed = existing.is_completed == SystemConstants.Status.YES

            # 只在进度推进时更新 completion_rate 和 last_position，防止回退
            if completion_rate > existing.completion_rate:
                existing.completion_rate = completion_rate
                if report_dto.position is not None:
                    existing.last_position = report_dto.position
            existing.total_duration += report_dto.duration_seconds
            existing.last_view_time = now
            existing.update_time = now

            # 有效时长累加（前端没传则回退到总时长，向后兼容）
            effective = report_dto.effective_duration_seconds
            if effective is None:
                effective = report_dto.duration_seconds
            existing.effective_duration += effective

            # 复习判定：资源已完成后再次阅读
            is_review = was_already_completed
            if is_review:
                existing.review_duration += effective
            else:
                existing.first_read_duration += effective

            # 判断是否为新一次阅读（距上次超过阈值）
            if old_last_view_time and (
                now - old_last_view_time.replace(tzinfo=None) > timedelta(minutes=_NEW_VIEW_THRESHOLD_MINUTES)
            ):
                existing.view_count += 1

            # 完成判定
            if completion_rate >= 100 and not was_already_completed:
                existing.is_completed = SystemConstants.Status.YES
                existing.complete_time = now

            await ResourceProgressMapper.update(existing, db)
        else:
            # 创建新记录
            effective = report_dto.effective_duration_seconds or report_dto.duration_seconds
            new_progress = EduStudentResourceProgress(
                student_id=student_id,
                course_id=course_id,
                chapter_id=chapter_id,
                resource_id=report_dto.resource_id,
                resource_type=resource_type,
                completion_rate=completion_rate,
                is_completed=SystemConstants.Status.YES if completion_rate >= 100 else SystemConstants.Status.NO,
                view_count=1,
                total_duration=report_dto.duration_seconds,
                effective_duration=effective,
                review_duration=0,
                first_read_duration=effective,
                last_position=report_dto.position,
                first_view_time=now,
                last_view_time=now,
                complete_time=now if completion_rate >= 100 else None,
                status=SystemConstants.Status.NORMAL,
                create_time=now,
                update_time=now,
            )
            existing = await ResourceProgressMapper.add(new_progress, db)

        # 4. 双写：写入学习事件
        is_review = existing.is_completed == SystemConstants.Status.YES if existing else False
        effective = report_dto.effective_duration_seconds or report_dto.duration_seconds
        event = EduStudentLearningEvent(
            student_id=student_id,
            course_id=course_id,
            chapter_id=chapter_id,
            event_type="resource_progress",
            event_source="ui",
            event_payload={
                "resource_id": report_dto.resource_id,
                "position": report_dto.position,
                "duration_seconds": report_dto.duration_seconds,
                "effective_duration_seconds": effective,
                "idle_seconds": report_dto.idle_seconds or 0,
                "completion_rate": completion_rate,
                "is_review": is_review,
            },
            duration_seconds=report_dto.duration_seconds,
            effective_duration_seconds=effective,
            is_review=is_review,
            event_time=now,
            status=SystemConstants.Status.NORMAL,
            create_time=now,
            update_time=now,
        )
        db.add(event)
        await db.flush()

        # 5. 刷新章节进度物化视图
        await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chapter_progress"))

        # 6. 三层汇总：章节 → 课程
        await ResourceProgressService._rollup_to_course(db, student_id, course_id, now)

        return _convert_to_detail_vo(existing)

    @staticmethod
    async def _rollup_to_course(db: AsyncSession, student_id: int, course_id: int, now: datetime) -> None:
        """汇总章节进度到课程级（查询物化视图）

        :param db: 数据库会话
        :param student_id: 学生ID
        :param course_id: 课程ID
        :param now: 当前时间
        """
        course_progress = await ChapterProgressMapper.calculate_course_progress(student_id, course_id, db)

        from graphedu.mapper.education.student_course import StudentCourseMapper

        student_course = await StudentCourseMapper.get_student_course(student_id, course_id, db)
        if student_course:
            student_course.progress = course_progress
            student_course.last_study_time = now
            await db.flush()

    @staticmethod
    async def get_resource_progress_detail(
        db: AsyncSession, student_id: int, resource_id: int
    ) -> StudentResourceProgressDetailVO | None:
        """查询单个资料的进度详情（用于断点续学）

        :param db: 数据库会话
        :param student_id: 学生ID
        :param resource_id: 资料ID
        :return: 进度详情，不存在返回 None
        """
        progress = await ResourceProgressMapper.get_by_student_and_resource(student_id, resource_id, db)
        if not progress:
            return None
        return _convert_to_detail_vo(progress)
