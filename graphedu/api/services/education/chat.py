"""聊天 API 控制器

本模块提供聊天相关的 REST API 接口，包括会话管理、消息发送等功能。

主要接口：
- 会话管理：创建、查询、更新、删除会话
- 消息发送：流式发送消息（SSE）
- 消息历史：查询会话的消息历史
"""

import json

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.agent import ChatMessage, ChatSseResponse
from graphedu.common.models.dto.educationv2.chat import (
    ChatSessionCreateDTO,
    ChatSessionQueryDTO,
    ChatSessionUpdateTitleDTO,
)
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.chat import ChatSessionDetailVO, ChatSessionListVO
from graphedu.common.resource import AsyncPostgresqlClient
from graphedu.common.resource.deps import get_db, get_db_client
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.agent.chat_agent import ChatAgent
from graphedu.services.education.chat_session import ChatSessionService

chat_controller = APIRouter(prefix="/education/chat", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 依赖注入：获取 ChatAgent 实例
# ============================================================================


async def get_chat_agent() -> ChatAgent:
    """获取 ChatAgent 实例（从全局单例）"""
    from graphedu.services.agent import get_agent

    return await get_agent()


# ============================================================================
# 会话管理接口
# ============================================================================


@chat_controller.get(
    "/sessions",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:session:list"))],
    response_model=ResponseType[PageResponse[ChatSessionListVO]],
)
async def get_session_list(
    query: ChatSessionQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取会话列表（分页）

    默认查询当前登录用户的会话列表，支持按课程ID、状态等条件筛选。
    """
    # 如果未指定 user_id，使用当前登录用户ID
    if query.user_id is None:
        query.user_id = current_user.detail.user.user_id

    page_result: PageResponse[ChatSessionListVO] = await ChatSessionService.get_session_list(
        query_db,
        query,
    )
    return ResponseUtil.success(data=page_result)


@chat_controller.post(
    "/sessions",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:session:add"))],
    response_model=ResponseType[ChatSessionDetailVO],
)
@SystemLog(
    title="创建聊天会话",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user", "query_db"},
)
async def create_session(
    data: ChatSessionCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """创建新的聊天会话

    支持创建全局聊天（不指定课程）或课程级聊天。
    """
    session_result = await ChatSessionService.create_session(
        query_db,
        user_id=current_user.detail.user.user_id,
        course_id=data.course_id,
        title=data.title,
    )
    return ResponseUtil.success(data=session_result)


@chat_controller.get(
    "/sessions/{conv_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:session:query"))],
    response_model=ResponseType[ChatSessionDetailVO],
)
async def get_session_detail(
    conv_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取会话详情"""
    detail_result = await ChatSessionService.get_session_detail(
        query_db,
        conv_id=conv_id,
        user_id=current_user.detail.user.user_id,
    )
    return ResponseUtil.success(data=detail_result)


@chat_controller.put(
    "/sessions/{conv_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:session:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="更新会话标题",
    business_type=SysConst.BusinessType.UPDATE,
    exclude_params={"current_user", "query_db"},
)
async def update_session_title(
    conv_id: int = Path(..., gt=0),
    data: ChatSessionUpdateTitleDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """更新会话标题"""
    await ChatSessionService.update_session_title(
        query_db,
        conv_id=conv_id,
        user_id=current_user.detail.user.user_id,
        new_title=data.title,
    )
    return ResponseUtil.success()


@chat_controller.delete(
    "/sessions/{conv_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:session:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="删除聊天会话",
    business_type=SysConst.BusinessType.DELETE,
    exclude_params={"current_user", "query_db"},
)
async def delete_session(
    conv_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除会话（逻辑删除）"""
    await ChatSessionService.delete_session(
        query_db,
        conv_id=conv_id,
        user_id=current_user.detail.user.user_id,
    )
    return ResponseUtil.success()


# ============================================================================
# 消息接口
# ============================================================================


@chat_controller.post(
    "/messages/stream",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:message:send"))],
)
async def send_message_stream(
    data: ChatMessage = Body(),
    db_client: AsyncPostgresqlClient = Depends(get_db_client),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    chat_agent: ChatAgent = Depends(get_chat_agent),
):
    """发送消息并流式响应（SSE）

    通过 Server-Sent Events (SSE) 实现流式响应。

    注意：本接口注入 db_client 而非 query_db，避免在流式响应期间
    长时间持有数据库事务导致连接池污染。

    事件格式：
    - {"type": "message", "data": {...}} - AI 消息
    - {"type": "thought_chain", "data": {...}} - 思维链
    - {"type": "tool", "data": {...}} - 工具消息
    - {"type": "end", "data": {"conv_id": 123}} - 结束（返回对话ID）
    - {"type": "error", "data": {"message": "..."}} - 错误
    """

    async def event_generator():
        """SSE 事件生成器"""
        async for event in ChatSessionService.send_message_stream(
            db_client,
            user_id=current_user.detail.user.user_id,
            chat_message=data,
            chat_agent=chat_agent,
        ):
            event: ChatSseResponse
            # 将事件字典转换为 JSON 字符串
            event_data = json.dumps(event, ensure_ascii=False, default=str)
            yield f"data: {event_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


@chat_controller.get(
    "/sessions/{conv_id}/messages",
    dependencies=[Depends(CheckUserInterfacePermit("education:chat:message:query"))],
    response_model=ResponseType[list[ChatMessage]],
)
async def get_message_history(
    conv_id: int = Path(..., gt=0),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    chat_agent: ChatAgent = Depends(get_chat_agent),
):
    """获取会话的消息历史

    从 LangGraph Checkpointer 获取消息历史。
    """
    messages: list[ChatMessage] = await ChatSessionService.get_message_history(
        query_db,
        conv_id=conv_id,
        user_id=current_user.detail.user.user_id,
        chat_agent=chat_agent,
    )

    return ResponseUtil.success(data=messages)
