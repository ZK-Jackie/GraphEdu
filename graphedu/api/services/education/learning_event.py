"""学习事件上报 API 控制器

提供学生端通用事件上报接口。

主要接口：
- POST /education/learning-event  上报学习事件
"""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.event import LearningEventCreateDTO
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.resource.deps import get_db
from graphedu.security.auth import SecurityService
from graphedu.services.education.learning_event import LearningEventService

learning_event_controller = APIRouter(
    prefix="/education/learning-event", dependencies=[Depends(SecurityService.get_current_user)]
)


# ============================================================================
# 上报学习事件
# ============================================================================
@learning_event_controller.post(
    "",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[dict],
)
async def report_learning_event(
    data: LearningEventCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """上报学习事件

    学生端通用事件上报，支持以下事件类型：
    - chapter_open: 打开章节
    - interest: 标记感兴趣
    - explain_request: 请求解释
    - map_click: 知识图谱点击
    - tool_map_query: 工具查询
    """
    data.student_id = current_user.detail.student_info.student_id
    event_id = await LearningEventService.report_event(query_db, data)
    return ResponseUtil.success(data={"eventId": event_id})
