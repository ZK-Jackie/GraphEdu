"""学生资料阅读进度 API 控制器

本模块提供资料进度相关的 REST API 接口：
- 学生端：进度上报、断点续学
"""

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.event import ResourceProgressReportDTO
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.student_learning_event import StudentResourceProgressDetailVO
from graphedu.common.resource.deps import get_db
from graphedu.security.auth import SecurityService
from graphedu.services.education.resource_progress import ResourceProgressService

# ============================================================================
# 路由器
# ============================================================================

resource_progress_controller = APIRouter(
    prefix="/education/resource-progress",
    dependencies=[Depends(SecurityService.get_current_user)],
)


# ============================================================================
# 学生端：进度上报
# ============================================================================


@resource_progress_controller.post(
    "",
    response_model=ResponseType[StudentResourceProgressDetailVO],
)
async def report_progress(
    report_data: ResourceProgressReportDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """学生端上报资料阅读进度（定时/关闭时调用）

    前端每 30 秒或页面失焦/关闭时调用此接口上报增量进度。
    后端自动从 JWT 获取 student_id，从资料表获取 chapter_id、course_id。
    """
    result = await ResourceProgressService.report_progress(query_db, report_data, current_user.detail.user.user_id)
    return ResponseUtil.success(data=result)


# ============================================================================
# 学生端：单资料进度详情（断点续学）
# ============================================================================


@resource_progress_controller.get(
    "/{resource_id}",
    response_model=ResponseType[StudentResourceProgressDetailVO],
)
async def get_resource_progress_detail(
    resource_id: int = Path(..., description="资料ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """查询单个资料的进度详情（用于断点续学恢复位置）"""
    result = await ResourceProgressService.get_resource_progress_detail(
        query_db,
        student_id=current_user.detail.user.user_id,
        resource_id=resource_id,
    )
    if result is None:
        return ResponseUtil.success(data=None, msg="暂无进度记录")
    return ResponseUtil.success(data=result)
