"""学生选课 API 控制器

本模块提供学生选课相关的 REST API 接口，包括学生选课的增删改查、
学习进度管理等功能。

主要接口：
- 选课列表：分页查询学生的选课列表
- 学生自主操作：选课、退课、更新学习进度
- 管理员操作：派发课程、批量派发、撤销课程
"""

from datetime import datetime

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.course import (
    StudentCourseCreateDTO,
    StudentCourseQueryDTO,
    StudentCourseUpdateDTO,
)
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.course import StudentCourseDetailVO, StudentCourseListVO
from graphedu.common.models.vo.educationv2.stats import (
    StudentChapterProgressVO,
    StudentCourseOverviewVO,
    StudentKnowledgeProfileVO,
    StudentWeakPointVO,
)
from graphedu.common.resource import AioS3Client
from graphedu.common.resource.deps import get_db, get_s3
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.student_course import StudentCourseService

student_course_controller = APIRouter(
    prefix="/education/student/course", dependencies=[Depends(SecurityService.get_current_user)]
)


# ============================================================================
# 查询接口（学生自主查询）
# ============================================================================


@student_course_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:course:list"))],
    response_model=ResponseType[PageResponse[StudentCourseListVO]],
)
async def get_my_course_list(
    query: StudentCourseQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取我的选课列表（分页）

    默认查询当前登录学生的选课列表，支持按课程ID、选课时间等条件筛选。
    """
    # 如果未指定 student_id，使用当前登录用户的学生ID
    if query.student_id is None:
        query.student_id = current_user.detail.student_info.student_id

    course_page_result: PageResponse[StudentCourseListVO] = await StudentCourseService.get_student_course_list(
        query_db, query, s3_client
    )
    return ResponseUtil.success(data=course_page_result)


@student_course_controller.get(
    "/{enrollment_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:course:query"))],
    response_model=ResponseType[StudentCourseDetailVO],
)
async def get_enrollment_detail(
    enrollment_id: int,
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取选课详细信息"""
    from graphedu.common.exceptions.services.education.student_course import StudentCourseNotFoundException

    detail_result = await StudentCourseService.get_enrollment_detail(query_db, enrollment_id, s3_client)
    if detail_result is None:
        raise StudentCourseNotFoundException(enrollment_id=enrollment_id)
    return ResponseUtil.success(data=detail_result)


@student_course_controller.get(
    "/{courseId}/overview",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[StudentCourseOverviewVO],
)
async def get_student_course_overview(
    course_id: int = Path(..., gt=0, alias="courseId"),
    week_start: datetime | None = Query(None, alias="weekStart", description="周一起始日期（YYYY-MM-DD），默认本周"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生课程学习概览（含统计和趋势数据）

    返回学生指定课程的学习概览信息，包括：
    - 学习进度（百分比）
    - 已完成章节数 / 总章节数
    - 累计学习时长
    - 最后学习时间
    - 排名（如：Top 5%）
    - 课程整体数据（总学生数、平均进度、今日活跃）
    - 指定周的学习活跃度趋势（补齐7天）
    """
    overview = await StudentCourseService.get_course_overview(
        query_db, current_user.detail.student_info.student_id, course_id, week_start=week_start
    )
    return ResponseUtil.success(data=overview)


@student_course_controller.get(
    "/{courseId}/chapter-progress",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[list[StudentChapterProgressVO]],
)
async def get_student_chapter_progress(
    course_id: int = Path(..., gt=0, alias="courseId"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生在课程下的章节+资源学习进度

    返回每个章节的完成进度及该章节下每个资源的阅读进度：
    - 章节名称、序号、完成度
    - 总资料数、已完成资料数
    - 每个资料的名称、类型、完成度、阅读次数、累计时长
    """
    result = await StudentCourseService.get_chapter_progress(
        query_db, current_user.detail.student_info.student_id, course_id
    )
    return ResponseUtil.success(data=result)


@student_course_controller.get(
    "/{courseId}/knowledge-profile",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[list[StudentKnowledgeProfileVO]],
)
async def get_knowledge_profile(
    course_id: int = Path(..., gt=0, alias="courseId"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生知识点掌握度画像"""
    result = await StudentCourseService.get_knowledge_profile(
        query_db, current_user.detail.student_info.student_id, course_id
    )
    return ResponseUtil.success(data=result)


@student_course_controller.get(
    "/{courseId}/weak-points",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[list[StudentWeakPointVO]],
)
async def get_weak_points(
    course_id: int = Path(..., gt=0, alias="courseId"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取学生薄弱知识点"""
    result = await StudentCourseService.get_weak_points(
        query_db, current_user.detail.student_info.student_id, course_id
    )
    return ResponseUtil.success(data=result)


# ============================================================================
# 学生自主操作接口
# ============================================================================


@student_course_controller.post(
    "/join",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[StudentCourseDetailVO],
)
@SystemLog(title="学生选课", business_type=SysConst.BusinessType.OTHER, exclude_params={"current_user"})
async def join_course(
    course_data: StudentCourseCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """学生自主选课

    学生可以选择公开且状态正常的课程。
    系统会自动检查：
    - 课程是否存在且可用（公开且状态正常）
    - 学生是否已选过该课程

    成功选课后会自动更新课程和学生表的课程计数。
    """
    result_vo = await StudentCourseService.join_course(
        query_db, current_user.detail.student_info.student_id, course_data.course_id, current_user, s3_client
    )
    return ResponseUtil.success(data=result_vo)


@student_course_controller.delete(
    "/leave/{course_id}",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[Empty],
)
@SystemLog(title="学生选课", business_type=SysConst.BusinessType.DELETE)
async def leave_course(
    course_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """学生退出课程

    学生可以主动退出已选的课程。
    系统会自动检查选课记录是否存在，并更新课程和学生表的课程计数。
    """
    await StudentCourseService.leave_course(query_db, current_user.detail.student_info.student_id, course_id)
    return ResponseUtil.success()


@student_course_controller.put(
    "/progress",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[Empty],
)
@SystemLog(title="学生选课", business_type=SysConst.BusinessType.UPDATE)
async def update_learning_progress(
    update_data: StudentCourseUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """更新学习进度

    学生可以更新自己的课程学习进度（0-100）。
    系统会自动更新选课记录的进度和最后学习时间。
    """
    await StudentCourseService.update_learning_progress(
        query_db, current_user.detail.student_info.student_id, update_data
    )
    return ResponseUtil.success()


# ============================================================================
# 管理员操作接口
# ============================================================================


@student_course_controller.post(
    "/assign",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:course:assign"))],
    response_model=ResponseType[StudentCourseDetailVO],
)
@SystemLog(
    title="学生选课管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def assign_course_to_student(
    student_id: int = Body(..., embed=True, description="学生ID"),
    course_id: int = Body(..., embed=True, description="课程ID"),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """派发课程给学生（管理员操作）

    管理员可以为学生派发指定课程，无需学生主动选择。
    系统会自动检查：
    - 学生是否存在
    - 课程是否可用
    - 是否已派发过

    成功派发后会自动更新课程和学生表的课程计数。
    """
    result_vo = await StudentCourseService.assign_course_to_student(
        query_db, student_id, course_id, current_user, s3_client
    )
    return ResponseUtil.success(data=result_vo)


@student_course_controller.post(
    "/batch-assign",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:course:assign"))],
    response_model=ResponseType[dict],
)
@SystemLog(
    title="学生选课管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def batch_assign_courses(
    student_ids: list[int] = Body(..., description="学生ID列表"),
    course_id: int = Body(..., embed=True, description="课程ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """批量派发课程（管理员操作，部分成功模式）

    管理员可以批量为多个学生派发同一课程。
    采用部分成功模式：即使部分学生派发失败，也会继续处理其他学生。

    返回结果包含：
    - success_count: 成功派发的数量
    - fail_count: 失败的数量
    - results: 每个学生的派发结果详情
    """
    result = await StudentCourseService.batch_assign_courses(query_db, student_ids, course_id, current_user)
    return ResponseUtil.success(data=result)


@student_course_controller.delete(
    "/revoke/{enrollment_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:course:revoke"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="学生选课管理", business_type=SysConst.BusinessType.DELETE)
async def revoke_course_from_student(
    enrollment_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """撤销学生的课程（管理员操作）

    管理员可以撤销学生的选课记录。
    系统会自动检查选课记录是否存在，并更新课程和学生表的课程计数。
    """
    await StudentCourseService.revoke_course_from_student(query_db, enrollment_id, current_user)
    return ResponseUtil.success()
