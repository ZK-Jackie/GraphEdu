"""课程练习管理服务模块。"""

from datetime import datetime
import logging
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common import get_config
from graphedu.common.exceptions.common.resource import (
    HTTPClientException,
    HTTPConnectionException,
    HTTPRequestException,
    HTTPTimeoutException,
)
from graphedu.common.exceptions.services.education.course_exercise import (
    CourseExerciseBatchGenerateFailedException,
    CourseExerciseChangeStatusFailedException,
    CourseExerciseCreateFailedException,
    CourseExerciseIdListEmptyException,
    CourseExerciseNotFoundException,
    CourseExerciseUpdateFailedException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.bo.dify import DifyFile
from graphedu.common.models.bo.teacher_course_exercise import (
    CourseExerciseGenerateRequest,
    CourseExerciseGenerateResponse,
    CourseExerciseWorkflowResponse,
)
from graphedu.common.models.dto.educationv2.course_exercise import (
    CourseExerciseBatchGenerateDTO,
    CourseExerciseCreateDTO,
    CourseExerciseQueryDTO,
    CourseExerciseUpdateDTO,
)
from graphedu.common.models.orm.education import EduCourseExercise
from graphedu.common.models.shared import QuestionOptionContent
from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem, PageResponse
from graphedu.common.models.vo.educationv2.course_exercise import (
    CourseExerciseDetailVO,
    CourseExerciseGenerateProgressVO,
    CourseExerciseGenerateTaskVO,
    CourseExerciseListVO,
)
from graphedu.common.resource import AioS3Client, AsyncHttpClient
from graphedu.mapper.education.chapter_resource import ChapterResourceMapper
from graphedu.mapper.education.course import CourseMapper
from graphedu.mapper.education.course_exercise import CourseExerciseMapper
from graphedu.services.external.dify import DifyService
from graphedu.services.system.upload import UploadService

# 资源类型 → Dify 文件类型映射
_RESOURCE_TYPE_TO_DIFY: dict[str, Literal["document", "image", "audio", "video", "custom"]] = {
    "document": "document",
    "video": "video",
    "text": "document",
}

logger = logging.getLogger(__name__)


def _map_celery_state(state: str) -> str:
    """将 Celery 状态映射为业务状态。"""
    mapping = {
        "PENDING": "pending",
        "STARTED": "processing",
        "PROGRESS": "processing",
        "SUCCESS": "success",
        "FAILURE": "failed",
        "REVOKED": "cancelled",
        "RETRY": "processing",
    }
    return mapping.get(state, "pending")


def _get_user_id(current_user: CurrentUser | None) -> int | None:
    if current_user and current_user.detail and current_user.detail.user:
        return current_user.detail.user.user_id
    return None


def _normalize_exercise_payload(payload: dict | list | None) -> Any:
    """把 ORM 的 JSON 数据转换成 VO 期望的结构。"""
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return payload
    return None


def _convert_orm_to_list_vo(exercise_orm: EduCourseExercise) -> CourseExerciseListVO:
    return CourseExerciseListVO(
        exercise_id=exercise_orm.exercise_id,
        course_id=exercise_orm.course_id,
        chapter_id=exercise_orm.chapter_id,
        exercise=_normalize_exercise_payload(exercise_orm.exercise),
        source=exercise_orm.source,
        status=exercise_orm.status,
        create_time=exercise_orm.create_time,
    )


def _convert_orm_to_detail_vo(exercise_orm: EduCourseExercise) -> CourseExerciseDetailVO:
    return CourseExerciseDetailVO(
        exercise_id=exercise_orm.exercise_id,
        course_id=exercise_orm.course_id,
        chapter_id=exercise_orm.chapter_id,
        exercise=_normalize_exercise_payload(exercise_orm.exercise),
        source=exercise_orm.source,
        status=exercise_orm.status,
        create_by=exercise_orm.create_by,
        create_time=exercise_orm.create_time,
        update_by=exercise_orm.update_by,
        update_time=exercise_orm.update_time,
    )


def _convert_generate_response_to_question_content(
    item: CourseExerciseGenerateResponse,
    question_type: str,
) -> QuestionOptionContent:
    """将 Dify workflow 生成的单题响应转为 QuestionOptionContent。"""
    # 处理答案
    if item.answer is None:
        answer_list: list[str] | None = None
    elif isinstance(item.answer, bool):
        answer_list = ["正确"] if item.answer else ["错误"]
    elif isinstance(item.answer, str):
        answer_list = [item.answer]
    else:
        answer_list = list(item.answer)

    # 处理选项
    options = item.options or (["正确", "错误"] if question_type == "judge" else ["A", "B", "C", "D"])

    return QuestionOptionContent(
        question_type=question_type,
        title=item.topic or "练习题",
        content=item.question,
        options=options,
        answer=answer_list,
        explanation=item.explanation,
    )


class CourseExerciseService:
    """课程练习管理服务类。"""

    @staticmethod
    async def add_course_exercise(
        query_db: AsyncSession,
        exercise_data: CourseExerciseCreateDTO,
        current_user: CurrentUser,
    ) -> CourseExerciseDetailVO:
        """添加课程练习"""
        course = await CourseMapper.get_by_id(exercise_data.course_id, query_db)
        if not course:
            from graphedu.common.exceptions.services.education.course import CourseNotFoundException

            raise CourseNotFoundException(course_id=exercise_data.course_id)

        try:
            new_exercise = EduCourseExercise(
                **exercise_data.model_dump(),
                status=SystemConstants.Status.NORMAL,
                create_by=_get_user_id(current_user),
                create_time=datetime.now(),
            )
            await CourseExerciseMapper.add_course_exercise(new_exercise, query_db)
        except Exception as e:
            raise CourseExerciseCreateFailedException(course_id=exercise_data.course_id) from e

        return _convert_orm_to_detail_vo(new_exercise)

    @staticmethod
    async def update_course_exercise(
        query_db: AsyncSession,
        exercise_data: CourseExerciseUpdateDTO,
        current_user: CurrentUser,
    ) -> CourseExerciseDetailVO:
        """更新课程练习。

        Args:
            query_db: 数据库会话
            exercise_data: 练习更新数据
            current_user: 当前用户

        Returns:
            更新后的练习详情
        """
        target_exercise = await CourseExerciseMapper.get_by_id(exercise_data.exercise_id, query_db)
        if not target_exercise:
            raise CourseExerciseNotFoundException(exercise_id=exercise_data.exercise_id)

        update_data = exercise_data.model_dump(exclude_unset=True, exclude={"exercise_id"})
        for field, value in update_data.items():
            setattr(target_exercise, field, value)

        target_exercise.update_by = _get_user_id(current_user)
        target_exercise.update_time = datetime.now()

        try:
            await CourseExerciseMapper.update(target_exercise, query_db)
        except Exception as e:
            raise CourseExerciseUpdateFailedException(exercise_id=exercise_data.exercise_id) from e

        return _convert_orm_to_detail_vo(target_exercise)

    @staticmethod
    async def list_course_exercise(
        query_db: AsyncSession,
        query_object: CourseExerciseQueryDTO,
    ) -> PageResponse[CourseExerciseListVO]:
        """获取课程练习列表。

        Args:
            query_db: 数据库会话
            query_object: 查询条件

        Returns:
            分页响应
        """
        rows, total = await CourseExerciseMapper.get_exercise_list(query_db, query_object, is_page=True)
        item_list = [_convert_orm_to_list_vo(row) for row in rows]
        return PageResponse(rows=item_list, page=query_object.page or 1, size=query_object.size or 10, total=total)

    @staticmethod
    async def get_course_exercise_detail(
        query_db: AsyncSession,
        exercise_id: int,
    ) -> CourseExerciseDetailVO | None:
        """获取课程练习详情。

        Args:
            query_db: 数据库会话
            exercise_id: 练习 ID

        Returns:
            练习详情，不存在则返回 None
        """
        exercise = await CourseExerciseMapper.get_by_id(exercise_id, query_db)
        if not exercise:
            return None
        return _convert_orm_to_detail_vo(exercise)

    @staticmethod
    async def delete_course_exercise(
        query_db: AsyncSession,
        exercise_id_list: list[int],
        current_user: CurrentUser,
    ) -> BatchDeleteResponse[int]:
        """批量删除课程练习。

        Args:
            query_db: 数据库会话
            exercise_id_list: 练习 ID 列表
            current_user: 当前用户

        Returns:
            批量删除响应
        """
        if not exercise_id_list:
            raise CourseExerciseIdListEmptyException

        results: list[DeleteResultItem[int]] = []
        for exercise_id in exercise_id_list:
            try:
                exercise = await CourseExerciseMapper.get_by_id(exercise_id, query_db)
                if not exercise:
                    results.append(DeleteResultItem(target_id=exercise_id, success=False, error="课程练习不存在"))
                    continue

                exercise.status = SystemConstants.Status.DELETED
                exercise.update_by = _get_user_id(current_user)
                exercise.update_time = datetime.now()
                await CourseExerciseMapper.update(exercise, query_db)
                results.append(DeleteResultItem(target_id=exercise_id, success=True, error=None))
            except Exception as e:
                results.append(DeleteResultItem(target_id=exercise_id, success=False, error=str(e)))

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def change_exercise_status(
        query_db: AsyncSession,
        exercise_id: int,
        status: str,
        current_user: CurrentUser,
    ) -> None:
        """修改课程练习状态。

        Args:
            query_db: 数据库会话
            exercise_id: 练习 ID
            status: 目标状态
            current_user: 当前用户
        """
        target_exercise = await CourseExerciseMapper.get_by_id(exercise_id, query_db)
        if not target_exercise:
            raise CourseExerciseNotFoundException(exercise_id=exercise_id)

        target_exercise.status = status
        target_exercise.update_by = _get_user_id(current_user)
        target_exercise.update_time = datetime.now()

        try:
            await CourseExerciseMapper.update(target_exercise, query_db)
        except Exception as e:
            raise CourseExerciseChangeStatusFailedException(exercise_id=exercise_id) from e

    @staticmethod
    async def batch_generate_exercises(
        query_db: AsyncSession,
        s3_client: AioS3Client,
        http_client: AsyncHttpClient,
        dto: CourseExerciseBatchGenerateDTO,
        current_user: CurrentUser,
    ) -> list[CourseExerciseDetailVO]:
        """教师端批量生成课程练习。

        流程：resource_ids → file_ids → OSS URLs → DifyFile → Dify workflow → 持久化
        """
        # 1. 验证课程存在
        course = await CourseMapper.get_by_id(dto.course_id, query_db)
        if not course:
            from graphedu.common.exceptions.services.education.course import CourseNotFoundException

            raise CourseNotFoundException(course_id=dto.course_id)

        # 获取配置
        config = get_config().dify

        try:
            # 2. resource_id → file_id
            file_ids: list[int] = []
            resource_type_map: dict[int, str] = {}
            for resource_id in dto.resource_ids:
                resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
                if not resource:
                    continue
                # 优先使用解析后的文本文件，回退到原始文件
                fid = resource.text_file_id or resource.file_id
                if fid:
                    file_ids.append(fid)
                    resource_type_map[fid] = resource.resource_type

            # 3. file_id → OSS URL
            file_url_map = await UploadService.get_file_url_map(file_ids, query_db, s3_client)

            # 4. 构造 DifyFile 列表
            dify_files: list[DifyFile] = []
            for fid, url in file_url_map.items():
                dify_files.append(
                    DifyFile(
                        type=_RESOURCE_TYPE_TO_DIFY.get(resource_type_map.get(fid, "document"), "document"),
                        transfer_method="remote_url",
                        url=url,
                    )
                )

            # 5. 构建 Dify workflow 请求
            request = CourseExerciseGenerateRequest(
                upload_files=dify_files or None,
                difficulty=dto.difficulty,
                question_type=dto.question_type,
                extra_info=dto.extra_info,
                number=dto.number,
            )

            # 6. 调用 Dify workflow
            workflow = config.workflows.teacher_exercise_generation
            workflow_response: CourseExerciseWorkflowResponse = await DifyService.invoke_workflow(
                inputs=request,
                user=str(_get_user_id(current_user) or "teacher"),
                api_key=workflow.api_key,
                base_url=config.base_url,
                http_client=http_client,
                workflow_id=workflow.id,
                return_model=CourseExerciseWorkflowResponse,
            )

            # 7. 验证工作流响应
            if not workflow_response or not workflow_response.output:
                logger.error(
                    f"Dify workflow 返回空响应: workflow_id={workflow.id or '(latest)'}, "
                    f"course_id={dto.course_id}, chapter_id={dto.chapter_id}"
                )
                raise CourseExerciseBatchGenerateFailedException(
                    course_id=dto.course_id,
                    message="工作流返回空数据，请检查 Dify 配置或稍后重试",
                )

            if len(workflow_response.output) == 0:
                logger.warning(
                    f"Dify workflow 未生成任何题目: workflow_id={workflow.id or '(latest)'}, "
                    f"course_id={dto.course_id}, chapter_id={dto.chapter_id}, request_number={dto.number}"
                )
                raise CourseExerciseBatchGenerateFailedException(
                    course_id=dto.course_id,
                    message="未生成任何题目，请尝试调整生成参数（难度、题型等）后重试",
                )

            # 8. 转换响应 → QuestionOptionContent → ORM 对象
            question_type = dto.question_type or "single"
            now = datetime.now()
            user_id = _get_user_id(current_user)

            exercises_orm: list[EduCourseExercise] = []
            for idx, item in enumerate(workflow_response.output):
                try:
                    question_content = _convert_generate_response_to_question_content(item, question_type)
                    exercises_orm.append(
                        EduCourseExercise(
                            course_id=dto.course_id,
                            chapter_id=dto.chapter_id,
                            exercise=question_content.model_dump(),
                            source="教师端批量生成",
                            status=SystemConstants.Status.NORMAL,
                            create_by=user_id,
                            create_time=now,
                            update_by=user_id,
                            update_time=now,
                        )
                    )
                except Exception as item_error:
                    logger.warning(
                        f"跳过无效的题目数据 (索引={idx}):"
                        f"{item_error}, "
                        f"item={item.model_dump() if hasattr(item, 'model_dump') else item}",
                        exc_info=True,
                    )
                    # 继续处理其他题目，不中断整个流程
                    continue

            if not exercises_orm:
                logger.error(f"所有题目数据均无效，无法保存: course_id={dto.course_id}, chapter_id={dto.chapter_id}")
                raise CourseExerciseBatchGenerateFailedException(
                    course_id=dto.course_id,
                    message="题目数据格式错误，请检查 Dify 工作流输出格式",
                )

            # 10. 批量持久化
            if exercises_orm:
                await CourseExerciseMapper.batch_add_course_exercises(exercises_orm, query_db)

            logger.info(
                f"教师端批量生成题目成功: course_id={dto.course_id}, chapter_id={dto.chapter_id}, "
                f"generated={len(exercises_orm)}/{dto.number}"
            )
            return [_convert_orm_to_detail_vo(orm) for orm in exercises_orm]

        except CourseExerciseBatchGenerateFailedException:
            raise
        except HTTPTimeoutException as e:
            logger.error(
                f"Dify workflow 请求超时: workflow_id={workflow.id or '(latest)'}, "
                f"course_id={dto.course_id}, timeout={e.kwargs.get('timeout', 'unknown')}",
                exc_info=True,
            )
            raise CourseExerciseBatchGenerateFailedException(
                course_id=dto.course_id,
                message="AI 题目生成超时，请稍后重试或减少生成数量",
            ) from e
        except HTTPConnectionException as e:
            logger.error(
                f"Dify workflow 连接失败: workflow_id={workflow.id or '(latest)'}, "
                f"course_id={dto.course_id}, url={e.kwargs.get('url', 'unknown')}",
                exc_info=True,
            )
            raise CourseExerciseBatchGenerateFailedException(
                course_id=dto.course_id,
                message="AI 服务连接失败，请检查网络或联系管理员",
            ) from e
        except HTTPRequestException as e:
            logger.error(
                f"Dify workflow 请求失败: workflow_id={workflow.id or '(latest)'}, "
                f"course_id={dto.course_id}, status_code={e.kwargs.get('status_code', 'unknown')}, "
                f"reason={e.kwargs.get('reason', 'unknown')}",
                exc_info=True,
            )
            raise CourseExerciseBatchGenerateFailedException(
                course_id=dto.course_id,
                message=f"AI 服务请求失败 ({e.kwargs.get('status_code', 'unknown')})，请稍后重试",
            ) from e
        except HTTPClientException as e:
            logger.error(
                f"Dify workflow 客户端错误: workflow_id={workflow.id or '(latest)'}, "
                f"course_id={dto.course_id}, operation={e.kwargs.get('operation', 'unknown')}",
                exc_info=True,
            )
            raise CourseExerciseBatchGenerateFailedException(
                course_id=dto.course_id,
                message="AI 服务客户端异常，请联系管理员",
            ) from e
        except Exception as e:
            logger.error(
                f"教师端批量生成题目失败: course_id={dto.course_id}, chapter_id={dto.chapter_id}, error={e}",
                exc_info=True,
            )
            raise CourseExerciseBatchGenerateFailedException(
                course_id=dto.course_id,
                message=f"题目生成失败: {e!s}",
            ) from e

    # ========================================================================
    # 异步生成方法
    # ========================================================================

    @staticmethod
    async def submit_generate_task(
        query_db: AsyncSession,
        dto: CourseExerciseBatchGenerateDTO,
        current_user: CurrentUser,
    ) -> CourseExerciseGenerateTaskVO:
        """提交异步生成任务：快速验证 → 派发 Celery → 返回 task_id。

        Args:
            query_db: 数据库会话
            dto: 批量生成参数
            current_user: 当前用户

        Returns:
            包含 task_id 的任务提交结果
        """
        # 快速验证：课程存在性
        course = await CourseMapper.get_by_id(dto.course_id, query_db)
        if not course:
            from graphedu.common.exceptions.services.education.course import CourseNotFoundException

            raise CourseNotFoundException(course_id=dto.course_id)

        # 派发 Celery 任务
        from graphedu.workers.course_exercise_tasks import generate_course_exercises

        user_id = _get_user_id(current_user)
        result = generate_course_exercises.apply_async(
            kwargs={
                "dto_data": dto.model_dump(mode="json"),
                "user_id": user_id,
            },
        )

        logger.info("已提交异步出题任务: task_id=%s, course_id=%s", result.id, dto.course_id)

        return CourseExerciseGenerateTaskVO(
            task_id=result.id,
            task_status="pending",
            message="任务已提交，正在生成中",
        )

    @staticmethod
    async def get_generate_progress(task_id: str) -> CourseExerciseGenerateProgressVO:
        """查询异步生成任务进度。

        Args:
            task_id: Celery 任务 ID

        Returns:
            任务进度信息
        """
        from celery.result import AsyncResult

        from graphedu.workers.celery import celery_app

        celery_task = AsyncResult(task_id, app=celery_app)
        status = _map_celery_state(celery_task.state)
        meta = celery_task.info if isinstance(celery_task.info, dict) else {}

        generated_count = 0
        message = None

        if status == "success" and celery_task.result:
            result = celery_task.result if isinstance(celery_task.result, dict) else {}
            generated_count = result.get("generated_count", 0)
        elif status == "failed":
            # Celery FAILURE 时 info 是异常对象
            if celery_task.result and isinstance(celery_task.result, dict):
                message = celery_task.result.get("message", "生成失败")
            else:
                message = str(celery_task.info) if celery_task.info else "生成失败"
        elif status in ("pending", "processing"):
            message = meta.get("step_description", "处理中...")

        progress_percent = meta.get("percent", 0)
        if status == "success":
            progress_percent = 100

        return CourseExerciseGenerateProgressVO(
            task_id=task_id,
            task_status=status,
            progress_percent=progress_percent,
            generated_count=generated_count,
            message=message,
        )
