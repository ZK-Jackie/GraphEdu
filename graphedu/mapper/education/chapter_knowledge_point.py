"""章节-知识点关联 Mapper 层

负责章节与知识图谱节点（EduKnowledgeNode）的多对多关联关系。
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduKnowledgeNodeChapter


class ChapterKnowledgePointMapper:
    """章节-知识点关联数据访问层"""

    @staticmethod
    async def add_link(chapter_id: int, node_uuid: UUID, db: AsyncSession) -> EduKnowledgeNodeChapter:
        """添加关联

        :param chapter_id: 章节ID
        :param node_uuid: 知识点业务UUID
        :param db: 数据库会话
        :return: 关联对象
        """
        link = EduKnowledgeNodeChapter(chapter_id=chapter_id, node_uuid=node_uuid)
        db.add(link)
        await db.flush()
        return link

    @staticmethod
    async def get_by_chapter(chapter_id: int, db: AsyncSession) -> Sequence[EduKnowledgeNodeChapter]:
        """查询章节关联的所有知识点

        :param chapter_id: 章节ID
        :param db: 数据库会话
        :return: 关联列表
        """
        stmt = select(EduKnowledgeNodeChapter).where(
            EduKnowledgeNodeChapter.chapter_id == chapter_id,
            EduKnowledgeNodeChapter.status == "0",  # 仅查询正常状态
        )
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def get_by_chapter_and_point(
        chapter_id: int, node_uuid: UUID, db: AsyncSession
    ) -> EduKnowledgeNodeChapter | None:
        """查询特定关联是否存在

        :param chapter_id: 章节ID
        :param node_uuid: 知识点业务UUID
        :param db: 数据库会话
        :return: 关联对象或 None
        """
        stmt = select(EduKnowledgeNodeChapter).where(
            EduKnowledgeNodeChapter.chapter_id == chapter_id,
            EduKnowledgeNodeChapter.node_uuid == node_uuid,
        )
        return (await db.execute(stmt)).scalars().first()

    @staticmethod
    async def delete_link(chapter_id: int, node_uuid: UUID, db: AsyncSession) -> int:
        """删除特定关联

        :param chapter_id: 章节ID
        :param node_uuid: 知识点业务UUID
        :param db: 数据库会话
        :return: 删除行数
        """
        stmt = delete(EduKnowledgeNodeChapter).where(
            EduKnowledgeNodeChapter.chapter_id == chapter_id,
            EduKnowledgeNodeChapter.node_uuid == node_uuid,
        )
        result = await db.execute(stmt)
        return result.rowcount

    @staticmethod
    async def delete_all_by_chapter(chapter_id: int, db: AsyncSession) -> int:
        """删除章节的所有知识点关联

        :param chapter_id: 章节ID
        :param db: 数据库会话
        :return: 删除行数
        """
        stmt = delete(EduKnowledgeNodeChapter).where(EduKnowledgeNodeChapter.chapter_id == chapter_id)
        result = await db.execute(stmt)
        return result.rowcount
