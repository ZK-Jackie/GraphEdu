"""首页仪表盘 API 控制器

根据用户角色（学生/教师）返回个性化首页数据。

学生端：
- GET /student/summary       → 总览统计
- GET /student/calendar      → 学习日历热力图数据
- GET /student/trend         → 学习趋势
- GET /student/courses       → 最近学习课程
- GET /student/weak-points   → 跨课程薄弱知识点

教师端：
- GET /teacher/summary       → 总览统计
- GET /teacher/courses       → 各课程概览
- GET /teacher/rankings      → 学生排名
- GET /teacher/trend         → 互动趋势
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.stats import (
    DailyActiveItemVO,
    DashboardCalendarItemVO,
    DashboardCourseItemVO,
    DashboardWeakPointVO,
    StudentDailyActiveItemVO,
    StudentDashboardSummaryVO,
    TeacherDashboardCourseVO,
    TeacherDashboardRankingVO,
    TeacherDashboardSummaryVO,
)
from graphedu.common.resource.deps import get_db, get_s3
from graphedu.common.resource.modules.database.oss import AioS3Client
from graphedu.security.auth import SecurityService
from graphedu.services.education.dashboard import DashboardService

dashboard_controller = APIRouter(
    prefix="/education/dashboard",
    dependencies=[Depends(SecurityService.get_current_user)],
)


# ============================================================================
# 学生端接口
# ============================================================================


@dashboard_controller.get(
    "/student/summary",
    response_model=ResponseType[StudentDashboardSummaryVO],
)
async def get_student_summary(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生仪表盘总览统计

    返回累计学习天数、总学习时长、在修课程数、连续学习天数。
    """
    student_id = current_user.detail.student_info.student_id
    result = await DashboardService.get_student_summary(query_db, student_id)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/student/calendar",
    response_model=ResponseType[list[DashboardCalendarItemVO]],
)
async def get_student_calendar(
    year: int = Query(default=None, ge=2020, le=2099, description="查询年份，默认当前年"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生学习日历热力图数据

    返回指定年份每日学习时长（分钟），用于日历热力图渲染。
    """
    if year is None:
        year = date.today().year
    student_id = current_user.detail.student_info.student_id
    result = await DashboardService.get_student_calendar(query_db, student_id, year)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/student/trend",
    response_model=ResponseType[list[StudentDailyActiveItemVO]],
)
async def get_student_trend(
    start_date: str = Query(..., alias="startDate", description="起始日期，格式 YYYY-MM-DD"),
    end_date: str = Query(..., alias="endDate", description="结束日期，格式 YYYY-MM-DD"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生学习趋势数据

    返回指定日期范围内每日学习活跃分钟数。
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    student_id = current_user.detail.student_info.student_id
    result = await DashboardService.get_student_trend(query_db, student_id, start, end)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/student/courses",
    response_model=ResponseType[list[DashboardCourseItemVO]],
)
async def get_student_recent_courses(
    limit: int = Query(default=6, ge=1, le=20, description="返回数量"),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生最近学习的课程

    按最后学习时间倒序，返回课程卡片数据（含封面 URL）。
    """
    student_id = current_user.detail.student_info.student_id
    result = await DashboardService.get_student_recent_courses(query_db, student_id, limit, s3_client)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/student/weak-points",
    response_model=ResponseType[list[DashboardWeakPointVO]],
)
async def get_student_weak_points(
    limit: int = Query(default=5, ge=1, le=20, description="返回数量"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生跨课程薄弱知识点

    按投入产出比倒序返回，展示需要重点复习的知识点。
    """
    student_id = current_user.detail.student_info.student_id
    result = await DashboardService.get_student_weak_points(query_db, student_id, limit)
    return ResponseUtil.success(data=result)


# ============================================================================
# 教师端接口
# ============================================================================


@dashboard_controller.get(
    "/teacher/summary",
    response_model=ResponseType[TeacherDashboardSummaryVO],
)
async def get_teacher_summary(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取教师仪表盘总览统计

    返回课程总数、总学生数、今日活跃学生数、平均掌握度。
    """
    result = await DashboardService.get_teacher_summary(query_db, current_user)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/teacher/courses",
    response_model=ResponseType[list[TeacherDashboardCourseVO]],
)
async def get_teacher_courses(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取教师各课程概览

    返回每门课程的学生数、平均进度、答题正确率。
    """
    result = await DashboardService.get_teacher_courses(query_db, current_user)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/teacher/rankings",
    response_model=ResponseType[list[TeacherDashboardRankingVO]],
)
async def get_teacher_rankings(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取教师跨课程学生排名

    按掌握度百分位降序返回 Top N 学生。
    """
    result = await DashboardService.get_teacher_rankings(query_db, current_user, limit)
    return ResponseUtil.success(data=result)


@dashboard_controller.get(
    "/teacher/trend",
    response_model=ResponseType[list[DailyActiveItemVO]],
)
async def get_teacher_trend(
    days: int = Query(default=30, ge=7, le=90, description="查询天数"),
    start_date: str = Query(default=None, alias="startDate", description="起始日期，格式 YYYY-MM-DD"),
    end_date: str = Query(default=None, alias="endDate", description="结束日期，格式 YYYY-MM-DD"),
    course_id: int = Query(default=None, alias="courseId", description="课程ID，不传则查全部课程"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取教师课程互动趋势数据

    支持两种查询模式：
    1. 按 days 天数回溯（默认 30 天）
    2. 按 startDate / endDate 日期范围查询（优先于 days）

    可选 courseId 参数，指定则只查该课程的趋势数据。
    """
    parsed_start = None
    parsed_end = None
    if start_date and end_date:
        parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    result = await DashboardService.get_teacher_trend(
        query_db, current_user, days, parsed_start, parsed_end, course_id
    )
    return ResponseUtil.success(data=result)
