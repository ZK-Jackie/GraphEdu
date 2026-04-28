"""GraphRAG 任务 Mapper - 数据访问层"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduChapterResource, EduCourse, EduGraphRAGTask


class GraphRAGTaskMapper:
    """GraphRAG 任务 Mapper - 数据访问层"""

    # ========================================================================
    # 基础 CRUD
    # ========================================================================

    @staticmethod
    async def get_by_id(task_id: int, db: AsyncSession) -> EduGraphRAGTask | None:
        """根据主键查询 GraphRAG 任务。"""
        result = await db.execute(
            select(EduGraphRAGTask).where(
                EduGraphRAGTask.task_id == task_id,
                EduGraphRAGTask.status != "2",
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_query(
        course_id: int | None,
        task_status: str | None,
        task_type: str | None,
        begin_time: datetime | None,
        end_time: datetime | None,
        page_num: int,
        page_size: int,
        db: AsyncSession,
    ) -> tuple[list[EduGraphRAGTask], int]:
        """根据查询条件分页查询 GraphRAG 任务列表。"""
        # 构建查询条件
        conditions = []
        if course_id is not None:
            conditions.append(EduGraphRAGTask.course_id == course_id)
        if task_status is not None:
            conditions.append(EduGraphRAGTask.task_status == task_status)
        if task_type is not None:
            conditions.append(EduGraphRAGTask.task_type == task_type)
        if begin_time is not None:
            conditions.append(EduGraphRAGTask.create_time >= begin_time)
        if end_time is not None:
            conditions.append(EduGraphRAGTask.create_time <= end_time)
        conditions.append(EduGraphRAGTask.status != "2")

        # 查询总记录数
        count_query = select(func.count(EduGraphRAGTask.task_id))
        if conditions:
            count_query = count_query.where(*conditions)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 查询分页数据
        query = (
            select(EduGraphRAGTask)
            .order_by(EduGraphRAGTask.create_time.desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        if conditions:
            query = query.where(*conditions)

        result = await db.execute(query)
        rows = list(result.scalars().all())

        return rows, total

    @staticmethod
    async def insert(task: EduGraphRAGTask, db: AsyncSession) -> EduGraphRAGTask:
        """新增 GraphRAG 任务。"""
        db.add(task)
        await db.flush()
        return task

    @staticmethod
    async def update(task: EduGraphRAGTask, db: AsyncSession) -> EduGraphRAGTask:
        """更新 GraphRAG 任务。"""
        await db.merge(task)
        await db.flush()
        return task

    @staticmethod
    async def delete_by_ids(task_ids: list[int], db: AsyncSession) -> int:
        """批量删除 GraphRAG 任务（软删除，设置 status 为 '2'）。"""
        if not task_ids:
            return 0
        result = await db.execute(
            update(EduGraphRAGTask).where(EduGraphRAGTask.task_id.in_(task_ids)).values(status="2")
        )
        await db.flush()
        return result.rowcount

    # ========================================================================
    # 状态更新
    # ========================================================================

    @staticmethod
    async def update_status(
        task_id: int,
        db: AsyncSession,
        *,
        task_status: str | None = None,
        task_message: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        update_by: int | None = None,
    ) -> None:
        """更新任务状态字段，仅修改显式传入的字段。"""
        updates: dict = {}
        if task_status is not None:
            updates["task_status"] = task_status
        if task_message is not None:
            updates["task_message"] = task_message
        if start_time is not None:
            updates["start_time"] = start_time
        if end_time is not None:
            updates["end_time"] = end_time
        if update_by is not None:
            updates["update_by"] = update_by
            updates["update_time"] = datetime.now()
        if not updates:
            return
        await db.execute(
            update(EduGraphRAGTask)
            .where(EduGraphRAGTask.task_id == task_id, EduGraphRAGTask.status != "2")
            .values(**updates)
        )
        await db.flush()

    # ========================================================================
    # 关联查询
    # ========================================================================

    @staticmethod
    async def get_resources_by_ids(resource_ids: list[int], db: AsyncSession) -> list[EduChapterResource]:
        """根据 ID 列表批量查询章节资源。"""
        if not resource_ids:
            return []
        result = await db.execute(
            select(EduChapterResource).where(
                EduChapterResource.resource_id.in_(resource_ids),
                EduChapterResource.status != "2",
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_buildable_resources(
        *,
        course_chapter_ids: list[int],
        parse_status: str,
        include_text_directly: bool,
        resource_name: str | None,
        page: int,
        size: int,
        db: AsyncSession,
    ) -> tuple[list[EduChapterResource], int]:
        """分页查询可构建 GraphRAG 的资源。"""
        if not course_chapter_ids:
            return [], 0

        conditions = [
            EduChapterResource.status != "2",
            EduChapterResource.chapter_id.in_(course_chapter_ids),
        ]
        # 非文本类型：已有文本化结果（parse_status=2 且 text_file_id 不为空）
        converted_buildable_condition = and_(
            EduChapterResource.resource_type != "text",
            EduChapterResource.parse_status == parse_status,
            EduChapterResource.text_file_id.isnot(None),
        )
        if include_text_directly:
            conditions.append(
                or_(
                    converted_buildable_condition,
                    EduChapterResource.resource_type == "text",
                )
            )
        else:
            conditions.append(converted_buildable_condition)

        if resource_name:
            conditions.append(EduChapterResource.resource_name.like(f"%{resource_name}%"))

        count_query = select(func.count(EduChapterResource.resource_id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(EduChapterResource)
            .where(and_(*conditions))
            .order_by(EduChapterResource.chapter_id, EduChapterResource.display_order)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(query)
        rows = list(result.scalars().all())
        return rows, total

    @staticmethod
    async def toggle_enable(task_id: int, course_id: int, db: AsyncSession, *, update_by: int | None = None) -> None:
        """切换启用状态：先禁用同课程所有任务，再启用目标任务。"""
        # 1. 禁用同课程所有任务
        await db.execute(
            update(EduGraphRAGTask)
            .where(
                EduGraphRAGTask.course_id == course_id,
                EduGraphRAGTask.status != "2",
            )
            .values(enabled="N", update_by=update_by, update_time=datetime.now())
        )
        # 2. 启用目标任务
        await db.execute(
            update(EduGraphRAGTask)
            .where(
                EduGraphRAGTask.task_id == task_id,
                EduGraphRAGTask.status != "2",
            )
            .values(enabled="Y", update_by=update_by, update_time=datetime.now())
        )
        await db.flush()

    @staticmethod
    async def get_enabled_task_for_course(course_id: int, db: AsyncSession) -> EduGraphRAGTask | None:
        """查询课程当前启用的、构建成功的 GraphRAG 任务。"""
        result = await db.execute(
            select(EduGraphRAGTask).where(
                EduGraphRAGTask.course_id == course_id,
                EduGraphRAGTask.enabled == "Y",
                EduGraphRAGTask.task_status == "success",
                EduGraphRAGTask.status != "2",
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_course_by_id(course_id: int, db: AsyncSession) -> EduCourse | None:
        """根据课程ID查询课程信息。"""
        result = await db.execute(select(EduCourse).where(EduCourse.course_id == course_id, EduCourse.status != "2"))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_courses_by_ids(course_ids: list[int], db: AsyncSession) -> dict[int, EduCourse]:
        """根据课程ID列表批量查询课程信息，返回 ID → 课程对象字典。"""
        if not course_ids:
            return {}
        result = await db.execute(
            select(EduCourse).where(
                EduCourse.course_id.in_(course_ids),
                EduCourse.status != "2",
            )
        )
        courses = result.scalars().all()
        return {course.course_id: course for course in courses}
