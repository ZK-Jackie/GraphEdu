"""聊天会话 Mapper 层

负责聊天会话数据的访问操作，包括会话的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.educationv2.chat import ChatSessionQueryDTO
from graphedu.common.models.orm.education import EduChatSession
from graphedu.common.utils.uuids import uuid7_str


class ChatSessionMapper:
    """聊天会话数据访问层

    提供聊天会话的 CRUD 操作。
    """

    @staticmethod
    async def create_session(
        user_id: int, course_id: int | None, title: str, db_session: AsyncSession
    ) -> EduChatSession:
        """创建聊天会话

        :param user_id: 用户ID
        :param course_id: 课程ID（可为None，表示全局聊天）
        :param title: 会话标题
        :param db_session: 数据库会话
        :return: 会话 ORM 对象
        """
        new_session = EduChatSession(
            session_uuid=uuid7_str(),
            user_id=user_id,
            course_id=course_id,
            title=title,
            message_count=0,
            status="0",  # 0=正常
            last_message_time=datetime.now(),
        )
        db_session.add(new_session)
        await db_session.flush()
        return new_session

    @staticmethod
    async def get_by_conv_id_and_user(conv_id: int, user_id: int, db_session: AsyncSession) -> EduChatSession | None:
        """根据对话ID和用户ID查询会话

        :param conv_id: 对话ID
        :param user_id: 用户ID
        :param db_session: 数据库会话
        :return: 会话 ORM 对象
        """
        stmt = select(EduChatSession).where(
            and_(
                EduChatSession.session_id == conv_id,
                EduChatSession.user_id == user_id,
                EduChatSession.status == "0",  # 只查询正常状态
            )
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_conv_id(conv_id: int, db_session: AsyncSession) -> EduChatSession | None:
        """根据对话ID查询会话（不验证用户）

        :param conv_id: 对话ID
        :param db_session: 数据库会话
        :return: 会话 ORM 对象
        """
        stmt = select(EduChatSession).where(
            and_(
                EduChatSession.session_id == conv_id,
                EduChatSession.status == "0",  # 只查询正常状态
            )
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def list_sessions(
        db: AsyncSession, query_object: ChatSessionQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[EduChatSession], int]:
        """查询会话列表（按最后消息时间倒序）

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (sessions, total) 元组，sessions为会话列表，total为总数
        """
        # 构建基础查询条件
        base_conditions = []

        if query_object.user_id:
            base_conditions.append(EduChatSession.user_id == query_object.user_id)
        if query_object.course_id:
            base_conditions.append(EduChatSession.course_id == query_object.course_id)
        if query_object.status:
            base_conditions.append(EduChatSession.status == query_object.status)
        else:
            # 默认只查询正常状态
            base_conditions.append(EduChatSession.status == "0")

        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduChatSession.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建主查询
        query = select(EduChatSession).where(and_(*base_conditions)).order_by(EduChatSession.last_message_time.desc())

        # 获取总数
        count_query = select(func.count()).select_from(EduChatSession).where(and_(*base_conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        sessions = result.scalars().all()

        return sessions, total

    @staticmethod
    async def update_title(session_orm: EduChatSession, new_title: str, db_session: AsyncSession) -> None:
        """更新会话标题

        :param session_orm: 会话 ORM 对象
        :param new_title: 新标题
        :param db_session: 数据库会话
        :return: None
        """
        session_orm.title = new_title
        await db_session.merge(session_orm)
        await db_session.flush()

    @staticmethod
    async def increment_message_count(conv_id: int, db_session: AsyncSession) -> None:
        """增加会话消息计数并更新最后消息时间

        :param conv_id: 对话ID
        :param db_session: 数据库会话
        :return: None
        """
        stmt = (
            update(EduChatSession)
            .where(EduChatSession.session_id == conv_id)
            .values(
                message_count=EduChatSession.message_count + 1,
                last_message_time=datetime.now(),
            )
        )
        await db_session.execute(stmt)
        await db_session.flush()

    @staticmethod
    async def delete_session(conv_id: int, user_id: int, db_session: AsyncSession) -> None:
        """逻辑删除会话（更新状态为"2"已删除）

        :param conv_id: 对话ID
        :param user_id: 用户ID
        :param db_session: 数据库会话
        :return: None
        """
        stmt = (
            update(EduChatSession)
            .where(
                and_(
                    EduChatSession.session_id == conv_id,
                    EduChatSession.user_id == user_id,
                )
            )
            .values(status="2")  # 2=已删除
        )
        await db_session.execute(stmt)
        await db_session.flush()

    @staticmethod
    async def update_session(
        conv_id: int,
        user_id: int,
        title: str | None,
        db_session: AsyncSession,
    ) -> None:
        """更新会话信息（标题）

        :param conv_id: 对话ID
        :param user_id: 用户ID
        :param title: 会话标题
        :param db_session: 数据库会话
        :return: None
        """
        update_values = {}
        if title is not None:
            update_values["title"] = title

        if update_values:
            stmt = (
                update(EduChatSession)
                .where(
                    and_(
                        EduChatSession.session_id == conv_id,
                        EduChatSession.user_id == user_id,
                    )
                )
                .values(**update_values)
            )
            await db_session.execute(stmt)
            await db_session.flush()
