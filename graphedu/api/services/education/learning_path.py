"""学习路径管理 API 控制器

本模块提供学习路径的 REST API 接口，支持查询、详情查看、删除和状态更新。

主要接口：
- GET  /education/learning-path/my               — 查询我的学习路径列表
- GET  /education/learning-path/{plan_id}         — 查看路径详情（含子图 + 进度）
- DELETE /education/learning-path/{plan_id}        — 删除路径
- PUT  /education/learning-path/{plan_id}/status   — 更新路径状态

设计约束（三层职能）：
- Controller（本文件）：仅负责接收参数、调用 Service 方法、返回响应
- Service：业务逻辑
- Mapper：纯 AGE 图数据库查询
"""

from fastapi import APIRouter, Body, Depends, Path, Query

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.learning_path import LearningPathStatusUpdateDTO
from graphedu.common.models.vo.base import Empty, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.learning_path import (
    LearningPathProgressDetailVO,
    LearningPlanDetailVO,
    LearningPlanListVO,
    LearningPlanProgressVO,
)
from graphedu.common.resource.deps import get_db_client
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient
from graphedu.mapper.education.syllabus_graph import SyllabusGraphMapper
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.learning_path import LearningPathService

learning_path_controller = APIRouter(
    prefix="/education/learning-path",
    dependencies=[Depends(SecurityService.get_current_user)],
)


# ============================================================================
# 查询我的学习路径列表
# ============================================================================


@learning_path_controller.get(
    "/my",
    dependencies=[Depends(CheckUserInterfacePermit("education:learningPath:list"))],
    response_model=ResponseType[list[LearningPlanListVO]],
)
async def get_my_learning_paths(
    course_id: int = Query(..., description="课程ID"),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """查询当前学生的学习路径列表。"""
    plans = await LearningPathService.get_student_plans(
        pg_client=pg_client,
        student_id=current_user.detail.user.user_id,
        course_id=course_id,
    )

    vo_list = [
        LearningPlanListVO(
            plan_id=p.plan_id,
            course_id=p.course_id,
            title=p.title,
            status=p.status,
            create_time=p.create_time,
        )
        for p in plans
    ]
    return ResponseUtil.success(data=vo_list)


# ============================================================================
# 查看学习路径详情（含子图 + 进度）
# ============================================================================


@learning_path_controller.get(
    "/{plan_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:learningPath:query"))],
    response_model=ResponseType[LearningPlanDetailVO],
)
async def get_learning_path_detail(
    plan_id: str = Path(..., description="学习计划 UUID"),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """查看学习路径详情，包含知识点子图和学习进度。"""
    # 1. 获取计划详情（子图）
    plan_record, nodes, relationships = await LearningPathService.get_plan_detail(
        pg_client=pg_client,
        plan_uuid=plan_id,
    )

    if not plan_record:
        return ResponseUtil.fail(msg="学习计划不存在")

    # 2. 获取学习进度
    progress = await LearningPathService.get_plan_progress(
        pg_client=pg_client,
        plan_uuid=plan_id,
        student_id=current_user.detail.user.user_id,
        course_id=plan_record.course_id,
    )

    # 3. 组装子图 VO（复用已有的 build_nvl_graph_data）
    graph_vo = None
    if nodes:
        graph_vo = SyllabusGraphMapper.build_nvl_graph_data(nodes, relationships)

    # 4. 组装进度 VO
    progress_vo = LearningPlanProgressVO(
        total=progress.total,
        mastered=progress.mastered,
        progress_pct=progress.progress_pct,
        details=[
            LearningPathProgressDetailVO(
                node_uuid=d.node_uuid,
                mastery_level=d.mastery_level,
                mastery_score=d.mastery_score,
                mastered=d.mastered,
            )
            for d in progress.details
        ],
    )

    # 5. 组装详情 VO
    plan_vo = LearningPlanListVO(
        plan_id=plan_record.plan_id,
        course_id=plan_record.course_id,
        title=plan_record.title,
        status=plan_record.status,
        create_time=plan_record.create_time,
    )

    detail_vo = LearningPlanDetailVO(
        plan=plan_vo,
        graph=graph_vo,
        progress=progress_vo,
    )
    return ResponseUtil.success(data=detail_vo)


# ============================================================================
# 删除学习路径
# ============================================================================


@learning_path_controller.delete(
    "/{plan_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:learningPath:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="删除学习路径",
    business_type=SysConst.BusinessType.DELETE,
    exclude_params={"current_user", "pg_client"},
)
async def delete_learning_path(
    plan_id: str = Path(..., description="学习计划 UUID"),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除学习路径（包括 AGE 图中的 LearningPlan 节点和 PLAN_STEP 关系）。"""
    await LearningPathService.delete_plan(pg_client=pg_client, plan_uuid=plan_id)
    return ResponseUtil.success()


# ============================================================================
# 更新学习路径状态
# ============================================================================


@learning_path_controller.put(
    "/{plan_id}/status",
    dependencies=[Depends(CheckUserInterfacePermit("education:learningPath:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="更新学习路径状态",
    business_type=SysConst.BusinessType.UPDATE,
    exclude_params={"current_user", "pg_client"},
)
async def update_learning_path_status(
    plan_id: str = Path(..., description="学习计划 UUID"),
    data: LearningPathStatusUpdateDTO = Body(),
    pg_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """更新学习路径状态（active/completed/archived）。"""
    success = await LearningPathService.update_plan_status(
        pg_client=pg_client,
        plan_uuid=plan_id,
        status=data.status,
    )
    if not success:
        return ResponseUtil.fail(msg="学习计划不存在或更新失败")
    return ResponseUtil.success()
