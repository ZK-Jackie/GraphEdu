"""GraphRAG 任务管理服务模块

该模块提供 GraphRAG 任务信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging
import uuid

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education import CourseNotFoundException
from graphedu.common.exceptions.services.education.graphrag_task import (
    GraphRAGBuildCourseNotFoundException,
    GraphRAGBuildResourceNotTextedException,
    GraphRAGBuildTaskCannotCancelException,
    GraphRAGBuildTaskCannotRetryException,
    GraphRAGTaskCannotEnableException,
    GraphRAGTaskIdListEmptyException,
    GraphRAGTaskNotFoundException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.graphrag_task import (
    GraphRAGBuildCreateDTO,
    GraphRAGResourceQueryDTO,
    GraphRAGTaskCreateDTO,
    GraphRAGTaskQueryDTO,
    GraphRAGTaskUpdateDTO,
)
from graphedu.common.models.orm.education import EduChapterResource, EduGraphRAGTask
from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem, PageResponse
from graphedu.common.models.vo.educationv2.chapter_resource import ChapterResourceListVO
from graphedu.common.models.vo.educationv2.graphrag_task import (
    GraphRAGBuildProgressVO,
    GraphRAGTaskDetailVO,
    GraphRAGTaskListVO,
)
from graphedu.mapper.education.chapter import ChapterMapper
from graphedu.mapper.education.graphrag_task import GraphRAGTaskMapper
from graphedu.workers.celery import celery_app
from graphedu.workers.graphrag_tasks import build_graphrag_index

logger = logging.getLogger(__name__)


def _safe_user_id(current_user: CurrentUser) -> int | None:
    """安全提取当前用户 ID。"""
    if current_user and current_user.detail and current_user.detail.user:
        return current_user.detail.user.user_id
    return None


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_task_orm_to_list_vo(task_orm: EduGraphRAGTask, course_name: str | None = None) -> GraphRAGTaskListVO:
    """将 GraphRAG 任务 ORM 对象转换为 GraphRAGTaskListVO。

    Args:
        task_orm: GraphRAG 任务 ORM 对象。
        course_name: 课程名称（可选）。

    Returns:
        GraphRAGTaskListVO: GraphRAG 任务列表项 VO。
    """
    return GraphRAGTaskListVO(
        task_id=task_orm.task_id,
        course_id=task_orm.course_id,
        resource_ids=task_orm.resource_ids,
        task_status=task_orm.task_status,
        task_type=task_orm.task_type,
        task_message=task_orm.task_message,
        entity_types=task_orm.entity_types,
        prompt_template=task_orm.prompt_template,
        stats=task_orm.stats,
        start_time=task_orm.start_time,
        end_time=task_orm.end_time,
        enabled=task_orm.enabled,
        status=task_orm.status,
        create_time=task_orm.create_time,
    )


def _convert_task_orm_to_detail_vo(task_orm: EduGraphRAGTask, course_name: str | None = None) -> GraphRAGTaskDetailVO:
    """将 GraphRAG 任务 ORM 对象转换为 GraphRAGTaskDetailVO。

    Args:
        task_orm: GraphRAG 任务 ORM 对象。
        course_name: 课程名称（可选）。

    Returns:
        GraphRAGTaskDetailVO: GraphRAG 任务详细信息 VO。
    """
    return GraphRAGTaskDetailVO(
        task_id=task_orm.task_id,
        course_id=task_orm.course_id,
        resource_ids=task_orm.resource_ids,
        task_status=task_orm.task_status,
        task_type=task_orm.task_type,
        task_message=task_orm.task_message,
        entity_types=task_orm.entity_types,
        prompt_template=task_orm.prompt_template,
        custom_prompt_template=task_orm.custom_prompt_template,
        stats=task_orm.stats,
        start_time=task_orm.start_time,
        end_time=task_orm.end_time,
        enabled=task_orm.enabled,
        status=task_orm.status,
        create_by=task_orm.create_by,
        create_time=task_orm.create_time,
        update_by=task_orm.update_by,
        update_time=task_orm.update_time,
    )


def _convert_resource_orm_to_list_vo(resource_orm: EduChapterResource) -> ChapterResourceListVO:
    """将章节资源 ORM 对象转换为 ChapterResourceListVO。"""
    return ChapterResourceListVO(
        resource_id=resource_orm.resource_id,
        chapter_id=resource_orm.chapter_id,
        resource_name=resource_orm.resource_name,
        resource_type=resource_orm.resource_type,
        file_id=resource_orm.file_id,
        resource_url=resource_orm.resource_url,
        resource_data=resource_orm.resource_data,
        parse_status=resource_orm.parse_status,
        display_order=resource_orm.display_order,
        is_visible=resource_orm.is_visible,
        status=resource_orm.status,
        create_time=resource_orm.create_time,
        file_url=None,
    )


def _map_celery_state_to_task_status(celery_state: str) -> str:
    """将 Celery 状态映射为 GraphRAG 任务状态。"""
    state = celery_state.upper()
    if state in {"STARTED", "PROGRESS", "RETRY"}:
        return "processing"
    if state == "SUCCESS":
        return "success"
    if state == "FAILURE":
        return "failed"
    if state == "REVOKED":
        return "cancelled"
    return "pending"


# ============================================================================
# GraphRAG 任务服务类
# ============================================================================


class GraphRAGTaskService:
    """GraphRAG 任务服务类

    提供 GraphRAG 任务的增删改查功能。
    """

    # ========================================================================
    # GraphRAG 构建方法
    # ========================================================================

    @staticmethod
    async def get_buildable_resources(
        db: AsyncSession,
        query: GraphRAGResourceQueryDTO,
    ) -> PageResponse[ChapterResourceListVO]:
        """获取可构建 GraphRAG 的资源列表。"""
        page = query.page or 1
        size = query.size or 10

        course = await GraphRAGTaskMapper.get_course_by_id(query.course_id, db)
        if not course:
            raise GraphRAGBuildCourseNotFoundException(course_id=query.course_id)

        chapters = await ChapterMapper.get_chapters_by_course_id(query.course_id, db)
        course_chapter_ids = [chapter.chapter_id for chapter in chapters]
        if not course_chapter_ids:
            return PageResponse(rows=[], page=page, size=size, total=0)

        rows, total = await GraphRAGTaskMapper.list_buildable_resources(
            course_chapter_ids=course_chapter_ids,
            parse_status=query.parse_status,
            include_text_directly=query.include_text_directly,
            resource_name=query.resource_name,
            page=page,
            size=size,
            db=db,
        )

        return PageResponse(
            rows=[_convert_resource_orm_to_list_vo(row) for row in rows],
            page=page,
            size=size,
            total=total,
        )

    @staticmethod
    async def submit_build_task(
        db: AsyncSession,
        build_data: GraphRAGBuildCreateDTO,
        current_user: CurrentUser,
    ) -> GraphRAGTaskDetailVO:
        """提交 GraphRAG 构建任务并触发 Celery 异步执行。"""
        course = await GraphRAGTaskMapper.get_course_by_id(build_data.course_id, db)
        if not course:
            raise GraphRAGBuildCourseNotFoundException(course_id=build_data.course_id)

        resources = await GraphRAGTaskMapper.get_resources_by_ids(build_data.resource_ids, db)
        resource_dict = {resource.resource_id: resource for resource in resources}
        for resource_id in build_data.resource_ids:
            if resource_id not in resource_dict:
                raise GraphRAGBuildResourceNotTextedException(
                    resource_name=f"ID {resource_id}",
                    current_status="不存在",
                )

            resource = resource_dict[resource_id]

            if resource.resource_type not in {"document", "text", "image", "audio", "video"}:
                raise GraphRAGBuildResourceNotTextedException(
                    resource_name=resource.resource_name,
                    current_status=f"资源类型不支持: {resource.resource_type}",
                )

            if resource.resource_type != "text" and resource.parse_status != SystemConstants.ProcessStatus.COMPLETED:
                raise GraphRAGBuildResourceNotTextedException(
                    resource_name=resource.resource_name,
                    current_status=resource.parse_status,
                )

            if resource.resource_type != "text" and not resource.text_file_id:
                raise GraphRAGBuildResourceNotTextedException(
                    resource_name=resource.resource_name,
                    current_status="未生成 text_file",
                )

            if resource.resource_type == "text" and not resource.file_id:
                raise GraphRAGBuildResourceNotTextedException(
                    resource_name=resource.resource_name,
                    current_status="text 资源 file_id 为空",
                )

        task_orm = EduGraphRAGTask(
            course_id=build_data.course_id,
            resource_ids=build_data.resource_ids,
            task_status="pending",
            task_type="graphrag_build",
            task_message="任务已提交，等待执行",
            entity_types=build_data.entity_types,
            prompt_template=build_data.prompt_template,
            stats=None,
            start_time=None,
            end_time=None,
            enabled="N",
            status=SystemConstants.Status.NORMAL,
            create_by=_safe_user_id(current_user),
            update_by=_safe_user_id(current_user),
        )
        task_orm = await GraphRAGTaskMapper.insert(task_orm, db)

        build_graphrag_index.apply_async((task_orm.task_id,), task_id=str(task_orm.task_id))

        logger.info("提交 GraphRAG 构建任务成功，任务ID: %s", task_orm.task_id)
        return _convert_task_orm_to_detail_vo(task_orm, course.course_name)

    @staticmethod
    async def get_build_progress(task_id: int, db: AsyncSession) -> GraphRAGBuildProgressVO:
        """获取 GraphRAG 构建进度。

        策略：优先信任数据库中的任务状态（已由 worker 持久化），
        只在任务仍在执行时（pending/processing）才查询 Celery 获取實時進度。
        """
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException(task_id=task_id)

        # 如果任务已经完成或失败或被取消，直接从数据库返回（无需查 Celery）
        if task_orm.task_status in {"success", "failed", "cancelled"}:
            progress_percent = 100 if task_orm.task_status == "success" else 0
            return GraphRAGBuildProgressVO(
                task_id=task_id,
                task_status=task_orm.task_status,
                current_step=None,
                progress_percent=progress_percent,
                stats=task_orm.stats,
                start_time=task_orm.start_time,
                estimated_end_time=None,
            )

        # 任务还在执行（pending/processing），查询 Celery 获取實時進度
        celery_task = AsyncResult(str(task_id), app=celery_app)
        progress_info = celery_task.info if isinstance(celery_task.info, dict) else {}

        # 如果 Celery 報告任務失敗或被取消（worker 崩潰場景），同步狀態回數據庫
        # 注意：不同步 SUCCESS —— 真正的 SUCCESS 只由 worker 通過 DB 寫入
        #
        # 重要：retry_build_task 使用唯一的 Celery task_id 派发，但
        # CeleryWorkflowCallbacks 仍使用 work_id=str(db_task_id) 写进度。
        # 若上一轮 cancel/revoke 在 backend 中残留了 REVOKED 结果，
        # AsyncResult(str(db_task_id)) 可能读到陈旧的 REVOKED，
        # 导致刚 retry 的任务被错误地同步回 "cancelled"。
        # 此处清除陈旧结果，让后续的 CeleryWorkflowCallbacks 回调写入新进度。
        if celery_task.state == "REVOKED":
            celery_app.backend.delete(str(task_id))
            celery_task = AsyncResult(str(task_id), app=celery_app)
            progress_info = celery_task.info if isinstance(celery_task.info, dict) else {}

        mapped_status = _map_celery_state_to_task_status(celery_task.state)
        if mapped_status in {"failed", "cancelled"} and task_orm.task_status != mapped_status:
            await GraphRAGTaskMapper.update_status(
                task_id,
                db,
                task_status=mapped_status,
                task_message=str(celery_task.info) if mapped_status == "failed" and celery_task.info else None,
                end_time=datetime.now(),
            )
            # 重新查詢更新後的狀態
            task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
            if not task_orm:
                raise GraphRAGTaskNotFoundException(task_id=task_id)

        progress_percent = int(progress_info.get("percent", 0))
        if task_orm.task_status == "success":
            progress_percent = 100
        elif task_orm.task_status == "processing" and progress_percent <= 0:
            progress_percent = 0

        return GraphRAGBuildProgressVO(
            task_id=task_id,
            task_status=task_orm.task_status,
            current_step=progress_info.get("current_workflow"),
            progress_percent=progress_percent,
            stats=task_orm.stats,
            start_time=task_orm.start_time,
            estimated_end_time=None,
        )

    @staticmethod
    async def cancel_build_task(task_id: int, db: AsyncSession, current_user: CurrentUser) -> bool:
        """取消 GraphRAG 构建任务。"""
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException(task_id=task_id)

        if task_orm.task_status not in ["pending", "processing"]:
            raise GraphRAGBuildTaskCannotCancelException(current_status=task_orm.task_status)

        # 撤销 Celery 任务
        celery_app.control.revoke(str(task_id), terminate=True)

        await GraphRAGTaskMapper.update_status(
            task_id,
            db,
            task_status="cancelled",
            task_message="用户取消任务",
            end_time=datetime.now(),
            update_by=_safe_user_id(current_user),
        )
        logger.info("取消 GraphRAG 构建任务成功，任务ID: %s", task_id)
        return True

    @staticmethod
    async def retry_build_task(db: AsyncSession, task_id: int, current_user: CurrentUser) -> GraphRAGTaskDetailVO:
        """重试/重建 GraphRAG 构建任务。

        重置任务状态为 pending 并重新派发 Celery 任务。
        支持对失败、已取消、已成功的任务进行重试/重建。

        Args:
            db: 数据库会话。
            task_id: 任务ID。
            current_user: 当前用户。

        Returns:
            GraphRAGTaskDetailVO: 更新后的任务详情。

        Raises:
            GraphRAGTaskNotFoundException: 任务不存在。
            GraphRAGBuildTaskCannotRetryException: 任务状态不允许重试。
        """
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException(task_id=task_id)

        if task_orm.task_status not in {"failed", "cancelled", "success"}:
            raise GraphRAGBuildTaskCannotRetryException(current_status=task_orm.task_status)

        # 重置任务状态
        is_rebuild = task_orm.task_status == "success"
        user_id = _safe_user_id(current_user)
        task_orm.task_status = "pending"
        task_orm.task_message = "任务已重新提交，等待执行"
        task_orm.start_time = None
        task_orm.end_time = None
        task_orm.update_by = user_id
        task_orm.update_time = datetime.now()

        # 重建成功的任务时，额外重置 enabled 和 stats
        if is_rebuild:
            task_orm.enabled = "N"
            task_orm.stats = None

        task_orm = await GraphRAGTaskMapper.update(task_orm, db)

        # 清除上一轮残留的 Celery 结果，防止 get_build_progress 读到旧状态
        celery_app.backend.delete(str(task_id))

        # 重新派发 Celery 任务
        # 使用唯一 Celery task_id 避开 worker 内存中的 revoked 集合。
        # 之前的 revoke() 或 cancel 操作会将 str(task_id) 加入 worker 的
        # in-memory _revoked_tasks 集合，该集合无法从客户端清除。
        # 用带后缀的新 task_id 可以完全避开此问题。
        # CeleryWorkflowCallbacks 使用 work_id=str(db_task_id) 写进度，
        # get_build_progress 通过 AsyncResult(str(db_task_id)) 读进度，
        # 两者均不受 Celery task_id 变更的影响。
        celery_task_id = f"{task_id}-retry-{uuid.uuid4().hex[:8]}"
        build_graphrag_index.apply_async((task_id,), task_id=celery_task_id)

        logger.info("重试 GraphRAG 构建任务，任务ID: %s", task_id)

        # 查询更新后的数据
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException(task_id=task_id)

        course = await GraphRAGTaskMapper.get_course_by_id(task_orm.course_id, db)
        course_name = course.course_name if course else None
        return _convert_task_orm_to_detail_vo(task_orm, course_name)

    @staticmethod
    async def enable_task(db: AsyncSession, task_id: int, current_user: CurrentUser) -> GraphRAGTaskDetailVO:
        """启用指定的 GraphRAG 任务（同一课程仅允许启用一个）。

        Args:
            db: 数据库会话。
            task_id: 要启用的任务ID。
            current_user: 当前用户。

        Returns:
            GraphRAGTaskDetailVO: 更新后的任务详情。

        Raises:
            GraphRAGTaskNotFoundException: 任务不存在。
            GraphRAGTaskCannotEnableException: 任务未构建成功，无法启用。
        """
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException(task_id=task_id)

        if task_orm.task_status != "success":
            raise GraphRAGTaskCannotEnableException(current_status=task_orm.task_status)

        await GraphRAGTaskMapper.toggle_enable(
            task_id=task_id,
            course_id=task_orm.course_id,
            db=db,
            update_by=_safe_user_id(current_user),
        )

        # 重新查询获取更新后的数据
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException(task_id=task_id)

        course = await GraphRAGTaskMapper.get_course_by_id(task_orm.course_id, db)
        course_name = course.course_name if course else None
        logger.info("启用 GraphRAG 任务成功，任务ID: %s, 课程ID: %s", task_id, task_orm.course_id)
        return _convert_task_orm_to_detail_vo(task_orm, course_name)

    # ========================================================================
    # 查询方法
    # ========================================================================

    @staticmethod
    async def list_task(db: AsyncSession, query: GraphRAGTaskQueryDTO) -> PageResponse[GraphRAGTaskListVO]:
        """分页查询 GraphRAG 任务列表。

        Args:
            db: 数据库会话。
            query: 查询条件 DTO。

        Returns:
            PageResponse[GraphRAGTaskListVO]: 分页结果。
        """
        page_num = query.page or 1
        page_size = query.size or 10

        rows, total = await GraphRAGTaskMapper.list_by_query(
            course_id=query.course_id,
            task_status=query.task_status,
            task_type=query.task_type,
            begin_time=query.begin_time,
            end_time=query.end_time,
            page_num=page_num,
            page_size=page_size,
            db=db,
        )

        # 获取关联的课程信息（批量查询）
        course_ids = list({row.course_id for row in rows})
        courses = await GraphRAGTaskMapper.get_courses_by_ids(course_ids, db)

        # 转换为 VO
        vo_list = []
        for row in rows:
            course = courses.get(row.course_id)
            course_name = course.course_name if course else None
            vo_list.append(_convert_task_orm_to_list_vo(row, course_name))

        return PageResponse(
            rows=vo_list,
            total=total,
        )

    @staticmethod
    async def get_task_detail(db: AsyncSession, task_id: int) -> GraphRAGTaskDetailVO:
        """查询 GraphRAG 任务详情。

        Args:
            db: 数据库会话。
            task_id: 任务ID。

        Returns:
            GraphRAGTaskDetailVO: 任务详细信息 VO。

        Raises:
            GraphRAGTaskNotFoundException: 任务不存在时抛出。
        """
        task_orm = await GraphRAGTaskMapper.get_by_id(task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException

        # 获取关联的课程名称
        course = await GraphRAGTaskMapper.get_course_by_id(task_orm.course_id, db)
        course_name = course.course_name if course else None

        return _convert_task_orm_to_detail_vo(task_orm, course_name)

    @staticmethod
    async def list_by_course_id(db: AsyncSession, course_id: int) -> list[GraphRAGTaskListVO]:
        """查询指定课程的所有 GraphRAG 任务（不分页）。

        Args:
            db: 数据库会话。
            course_id: 课程ID。

        Returns:
            list[GraphRAGTaskListVO]: 任务列表。
        """
        rows, _ = await GraphRAGTaskMapper.list_by_query(
            course_id=course_id,
            task_status=None,
            task_type=None,
            begin_time=None,
            end_time=None,
            page_num=1,
            page_size=1000,
            db=db,
        )

        return [_convert_task_orm_to_list_vo(row) for row in rows]

    # ========================================================================
    # 新增方法
    # ========================================================================

    @staticmethod
    async def add_task(
        db: AsyncSession, task_data: GraphRAGTaskCreateDTO, current_user: CurrentUser
    ) -> GraphRAGTaskDetailVO:
        """新增 GraphRAG 任务。

        Args:
            db: 数据库会话。
            task_data: 创建任务 DTO。
            current_user: 当前用户。

        Returns:
            GraphRAGTaskDetailVO: 创建的任务详细信息 VO。

        Raises:
            UserIdNotFoundException: 课程不存在时抛出。
        """
        # 验证课程是否存在
        course = await GraphRAGTaskMapper.get_course_by_id(task_data.course_id, db)
        if not course:
            raise CourseNotFoundException

        # 创建 ORM 对象
        task_orm = EduGraphRAGTask(
            course_id=task_data.course_id,
            resource_ids=task_data.resource_ids,  # type: ignore[arg-type]
            task_status="pending",
            task_type=task_data.task_type,
            entity_types=task_data.entity_types,  # type: ignore[arg-type]
            prompt_template=task_data.prompt_template,
            custom_prompt_template=task_data.custom_prompt_template,
            create_by=_safe_user_id(current_user),
            update_by=_safe_user_id(current_user),
        )

        # 保存到数据库
        task_orm = await GraphRAGTaskMapper.insert(task_orm, db)

        return _convert_task_orm_to_detail_vo(task_orm, course.course_name)

    # ========================================================================
    # 修改方法
    # ========================================================================

    @staticmethod
    async def update_task(
        db: AsyncSession, task_data: GraphRAGTaskUpdateDTO, current_user: CurrentUser
    ) -> GraphRAGTaskDetailVO:
        """修改 GraphRAG 任务。

        Args:
            db: 数据库会话。
            task_data: 更新任务 DTO。
            current_user: 当前用户。

        Returns:
            GraphRAGTaskDetailVO: 更新后的任务详细信息 VO。

        Raises:
            GraphRAGTaskNotFoundException: 任务不存在时抛出。
        """
        # 查询原任务
        task_orm = await GraphRAGTaskMapper.get_by_id(task_data.task_id, db)
        if not task_orm:
            raise GraphRAGTaskNotFoundException

        # 更新字段
        if task_data.task_status is not None:
            task_orm.task_status = task_data.task_status
        if task_data.task_message is not None:
            task_orm.task_message = task_data.task_message
        if task_data.entity_types is not None:
            task_orm.entity_types = task_data.entity_types  # type: ignore[arg-type]
        if task_data.prompt_template is not None:
            task_orm.prompt_template = task_data.prompt_template
        if task_data.custom_prompt_template is not None:
            task_orm.custom_prompt_template = task_data.custom_prompt_template
        if task_data.stats is not None:
            task_orm.stats = task_data.stats
        if task_data.start_time is not None:
            task_orm.start_time = task_data.start_time
        if task_data.end_time is not None:
            task_orm.end_time = task_data.end_time

        task_orm.update_by = _safe_user_id(current_user)
        task_orm.update_time = datetime.now()

        # 保存到数据库
        task_orm = await GraphRAGTaskMapper.update(task_orm, db)

        # 获取课程名称
        course = await GraphRAGTaskMapper.get_course_by_id(task_orm.course_id, db)
        course_name = course.course_name if course else None

        return _convert_task_orm_to_detail_vo(task_orm, course_name)

    # ========================================================================
    # 删除方法
    # ========================================================================

    @staticmethod
    async def delete_tasks(db: AsyncSession, task_ids_str: str) -> BatchDeleteResponse[int]:
        """批量删除 GraphRAG 任务（软删除）。

        Args:
            db: 数据库会话。
            task_ids_str: 任务ID字符串（逗号分隔）。

        Returns:
            BatchDeleteResponse[int]: 批量删除结果。

        Raises:
            GraphRAGTaskIdListEmptyException: 任务ID列表为空时抛出。
        """
        # 解析任务ID列表
        task_ids = [int(id_str) for id_str in task_ids_str.split(",") if id_str.strip()]

        if not task_ids:
            raise GraphRAGTaskIdListEmptyException

        # 执行软删除
        deleted_count = await GraphRAGTaskMapper.delete_by_ids(task_ids, db)

        # 构建删除结果
        results: list[DeleteResultItem[int]] = []
        for task_id in task_ids:
            results.append(DeleteResultItem(target_id=task_id, success=True))

        return BatchDeleteResponse(
            success_count=deleted_count,
            fail_count=len(task_ids) - deleted_count,
            total_count=len(task_ids),
            results=results,
        )
