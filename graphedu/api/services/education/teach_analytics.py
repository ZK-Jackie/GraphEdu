"""教师工作台分析 API 控制器

提供教师查看课程学生、数据分析的 REST API 接口。

主要接口：
- GET /education/teach/course/{course_id}/students  课程学生列表及统计
- GET /education/teach/course/{course_id}/analytics 课程数据分析
- GET /education/teach/course/{course_id}/rankings   课程学生排名
- GET /education/teach/course/{course_id}/student/{student_id}/chapter-learning
    学生章节学习汇总
- GET /education/teach/course/{course_id}/student/{student_id}/chapter/{chapter_id}/detail
    学生章节可展开详情
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.course import CourseStudentsResultVO
from graphedu.common.models.vo.educationv2.stats import (
    CourseAnalyticsVO,
    StudentChapterDetailResultVO,
    StudentChapterLearningResultVO,
    StudentRankingItemVO,
)
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.auth import SecurityService
from graphedu.services.education.teach_analytics import TeachAnalyticsService

teach_analytics_controller = APIRouter(
    prefix="/education/teach", dependencies=[Depends(SecurityService.get_current_user)]
)


# ============================================================================
# 课程学生列表
# ============================================================================
@teach_analytics_controller.get(
    "/course/{course_id}/students",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[CourseStudentsResultVO],
)
async def get_course_students(
    course_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取课程学生列表及统计数据"""
    result = await TeachAnalyticsService.get_course_students(query_db, course_id, current_user, page, size)
    return ResponseUtil.success(data=result)


# ============================================================================
# 课程数据分析
# ============================================================================
@teach_analytics_controller.get(
    "/course/{course_id}/analytics",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[CourseAnalyticsVO],
)
async def get_course_analytics(
    course_id: int,
    time_range: Literal["week", "month", "all"] = Query(default="month", description="时间范围"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取课程数据分析"""
    result = await TeachAnalyticsService.get_course_analytics(query_db, course_id, current_user, time_range)
    return ResponseUtil.success(data=result)


# ============================================================================
# 课程学生排名
# ============================================================================
@teach_analytics_controller.get(
    "/course/{course_id}/rankings",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[list[StudentRankingItemVO]],
)
async def get_course_rankings(
    course_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取课程学生排名列表"""
    result = await TeachAnalyticsService.get_course_rankings(query_db, course_id, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 学生章节学习汇总
# ============================================================================
@teach_analytics_controller.get(
    "/course/{course_id}/student/{student_id}/chapter-learning",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[StudentChapterLearningResultVO],
)
async def get_student_chapter_learning(
    course_id: int,
    student_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生在课程中的章节学习汇总数据"""
    result = await TeachAnalyticsService.get_student_chapter_learning(
        query_db, course_id, student_id, current_user
    )
    return ResponseUtil.success(data=result)


# ============================================================================
# 学生章节可展开详情
# ============================================================================
@teach_analytics_controller.get(
    "/course/{course_id}/student/{student_id}/chapter/{chapter_id}/detail",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[StudentChapterDetailResultVO],
)
async def get_student_chapter_detail(
    course_id: int,
    student_id: int,
    chapter_id: int,
    detail_type: Literal["resources", "exercises", "mastery"] = Query(
        ..., description="详情类型（resources/exercises/mastery）"
    ),
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生在某章节的可展开详情（资料阅读/答题记录/知识点掌握）"""
    result = await TeachAnalyticsService.get_student_chapter_detail(
        query_db, course_id, student_id, chapter_id, detail_type, current_user, page, size
    )
    return ResponseUtil.success(data=result)
