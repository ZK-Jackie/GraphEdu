"""章节资料管理 API 控制器

本模块提供章节资料相关的 REST API 接口，包括资料的增删改查、
状态管理、排序、PDF 解析及 GraphRAG 构建等功能。

主要接口：
- 资料列表：分页查询资料列表，支持多条件筛选
- 资料管理：新增、修改、删除资料
- 状态管理：启用/停用资料
- 排序管理：调整资料显示顺序
- 按章节查询：获取指定章节的资料列表（学生端）
- 资料详情：查询资料详细信息
- PDF 解析：提交解析任务、查询解析状态
- 图谱构建：触发 GraphRAG 索引构建
"""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.base import DTO
from graphedu.common.models.dto.educationv2.chapter_resource import (
    ChapterResourceCreateDTO,
    ChapterResourceQueryDTO,
    ChapterResourceUpdateDTO,
)
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.chapter_resource import (
    ChapterResourceDetailVO,
    ChapterResourceListVO,
    ChapterResourceParseStatusVO,
    ChapterResourceParseSubmitVO,
)
from graphedu.common.resource import AioS3Client
from graphedu.common.resource.deps import get_db, get_s3
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.chapter_resource import ChapterResourceService

# ============================================================================
# 控制器内联 DTO（仅用于本控制器）
# ============================================================================


class _ChangeStatusBody(DTO):
    """修改资料状态请求体"""

    resource_id: int = Field(description="资料ID")
    status: Literal["0", "1", "2"] = Field(description="状态（0正常 1停用 2已删除）")


class _ReorderBody(DTO):
    """调整资料顺序请求体"""

    chapter_id: int = Field(description="章节ID")
    resource_orders: dict[int, int] = Field(description="资料ID到新序号的映射 {resourceId: newOrder}")


# ============================================================================
# 路由器
# ============================================================================

chapter_resource_controller = APIRouter(
    prefix="/education/chapter-resource",
    dependencies=[Depends(SecurityService.get_current_user)],
)


# ============================================================================
# 资料列表查询
# ============================================================================


@chapter_resource_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:list"))],
    response_model=ResponseType[PageResponse[ChapterResourceListVO]],
)
async def get_chapter_resource_list(
    query: ChapterResourceQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取章节资料列表（分页）"""
    result = await ChapterResourceService.list_chapter_resource(query_db, query, s3_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# 资料新增
# ============================================================================


@chapter_resource_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:add"))],
    response_model=ResponseType[ChapterResourceDetailVO],
)
@SystemLog(title="章节资料管理", business_type=SysConst.BusinessType.INSERT)
async def add_chapter_resource(
    resource_data: ChapterResourceCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """新增章节资料"""
    result = await ChapterResourceService.add_chapter_resource(query_db, resource_data, current_user, s3_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# 资料修改
# ============================================================================
@chapter_resource_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:edit"))],
    response_model=ResponseType[ChapterResourceDetailVO],
)
@SystemLog(title="章节资料管理", business_type=SysConst.BusinessType.UPDATE)
async def update_chapter_resource(
    resource_data: ChapterResourceUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """修改章节资料"""
    result = await ChapterResourceService.update_chapter_resource(query_db, resource_data, current_user, s3_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# 修改资料状态（固定路径优先于参数路径）
# ============================================================================


@chapter_resource_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节资料管理", business_type=SysConst.BusinessType.UPDATE)
async def change_resource_status(
    body: _ChangeStatusBody = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改资料状态（启用/停用）"""
    await ChapterResourceService.change_resource_status(query_db, body.resource_id, body.status, current_user)
    return ResponseUtil.success()


# ============================================================================
# 调整资料顺序（固定路径优先于参数路径）
# ============================================================================


@chapter_resource_controller.put(
    "/reorder",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节资料管理", business_type=SysConst.BusinessType.UPDATE)
async def reorder_chapter_resources(
    body: _ReorderBody = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """调整章节内资料显示顺序"""
    await ChapterResourceService.reorder_resources(query_db, body.chapter_id, body.resource_orders, current_user)
    return ResponseUtil.success()


# ============================================================================
# 按章节获取资料列表（学生端，固定路径前缀优先于参数路径）
# ============================================================================


@chapter_resource_controller.get(
    "/chapter/{chapter_id}",
    response_model=ResponseType[list[ChapterResourceListVO]],
)
async def get_resources_by_chapter(
    chapter_id: int = Path(..., description="章节ID"),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """按章节获取资料列表（学生端，仅返回可见资料）"""
    result = await ChapterResourceService.get_resources_by_chapter(
        query_db, chapter_id, s3_client, include_hidden=False
    )
    return ResponseUtil.success(data=result)


# ============================================================================
# 资料详情（参数路径，需在所有固定路径之后）
# ============================================================================


@chapter_resource_controller.get(
    "/{resource_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:query"))],
    response_model=ResponseType[ChapterResourceDetailVO],
)
async def get_chapter_resource_detail(
    resource_id: int = Path(..., description="资料ID"),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取资料详细信息"""
    result = await ChapterResourceService.get_chapter_resource_detail(query_db, resource_id, s3_client)
    if result is None:
        return ResponseUtil.error(msg="资料不存在")
    return ResponseUtil.success(data=result)


# ============================================================================
# 资料删除（批量）
# ============================================================================


@chapter_resource_controller.delete(
    "/{resource_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:remove"))],
    response_model=ResponseType[BatchDeleteResponse],
)
@SystemLog(title="章节资料管理", business_type=SysConst.BusinessType.DELETE)
async def delete_chapter_resource(
    resource_ids: str = Path(..., description="资料ID，多个用逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除章节资料（支持批量）"""
    id_list = [int(i) for i in resource_ids.split(",") if i.strip()]
    result = await ChapterResourceService.delete_chapter_resource(query_db, id_list, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# PDF 解析任务
# ============================================================================


@chapter_resource_controller.post(
    "/{resource_id}/parse",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:edit"))],
    response_model=ResponseType[ChapterResourceParseSubmitVO],
)
@SystemLog(title="章节资料管理", business_type=SysConst.BusinessType.OTHER)
async def submit_parse(
    resource_id: int = Path(..., alias="resourceId", description="资料ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """提交 MinerU PDF 解析任务"""
    result = await ChapterResourceService.submit_parse(query_db, resource_id, current_user, s3_client)
    return ResponseUtil.success(data=result)


@chapter_resource_controller.get(
    "/{resourceId}/parse-status",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter-resource:query"))],
    response_model=ResponseType[ChapterResourceParseStatusVO],
)
async def get_parse_status(
    resource_id: int = Path(..., alias="resourceId", description="资料ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取 PDF 解析及 GraphRAG 构建状态"""
    result = await ChapterResourceService.check_parse_status(query_db, resource_id, current_user, s3_client)
    return ResponseUtil.success(data=result)
