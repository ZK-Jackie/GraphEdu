"""知识图谱管理 API 控制器

本模块提供知识图谱管理相关的 REST API 接口，包括知识图谱的增删改查、
状态管理以及 Phase 4 图谱操作（提取、保存、节点/关系 CRUD）。

设计约束（三层职能）：
- Controller（本文件）：仅负责接收参数、调用单一 Service 方法、返回响应
- Service：业务逻辑、BO/VO 转换、AGE+SQL 编排
- Mapper：纯数据库查询
"""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto import (
    KnowledgeExtractionRequestDTO,
    KnowledgeGraphCreateDTO,
    KnowledgeGraphQueryDTO,
    KnowledgeGraphUpdateDTO,
    KnowledgePointCreateDTO,
    KnowledgePointUpdateDTO,
    KnowledgeRelationshipCreateDTO,
    KnowledgeRelationshipUpdateDTO,
    SaveExtractionRequestDTO,
)
from graphedu.common.models.dto.educationv2.knowledge_graph import AutoGenerateRequestDTO, NodeNeighborsQueryDTO
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.knowledge_graph import (
    AutoGenerateSubmitVO,
    GraphRelationshipCreatedVO,
    GraphRelationshipDetailVO,
    KnowledgeExtractionResultVO,
    KnowledgeGraphDetailVO,
    KnowledgeGraphListVO,
    KnowledgePointVO,
    NodeNeighborsVO,
    NvlGraphDataVO,
    TopNodesVO,
)
from graphedu.common.resource import AioS3Client
from graphedu.common.resource.deps import get_db, get_db_client, get_s3
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.knowledge_graph import KnowledgeGraphService

knowledge_graph_controller = APIRouter(
    prefix="/education/knowledge-graph", dependencies=[Depends(SecurityService.get_current_user)]
)


# ============================================================================
# 知识图谱列表查询
# ============================================================================
@knowledge_graph_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:list"))],
    response_model=ResponseType[PageResponse[KnowledgeGraphListVO]],
)
async def get_knowledge_graph_list(
    query: KnowledgeGraphQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取知识图谱列表（分页）"""
    result = await KnowledgeGraphService.list_knowledge_graph(query_db, query)
    return ResponseUtil.success(data=result)


# ============================================================================
# 学生可访问的知识图谱列表（强制只返回已启用且非草稿的图谱）
# ============================================================================


@knowledge_graph_controller.get(
    "/list-visible",
    response_model=ResponseType[PageResponse[KnowledgeGraphListVO]],
)
async def get_visible_knowledge_graph_list(
    course_id: int = Query(..., description="课程ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取学生可见的知识图谱列表（仅返回已启用且非草稿的图谱）

    该接口仅要求登录，无需管理权限。强制过滤 status='0' 且 is_draft='N'，
    确保学生无法查看到草稿或未启用的知识图谱。
    """
    query = KnowledgeGraphQueryDTO(
        course_id=course_id,
        status="0",
        is_draft="N",
        page=1,
        size=100,
    )
    result = await KnowledgeGraphService.list_knowledge_graph(query_db, query)
    return ResponseUtil.success(data=result)


# ============================================================================
# 知识图谱新增
# ============================================================================
@knowledge_graph_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:add"))],
    response_model=ResponseType[KnowledgeGraphDetailVO],
)
@SystemLog(
    title="知识图谱管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def add_knowledge_graph(
    graph_data: KnowledgeGraphCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增知识图谱"""
    result = await KnowledgeGraphService.add_knowledge_graph(query_db, graph_data, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 知识图谱修改
# ============================================================================
@knowledge_graph_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[KnowledgeGraphDetailVO],
)
@SystemLog(title="知识图谱管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_knowledge_graph(
    graph_data: KnowledgeGraphUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改知识图谱"""
    result = await KnowledgeGraphService.update_knowledge_graph(query_db, graph_data, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 知识图谱删除
# ============================================================================
@knowledge_graph_controller.delete(
    "/{graph_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="知识图谱管理", business_type=SysConst.BusinessType.DELETE)
async def delete_knowledge_graph(
    graph_ids: str = Path(..., pattern="^[0-9,]+$", description="知识图谱ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除知识图谱（支持批量删除）"""
    graph_id_list = [int(gid) for gid in graph_ids.split(",") if gid]
    await KnowledgeGraphService.delete_knowledge_graph(query_db, graph_id_list, current_user)
    return ResponseUtil.success()


# ============================================================================
# 修改知识图谱状态
# ============================================================================
@knowledge_graph_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="知识图谱管理", business_type=SysConst.BusinessType.UPDATE)
async def change_knowledge_graph_status(
    graph_id: int = Body(..., embed=True, description="知识图谱ID"),
    status: str = Body(..., embed=True, description="状态"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改知识图谱状态"""
    await KnowledgeGraphService.change_knowledge_graph_status(query_db, graph_id, status, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取知识图谱详情
# ============================================================================
@knowledge_graph_controller.get(
    "/{graph_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:query"))],
    response_model=ResponseType[KnowledgeGraphDetailVO],
)
async def get_knowledge_graph_detail(
    graph_id: int = Path(..., description="知识图谱ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取知识图谱详细信息"""
    result = await KnowledgeGraphService.get_knowledge_graph_detail(query_db, graph_id)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：知识点提取（LLM）
# ============================================================================
@knowledge_graph_controller.post(
    "/{graph_id}/extract",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:extract"))],
    response_model=ResponseType[KnowledgeExtractionResultVO],
)
async def extract_knowledge_points(
    graph_id: int = Path(..., description="知识图谱ID"),
    extract_req: KnowledgeExtractionRequestDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """使用 LLM 从文档/提纲提取知识点草稿（未入库，需确认后保存）。

    支持三种模式：markdown（解析文档）、skeleton（教师提纲）、combined（合并）。
    """
    result = await KnowledgeGraphService.extract_knowledge_points(graph_id, extract_req, query_db, s3_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：保存审核后的提取结果到 AGE
# ============================================================================
@knowledge_graph_controller.post(
    "/{graph_id}/save-extraction",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:extract"))],
    response_model=ResponseType[NvlGraphDataVO],
)
async def save_extraction(
    graph_id: int = Path(..., description="知识图谱ID"),
    save_req: SaveExtractionRequestDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """将教师审核确认后的知识点和关系批量写入图数据库，并更新图谱统计数据。"""
    result = await KnowledgeGraphService.save_extraction(graph_id, save_req, query_db, pg_client, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：获取图谱 NVL 可视化数据
# ============================================================================
@knowledge_graph_controller.get(
    "/{graph_id}/nvl-data",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:query"))],
    response_model=ResponseType[NvlGraphDataVO],
)
async def get_nvl_data(
    graph_id: int = Path(..., description="知识图谱ID"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """获取图谱 NVL 可视化格式数据（节点 + 关系）。"""
    result = await KnowledgeGraphService.get_graph_nvl_data(graph_id, query_db, pg_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：节点搜索
# ============================================================================
@knowledge_graph_controller.get(
    "/{graph_id}/nodes/search",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:query"))],
    response_model=ResponseType[list[KnowledgePointVO]],
)
async def search_graph_nodes(
    graph_id: int = Path(..., description="知识图谱ID"),
    keyword: str = Query(..., description="搜索关键词"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """按关键词搜索图谱中的知识点节点（标题模糊匹配）。"""
    result = await KnowledgeGraphService.search_graph_nodes(graph_id, keyword, query_db, pg_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：手动创建知识点节点
# ============================================================================
@knowledge_graph_controller.post(
    "/{graph_id}/nodes",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[KnowledgePointVO],
)
async def create_graph_node(
    graph_id: int = Path(..., description="知识图谱ID"),
    node_data: KnowledgePointCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """手动创建知识点节点。"""
    result = await KnowledgeGraphService.create_graph_node(graph_id, node_data, query_db, pg_client, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：更新知识点节点
# ============================================================================
@knowledge_graph_controller.put(
    "/{graph_id}/nodes/{node_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[Empty],
)
async def update_graph_node(
    graph_id: int = Path(..., description="知识图谱ID"),
    node_id: str = Path(..., description="节点ID"),
    node_data: KnowledgePointUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改知识点节点属性。"""
    await KnowledgeGraphService.update_graph_node(graph_id, node_id, node_data, query_db, pg_client, current_user)
    return ResponseUtil.success()


# ============================================================================
# Phase 4：删除知识点节点
# ============================================================================
@knowledge_graph_controller.delete(
    "/{graph_id}/nodes/{node_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[Empty],
)
async def delete_graph_node(
    graph_id: int = Path(..., description="知识图谱ID"),
    node_id: str = Path(..., description="节点ID"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """删除知识点节点（级联删除关系）。"""
    await KnowledgeGraphService.delete_graph_node(graph_id, node_id, query_db, pg_client)
    return ResponseUtil.success()


# ============================================================================
# Phase 4：创建关系
# ============================================================================
@knowledge_graph_controller.post(
    "/{graph_id}/relationships",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[GraphRelationshipCreatedVO],
)
async def create_graph_relationship(
    graph_id: int = Path(..., description="知识图谱ID"),
    rel_data: KnowledgeRelationshipCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """在两个知识点之间创建关系（RELATED_TO / PRIOR_TO / SUBTOPIC_OF）。"""
    result = await KnowledgeGraphService.create_graph_relationship(graph_id, rel_data, query_db, pg_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：更新关系
# ============================================================================
@knowledge_graph_controller.put(
    "/{graph_id}/relationships/{rel_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[GraphRelationshipDetailVO],
)
async def update_graph_relationship(
    graph_id: int = Path(..., description="知识图谱ID"),
    rel_id: str = Path(..., description="关系ID"),
    rel_data: KnowledgeRelationshipUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """更新关系属性（关系类型/描述/置信度），不允许修改起点和终点。"""
    result = await KnowledgeGraphService.update_graph_relationship(graph_id, rel_id, rel_data, query_db, pg_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：查询关系详情
# ============================================================================
@knowledge_graph_controller.get(
    "/{graph_id}/relationships/{rel_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:view"))],
    response_model=ResponseType[GraphRelationshipDetailVO],
)
async def get_graph_relationship(
    graph_id: int = Path(..., description="知识图谱ID"),
    rel_id: str = Path(..., description="关系ID"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """查询图谱关系详情。"""
    result = await KnowledgeGraphService.get_graph_relationship(graph_id, rel_id, query_db, pg_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# Phase 4：删除关系
# ============================================================================
@knowledge_graph_controller.delete(
    "/{graph_id}/relationships/{rel_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:edit"))],
    response_model=ResponseType[Empty],
)
async def delete_graph_relationship(
    graph_id: int = Path(..., description="知识图谱ID"),
    rel_id: str = Path(..., description="关系ID"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """删除图谱关系。"""
    await KnowledgeGraphService.delete_graph_relationship(graph_id, rel_id, query_db, pg_client)
    return ResponseUtil.success()


# ============================================================================
# 获取图谱顶层节点（入度为0的节点）
# ============================================================================
@knowledge_graph_controller.get(
    "/{graph_id}/top-nodes",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:query"))],
    response_model=ResponseType[TopNodesVO],
)
async def get_top_nodes(
    graph_id: int = Path(..., description="知识图谱ID"),
    limit: int = Query(10, ge=1, le=100, description="返回节点数量限制"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """获取知识图谱的顶层节点（入度为0的节点，代表没有前置依赖的知识点）。"""
    result = await KnowledgeGraphService.get_graph_top_nodes(graph_id, query_db, pg_client, limit)
    return ResponseUtil.success(data=result)


# ============================================================================
# 获取节点邻居
# ============================================================================
@knowledge_graph_controller.get(
    "/{graph_id}/nodes/{node_id}/neighbors",
    dependencies=[Depends(CheckUserInterfacePermit("education:knowledgeGraph:query"))],
    response_model=ResponseType[NodeNeighborsVO],
)
async def get_node_neighbors(
    graph_id: int = Path(..., description="知识图谱ID"),
    node_id: str = Path(..., description="节点ID"),
    depth: int = Query(1, ge=1, le=3, description="查询深度（1=直接邻居，2=两跳邻居）"),
    limit: int = Query(20, ge=1, le=100, description="每层返回的节点数量限制"),
    direction: Literal["in", "out", "both"] = Query("both", description="关系方向（in/out/both）"),
    query_db: AsyncSession = Depends(get_db),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
):
    """获取指定节点的邻居节点和关系，支持分层查询。"""
    query_dto = NodeNeighborsQueryDTO(depth=depth, limit=limit, direction=direction)
    result = await KnowledgeGraphService.get_node_neighbors(graph_id, node_id, query_dto, query_db, pg_client)
    return ResponseUtil.success(data=result)


@knowledge_graph_controller.post(
    "/auto-generate/submit",
    response_model=ResponseType[AutoGenerateSubmitVO],
    dependencies=[Depends(SecurityService.get_current_user)],
    summary="提交异步自动生成知识图谱任务",
)
async def submit_auto_generate(
    dto: AutoGenerateRequestDTO,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """提交异步自动生成知识图谱任务，立即返回 graph_id，后续由 Celery Worker 异步完成。"""
    result = await KnowledgeGraphService.submit_auto_generate(dto, query_db, current_user)
    return ResponseUtil.success(data=result)


@knowledge_graph_controller.put(
    "/{graph_id}/confirm",
    response_model=ResponseType[KnowledgeGraphDetailVO],
    dependencies=[Depends(SecurityService.get_current_user)],
    summary="确认知识图谱（草稿转正）",
)
async def confirm_knowledge_graph(
    graph_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """教师审核编辑完成后，将草稿知识图谱标记为已确认。"""
    result = await KnowledgeGraphService.confirm_graph(graph_id, query_db, current_user)
    return ResponseUtil.success(data=result)

