"""GraphRAG 任务管理 API 控制器

本模块提供 GraphRAG 任务管理相关的 REST API 接口，包括任务的增删改查等功能。

主要接口：
- 任务列表：分页查询任务列表，支持多条件筛选
- 任务管理：新增、修改、删除任务
- 任务详情：查询任务详细信息
- 课程任务：查询指定课程的所有任务
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.graphrag_task import (
    GraphRAGBuildCreateDTO,
    GraphRAGResourceQueryDTO,
    GraphRAGTaskCreateDTO,
    GraphRAGTaskQueryDTO,
    GraphRAGTaskUpdateDTO,
)
from graphedu.common.models.vo.base import BatchDeleteResponse, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.chapter_resource import ChapterResourceListVO
from graphedu.common.models.vo.educationv2.graphrag_task import (
    GraphRAGBuildProgressVO,
    GraphRAGTaskDetailVO,
    GraphRAGTaskListVO,
)
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.graphrag_task import GraphRAGTaskService

graphrag_task_controller = APIRouter(
    prefix="/education/graphrag-task",
    dependencies=[Depends(SecurityService.get_current_user)],
)


# ============================================================================
# 任务列表查询
# ============================================================================


@graphrag_task_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:list"))],
    response_model=ResponseType[PageResponse[GraphRAGTaskListVO]],
)
async def get_graphrag_task_list(
    query: GraphRAGTaskQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取 GraphRAG 任务列表（分页）"""
    task_page_result: PageResponse[GraphRAGTaskListVO] = await GraphRAGTaskService.list_task(query_db, query)
    return ResponseUtil.success(data=task_page_result)


# ============================================================================
# 构建资源与构建任务
# ============================================================================


@graphrag_task_controller.get(
    "/build/resources",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:list"))],
    response_model=ResponseType[PageResponse[ChapterResourceListVO]],
)
async def get_buildable_resources(
    query: GraphRAGResourceQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取可构建 GraphRAG 的资源列表（仅已文本化资源）。"""
    result = await GraphRAGTaskService.get_buildable_resources(query_db, query)
    return ResponseUtil.success(data=result)


@graphrag_task_controller.post(
    "/build/submit",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:add"))],
    response_model=ResponseType[GraphRAGTaskDetailVO],
)
@SystemLog(
    title="GraphRAG 任务管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user", "query_db"},
)
async def submit_build_task(
    build_data: GraphRAGBuildCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """提交 GraphRAG 构建任务。"""
    result_vo = await GraphRAGTaskService.submit_build_task(query_db, build_data, current_user)
    return ResponseUtil.success(data=result_vo)


@graphrag_task_controller.get(
    "/build/progress/{task_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:query"))],
    response_model=ResponseType[GraphRAGBuildProgressVO],
)
async def get_build_progress(
    task_id: int = Path(description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取 GraphRAG 构建进度。"""
    progress_vo = await GraphRAGTaskService.get_build_progress(task_id, query_db)
    return ResponseUtil.success(data=progress_vo)


@graphrag_task_controller.delete(
    "/build/cancel/{task_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:remove"))],
    response_model=ResponseType,
)
@SystemLog(
    title="GraphRAG 任务管理",
    business_type=SysConst.BusinessType.DELETE,
    exclude_params={"current_user", "query_db"},
)
async def cancel_build_task(
    task_id: int = Path(description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """取消 GraphRAG 构建任务。"""
    await GraphRAGTaskService.cancel_build_task(task_id, query_db, current_user)
    return ResponseUtil.success(msg="任务取消成功")


# ============================================================================
# 重试任务
# ============================================================================


@graphrag_task_controller.post(
    "/build/retry/{task_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:add"))],
    response_model=ResponseType[GraphRAGTaskDetailVO],
)
@SystemLog(
    title="GraphRAG 任务管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user", "query_db"},
)
async def retry_build_task(
    task_id: int = Path(description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """重试失败的 GraphRAG 构建任务。"""
    result_vo = await GraphRAGTaskService.retry_build_task(query_db, task_id, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 启用任务
# ============================================================================


@graphrag_task_controller.put(
    "/{task_id}/enable",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:edit"))],
    response_model=ResponseType[GraphRAGTaskDetailVO],
)
@SystemLog(
    title="GraphRAG 任务管理",
    business_type=SysConst.BusinessType.UPDATE,
    exclude_params={"current_user", "query_db"},
)
async def enable_graphrag_task(
    task_id: int = Path(description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """启用 GraphRAG 任务（同一课程仅允许启用一个）。"""
    result_vo = await GraphRAGTaskService.enable_task(query_db, task_id, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 任务详情
# ============================================================================


@graphrag_task_controller.get(
    "/{task_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:query"))],
    response_model=ResponseType[GraphRAGTaskDetailVO],
)
async def get_graphrag_task_detail(
    task_id: int = Path(description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取 GraphRAG 任务详情"""
    task_vo = await GraphRAGTaskService.get_task_detail(query_db, task_id)
    return ResponseUtil.success(data=task_vo)


# ============================================================================
# 课程任务列表
# ============================================================================


@graphrag_task_controller.get(
    "/course/{course_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:list"))],
    response_model=ResponseType[list[GraphRAGTaskListVO]],
)
async def get_tasks_by_course(
    course_id: int = Path(description="课程ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取指定课程的所有 GraphRAG 任务（不分页）"""
    task_list = await GraphRAGTaskService.list_by_course_id(query_db, course_id)
    return ResponseUtil.success(data=task_list)


# ============================================================================
# 任务新增
# ============================================================================


@graphrag_task_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:add"))],
    response_model=ResponseType[GraphRAGTaskDetailVO],
)
@SystemLog(
    title="GraphRAG 任务管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def add_graphrag_task(
    task_data: GraphRAGTaskCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增 GraphRAG 任务"""
    result_vo = await GraphRAGTaskService.add_task(query_db, task_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 任务修改
# ============================================================================


@graphrag_task_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:edit"))],
    response_model=ResponseType[GraphRAGTaskDetailVO],
)
@SystemLog(title="GraphRAG 任务管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_graphrag_task(
    task_data: GraphRAGTaskUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改 GraphRAG 任务"""
    result_vo = await GraphRAGTaskService.update_task(query_db, task_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 任务删除
# ============================================================================


@graphrag_task_controller.delete(
    "/{task_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:graphrag-task:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="GraphRAG 任务管理", business_type=SysConst.BusinessType.DELETE)
async def delete_graphrag_task(
    task_ids: str = Path(description="任务ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
):
    """删除 GraphRAG 任务"""
    result = await GraphRAGTaskService.delete_tasks(query_db, task_ids)
    return ResponseUtil.success(data=result)
