"""Admin 仪表盘 API 控制器

提供管理员首页仪表盘数据接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.admin_dashboard import AdminDashboardSummaryVO
from graphedu.common.resource.deps import get_db
from graphedu.security.auth import SecurityService
from graphedu.services.system.admin_dashboard import AdminDashboardService

admin_dashboard_controller = APIRouter(
    prefix="/system/admin/dashboard",
    dependencies=[Depends(SecurityService.get_current_user)],
)


@admin_dashboard_controller.get(
    "/overview",
    response_model=ResponseType[AdminDashboardSummaryVO],
)
async def get_overview(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取管理员仪表盘总览统计

    返回用户数、学生数、教师数、课程数、知识图谱数、今日登录数。
    """
    result = await AdminDashboardService.get_overview(query_db)
    return ResponseUtil.success(data=result)
