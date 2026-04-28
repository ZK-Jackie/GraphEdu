"""GraphRAG Celery 任务

包含 GraphRAG 索引构建任务（build_graphrag_index）。
MinerU 解析直接由主 API 程序处理，不走 Celery。
"""

import asyncio
from datetime import datetime
import logging
import re
import sys
from zoneinfo import ZoneInfo

from anyio import Path
from celery import Task
from graphrag.api import build_index as graphrag_build_index
from graphrag.config.enums import IndexingMethod
from graphrag_celery_callback.celery_workflow_callbacks import CeleryWorkflowCallbacks
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.config.manager import get_config
from graphedu.common.resource import ContainerMode, WorkerContainer, try_get_container
from graphedu.mapper.education.graphrag_task import GraphRAGTaskMapper
from graphedu.mapper.system.upload import UploadMapper
from graphedu.services.external.graphrag import build_graphrag_config
from graphedu.workers.celery import celery_app

logger = logging.getLogger(__name__)


def _now() -> datetime:
    """返回上海时间"""
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def _detect_input_suffix(file_name: str, default: str = ".txt") -> str:
    """从文件名中检测扩展名，返回 .md 或 .txt。"""
    match = re.search(r"\.(\w+)(?:\?|$)", file_name, re.IGNORECASE)
    if match:
        ext = match.group(1).lower()
        if ext in ("md", "markdown", "txt", "text"):
            return f".{ext}" if ext in ("md", "txt") else ".md"
    return default


async def _check_task_cancelled(graphrag_task_id: int, db: AsyncSession) -> bool:
    """检查任务是否已被用户取消，若取消则返回 True。"""
    latest_task = await GraphRAGTaskMapper.get_by_id(graphrag_task_id, db)
    return latest_task is not None and latest_task.task_status == "cancelled"


@celery_app.task(bind=True, name="graphedu.workers.build_graphrag_index", max_retries=2)
def build_graphrag_index(self: Task, graphrag_task_id: int):
    """为 EduGraphRAGTask 中的资源列表构建 GraphRAG 索引。

    Args:
        self: Celery 任务实例（通过 bind=True 传入）
        graphrag_task_id: EduGraphRAGTask 主键 ID。

    Returns:
        dict: 构建结果摘要。
    """

    async def _process():
        # 准备资源
        container: WorkerContainer = await try_get_container(ContainerMode.WORKER)
        db_client = await container.postgresql_client()
        s3_client = await container.s3_client()

        cfg = get_config()
        gr_cfg = cfg.graphrag
        # self.request.id 已被 apply_async(task_id=str(graphrag_task_id)) 设置为系统 ID
        namespace = str(graphrag_task_id)

        # ── 1. 查询 GraphRAG 任务对象 ─────────────────────────────────────
        async with db_client.session_context() as db:
            graphrag_task = await GraphRAGTaskMapper.get_by_id(graphrag_task_id, db)
            if not graphrag_task:
                logger.error("GraphRAG 任务 %d 不存在", graphrag_task_id)
                return {"status": "error", "message": f"任务 {graphrag_task_id} 不存在"}

            resource_ids: list[int] = list(graphrag_task.resource_ids or [])
            # 读取用户配置的实体类型和提示词模板
            task_entity_types: list[str] | None = (
                list(graphrag_task.entity_types) if graphrag_task.entity_types else None
            )
            task_prompt_template: str | None = graphrag_task.prompt_template

            # ── 2. 标记任务为处理中 ────────────────────────────────────────
            await GraphRAGTaskMapper.update_status(
                graphrag_task_id,
                db,
                task_status="processing",
                start_time=_now(),
            )

        # ── 3. 批量查询资源 ───────────────────────────────────────────────
        async with db_client.session_context() as db:
            resources = await GraphRAGTaskMapper.get_resources_by_ids(resource_ids, db)

        # ── 4. 逐资源获取文本内容 ─────────────────────────────────────────
        working_dir = await Path(gr_cfg.working_dir).resolve()
        input_dir = working_dir / namespace / "input"
        await input_dir.mkdir(parents=True, exist_ok=True)

        valid_resource_ids: list[int] = []

        for resource in resources:
            rid = resource.resource_id
            rtype = resource.resource_type
            # input_suffix = ".md"
            # source_type = "document-parse"

            # 确定文件来源：text 类型用 file_id，其他类型用 text_file_id
            if rtype == "text":
                source_file_id = resource.file_id
                if not source_file_id:
                    logger.warning("跳过资源 %d：text 类型但 file_id 为空", rid)
                    continue
                source_type = "direct-text"
            else:
                source_file_id = resource.text_file_id
                source_type = f"converted-{rtype}"

            if not source_file_id:
                logger.warning("跳过资源 %d：无可用文件 ID", rid)
                continue

            # 统一通过 OSS 获取文件内容
            async with db_client.session_context() as db:
                upload = await UploadMapper.get_by_id(source_file_id, db)

            if not upload or not upload.file_path:
                msg = f"资源 {rid} 的 file_id={source_file_id} 在 sys_upload 中不存在或 file_path 为空"
                logger.error(msg)
                async with db_client.session_context() as db:
                    await GraphRAGTaskMapper.update_status(
                        graphrag_task_id,
                        db,
                        task_status="failed",
                        task_message=msg,
                        end_time=_now(),
                    )
                return {"status": "error", "message": msg}

            try:
                logger.info("从 S3 下载文本: resource_id=%d, file_path=%s", rid, upload.file_path)
                bytesio = await s3_client.download_to_bytesio(upload.file_path)
                content: str = bytesio.read().decode("utf-8")
            except Exception as e:
                logger.warning("跳过资源 %d：从 OSS 下载失败: %s", rid, e)
                continue

            # 根据上传文件名检测扩展名
            input_suffix = _detect_input_suffix(upload.file_name or "", default=".txt" if rtype == "text" else ".md")

            # 写入 input 目录
            input_file = input_dir / f"{rid}{input_suffix}"
            await input_file.write_text(content, encoding="utf-8")
            valid_resource_ids.append(rid)
            logger.info("已写入 input 文件: %s, source=%s", input_file, source_type)

        # ── 5. 无有效文档时直接失败 ───────────────────────────────────────
        if not valid_resource_ids:
            msg = "任务中无可处理的文本资源（所有资源均被跳过）"
            logger.error("任务 %d：%s", graphrag_task_id, msg)
            async with db_client.session_context() as db:
                await GraphRAGTaskMapper.update_status(
                    graphrag_task_id,
                    db,
                    task_status="failed",
                    task_message=msg,
                    end_time=_now(),
                )
            return {"status": "failed", "message": msg}

        # ── 6. 检查是否已取消 ──────────────────────────────────────────────
        async with db_client.session_context() as db:
            if await _check_task_cancelled(graphrag_task_id, db):
                return {"status": "cancelled", "message": "任务已取消"}

        # ── 7. 构建 GraphRagConfig 并执行索引 ─────────────────────────────
        # namespace == str(graphrag_task_id)，重试时所有存储均幂等（upsert/覆盖）
        graphrag_config = build_graphrag_config(
            namespace=namespace,
            entity_types=task_entity_types,
            prompt_template=task_prompt_template,
        )
        method = IndexingMethod(gr_cfg.method)
        # work_id 使用系统 task_id，与 Celery backend 中的 task meta key 对齐
        callbacks = [CeleryWorkflowCallbacks(work_id=namespace, celery_app=celery_app)]  # type: ignore[list-item]

        logger.info(
            "开始构建索引: graphrag_task_id=%d, resources=%s, method=%s, entity_types=%s, prompt=%s",
            graphrag_task_id,
            valid_resource_ids,
            method,
            task_entity_types,
            task_prompt_template,
        )
        try:
            results = await graphrag_build_index(
                config=graphrag_config,
                method=method,
                is_update_run=False,
                callbacks=callbacks,  # type: ignore[arg-type]
                verbose=False,
            )
            errors = [str(r.error) for r in results if r.error is not None]
            if errors:
                msg = f"索引构建过程中出现错误: {','.join(errors)}"
                raise RuntimeError(msg)
        except Exception as e:
            msg = str(e)
            logger.error("索引构建失败: graphrag_task_id=%d, error=%s", graphrag_task_id, msg)
            async with db_client.session_context() as db:
                if await _check_task_cancelled(graphrag_task_id, db):
                    return {"status": "cancelled", "message": "任务已取消"}

                await GraphRAGTaskMapper.update_status(
                    graphrag_task_id,
                    db,
                    task_status="failed",
                    task_message=msg,
                    end_time=_now(),
                )
            raise self.retry(exc=e, countdown=120) from e

        # ── 8. 成功：更新各资源和任务状态 ─────────────────────────────────
        async with db_client.session_context() as db:
            if await _check_task_cancelled(graphrag_task_id, db):
                logger.info("任务已取消，跳过成功回写: graphrag_task_id=%d", graphrag_task_id)
                return {
                    "status": "cancelled",
                    "graphrag_task_id": graphrag_task_id,
                    "resource_ids": valid_resource_ids,
                }

            await GraphRAGTaskMapper.update_status(
                graphrag_task_id,
                db,
                task_status="success",
                end_time=_now(),
            )

        logger.info(
            "构建完成: graphrag_task_id=%d, resources=%s",
            graphrag_task_id,
            valid_resource_ids,
        )
        return {
            "status": "success",
            "graphrag_task_id": graphrag_task_id,
            "resource_ids": valid_resource_ids,
        }

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_process(), **asyncio_run_kwargs)
