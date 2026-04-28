"""知识点向量嵌入 Mapper 模块。

提供基于 pgvector 的知识点向量相似度检索和 embedding 写入功能。
"""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduKnowledgePointEmbedding

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 1024


class KnowledgePointEmbeddingMapper:
    """知识点向量嵌入数据访问层。"""

    @staticmethod
    async def search_by_embedding(
        course_id: int,
        query_embedding: list[float],
        top_k: int = 10,
        distance_threshold: float = 0.5,
        db_session: AsyncSession | None = None,
    ) -> list[EduKnowledgePointEmbedding]:
        """通过向量相似度检索知识点。

        :param course_id: 课程 ID
        :param query_embedding: 查询向量
        :param top_k: 返回数量上限
        :param distance_threshold: cosine 距离阈值
        :param db_session: 数据库会话
        :return: 按相似度排序的知识点嵌入列表
        """
        if not query_embedding or len(query_embedding) != _EMBEDDING_DIM:
            logger.warning(
                "Invalid embedding dimension: expected %d, got %s",
                _EMBEDDING_DIM,
                len(query_embedding) if query_embedding else 0,
            )
            return []

        distance = EduKnowledgePointEmbedding.embedding.cosine_distance(query_embedding)
        stmt = (
            select(EduKnowledgePointEmbedding)
            .where(
                EduKnowledgePointEmbedding.course_id == course_id,
                distance < distance_threshold,
            )
            .order_by(distance.asc())
            .limit(top_k)
        )
        result = await db_session.execute(stmt)
        return list(result.scalars())

    @staticmethod
    async def upsert_embedding(
        node_uuid: UUID,
        course_id: int,
        title: str,
        embedding: list[float],
        db_session: AsyncSession | None = None,
    ) -> None:
        """插入或更新知识点 embedding（按 node_uuid 去重）。

        :param node_uuid: 知识点业务 UUID
        :param course_id: 课程 ID
        :param title: 知识点标题
        :param embedding: 向量嵌入
        :param db_session: 数据库会话
        """
        stmt = insert(EduKnowledgePointEmbedding)
        stmt = stmt.on_conflict_do_update(
            index_elements=["node_uuid"],
            set_={
                "title": title,
                "embedding": embedding,
            },
        )
        await db_session.execute(
            stmt,
            {"node_uuid": node_uuid, "course_id": course_id, "title": title, "embedding": embedding},
        )
        await db_session.flush()

    @staticmethod
    async def get_existing_node_uuids(
        course_id: int,
        db_session: AsyncSession | None = None,
    ) -> set[UUID]:
        """获取指定课程中已有 embedding 的知识点 UUID 集合。

        :param course_id: 课程 ID
        :param db_session: 数据库会话
        :return: 已有 embedding 的 node_uuid 集合
        """
        stmt = select(EduKnowledgePointEmbedding.node_uuid).where(EduKnowledgePointEmbedding.course_id == course_id)
        result = await db_session.execute(stmt)
        return {row[0] for row in result.all()}

    @staticmethod
    async def delete_by_node_uuid(node_uuid: UUID, db_session: AsyncSession) -> None:
        """删除指定知识点的 embedding 记录。

        :param node_uuid: 知识点业务 UUID
        :param db_session: 数据库会话
        """
        stmt = delete(EduKnowledgePointEmbedding).where(EduKnowledgePointEmbedding.node_uuid == node_uuid)
        await db_session.execute(stmt)
        await db_session.flush()

    @staticmethod
    async def delete_by_course_id(course_id: int, db_session: AsyncSession) -> None:
        """删除指定课程的所有知识点 embedding 记录。

        :param course_id: 课程 ID
        :param db_session: 数据库会话
        """
        stmt = delete(EduKnowledgePointEmbedding).where(EduKnowledgePointEmbedding.course_id == course_id)
        await db_session.execute(stmt)
        await db_session.flush()
