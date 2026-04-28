"""AI 习题生成 Celery 任务"""

import asyncio
import logging
import sys
from typing import Any, Literal

from celery import Task

from graphedu.common import get_config
from graphedu.common.exceptions.common.resource import (
    HTTPClientException,
    HTTPConnectionException,
    HTTPRequestException,
    HTTPTimeoutException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo.dify import DifyFile
from graphedu.common.models.bo.teacher_course_exercise import (
    CourseExerciseGenerateRequest,
    CourseExerciseWorkflowResponse,
)
from graphedu.common.models.dto.educationv2.course_exercise import CourseExerciseBatchGenerateDTO
from graphedu.common.models.orm.education import EduCourseExercise
from graphedu.common.models.shared import QuestionOptionContent
from graphedu.common.resource import ContainerMode, WorkerContainer, try_get_container
from graphedu.mapper.education.chapter_resource import ChapterResourceMapper
from graphedu.mapper.education.course import CourseMapper
from graphedu.mapper.education.course_exercise import CourseExerciseMapper
from graphedu.services.external.dify import DifyService
from graphedu.services.system.upload import UploadService
from graphedu.workers.celery import celery_app

# 资源类型 → Dify 文件类型映射
_RESOURCE_TYPE_TO_DIFY: dict[str, Literal["document", "image", "audio", "video", "custom"]] = {
    "document": "document",
    "video": "video",
    "text": "document",
}

logger = logging.getLogger(__name__)


def _convert_generate_response_to_question_content(
    item: "CourseExerciseWorkflowResponse.__class__",
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


@celery_app.task(
    bind=True,
    name="graphedu.workers.generate_course_exercises",
    max_retries=1,
    track_started=True,
)
def generate_course_exercises(self: Task, dto_data: dict, user_id: int | None) -> dict[str, Any]:
    """Celery 异步任务：AI 批量生成课程练习。

    Args:
        self: Celery 任务实例
        dto_data: 序列化的 CourseExerciseBatchGenerateDTO
        user_id: 当前用户 ID

    Returns:
        生成结果摘要
    """

    async def _process():
        container: WorkerContainer = await try_get_container(ContainerMode.WORKER)
        db_client = await container.postgresql_client()
        s3_client = await container.s3_client()
        http_client = await container.http_client()

        dto = CourseExerciseBatchGenerateDTO(**dto_data)
        config = get_config().dify

        # ── 1. 验证课程存在 ──────────────────────────────────────────────
        async with db_client.session_context() as db:
            course = await CourseMapper.get_by_id(dto.course_id, db)
            if not course:
                return {"status": "error", "message": f"课程 {dto.course_id} 不存在"}

        # ── 2. resource_id → file_id → OSS URL ────────────────────────────
        self.update_state(
            state="PROGRESS",
            meta={"step": "resolving_resources", "percent": 10, "step_description": "解析课程资料..."},
        )

        file_ids: list[int] = []
        resource_type_map: dict[int, str] = {}
        async with db_client.session_context() as db:
            for resource_id in dto.resource_ids:
                resource = await ChapterResourceMapper.get_by_id(resource_id, db)
                if not resource:
                    continue
                fid = resource.text_file_id or resource.file_id
                if fid:
                    file_ids.append(fid)
                    resource_type_map[fid] = resource.resource_type

        # ── 3. file_id → OSS URL ──────────────────────────────────────────
        async with db_client.session_context() as db:
            file_url_map = await UploadService.get_file_url_map(file_ids, db, s3_client)

        # ── 4. 构造 DifyFile 列表 ──────────────────────────────────────────
        dify_files: list[DifyFile] = []
        for fid, url in file_url_map.items():
            dify_files.append(
                DifyFile(
                    type=_RESOURCE_TYPE_TO_DIFY.get(resource_type_map.get(fid, "document"), "document"),
                    transfer_method="remote_url",
                    url=url,
                )
            )

        # ── 5. 调用 Dify workflow ──────────────────────────────────────────
        self.update_state(
            state="PROGRESS",
            meta={"step": "calling_ai", "percent": 30, "step_description": "AI 正在生成题目..."},
        )

        request = CourseExerciseGenerateRequest(
            upload_files=dify_files or None,
            difficulty=dto.difficulty,
            question_type=dto.question_type,
            extra_info=dto.extra_info,
            number=dto.number,
        )

        workflow = config.workflows.teacher_exercise_generation

        try:
            workflow_response: CourseExerciseWorkflowResponse = await DifyService.invoke_workflow(
                inputs=request,
                user=str(user_id or "teacher"),
                api_key=workflow.api_key,
                base_url=config.base_url,
                http_client=http_client,
                workflow_id=workflow.id,
                return_model=CourseExerciseWorkflowResponse,
            )
        except HTTPTimeoutException:
            logger.error("Dify workflow 请求超时: course_id=%s", dto.course_id, exc_info=True)
            return {"status": "failed", "message": "AI 题目生成超时，请稍后重试或减少生成数量"}
        except HTTPConnectionException:
            logger.error("Dify workflow 连接失败: course_id=%s", dto.course_id, exc_info=True)
            return {"status": "failed", "message": "AI 服务连接失败，请检查网络或联系管理员"}
        except HTTPRequestException:
            logger.error("Dify workflow 请求失败: course_id=%s", dto.course_id, exc_info=True)
            return {"status": "failed", "message": "AI 服务请求失败，请稍后重试"}
        except HTTPClientException:
            logger.error("Dify workflow 客户端错误: course_id=%s", dto.course_id, exc_info=True)
            return {"status": "failed", "message": "AI 服务客户端异常，请联系管理员"}

        # ── 6. 验证响应 ────────────────────────────────────────────────────
        if not workflow_response or not workflow_response.output:
            logger.error("Dify workflow 返回空响应: course_id=%s", dto.course_id)
            return {"status": "failed", "message": "工作流返回空数据，请检查 Dify 配置或稍后重试"}

        if len(workflow_response.output) == 0:
            logger.warning("Dify workflow 未生成任何题目: course_id=%s", dto.course_id)
            return {"status": "failed", "message": "未生成任何题目，请尝试调整生成参数后重试"}

        # ── 7. 转换并持久化 ────────────────────────────────────────────────
        self.update_state(
            state="PROGRESS",
            meta={"step": "saving", "percent": 80, "step_description": "保存生成的题目..."},
        )

        from datetime import datetime

        question_type = dto.question_type or "single"
        now = datetime.now()

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
                logger.warning("跳过无效的题目数据 (索引=%d): %s", idx, item_error, exc_info=True)
                continue

        if not exercises_orm:
            logger.error("所有题目数据均无效: course_id=%s", dto.course_id)
            return {"status": "failed", "message": "题目数据格式错误，请检查 Dify 工作流输出格式"}

        async with db_client.session_context() as db:
            await CourseExerciseMapper.batch_add_course_exercises(exercises_orm, db)

        logger.info(
            "教师端异步生成题目成功: course_id=%s, chapter_id=%s, generated=%d/%d",
            dto.course_id,
            dto.chapter_id,
            len(exercises_orm),
            dto.number,
        )
        return {"status": "success", "generated_count": len(exercises_orm)}

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_process(), **asyncio_run_kwargs)
