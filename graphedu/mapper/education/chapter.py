"""课程章节管理 Mapper 层

负责课程章节数据的访问操作，包括章节信息的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.chapter import ChapterQueryDTO
from graphedu.common.models.orm.education import EduChapter


class ChapterMapper:
    """章节数据访问层

    提供章节信息的 CRUD 操作。
    """

    @staticmethod
    async def add_chapter(chapter_info: EduChapter, db_session: AsyncSession) -> EduChapter:
        """添加章节

        :param db_session: 数据库会话
        :param chapter_info: 章节信息
        :return: 章节对象
        """
        db_session.add(chapter_info)
        await db_session.flush()
        return chapter_info

    @staticmethod
    async def get_by_id(chapter_id: int, db_session: AsyncSession) -> EduChapter | None:
        """根据章节ID查询章节信息

        :param db_session: 数据库会话
        :param chapter_id: 章节ID
        :return: 章节对象
        """
        stmt = select(EduChapter).where(
            EduChapter.chapter_id == chapter_id, EduChapter.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_chapter_list(
        db: AsyncSession, query_object: ChapterQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[EduChapter], int]:
        """根据查询参数获取章节列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组
        """
        # 构建基础查询条件
        base_conditions = [EduChapter.status != SystemConstants.Status.DELETED]

        if query_object.chapter_id is not None:
            base_conditions.append(EduChapter.chapter_id == query_object.chapter_id)
        if query_object.course_id is not None:
            base_conditions.append(EduChapter.course_id == query_object.course_id)
        if query_object.parent_id is not None:
            base_conditions.append(EduChapter.parent_id == query_object.parent_id)
        if query_object.chapter_name:
            base_conditions.append(EduChapter.chapter_name.like(f"%{query_object.chapter_name}%"))
        if query_object.status:
            base_conditions.append(EduChapter.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduChapter.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建查询
        query = select(EduChapter).where(and_(*base_conditions)).order_by(EduChapter.course_id, EduChapter.chapter_no)

        # 获取总数
        count_query = select(func.count()).select_from(EduChapter).where(and_(*base_conditions))
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
    async def get_chapters_by_course_id(course_id: int, db_session: AsyncSession) -> list[EduChapter]:
        """根据课程ID获取所有章节列表

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 章节列表
        """
        stmt = (
            select(EduChapter)
            .where(and_(EduChapter.course_id == course_id, EduChapter.status != SystemConstants.Status.DELETED))
            .order_by(EduChapter.chapter_no)
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_chapter_tree(course_id: int, db_session: AsyncSession) -> list[EduChapter]:
        """根据课程ID获取章节树形结构

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 章节列表（树形结构）
        """
        stmt = (
            select(EduChapter)
            .where(and_(EduChapter.course_id == course_id, EduChapter.status != SystemConstants.Status.DELETED))
            .order_by(EduChapter.chapter_no)
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(chapter_info: EduChapter, query_db: AsyncSession) -> None:
        """更新章节信息

        :param query_db: 数据库会话
        :param chapter_info: 章节信息
        :return: None
        """
        await query_db.merge(chapter_info)
        await query_db.flush()

    @staticmethod
    async def delete_chapter(chapter_id: int, query_db: AsyncSession) -> None:
        """根据章节ID软删除章节

        :param query_db: 数据库会话
        :param chapter_id: 章节ID
        :return: None
        """
        chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if chapter:
            chapter.status = SystemConstants.Status.DELETED
            await ChapterMapper.update(chapter, query_db)

    @staticmethod
    async def get_chapter_children(course_id: int, parent_id: int, db_session: AsyncSession) -> list[EduChapter]:
        """获取指定课程和父章节ID的直接子节点

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :param parent_id: 父章节ID
        :return: 子章节列表
        """
        stmt = (
            select(EduChapter)
            .where(
                and_(
                    EduChapter.course_id == course_id,
                    EduChapter.parent_id == parent_id,
                    EduChapter.status != SystemConstants.Status.DELETED,
                )
            )
            .order_by(EduChapter.chapter_no)
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def has_children(chapter_id: int, db_session: AsyncSession) -> bool:
        """检查章节是否有子章节

        :param db_session: 数据库会话
        :param chapter_id: 章节ID
        :return: 是否有子章节
        """
        stmt = (
            select(func.count())
            .select_from(EduChapter)
            .where(and_(EduChapter.parent_id == chapter_id, EduChapter.status != SystemConstants.Status.DELETED))
        )
        result = await db_session.execute(stmt)
        count = result.scalar() or 0
        return count > 0
