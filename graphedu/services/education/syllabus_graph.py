"""大纲图谱服务模块

该模块提供知识图谱中知识点和关系的管理功能。

职责：
1. 对 Apache AGE 图数据库中的知识点和关系进行 CRUD 操作
2. 处理业务逻辑和异常
3. 提供图谱查询和可视化数据接口
"""

import asyncio
from dataclasses import dataclass, field
import logging

from langchain_openai import OpenAIEmbeddings

from graphedu.common import get_config
from graphedu.common.exceptions.services.education import (
    KnowledgeNodeCreateFailedException,
    KnowledgeNodeNotFoundException,
    KnowledgeRelationshipCreateFailedException,
)
from graphedu.common.models.orm.knowledge_graph import (
    KnowledgePoint,
    KnowledgePointMutation,
    KnowledgePointRecord,
    KnowledgeRelationshipPayload,
    KnowledgeRelationshipRecord,
    normalize_relationship_name,
)
from graphedu.common.models.vo.educationv2.knowledge_graph import NvlGraphDataVO
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient
from graphedu.common.utils.uuids import uuid7_str
from graphedu.mapper.education.syllabus_graph import SyllabusGraphMapper
from graphedu.services.education.dependency_inference import KnowledgeRelationshipBO
from graphedu.services.education.knowledge_extraction import KnowledgePointBO

logger = logging.getLogger(__name__)


@dataclass
class SaveGraphResult:
    """图谱保存结果 BO"""

    node_count: int
    """创建的知识点节点数量"""

    rel_count: int
    """创建的关系数量"""

    title_to_uuid: dict[str, str] = field(default_factory=dict)
    """知识点标题 → 业务 UUID 映射"""


# ============================================================================
# SyllabusGraphService 类
# ============================================================================


class SyllabusGraphService:
    """大纲图谱服务类

    提供知识点节点和关系的 CRUD 操作，以及图谱的整体读取接口。
    """

    _embedding_llm: OpenAIEmbeddings | None = None

    # ========================================================================
    # 图谱初始化
    # ========================================================================

    @staticmethod
    async def ensure_graph_exists(pg_client: AsyncPostgresqlClient) -> None:
        """确保 AGE 图已创建（幂等操作）。

        Args:
            pg_client: PostgreSQL 异步客户端实例。

        Returns:
            None
        """
        try:
            await SyllabusGraphMapper.ensure_graph_exists(pg_client)
        except Exception as e:
            logger.error(f"确保图谱存在失败: {e}")
            raise

    # ========================================================================
    # 知识点节点操作
    # ========================================================================

    @staticmethod
    async def create_knowledge_point(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        title: str,
        description: str = "",
        importance: int = 3,
        source: str = "ai",
        create_by: int | None = None,
        graph_id: int | None = None,
    ) -> KnowledgePointRecord:
        """在 AGE 图中创建一个 KnowledgePoint 节点，返回节点 ID 字符串。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            course_id: 课程ID。
            title: 知识点标题。
            description: 知识点描述（可选）。
            importance: 重要程度（1-5）。
            source: 来源（ai/manual）。
            create_by: 创建人 ID。
            graph_id: 知识图谱ID。

        Returns:
            AGE 节点 ID 字符串。

        Raises:
            KnowledgeNodeCreateFailedException: 节点创建失败。
        """
        node_uuid = uuid7_str()
        try:
            point = KnowledgePoint.model_validate(
                {
                    "node_id": node_uuid,
                    "course_id": course_id,
                    "graph_id": graph_id,
                    "title": title,
                    "description": description,
                    "importance": importance,
                    "source": source,
                    "create_by": create_by,
                    "update_by": create_by,
                }
            )
            node_id = await SyllabusGraphMapper.create_knowledge_point(pg_client, point)
            if not node_id:
                raise KnowledgeNodeCreateFailedException(title=title)
            return KnowledgePointRecord.model_validate(
                {
                    **point.model_dump(mode="json"),
                    "id": node_id,
                    "uuid": str(point.node_id),
                    "importance": point.importance or 3,
                }
            )

        except KnowledgeNodeCreateFailedException:
            raise
        except Exception as e:
            logger.error(f"创建知识点失败: {title}, 错误: {e}")
            raise KnowledgeNodeCreateFailedException(title=title) from e

    @staticmethod
    async def update_knowledge_point(
        pg_client: AsyncPostgresqlClient,
        node_id: str,
        title: str | None = None,
        description: str | None = None,
        importance: int | None = None,
        update_by: int | None = None,
    ) -> KnowledgePointRecord:
        """更新 KnowledgePoint 节点属性。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            node_id: 节点ID字符串。
            title: 新标题（None 则不更新）。
            description: 新描述（None 则不更新）。
            importance: 新重要程度（None 则不更新）。
            update_by: 更新人 ID。

        Returns:
            是否找到节点并更新。

        Raises:
            KnowledgeNodeNotFoundException: 节点不存在。
        """
        try:
            # 先检查节点是否存在
            existing = await SyllabusGraphMapper.get_knowledge_point(pg_client, int(node_id))
            if not existing:
                raise KnowledgeNodeNotFoundException(node_id=node_id)

            mutation = KnowledgePointMutation.model_validate(
                {
                    "title": title,
                    "description": description,
                    "importance": importance,
                    "update_by": update_by,
                }
            )
            await SyllabusGraphMapper.update_knowledge_point(pg_client, int(node_id), mutation)
            result = await SyllabusGraphMapper.get_knowledge_point(pg_client, int(node_id))
            if not result:
                raise KnowledgeNodeNotFoundException(node_id=node_id)
            logger.info(f"更新知识点成功: {node_id}")
            return result

        except KnowledgeNodeNotFoundException:
            raise
        except Exception as e:
            logger.error(f"更新知识点失败: {node_id}, 错误: {e}")
            raise KnowledgeNodeNotFoundException(node_id=node_id) from e

    @staticmethod
    async def delete_knowledge_point(pg_client: AsyncPostgresqlClient, node_id: str) -> None:
        """删除 KnowledgePoint 节点及其所有关联关系（DETACH DELETE）。

        同时级联清理 edu_knowledge_point_embedding 和 edu_exercise_knowledge_point 中的关联记录。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            node_id: 节点ID字符串。

        Raises:
            KnowledgeNodeNotFoundException: 节点不存在。
        """
        try:
            # 先检查节点是否存在
            existing = await SyllabusGraphMapper.get_knowledge_point(pg_client, int(node_id))
            if not existing:
                raise KnowledgeNodeNotFoundException(node_id=node_id)

            await SyllabusGraphMapper.delete_knowledge_point(pg_client, int(node_id))
            logger.info(f"删除知识点成功: {node_id}")

            # 级联清理关联的 embedding 和习题关联记录
            if existing.uuid:
                await SyllabusGraphService._cascade_delete_relations(existing.uuid)

        except KnowledgeNodeNotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除知识点失败: {node_id}, 错误: {e}")
            raise

    @staticmethod
    async def get_knowledge_point(pg_client: AsyncPostgresqlClient, node_id: str) -> KnowledgePointRecord:
        """按节点ID查询知识点属性。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            node_id: 节点ID字符串。

        Returns:
            节点属性字典，包含 id, title, description, importance 等。

        Raises:
            KnowledgeNodeNotFoundException: 节点不存在。
        """
        try:
            result = await SyllabusGraphMapper.get_knowledge_point(pg_client, int(node_id))
            if not result:
                raise KnowledgeNodeNotFoundException(node_id=node_id)

            return result

        except KnowledgeNodeNotFoundException:
            raise
        except Exception as e:
            logger.error(f"查询知识点失败: {node_id}, 错误: {e}")
            raise KnowledgeNodeNotFoundException(node_id=node_id) from e

    # ========================================================================
    # 关系操作
    # ========================================================================

    @staticmethod
    async def create_relationship(
        pg_client: AsyncPostgresqlClient,
        source_id: str,
        target_id: str,
        relation_type: str = "RELATED_TO",
        confidence: float = 1.0,
        description: str | None = None,
        graph_id: int | None = None,
    ) -> str:
        """在两个知识点之间创建关系。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            source_id: 源节点ID。
            target_id: 目标节点ID。
            relation_type: 关系类型（PREREQUISITE/RELATED_TO）。
            confidence: 置信度（0-1）。
            description: 关系描述。
            graph_id: 知识图谱ID（可选）。

        Returns:
            关系ID字符串。

        Raises:
            KnowledgeRelationshipCreateFailedException: 关系创建失败。
            KnowledgeNodeNotFoundException: 源节点或目标节点不存在。
        """
        try:
            # 先检查节点是否存在
            source_node = await SyllabusGraphMapper.get_knowledge_point(pg_client, int(source_id))
            target_node = await SyllabusGraphMapper.get_knowledge_point(pg_client, int(target_id))

            if not source_node:
                raise KnowledgeNodeNotFoundException(node_id=source_id)
            if not target_node:
                raise KnowledgeNodeNotFoundException(node_id=target_id)

            payload = KnowledgeRelationshipPayload.model_validate(
                {
                    "from_node_id": source_id,
                    "to_node_id": target_id,
                    "type": normalize_relationship_name(relation_type),
                    "confidence": confidence,
                    "description": description,
                    "graph_id": graph_id,
                }
            )
            result = await SyllabusGraphMapper.create_relationship(pg_client, payload)

            if not result:
                raise KnowledgeRelationshipCreateFailedException(source_id=source_id, target_id=target_id)

            logger.info(f"创建关系成功: {source_id} -> {target_id} ({relation_type})")
            return result

        except (KnowledgeNodeNotFoundException, KnowledgeRelationshipCreateFailedException):
            raise
        except Exception as e:
            logger.error(f"创建关系失败: {source_id} -> {target_id}, 错误: {e}")
            raise KnowledgeRelationshipCreateFailedException(source_id=source_id, target_id=target_id) from e

    @staticmethod
    async def get_relationship_by_id(
        pg_client: AsyncPostgresqlClient,
        rel_id: str,
        graph_id: int | None = None,
    ) -> KnowledgeRelationshipRecord:
        """查询指定 ID 的关系详情。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            rel_id: 关系ID字符串。
            graph_id: 知识图谱ID（可选）。

        Returns:
            包含 id/type/from_node_id/to_node_id/confidence 的字典。

        Raises:
            KnowledgeRelationshipNotFoundException: 关系不存在。
        """
        from graphedu.common.exceptions.services.education import KnowledgeRelationshipNotFoundException

        try:
            result = await SyllabusGraphMapper.get_relationship_by_id(pg_client, int(rel_id), graph_id)
        except Exception as e:
            logger.error(f"查询关系失败: {rel_id}, 错误: {e}")
            raise KnowledgeRelationshipNotFoundException(rel_id=rel_id) from e

        if result is None:
            raise KnowledgeRelationshipNotFoundException(rel_id=rel_id)
        return result

    @staticmethod
    async def update_relationship(
        pg_client: AsyncPostgresqlClient,
        rel_id: str,
        relation_type: str | None = None,
        confidence: float | None = None,
        description: str | None = None,
        graph_id: int | None = None,
    ) -> KnowledgeRelationshipRecord:
        """更新关系属性（关系类型、置信度、描述），不改变源节点和目标节点。"""
        from graphedu.common.exceptions.services.education import KnowledgeRelationshipNotFoundException

        try:
            result = await SyllabusGraphMapper.update_relationship(
                pg_client=pg_client,
                rel_id=int(rel_id),
                relation_type=relation_type,
                confidence=confidence,
                description=description,
                graph_id=graph_id,
            )
        except Exception as e:
            logger.error(f"更新关系失败: {rel_id}, 错误: {e}")
            raise KnowledgeRelationshipNotFoundException(rel_id=rel_id) from e

        if result is None:
            raise KnowledgeRelationshipNotFoundException(rel_id=rel_id)

        logger.info(f"更新关系成功: {rel_id}")
        return result

    @staticmethod
    async def delete_relationship(pg_client: AsyncPostgresqlClient, rel_id: str, graph_id: int | None = None) -> None:
        """删除指定 ID 的关系。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            rel_id: 关系ID字符串。
            graph_id: 知识图谱ID（可选）。

        Raises:
            KnowledgeRelationshipNotFoundException: 关系不存在。
        """
        from graphedu.common.exceptions.services.education import KnowledgeRelationshipNotFoundException

        try:
            # 注意：AGE 中没有直接按 id 查询关系的简单方法
            # 这里直接执行删除，如果关系不存在也不会报错
            await SyllabusGraphMapper.delete_relationship(pg_client, int(rel_id), graph_id)
            logger.info(f"删除关系成功: {rel_id}")

        except Exception as e:
            logger.error(f"删除关系失败: {rel_id}, 错误: {e}")
            raise KnowledgeRelationshipNotFoundException(rel_id=rel_id) from e

    # ========================================================================
    # 图谱批量写入（审核确认后调用）
    # ========================================================================

    @staticmethod
    async def save_graph_from_extraction(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        points: list[KnowledgePointBO],
        relationships: list[KnowledgeRelationshipBO],
        operator_id: int | None = None,
        graph_id: int | None = None,
    ) -> SaveGraphResult:
        """将审核后的提取结果批量写入 AGE 图谱。

        1. 删除该图谱旧的知识点（覆盖式保存）。
        2. 创建新的 KnowledgePoint 节点。
        3. 根据标题匹配，创建 PREREQUISITE / RELATED_TO 关系。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            course_id: 课程ID（用于隔离不同课程的数据）。
            points: 审核后的知识点列表。
            relationships: 审核后的关系列表。
            operator_id: 操作人 ID。
            graph_id: 知识图谱ID。

        Returns:
            SaveGraphResult: 保存结果，包含节点数量、关系数量和标题→UUID映射。
        """
        try:
            await SyllabusGraphService.ensure_graph_exists(pg_client)

            # 1. 删除该图谱的旧节点（级联删除关系）
            await SyllabusGraphMapper.delete_graph_nodes(pg_client, course_id, graph_id)
            logger.info(f"图谱 {graph_id} 旧知识点已清除")

            # 1.1 级联清理该课程的所有 embedding 和习题关联记录
            await SyllabusGraphService._cascade_delete_course_relations(course_id)

            # 2. 创建新节点，记录 title → node_id 映射
            title_to_id: dict[str, str] = {}
            title_to_uuid: dict[str, str] = {}
            for point in points:
                node = await SyllabusGraphService.create_knowledge_point(
                    pg_client,
                    course_id=course_id,
                    title=point.title,
                    description=point.description,
                    importance=point.importance,
                    source=point.source,
                    create_by=operator_id,
                    graph_id=graph_id,
                )
                title_to_id[point.title] = node.id
                title_to_uuid[point.title] = node.uuid

            logger.info(f"课程 {course_id} 创建知识点 {len(title_to_id)} 个")

            # 3. 创建关系
            rel_count = 0
            for rel in relationships:
                src_id = title_to_id.get(rel.source_title)
                tgt_id = title_to_id.get(rel.target_title)
                if not src_id or not tgt_id:
                    logger.warning(f"跳过无效关系: {rel.source_title} -> {rel.target_title}")
                    continue

                try:
                    await SyllabusGraphService.create_relationship(
                        pg_client,
                        src_id,
                        tgt_id,
                        rel.relation_type,
                        rel.confidence,
                        getattr(rel, "description", None),
                    )
                    rel_count += 1
                except Exception as e:
                    logger.error(f"创建关系失败: {rel.source_title} -> {rel.target_title}, 错误: {e}")

            logger.info(f"课程 {course_id} 创建关系 {rel_count} 条")
            return SaveGraphResult(
                node_count=len(title_to_id),
                rel_count=rel_count,
                title_to_uuid=title_to_uuid,
            )

        except Exception as e:
            logger.error(f"保存图谱失败: 课程 {course_id}, 错误: {e}")
            raise

    # ========================================================================
    # 图谱查询（NVL 可视化数据）
    # ========================================================================

    @staticmethod
    async def get_graph_nvl_data(
        pg_client: AsyncPostgresqlClient, course_id: int, graph_id: int | None = None
    ) -> NvlGraphDataVO:
        """获取课程图谱的 NVL 格式可视化数据。

        返回节点和关系列表，供前端 Neo4j Visualization Library 渲染。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            course_id: 课程ID。
            graph_id: 知识图谱ID（可选，为 None 时兼容旧数据）。

        Returns:
            NvlGraphDataVO。
        """
        try:
            node_results = await SyllabusGraphMapper.get_graph_nodes(pg_client, course_id, graph_id)
            rel_results = await SyllabusGraphMapper.get_graph_relationships(pg_client, course_id, graph_id)
            return SyllabusGraphMapper.build_nvl_graph_data(node_results, rel_results)

        except Exception as e:
            logger.error(f"获取图谱可视化数据失败: 课程 {course_id}, 错误: {e}")
            return NvlGraphDataVO(nodes=[], relationships=[], total_nodes=0, total_relationships=0)

    @staticmethod
    async def search_nodes(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        keyword: str,
        graph_id: int | None = None,
    ) -> list[KnowledgePointRecord]:
        """按关键词搜索知识点（基于标题模糊匹配）。

        Args:
            pg_client: PostgreSQL 异步客户端实例。
            course_id: 课程ID。
            keyword: 搜索关键词。
            graph_id: 知识图谱ID（可选）。

        Returns:
            匹配的节点列表，每项含 id, title, description, importance。
        """
        try:
            return await SyllabusGraphMapper.search_nodes(pg_client, course_id, keyword, graph_id=graph_id)

        except Exception as e:
            logger.error(f"搜索知识点失败: 课程 {course_id}, 关键词 {keyword}, 错误: {e}")
            return []

    @staticmethod
    def _get_embedding_llm() -> OpenAIEmbeddings:
        """获取 embedding_llm 实例（懒加载）。"""
        if SyllabusGraphService._embedding_llm is None:
            emb_cfg = get_config().model.embeddings
            SyllabusGraphService._embedding_llm = OpenAIEmbeddings(**emb_cfg.get_lc_attr())
        return SyllabusGraphService._embedding_llm

    @staticmethod
    async def search_nodes_by_vector(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        keyword: str,
        limit: int = 20,
        graph_id: int | None = None,
    ) -> list[KnowledgePointRecord]:
        """基于向量相似度检索知识点。

        检索流程：
        1) 使用 embedding_llm 生成查询向量
        2) 在 edu_chapter.embedding 上做相似度召回
        3) 通过 edu_knowledge_node_chapter 映射到知识图谱节点
        """
        try:
            embedding_llm = SyllabusGraphService._get_embedding_llm()
            query_embedding = await embedding_llm.aembed_query(keyword)
            if not query_embedding:
                return []

            return await SyllabusGraphMapper.search_nodes_by_chapter_embedding(
                pg_client=pg_client,
                course_id=course_id,
                query_embedding=query_embedding,
                chapter_limit=max(limit * 2, 20),
                node_limit=limit,
                graph_id=graph_id,
            )

        except Exception as e:
            logger.error(f"向量检索知识点失败: 课程 {course_id}, 关键词 {keyword}, 错误: {e}")
            return []

    @staticmethod
    async def search_nodes_hybrid(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        keyword: str,
        keyword_limit: int = 20,
        vector_limit: int = 20,
        graph_id: int | None = None,
    ) -> tuple[list[KnowledgePointRecord], list[KnowledgePointRecord], list[KnowledgePointRecord]]:
        """并行执行关键词检索与向量检索，并返回去重合并结果。"""
        try:
            keyword_task = SyllabusGraphService.search_nodes(pg_client, course_id, keyword, graph_id=graph_id)
            vector_task = SyllabusGraphService.search_nodes_by_vector(
                pg_client, course_id, keyword, limit=vector_limit, graph_id=graph_id
            )
            keyword_nodes, vector_nodes = await asyncio.gather(keyword_task, vector_task)

            keyword_nodes = keyword_nodes[:keyword_limit]
            merged_by_id: dict[str, KnowledgePointRecord] = {}
            for node in keyword_nodes:
                merged_by_id[node.id] = node
            for node in vector_nodes:
                merged_by_id.setdefault(node.id, node)

            merged_nodes = list(merged_by_id.values())
            return merged_nodes, keyword_nodes, vector_nodes

        except Exception as e:
            logger.error(f"混合检索知识点失败: 课程 {course_id}, 关键词 {keyword}, 错误: {e}")
            return [], [], []

    @staticmethod
    async def get_two_hop_subgraph_from_seeds(
        pg_client: AsyncPostgresqlClient,
        seed_nodes: list[KnowledgePointRecord],
        node_limit: int = 80,
        relation_limit: int = 160,
    ) -> tuple[list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """基于种子节点扩展两跳子图。"""
        if not seed_nodes:
            return [], []

        node_map: dict[str, KnowledgePointRecord] = {node.id: node for node in seed_nodes}
        relation_map: dict[str, KnowledgeRelationshipRecord] = {}

        for seed in seed_nodes:
            neighbors, relations = await SyllabusGraphMapper.get_node_neighbors(
                pg_client=pg_client,
                node_id=seed.id,
                depth=2,
                limit=node_limit,
                direction="both",
            )
            for node in neighbors:
                if len(node_map) >= node_limit:
                    break
                node_map.setdefault(node.id, node)

            for relation in relations:
                if len(relation_map) >= relation_limit:
                    break
                relation_map.setdefault(relation.id, relation)

            if len(node_map) >= node_limit and len(relation_map) >= relation_limit:
                break

        return list(node_map.values())[:node_limit], list(relation_map.values())[:relation_limit]

    # ========================================================================
    # 级联清理辅助方法
    # ========================================================================

    @staticmethod
    async def _cascade_delete_relations(node_uuid: str) -> None:
        """级联删除指定知识点的 embedding 和习题关联记录。

        :param node_uuid: 知识点业务 UUID
        """
        from uuid import UUID

        from graphedu.mapper.education.exercise_knowledge_point import ExerciseKnowledgePointMapper
        from graphedu.mapper.education.knowledge_point_embedding import KnowledgePointEmbeddingMapper

        try:
            from graphedu.common.resource import ContainerMode, try_get_container

            container = await try_get_container(ContainerMode.SERVICE)
            pg_client = await container.postgresql_client()

            async with pg_client.session_context() as db_session:
                uuid_obj = UUID(node_uuid)
                await KnowledgePointEmbeddingMapper.delete_by_node_uuid(uuid_obj, db_session)
                await ExerciseKnowledgePointMapper.delete_by_node_uuid(uuid_obj, db_session)
            logger.info(f"级联清理知识点关联记录成功: {node_uuid}")
        except Exception as e:
            logger.warning(f"级联清理知识点关联记录失败: {node_uuid}, 错误: {e}")

    @staticmethod
    async def _cascade_delete_course_relations(course_id: int) -> None:
        """级联删除指定课程的所有 embedding 和习题关联记录。

        :param course_id: 课程 ID
        """
        from graphedu.mapper.education.exercise_knowledge_point import ExerciseKnowledgePointMapper
        from graphedu.mapper.education.knowledge_point_embedding import KnowledgePointEmbeddingMapper

        try:
            from graphedu.common.resource import ContainerMode, try_get_container

            container = await try_get_container(ContainerMode.SERVICE)
            pg_client = await container.postgresql_client()

            async with pg_client.session_context() as db_session:
                # 先获取该课程所有 node_uuid，用于清理 exercise_knowledge_point
                node_uuids = await KnowledgePointEmbeddingMapper.get_existing_node_uuids(course_id, db_session)
                # 删除 embedding
                await KnowledgePointEmbeddingMapper.delete_by_course_id(course_id, db_session)
                # 删除习题关联
                if node_uuids:
                    await ExerciseKnowledgePointMapper.delete_by_node_uuids(list(node_uuids), db_session)
            logger.info(f"级联清理课程 {course_id} 的关联记录成功")
        except Exception as e:
            logger.warning(f"级联清理课程 {course_id} 的关联记录失败: {e}")
