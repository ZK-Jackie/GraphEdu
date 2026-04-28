"""聊天会话服务模块

该模块提供聊天会话的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑（会话管理、消息发送）。
3. 调用 ChatAgent 实现流式响应。
4. 将 ORM 对象转换为 VO 返回。
"""

from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.chat_session import (
    ChatAgentNotInitializedException,
    ChatSessionNotFoundException,
)
from graphedu.common.models.bo.agent import InvokableConfig, InvokableValues
from graphedu.common.models.dto.educationv2.agent import (
    ChatMessage,
    ChatSseResponse,
    RoleEnum,
)
from graphedu.common.models.dto.educationv2.chat import ChatSessionQueryDTO
from graphedu.common.models.orm.education import EduChatSession
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.educationv2.chat import ChatSessionDetailVO, ChatSessionListVO
from graphedu.common.resource import AsyncPostgresqlClient
from graphedu.common.utils.uuids import uuid7_str
from graphedu.mapper.education.chat_session import ChatSessionMapper
from graphedu.services.agent.chat_agent import ChatAgent

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_session_orm_to_list_vo(session_orm: EduChatSession) -> ChatSessionListVO:
    """将会话 ORM 对象转换为 ChatSessionListVO。

    Args:
        session_orm: 会话 ORM 对象。

    Returns:
        ChatSessionListVO: 会话列表项 VO。
    """
    return ChatSessionListVO(
        conv_id=session_orm.session_id,
        user_id=session_orm.user_id,
        course_id=session_orm.course_id,
        title=session_orm.title,
        message_count=session_orm.message_count,
        status=session_orm.status,
        create_time=session_orm.create_time,
        last_message_time=session_orm.last_message_time,
        course_name=None,  # 如果需要课程名称，需要额外查询
    )


def _convert_session_orm_to_detail_vo(session_orm: EduChatSession) -> ChatSessionDetailVO:
    """将会话 ORM 对象转换为 ChatSessionDetailVO。

    Args:
        session_orm: 会话 ORM 对象。

    Returns:
        ChatSessionDetailVO: 会话详细信息 VO。
    """
    return ChatSessionDetailVO(
        conv_id=session_orm.session_id,
        user_id=session_orm.user_id,
        course_id=session_orm.course_id,
        title=session_orm.title,
        context_summary=session_orm.context_summary,
        message_count=session_orm.message_count,
        status=session_orm.status,
        create_by=session_orm.create_by,
        create_time=session_orm.create_time,
        update_by=session_orm.update_by,
        update_time=session_orm.update_time,
        last_message_time=session_orm.last_message_time,
        course=None,  # 如果需要课程信息，需要额外查询
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_session_exists(conv_id: int, user_id: int, query_db: AsyncSession) -> EduChatSession:
    """检查会话是否存在且属于该用户。

    Args:
        conv_id: 对话ID。
        user_id: 用户ID。
        query_db: 数据库会话。

    Returns:
        EduChatSession: 会话对象。

    Raises:
        ChatSessionNotFoundException: 会话不存在。
    """
    session = await ChatSessionMapper.get_by_conv_id_and_user(conv_id, user_id, query_db)
    if not session:
        raise ChatSessionNotFoundException
    return session


# ============================================================================
# ChatSessionService 类
# ============================================================================


class ChatSessionService:
    """聊天会话服务类

    提供聊天会话的增删改查和消息发送功能。
    """

    @staticmethod
    async def create_session(
        query_db: AsyncSession,
        user_id: int,
        course_id: int | None,
        title: str | None,
    ) -> ChatSessionDetailVO:
        """创建新的聊天会话。

        Args:
            query_db: 数据库会话。
            user_id: 用户ID。
            course_id: 课程ID（可选）。
            title: 会话标题（可选）。

        Returns:
            ChatSessionDetailVO: 创建成功的会话 VO。
        """
        # 默认标题
        if not title:
            title = "新对话"

        # 创建会话
        session_orm = await ChatSessionMapper.create_session(
            user_id=user_id,
            course_id=course_id,
            title=title,
            db_session=query_db,
        )

        logger.info(f"创建聊天会话成功: user_id={user_id}, conv_id={session_orm.session_id}, course_id={course_id}")

        return _convert_session_orm_to_detail_vo(session_orm)

    @staticmethod
    async def get_session_list(
        query_db: AsyncSession,
        query_object: ChatSessionQueryDTO,
    ) -> PageResponse[ChatSessionListVO]:
        """查询会话列表。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[ChatSessionListVO]: 分页结果。
        """
        sessions, total = await ChatSessionMapper.list_sessions(query_db, query_object, is_page=True)

        # 将 ORM 对象转换为 ChatSessionListVO
        session_list = [_convert_session_orm_to_list_vo(session) for session in sessions]

        return PageResponse(
            rows=session_list,
            page=query_object.page,
            size=query_object.size,
            total=total,
        )

    @staticmethod
    async def get_session_detail(
        query_db: AsyncSession,
        conv_id: int,
        user_id: int,
    ) -> ChatSessionDetailVO:
        """获取会话详情。

        Args:
            query_db: 数据库会话。
            conv_id: 对话ID。
            user_id: 用户ID。

        Returns:
            ChatSessionDetailVO: 会话详细信息 VO。

        Raises:
            ChatSessionNotFoundException: 会话不存在。
        """
        session_orm = await _check_session_exists(conv_id, user_id, query_db)
        return _convert_session_orm_to_detail_vo(session_orm)

    @staticmethod
    async def update_session_title(
        query_db: AsyncSession,
        conv_id: int,
        user_id: int,
        new_title: str,
    ) -> None:
        """更新会话标题。

        Args:
            query_db: 数据库会话。
            conv_id: 对话ID。
            user_id: 用户ID。
            new_title: 新标题。

        Raises:
            ChatSessionNotFoundException: 会话不存在。
        """
        session_orm = await _check_session_exists(conv_id, user_id, query_db)
        await ChatSessionMapper.update_title(session_orm, new_title, query_db)
        logger.info(f"更新会话标题成功: conv_id={conv_id}, new_title={new_title}")

    @staticmethod
    async def delete_session(
        query_db: AsyncSession,
        conv_id: int,
        user_id: int,
    ) -> None:
        """删除会话（逻辑删除）。

        Args:
            query_db: 数据库会话。
            conv_id: 对话ID。
            user_id: 用户ID。

        Raises:
            ChatSessionNotFoundException: 会话不存在。
        """
        # 先检查会话是否存在
        await _check_session_exists(conv_id, user_id, query_db)

        # 执行删除
        await ChatSessionMapper.delete_session(conv_id, user_id, query_db)
        logger.info(f"删除会话成功: conv_id={conv_id}, user_id={user_id}")

    @staticmethod
    async def get_message_history(
        query_db: AsyncSession,
        conv_id: int,
        user_id: int,
        chat_agent: ChatAgent,
    ) -> list[ChatMessage]:
        """获取会话的消息历史。

        Args:
            query_db: 数据库会话。
            conv_id: 对话ID。
            user_id: 用户ID。
            chat_agent: ChatAgent 实例。

        Returns:
            list[ChatMessage]: 消息历史列表。

        Raises:
            ChatSessionNotFoundException: 会话不存在。
            ChatAgentNotInitializedException: Agent 未初始化。
        """
        # 验证会话存在
        await _check_session_exists(conv_id, user_id, query_db)

        # 检查 Agent 是否已初始化
        if not chat_agent.is_initialized():
            raise ChatAgentNotInitializedException

        # 从 LangGraph Checkpointer 获取消息历史
        config = InvokableConfig(
            thread_id=ChatMessage.build_chat_uid(user_id, conv_id),
            user_id=user_id,
            conv_id=conv_id,
        )
        messages = await chat_agent.async_get_history(config)

        logger.info(f"获取消息历史成功: conv_id={conv_id}, message_count={len(messages)}")

        return messages

    @staticmethod
    async def send_message_stream(
        db_client: AsyncPostgresqlClient,
        user_id: int,
        chat_message: ChatMessage,
        chat_agent: ChatAgent,
    ) -> AsyncGenerator[ChatSseResponse]:
        """发送消息并流式响应。

        注意：本方法使用独立的短事务进行数据库操作，避免在 LLM 流式响应期间长时间持有事务。

        Args:
            db_client: PostgreSQL 数据库客户端（用于创建短事务）。
            user_id: 用户ID。
            chat_message: 用户发送的 ChatMessage。
            chat_agent: ChatAgent 实例。

        Yields:
            ChatSseResponse: SSE 事件对象，格式：{"type": "message|thought_chain|tool|end|error", "data": ...}

        Raises:
            ChatSessionNotFoundException: 会话不存在。
            ChatAgentNotInitializedException: Agent 未初始化。
        """
        conv_id = chat_message.conv_id

        try:
            # 1. 短事务：验证会话存在
            async with db_client.session_context() as query_db:
                session = await _check_session_exists(conv_id, user_id, query_db)
                course_id = session.course_id

            # 2. 检查 Agent 是否已初始化
            if not chat_agent.is_initialized():
                raise ChatAgentNotInitializedException

            # 3. 准备用户消息
            user_message = chat_message.model_copy(update={"user_id": user_id, "message_id": uuid7_str()}, deep=True)

            if not user_message.contents:
                raise ValueError("消息内容不能为空")

            # 4. 准备 Agent 配置
            config = InvokableConfig(
                thread_id=user_message.chat_uid,
                user_id=user_id,
                conv_id=conv_id,
                course_id=course_id,
            )

            # 5. 准备输入值
            values = InvokableValues(new_message=user_message)

            # 6. 流式调用 Agent（不持有数据库事务）
            async for msg in chat_agent.async_stream(values, config):
                if msg.role == RoleEnum.AI:
                    # AI 消息
                    yield ChatSseResponse(type="message", data=msg.model_dump(by_alias=False))

                elif msg.role == RoleEnum.THINKING:
                    # 思维链消息
                    yield ChatSseResponse(type="thought_chain", data=msg.model_dump(by_alias=False))

                elif msg.role == RoleEnum.TOOL:
                    # 工具消息
                    yield ChatSseResponse(type="tool", data=msg.model_dump(by_alias=False))

            # 7. 短事务：更新会话消息计数
            async with db_client.session_context() as query_db:
                await ChatSessionMapper.increment_message_count(conv_id, query_db)

            # 8. 发送结束事件
            yield ChatSseResponse(type="end", data={"conv_id": conv_id})

            logger.info(f"发送消息成功: conv_id={conv_id}, user_id={user_id}")

        except Exception as e:
            logger.error(f"发送消息失败: conv_id={conv_id}, error={e}")
            yield ChatSseResponse(type="error", data={"message": str(e)})
            return
