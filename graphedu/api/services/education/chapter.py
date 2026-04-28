"""章节管理 API 控制器

本模块提供章节管理相关的 REST API 接口，包括章节的增删改查、
状态管理、树形结构获取等功能。

主要接口：
- 章节列表：分页查询章节列表，支持多条件筛选
- 章节管理：新增、修改、删除章节
- 状态管理：启用/停用章节
- 章节详情：查询章节详细信息
- 章节树：获取课程的章节树形结构（完整树/懒加载/下拉选择）
- 章节移动：移动章节到不同父节点
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.chapter import (
    ChapterCreateDTO,
    ChapterDescriptionGenerateDTO,
    ChapterMoveDTO,
    ChapterQueryDTO,
    ChapterStatusChangeDTO,
    ChapterUpdateDTO,
)
from graphedu.common.models.dto.educationv2.chapter_resource import (
    ChapterResourceBatchDeleteDTO,
    ChapterResourceCreateDTO,
    ChapterResourceReorderDTO,
    ChapterResourceStatusChangeDTO,
    ChapterResourceUpdateDTO,
)
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.chapter import (
    ChapterDescriptionResultVO,
    ChapterDetailVO,
    ChapterListVO,
    ChapterTreeBriefVO,
    ChapterTreeVO,
)
from graphedu.common.models.vo.educationv2.chapter_resource import (
    ChapterResourceBatchDeleteResultVO,
    ChapterResourceDetailVO,
    ChapterResourceListVO,
)
from graphedu.common.models.vo.educationv2.knowledge_graph import (
    ChapterKnowledgePointLinkResultVO,
    KnowledgeNodeChapterDetailVO,
)
from graphedu.common.resource import AioS3Client, AsyncPostgresqlClient
from graphedu.common.resource.deps import get_db, get_db_client, get_s3
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.chapter import ChapterService

chapter_controller = APIRouter(prefix="/education/chapter", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 章节列表查询
# ============================================================================
@chapter_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:list"))],
    response_model=ResponseType[PageResponse[ChapterListVO]],
)
async def get_chapter_list(
    query: ChapterQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取章节列表（分页）"""
    chapter_page_result: PageResponse[ChapterListVO] = await ChapterService.list_chapter(query_db, query)
    return ResponseUtil.success(data=chapter_page_result)


# ============================================================================
# 章节新增
# ============================================================================
@chapter_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:add"))],
    response_model=ResponseType[ChapterDetailVO],
)
@SystemLog(
    title="章节管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def add_chapter(
    chapter_data: ChapterCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增章节"""
    result_vo = await ChapterService.add_chapter(query_db, chapter_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 章节修改
# ============================================================================
@chapter_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[ChapterDetailVO],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_chapter(
    chapter_data: ChapterUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改章节"""
    result_vo = await ChapterService.update_chapter(query_db, chapter_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 章节删除
# ============================================================================
@chapter_controller.delete(
    "/{chapter_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.DELETE)
async def delete_chapter(
    chapter_ids: str = Path(..., pattern="^[0-9,]+$", description="章节ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除章节（支持批量删除，返回详细结果）"""
    chapter_id_list = [int(cid) for cid in chapter_ids.split(",") if cid]
    result = await ChapterService.delete_chapter(query_db, chapter_id_list, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 修改章节状态
# ============================================================================
@chapter_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.UPDATE)
async def change_chapter_status(
    status_data: ChapterStatusChangeDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改章节状态"""
    await ChapterService.change_chapter_status(query_db, status_data.chapter_id, status_data.status, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取章节详情
# ============================================================================
@chapter_controller.get(
    "/{chapter_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:query"))],
    response_model=ResponseType[ChapterDetailVO],
)
async def get_chapter_detail(
    chapter_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """获取章节详细信息"""
    from graphedu.common.exceptions.services.education.chapter import ChapterNotFoundException

    detail_result = await ChapterService.get_chapter_detail(query_db, chapter_id)
    if detail_result is None:
        raise ChapterNotFoundException(chapter_id=chapter_id)
    return ResponseUtil.success(data=detail_result)


# ============================================================================
# 获取课程章节树
# ============================================================================
@chapter_controller.get(
    "/tree/{course_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:query"))],
    response_model=ResponseType[list[ChapterTreeVO]],
)
async def get_chapter_tree(
    course_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """获取课程的章节树形结构（完整树）"""
    tree_result = await ChapterService.get_chapter_tree(query_db, course_id)
    return ResponseUtil.success(data=tree_result)


@chapter_controller.get(
    "/tree/{course_id}/lazy",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:query"))],
    response_model=ResponseType[list[ChapterTreeVO]],
)
async def get_chapter_tree_lazy(
    course_id: int,
    parent_id: int = Query(alias="parentId", description="父章节ID（默认0表示根节点）"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取课程的章节树形结构（懒加载模式）"""
    tree_result = await ChapterService.get_chapter_tree_lazy(query_db, course_id, parent_id)
    return ResponseUtil.success(data=tree_result)


@chapter_controller.get(
    "/tree/{course_id}/select",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:query"))],
    response_model=ResponseType[list[ChapterTreeBriefVO]],
)
async def get_chapter_tree_for_select(
    course_id: int,
    parent_id: int = Query(alias="parentId", description="父章节ID（默认0，用于兼容）"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取课程的章节树形结构（下拉选择模式，返回简要完整树）"""
    tree_result = await ChapterService.get_chapter_tree_for_select(query_db, course_id, parent_id)
    return ResponseUtil.success(data=tree_result)


# ============================================================================
# 移动章节
# ============================================================================
@chapter_controller.put(
    "/move",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.UPDATE)
async def move_chapter(
    move_data: ChapterMoveDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """移动章节（修改父节点和序号）"""
    await ChapterService.move_chapter(
        query_db, move_data.chapter_id, move_data.new_parent_id, move_data.new_chapter_no, current_user
    )
    return ResponseUtil.success()


# ============================================================================
# 生成章节描述（GraphRAG Local Search 驱动）
# ============================================================================
@chapter_controller.post(
    "/{chapter_id}/generate-description",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[ChapterDescriptionResultVO],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.OTHER)
async def generate_chapter_description(
    chapter_id: int,
    generate_data: ChapterDescriptionGenerateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """直接调用 GraphRAG Local Search 自动生成章节描述

    同步调用并等待 GraphRAG local search 返回描述文本，
    成功后返回 {description, chapter_id}。
    """
    result = await ChapterService.submit_generate_description(
        query_db, chapter_id, generate_data.graphrag_task_id, current_user
    )
    return ResponseUtil.success(data=result)


# ============================================================================
# 知识点关联管理（嵌套路由）
# ============================================================================


@chapter_controller.get(
    "/{chapter_id}/knowledge-points",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:query"))],
    response_model=ResponseType[list[KnowledgeNodeChapterDetailVO]],
)
async def get_chapter_knowledge_points(
    chapter_id: int,
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """获取章节关联的知识点列表"""
    result = await ChapterService.get_knowledge_points(chapter_id, query_db, pg_client)
    return ResponseUtil.success(data=result)


@chapter_controller.post(
    "/{chapter_id}/knowledge-points/link",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[ChapterKnowledgePointLinkResultVO],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.OTHER)
async def link_chapter_knowledge_points(
    chapter_id: int,
    point_ids: list[str] = Body(..., embed=True, description="知识点节点ID列表"),
    query_db: AsyncSession = Depends(get_db)
):
    """批量关联知识点到章节"""
    result = await ChapterService.link_knowledge_points(chapter_id, point_ids, query_db)
    return ResponseUtil.success(data=result)


@chapter_controller.delete(
    "/{chapter_id}/knowledge-points/{point_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.DELETE)
async def unlink_chapter_knowledge_point(
    chapter_id: int,
    point_id: str = Path(..., description="知识点节点ID"),
    query_db: AsyncSession = Depends(get_db)
):
    """解除章节与知识点的关联"""
    await ChapterService.unlink_knowledge_point(chapter_id, point_id, query_db)
    return ResponseUtil.success()


# ============================================================================
# 章节资源管理（嵌套路由）
# ============================================================================


@chapter_controller.get(
    "/{chapter_id}/resources",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:query"))],
    response_model=ResponseType[list[ChapterResourceListVO]],
)
async def get_chapter_resources(
    chapter_id: int,
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取章节的资源列表"""
    resources = await ChapterService.get_resources(query_db, chapter_id, s3_client, include_hidden=True)
    return ResponseUtil.success(data=resources)


@chapter_controller.post(
    "/{chapter_id}/resources",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[ChapterResourceDetailVO],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.INSERT)
async def add_chapter_resource(
    chapter_id: int,
    resource_data: ChapterResourceCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """为章节添加资源"""
    # 确保资源关联到正确的章节
    resource_data.chapter_id = chapter_id
    result_vo = await ChapterService.add_resource(query_db, resource_data, current_user, s3_client)
    return ResponseUtil.success(data=result_vo)


@chapter_controller.put(
    "/{chapter_id}/resources/{resource_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[ChapterResourceDetailVO],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.UPDATE)
async def update_chapter_resource(
    chapter_id: int,
    resource_id: int,
    resource_data: ChapterResourceUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """更新章节资源"""
    # 确保资源 ID 匹配
    resource_data.resource_id = resource_id
    result_vo = await ChapterService.update_resource(query_db, resource_data, current_user, s3_client)
    return ResponseUtil.success(data=result_vo)


@chapter_controller.delete(
    "/{chapter_id}/resources",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:remove"))],
    response_model=ResponseType[ChapterResourceBatchDeleteResultVO],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.DELETE)
async def delete_chapter_resources(
    chapter_id: int,
    delete_data: ChapterResourceBatchDeleteDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除章节资源（支持批量删除）"""
    resource_id_list = [int(rid) for rid in delete_data.resource_ids.split(",") if rid]
    result = await ChapterService.delete_resources(query_db, resource_id_list, current_user)
    return ResponseUtil.success(data=result)


@chapter_controller.put(
    "/{chapter_id}/resources/reorder",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.UPDATE)
async def reorder_chapter_resources(
    chapter_id: int,
    reorder_data: ChapterResourceReorderDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """调整章节资源顺序"""
    await ChapterService.reorder_resources(query_db, chapter_id, reorder_data.resource_orders, current_user)
    return ResponseUtil.success()


@chapter_controller.put(
    "/{chapter_id}/resources/{resource_id}/status",
    dependencies=[Depends(CheckUserInterfacePermit("education:chapter:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="章节管理", business_type=SysConst.BusinessType.UPDATE)
async def change_chapter_resource_status(
    chapter_id: int,
    resource_id: int,
    status_data: ChapterResourceStatusChangeDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改资源状态"""
    await ChapterService.change_resource_status(query_db, resource_id, status_data.status, current_user)
    return ResponseUtil.success()
