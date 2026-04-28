"""章节资料管理服务模块

该模块提供章节资料信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
from io import BytesIO
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.chapter import ChapterNotFoundException
from graphedu.common.exceptions.services.education.chapter_resource import (
    ChapterResourceCreateFailedException,
    ChapterResourceIdListEmptyException,
    ChapterResourceNotFoundException,
    ChapterResourceUpdateFailedException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.chapter_resource import (
    ChapterResourceCreateDTO,
    ChapterResourceQueryDTO,
    ChapterResourceUpdateDTO,
)
from graphedu.common.models.orm.education import EduChapterResource
from graphedu.common.models.vo import BatchDeleteResponse, DeleteResultItem
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.educationv2.chapter_resource import (
    ChapterResourceDetailVO,
    ChapterResourceListVO,
    ChapterResourceParseStatusVO,
    ChapterResourceParseSubmitVO,
)
from graphedu.common.models.vo.systemv2.upload import FileInfoVO
from graphedu.mapper.education.chapter import ChapterMapper
from graphedu.mapper.education.chapter_resource import ChapterResourceMapper
from graphedu.mapper.system.upload import UploadMapper
from graphedu.services.external.mineru import MineruService
from graphedu.services.system.upload import UploadService

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_resource_orm_to_list_vo(
    resource_orm: EduChapterResource, file_info: FileInfoVO | None = None
) -> ChapterResourceListVO:
    """将章节资料 ORM 对象转换为 ChapterResourceListVO。

    Args:
        resource_orm: 章节资料 ORM 对象。
        file_info: 文件上传信息（可选）。

    Returns:
        ChapterResourceListVO: 章节资料列表项 VO。
    """
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
        file_info=file_info,
    )


def _convert_resource_orm_to_detail_vo(
    resource_orm: EduChapterResource, file_info: FileInfoVO | None = None
) -> ChapterResourceDetailVO:
    """将章节资料 ORM 对象转换为 ChapterResourceDetailVO。

    Args:
        resource_orm: 章节资料 ORM 对象。
        file_info: 文件上传信息（可选）。

    Returns:
        ChapterResourceDetailVO: 章节资料详细信息 VO。
    """
    return ChapterResourceDetailVO(
        resource_id=resource_orm.resource_id,
        chapter_id=resource_orm.chapter_id,
        resource_name=resource_orm.resource_name,
        resource_type=resource_orm.resource_type,
        file_id=resource_orm.file_id,
        resource_url=resource_orm.resource_url,
        description=resource_orm.description,
        resource_data=resource_orm.resource_data,
        text_file_id=resource_orm.text_file_id,
        parse_status=resource_orm.parse_status,
        display_order=resource_orm.display_order,
        is_visible=resource_orm.is_visible,
        status=resource_orm.status,
        create_by=resource_orm.create_by,
        create_time=resource_orm.create_time,
        update_by=resource_orm.update_by,
        update_time=resource_orm.update_time,
        file_url=None,
        file_info=file_info,
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _get_next_display_order(chapter_id: int, query_db: AsyncSession) -> int:
    """获取章节的下一个显示序号。

    Args:
        chapter_id: 章节 ID。
        query_db: 数据库会话。

    Returns:
        int: 下一个显示序号。
    """
    from sqlalchemy import and_, func, select

    stmt = select(func.max(EduChapterResource.display_order)).where(
        and_(
            EduChapterResource.chapter_id == chapter_id,
            EduChapterResource.status != SystemConstants.Status.DELETED,
        )
    )
    result = await query_db.execute(stmt)
    max_order = result.scalar()
    return (max_order or 0) + 1


# ============================================================================
# ChapterResourceService 类
# ============================================================================


class ChapterResourceService:
    """章节资料管理服务类

    提供章节资料的增删改查功能。
    """

    @staticmethod
    async def add_chapter_resource(
        query_db: AsyncSession,
        resource_data: ChapterResourceCreateDTO,
        current_user: CurrentUser,
        s3_client,
    ) -> ChapterResourceDetailVO:
        """新增章节资料信息。

        Args:
            query_db: 数据库会话。
            resource_data: 新增资料 DTO。
            current_user: 当前登录用户。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceDetailVO: 创建成功的资料 VO。

        Raises:
            ChapterNotFoundException: 章节不存在。
            ChapterResourceCreateFailedException: 资料新增失败。
        """
        # 1. 检查章节是否存在
        chapter = await ChapterMapper.get_by_id(resource_data.chapter_id, query_db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=resource_data.chapter_id)

        # 2. 自动设置显示序号
        if not resource_data.display_order or resource_data.display_order <= 0:
            resource_data.display_order = await _get_next_display_order(resource_data.chapter_id, query_db)

        # 3. DTO → ORM
        resource_dict = resource_data.model_dump(exclude_unset=True)
        if resource_data.resource_type == "text":
            resource_dict["parse_status"] = SystemConstants.ProcessStatus.COMPLETED

        new_resource = EduChapterResource(
            **resource_dict,
            status=SystemConstants.Status.NORMAL,
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
            create_time=datetime.now(),
        )

        # 4. 新增资料
        try:
            await ChapterResourceMapper.add_chapter_resource(new_resource, query_db)
        except Exception as e:
            raise ChapterResourceCreateFailedException(resource_name=resource_data.resource_name) from e

        logger.info(f"新增章节资料成功: {resource_data.resource_name}")

        # 5. 返回创建后的资料 VO
        resource_vo = _convert_resource_orm_to_detail_vo(new_resource)

        # 获取文件 URL 和文件信息
        if s3_client and resource_vo.file_id:
            resource_vo.file_url = await UploadService.get_file_url(resource_vo.file_id, query_db, s3_client)
        if resource_vo.file_id:
            upload_record = await UploadMapper.get_by_id(resource_vo.file_id, query_db)
            if upload_record:
                resource_vo.file_info = FileInfoVO.model_validate(upload_record)

        return resource_vo

    @staticmethod
    async def update_chapter_resource(
        query_db: AsyncSession,
        resource_data: ChapterResourceUpdateDTO,
        current_user: CurrentUser,
        s3_client,
    ) -> ChapterResourceDetailVO:
        """更新章节资料信息。

        Args:
            query_db: 数据库会话。
            resource_data: 更新资料 DTO。
            current_user: 当前登录用户。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceDetailVO: 更新后的资料 VO.

        Raises:
            ChapterResourceNotFoundException: 资料不存在。
            ChapterResourceUpdateFailedException: 资料更新失败。
        """
        # 1. 获取目标资料
        target_resource = await ChapterResourceMapper.get_by_id(resource_data.resource_id, query_db)
        if not target_resource:
            raise ChapterResourceNotFoundException(resource_id=resource_data.resource_id)

        # 2. 更新目标资料
        update_data = resource_data.model_dump(exclude_unset=True, exclude={"resource_id"})
        for field, value in update_data.items():
            setattr(target_resource, field, value)

        target_resource.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_resource.update_time = datetime.now()

        try:
            await ChapterResourceMapper.update(target_resource, query_db)
        except Exception as e:
            raise ChapterResourceUpdateFailedException(resource_id=resource_data.resource_id) from e

        # 3. 返回更新后的资料 VO
        resource_vo = _convert_resource_orm_to_detail_vo(target_resource)

        # 获取文件 URL 和文件信息
        if s3_client and resource_vo.file_id:
            resource_vo.file_url = await UploadService.get_file_url(resource_vo.file_id, query_db, s3_client)
        if resource_vo.file_id:
            upload_record = await UploadMapper.get_by_id(resource_vo.file_id, query_db)
            if upload_record:
                resource_vo.file_info = FileInfoVO.model_validate(upload_record)

        return resource_vo

    @staticmethod
    async def list_chapter_resource(
        query_db: AsyncSession, query_object: ChapterResourceQueryDTO, s3_client=None
    ) -> PageResponse[ChapterResourceListVO]:
        """获取章节资料列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。
            s3_client: S3 客户端（可选，用于生成文件访问 URL）。

        Returns:
            PageResponse[ChapterResourceListVO]: 分页结果。
        """
        rows, total = await ChapterResourceMapper.get_resource_list(query_db, query_object, is_page=True)

        # 将 ORM 对象转换为 ChapterResourceListVO
        resource_list = [_convert_resource_orm_to_list_vo(row) for row in rows]

        # 批量获取文件 URL 和文件信息
        if s3_client:
            file_ids = [resource.file_id for resource in resource_list if resource.file_id]
            if file_ids:
                url_map = await UploadService.get_file_url_map(file_ids, query_db, s3_client)
                upload_records = await UploadMapper.get_by_ids(file_ids, query_db)
                file_info_map = {r.file_id: FileInfoVO.model_validate(r) for r in upload_records}
                for resource in resource_list:
                    if resource.file_id:
                        resource.file_url = url_map.get(resource.file_id)
                        resource.file_info = file_info_map.get(resource.file_id)

        return PageResponse(rows=resource_list, page=query_object.page or 1, size=query_object.size or 10, total=total)

    @staticmethod
    async def delete_chapter_resource(
        query_db: AsyncSession, resource_id_list: list[int], current_user: CurrentUser
    ) -> BatchDeleteResponse[int]:
        """删除章节资料信息（批量，部分成功模式）。

        Args:
            query_db: 数据库会话。
            resource_id_list: 资料 ID 列表。
            current_user: 当前用户。

        Returns:
            BatchDeleteResponse[int]: 包含成功数量、失败数量和详细结果的响应对象

        Raises:
            ChapterResourceIdListEmptyException: 资料 ID 列表为空。
        """
        if not resource_id_list:
            raise ChapterResourceIdListEmptyException

        results: list[DeleteResultItem[int]] = []

        for resource_id in resource_id_list:
            try:
                resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
                if not resource:
                    results.append(DeleteResultItem(target_id=resource_id, success=False, error="资料不存在"))
                    continue

                # 软删除资料
                resource.status = SystemConstants.Status.DELETED
                resource.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                resource.update_time = datetime.now()
                await ChapterResourceMapper.update(resource, query_db)

                results.append(DeleteResultItem(target_id=resource_id, success=True, error=None))

            except Exception as e:
                results.append(DeleteResultItem(target_id=resource_id, success=False, error=str(e)))

        success_cnt = sum(1 for r in results if r.success)
        fail_cnt = sum(1 for r in results if not r.success)
        logger.info(f"批量删除章节资料完成: 成功 {success_cnt}, 失败 {fail_cnt}")

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def change_resource_status(
        query_db: AsyncSession, resource_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改资料状态。

        Args:
            query_db: 数据库会话。
            resource_id: 资料 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            ChapterResourceNotFoundException: 资料不存在。
        """
        resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
        if not resource:
            raise ChapterResourceNotFoundException(resource_id=resource_id)

        resource.status = status
        resource.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        resource.update_time = datetime.now()
        await ChapterResourceMapper.update(resource, query_db)
        logger.info(f"修改资料状态成功: {resource_id}")

    @staticmethod
    async def get_chapter_resource_detail(
        query_db: AsyncSession, resource_id: int, s3_client
    ) -> ChapterResourceDetailVO | None:
        """获取资料详细信息。

        Args:
            query_db: 数据库会话。
            resource_id: 资料 ID。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceDetailVO | None: 资料详细信息 VO。
        """
        resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
        if not resource:
            return None

        resource_vo = _convert_resource_orm_to_detail_vo(resource)

        # 获取文件 URL 和文件信息
        if s3_client and resource_vo.file_id:
            resource_vo.file_url = await UploadService.get_file_url(resource_vo.file_id, query_db, s3_client)
        if resource_vo.file_id:
            upload_record = await UploadMapper.get_by_id(resource_vo.file_id, query_db)
            if upload_record:
                resource_vo.file_info = FileInfoVO.model_validate(upload_record)

        return resource_vo

    @staticmethod
    async def get_resources_by_chapter(
        query_db: AsyncSession, chapter_id: int, s3_client, include_hidden: bool = False
    ) -> list[ChapterResourceListVO]:
        """按章节获取资料列表。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            s3_client: S3 客户端。
            include_hidden: 是否包含隐藏内容（管理员视角传 True，学生视角传 False）。

        Returns:
            list[ChapterResourceListVO]: 资料列表。

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        # 检查章节是否存在
        chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 获取资料列表（管理员可见全部，学生仅可见可见内容）
        resources = await ChapterResourceMapper.get_resources_by_chapter_id(
            chapter_id, query_db, include_hidden=include_hidden
        )

        # 转换为 VO
        resource_list = [_convert_resource_orm_to_list_vo(resource) for resource in resources]

        # 批量获取文件 URL 和文件信息
        if s3_client:
            file_ids = [resource.file_id for resource in resource_list if resource.file_id]
            if file_ids:
                url_map = await UploadService.get_file_url_map(file_ids, query_db, s3_client)
                upload_records = await UploadMapper.get_by_ids(file_ids, query_db)
                file_info_map = {r.file_id: FileInfoVO.model_validate(r) for r in upload_records}
                for resource in resource_list:
                    if resource.file_id:
                        resource.file_url = url_map.get(resource.file_id)
                        resource.file_info = file_info_map.get(resource.file_id)

        return resource_list

    @staticmethod
    async def reorder_resources(
        query_db: AsyncSession, chapter_id: int, resource_orders: dict[int, int], current_user: CurrentUser
    ) -> None:
        """调整资料顺序。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            resource_orders: 资料 ID 到新序号的映射 {resource_id: new_order}。
            current_user: 当前用户。

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        # 检查章节是否存在
        chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 更新每个资料的显示顺序
        for resource_id, new_order in resource_orders.items():
            resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
            if resource and resource.chapter_id == chapter_id:
                resource.display_order = new_order
                resource.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                resource.update_time = datetime.now()
                await ChapterResourceMapper.update(resource, query_db)

        logger.info(f"调整资料顺序成功: 章节 {chapter_id}")

    @staticmethod
    async def submit_parse(
        query_db: AsyncSession,
        resource_id: int,
        current_user: CurrentUser,
        s3_client,
    ) -> ChapterResourceParseSubmitVO:
        """提交 MinerU PDF 解析任务。

        Args:
            query_db: 数据库会话。
            resource_id: 资料 ID。
            current_user: 当前用户。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceParseSubmitVO: 提交解析任务结果。

        Raises:
            ChapterResourceNotFoundException: 资料不存在。
        """
        # 1. 获取资料
        resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
        if not resource:
            raise ChapterResourceNotFoundException(resource_id=resource_id)

        # 2. 获取 PDF 文件 URL
        file_url = await UploadService.get_file_url(resource.file_id, query_db, s3_client)
        if not file_url:
            raise ChapterResourceUpdateFailedException(msg=f"资料 {resource_id} 没有关联的 PDF 文件，无法提交解析。")

        # 3. 提交 MinerU 解析任务
        task_response = await MineruService.submit_parse_task(pdf_url=file_url, title=resource.resource_name)
        mineru_task_id = task_response.task_id

        # 4. 更新解析状态
        resource.parse_status = SystemConstants.ProcessStatus.RUNNING
        resource_data = resource.resource_data or {}
        resource_data["mineru_task_id"] = mineru_task_id
        resource.resource_data = resource_data
        resource.update_by = current_user.detail.user.user_id if current_user and current_user.detail.user else None
        resource.update_time = datetime.now()
        await ChapterResourceMapper.update(resource, query_db)

        logger.info(
            "提交 MinerU 解析任务成功: resource_id=%d, mineru_task_id=%s",
            resource_id,
            mineru_task_id,
        )
        return ChapterResourceParseSubmitVO(
            resource_id=resource_id,
            mineru_task_id=mineru_task_id,
            parse_status=SystemConstants.ProcessStatus.RUNNING,
        )

    @staticmethod
    async def check_parse_status(
        query_db: AsyncSession,
        resource_id: int,
        current_user: CurrentUser,
        s3_client,
    ) -> ChapterResourceParseStatusVO:
        """检查并更新解析状态。

        Args:
            query_db: 数据库会话。
            resource_id: 资料 ID。
            current_user: 当前用户。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceParseStatusVO: 解析与图谱构建状态。
        """
        # 1. 获取资料
        resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
        if not resource:
            raise ChapterResourceNotFoundException(resource_id=resource_id)

        parse_status = resource.parse_status

        # 2. 如果解析中，主动查询 MinerU 状态
        if parse_status in (SystemConstants.ProcessStatus.RUNNING, SystemConstants.ProcessStatus.PENDING):
            # 从 resource_data 获取 mineru_task_id
            task_id = None
            if resource.resource_data:
                task_id = resource.resource_data.get("mineru_task_id")

            if task_id:
                status_resp = await MineruService.get_task_status(task_id)

                # 根据 MinerU API 响应状态更新资源状态
                if status_resp.status == "submitted" or status_resp.status == "processing":
                    resource.parse_status = SystemConstants.ProcessStatus.RUNNING
                elif status_resp.status == "completed":
                    # 下载 Markdown
                    result_url = status_resp.result.get("result_url") if status_resp.result else None
                    markdown_pages: list[str] = []
                    if result_url:
                        markdown_pages = await MineruService.download_result(result_url)

                    full_markdown = "\n\n---\n\n".join(markdown_pages)

                    # 上传 Markdown 到 S3
                    s3_key = f"graphrag/markdown/resource_{resource_id}.md"
                    if s3_client and full_markdown:
                        await s3_client.upload_object(
                            BytesIO(full_markdown.encode("utf-8")),
                            s3_key,
                        )

                    # 更新解析状态
                    resource.parse_status = SystemConstants.ProcessStatus.COMPLETED
                    resource_data = resource.resource_data or {}
                    resource_data["page_count"] = len(markdown_pages)
                    resource_data["markdown_length"] = len(full_markdown)
                    if full_markdown:
                        resource_data["markdown_s3_key"] = s3_key
                    resource_data["mineru_task_id"] = task_id
                    resource.resource_data = resource_data
                    await ChapterResourceMapper.update(resource, query_db)

                    logger.info(f"MinerU 解析完成: resource_id={resource_id}")

                elif status_resp.status in ("failed", "error"):
                    resource.parse_status = SystemConstants.ProcessStatus.ERROR
                    resource_data = resource.resource_data or {}
                    resource_data["error_message"] = status_resp.message or "MinerU 解析失败"
                    resource.resource_data = resource_data
                    await ChapterResourceMapper.update(resource, query_db)

        markdown_s3_key = resource.resource_data.get("markdown_s3_key") if resource.resource_data else None
        markdown_url = None
        if markdown_s3_key and s3_client:
            markdown_url = await s3_client.generate_presigned_url(markdown_s3_key, expiration=3600)

        return ChapterResourceParseStatusVO(
            resource_id=resource_id,
            parse_status=resource.parse_status,
            mineru_task_id=resource.resource_data.get("mineru_task_id") if resource.resource_data else None,
            text_file_id=resource.text_file_id,
            page_count=resource.resource_data.get("page_count") if resource.resource_data else None,
            markdown_length=resource.resource_data.get("markdown_length") if resource.resource_data else None,
            markdown_s3_key=markdown_s3_key,
            markdown_url=markdown_url,
            error_message=resource.resource_data.get("error_message") if resource.resource_data else None,
        )
