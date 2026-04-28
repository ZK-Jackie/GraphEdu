"""学习事件上报服务模块

提供学生端通用事件上报功能。
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.educationv2.event import LearningEventCreateDTO
from graphedu.mapper.education.learning_event import LearningEventMapper

logger = logging.getLogger(__name__)


class LearningEventService:
    """学习事件上报服务"""

    @staticmethod
    async def report_event(
        query_db: AsyncSession,
        dto: LearningEventCreateDTO,
    ) -> int:
        """上报学习事件

        Args:
            query_db: 数据库会话。
            dto: 事件上报 DTO。

        Returns:
            int: 创建的事件ID。
        """
        dto.event_source = "ui"
        event = await LearningEventMapper.create_event(
            dto,
            db_session=query_db,
        )
        return event.event_id
