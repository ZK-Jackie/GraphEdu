"""章节资料管理 Mapper 层

负责章节资料数据的访问操作，包括章节资料的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.chapter_resource import ChapterResourceQueryDTO
from graphedu.common.models.orm.education import EduChapterResource


class ChapterResourceMapper:
    """章节资料数据访问层

    提供章节资料的 CRUD 操作。
    """

    @staticmethod
    async def add_chapter_resource(resource_info: EduChapterResource, db_session: AsyncSession) -> EduChapterResource:
        """添加章节资料

        :param db_session: 数据库会话
        :param resource_info: 章节资料信息
        :return: 章节资料对象
        """
        db_session.add(resource_info)
        await db_session.flush()
        return resource_info

    @staticmethod
    async def get_by_id(resource_id: int, db_session: AsyncSession) -> EduChapterResource | None:
        """根据资料ID查询章节资料信息

        :param db_session: 数据库会话
        :param resource_id: 资料ID
        :return: 章节资料对象
        """
        stmt = select(EduChapterResource).where(
            EduChapterResource.resource_id == resource_id, EduChapterResource.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_resource_list(
        db: AsyncSession, query_object: ChapterResourceQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[EduChapterResource], int]:
        """根据查询参数获取章节资料列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组
        """
        # 构建基础查询条件
        base_conditions = [EduChapterResource.status != SystemConstants.Status.DELETED]

        if query_object.resource_id is not None:
            base_conditions.append(EduChapterResource.resource_id == query_object.resource_id)
        if query_object.chapter_id is not None:
            base_conditions.append(EduChapterResource.chapter_id == query_object.chapter_id)
        if query_object.resource_name:
            base_conditions.append(EduChapterResource.resource_name.like(f"%{query_object.resource_name}%"))
        if query_object.resource_type:
            base_conditions.append(EduChapterResource.resource_type == query_object.resource_type)
        if query_object.is_visible:
            base_conditions.append(EduChapterResource.is_visible == query_object.is_visible)
        if query_object.status:
            base_conditions.append(EduChapterResource.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduChapterResource.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建查询
        query = (
            select(EduChapterResource)
            .where(and_(*base_conditions))
            .order_by(EduChapterResource.chapter_id, EduChapterResource.display_order)
        )

        # 获取总数
        count_query = select(func.count()).select_from(EduChapterResource).where(and_(*base_conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.scalars().all()

        return rows, total

    @staticmethod
    async def get_resources_by_chapter_id(
        chapter_id: int, db_session: AsyncSession, include_hidden: bool = False
    ) -> list[EduChapterResource]:
        """根据章节ID获取资料列表

        :param db_session: 数据库会话
        :param chapter_id: 章节ID
        :param include_hidden: 是否包含隐藏内容（管理员视角为 True，学生视角为 False）
        :return: 资料列表
        """
        conditions = [
            EduChapterResource.chapter_id == chapter_id,
            EduChapterResource.status != SystemConstants.Status.DELETED,
        ]
        if not include_hidden:
            conditions.append(EduChapterResource.is_visible == "Y")

        stmt = select(EduChapterResource).where(and_(*conditions)).order_by(EduChapterResource.display_order)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(resource_info: EduChapterResource, query_db: AsyncSession) -> None:
        """更新章节资料信息

        :param query_db: 数据库会话
        :param resource_info: 章节资料信息
        :return: None
        """
        await query_db.merge(resource_info)
        await query_db.flush()

    @staticmethod
    async def delete_chapter_resource(resource_id: int, query_db: AsyncSession) -> None:
        """根据资料ID软删除章节资料

        :param query_db: 数据库会话
        :param resource_id: 资料ID
        :return: None
        """
        resource = await ChapterResourceMapper.get_by_id(resource_id, query_db)
        if resource:
            resource.status = SystemConstants.Status.DELETED
            await ChapterResourceMapper.update(resource, query_db)
