"""大纲图谱 Mapper 层。

负责对 Apache AGE 图数据库中 KnowledgePoint 节点和关系的数据访问操作。
"""

from datetime import UTC, datetime
import logging
from typing import Any

from sqlalchemy import func, select

from graphedu.common import get_config
from graphedu.common.models.constants import SystemConstants
from graphedu.common.models.orm.education import EduChapter, EduKnowledgeNodeChapter
from graphedu.common.models.orm.knowledge_graph import (
    KnowledgePoint,
    KnowledgePointMutation,
    KnowledgePointRecord,
    KnowledgeRelationshipPayload,
    KnowledgeRelationshipRecord,
    normalize_relationship_name,
)
from graphedu.common.models.vo.educationv2.knowledge_graph import (
    NvlGraphDataVO,
    NvlNodePropertiesVO,
    NvlNodeVO,
    NvlRelationshipPropertiesVO,
    NvlRelationshipVO,
)
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient

logger = logging.getLogger(__name__)
_GRAPH_NAME = get_config().datasource.age.visualized_graph_name

# 向量检索常量
_EMBEDDING_DIM = 1024  # EduChapter.embedding 向量维度
_MAX_CHAPTER_LIMIT = 100  # 章节召回数量上限
_MAX_NODE_LIMIT = 50  # 节点召回数量上限


class SyllabusGraphMapper:
    """大纲图谱数据访问层

    提供知识点节点和关系的 CRUD 操作，封装所有 Cypher 查询。
    """

    # ========================================================================
    # 图谱初始化
    # ========================================================================

    @staticmethod
    async def ensure_graph_exists(pg_client: AsyncPostgresqlClient) -> None:
        """确保 AGE 图已创建（幂等操作）。

        :param pg_client: PostgreSQL 异步客户端实例
        :return: None
        """
        await pg_client.ensure_graph_created(graph_name=_GRAPH_NAME)

    # ========================================================================
    # 知识点节点操作
    # ========================================================================

    @staticmethod
    async def create_knowledge_point(
        pg_client: AsyncPostgresqlClient,
        point: KnowledgePoint,
    ) -> str | None:
        """在 AGE 图中创建一个 KnowledgePoint 节点。

        :param pg_client: PostgreSQL 异步客户端实例
        :param point: 知识点实体
        :return: 节点 ID，失败返回 None
        """
        point_data = point.model_dump(mode="json")
        cypher = """
            CREATE (n:KnowledgePoint {
                uuid: :uuid,
                course_id: :course_id,
                graph_id: :graph_id,
                title: :title,
                description: :description,
                importance: :importance,
                source: :source,
                create_time: :create_time,
                create_by: :create_by,
                update_time: :update_time,
                update_by: :update_by
            })
            RETURN id(n)
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["node_id"],
            params={
                "uuid": str(point_data["node_id"]),
                "course_id": point_data["course_id"],
                "graph_id": point_data.get("graph_id"),
                "title": point_data["title"],
                "description": point_data.get("description"),
                "importance": point_data.get("importance") or 3,
                "source": point_data["source"],
                "create_time": point_data["create_time"],
                "create_by": point_data.get("create_by"),
                "update_time": point_data["update_time"],
                "update_by": point_data.get("update_by"),
            },
        )
        if not results:
            return None
        node_id = results[0].get("node_id")
        return str(node_id) if node_id is not None else None

    @staticmethod
    async def update_knowledge_point(
        pg_client: AsyncPostgresqlClient,
        node_id: int,
        mutation: KnowledgePointMutation,
    ) -> bool:
        """更新 KnowledgePoint 节点属性。

        :param pg_client: PostgreSQL 异步客户端实例
        :param node_id: 节点ID（整数）
        :param mutation: 更新数据
        :return: 是否找到节点并更新
        """
        mutation_data = mutation.model_dump(exclude_none=True, mode="json")
        if not {"title", "description", "importance"}.intersection(mutation_data):
            return True

        # 构建动态 SET 子句
        set_clauses = []
        params: dict[str, Any] = {"node_id": node_id}

        if "title" in mutation_data:
            set_clauses.append("n.title = :title")
            params["title"] = mutation_data["title"]
        if "description" in mutation_data:
            set_clauses.append("n.description = :description")
            params["description"] = mutation_data["description"]
        if "importance" in mutation_data:
            set_clauses.append("n.importance = :importance")
            params["importance"] = mutation_data["importance"]

        set_clauses.append("n.update_time = :update_time")
        params["update_time"] = mutation_data.get("update_time", datetime.now(UTC).isoformat())
        if mutation_data.get("update_by") is not None:
            set_clauses.append("n.update_by = :update_by")
            params["update_by"] = mutation_data["update_by"]

        set_clause = ", ".join(set_clauses)
        cypher = f"""
        MATCH (n:KnowledgePoint) WHERE id(n) = :node_id
        SET {set_clause}
        RETURN id(n)
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME, cypher_stmt=cypher, cols=["node_id"], params=params
        )
        return bool(results)

    @staticmethod
    async def delete_knowledge_point(pg_client: AsyncPostgresqlClient, node_id: int) -> None:
        """删除 KnowledgePoint 节点及其所有关联关系（DETACH DELETE）。

        :param pg_client: PostgreSQL 异步客户端实例
        :param node_id: 节点ID（整数）
        :return: None
        """
        cypher = """
        MATCH (n:KnowledgePoint) WHERE id(n) = :node_id
        DETACH DELETE n
        """
        await pg_client.execute_cypher(graph_name=_GRAPH_NAME, cypher_stmt=cypher, params={"node_id": node_id})

    @staticmethod
    async def get_knowledge_point(pg_client: AsyncPostgresqlClient, node_id: int) -> KnowledgePointRecord | None:
        """按节点ID查询知识点属性。

        :param pg_client: PostgreSQL 异步客户端实例
        :param node_id: 节点ID（整数）
        :return: 节点属性字典，包含 id, title, description, importance 等
        """
        cypher = """
        MATCH (n:KnowledgePoint) WHERE id(n) = :node_id
        RETURN id(n) AS id, n.uuid AS uuid, n.course_id AS course_id,
               n.graph_id AS graph_id, n.title AS title, n.description AS description,
               n.importance AS importance, n.source AS source,
               n.create_time AS create_time, n.create_by AS create_by,
               n.update_time AS update_time, n.update_by AS update_by
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=[
                "id",
                "uuid",
                "course_id",
                "graph_id",
                "title",
                "description",
                "importance",
                "source",
                "create_time",
                "create_by",
                "update_time",
                "update_by",
            ],
            params={"node_id": node_id},
        )
        return KnowledgePointRecord.model_validate(results[0]) if results else None

    # ========================================================================
    # 关系操作
    # ========================================================================

    @staticmethod
    async def create_relationship(
        pg_client: AsyncPostgresqlClient,
        relationship: KnowledgeRelationshipPayload,
    ) -> str | None:
        """在两个知识点之间创建关系。

        :param pg_client: PostgreSQL 异步客户端实例
        :param relationship: 关系实体
        :return: 关系ID，失败返回 None
        """
        payload = relationship.model_dump(mode="json")
        relation_type = normalize_relationship_name(payload["type"])
        graph_id = payload.get("graph_id")

        # 根据 graph_id 是否为 None 构建 WHERE 条件
        if graph_id is not None:
            cypher = f"""
            MATCH (a:KnowledgePoint {{graph_id: :graph_id}}), (b:KnowledgePoint {{graph_id: :graph_id}})
            WHERE id(a) = :source_id AND id(b) = :target_id
            CREATE (a)-[r:{relation_type} {{confidence: :confidence, description: :description}}]->(b)
            RETURN id(r)
            """
            params = {
                "source_id": int(payload["from_node_id"]),
                "target_id": int(payload["to_node_id"]),
                "graph_id": graph_id,
                "confidence": payload.get("confidence") if payload.get("confidence") is not None else 1.0,
                "description": payload.get("description"),
            }
        else:
            cypher = f"""
            MATCH (a:KnowledgePoint), (b:KnowledgePoint)
            WHERE id(a) = :source_id AND id(b) = :target_id
            CREATE (a)-[r:{relation_type} {{confidence: :confidence, description: :description}}]->(b)
            RETURN id(r)
            """
            params = {
                "source_id": int(payload["from_node_id"]),
                "target_id": int(payload["to_node_id"]),
                "confidence": payload.get("confidence") if payload.get("confidence") is not None else 1.0,
                "description": payload.get("description"),
            }

        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["rel_id"],
            params=params,
        )
        if not results:
            return None
        rel_id = results[0].get("rel_id")
        return str(rel_id) if rel_id is not None else None

    @staticmethod
    async def delete_relationship(pg_client: AsyncPostgresqlClient, rel_id: int, graph_id: int | None = None) -> None:
        """删除指定 ID 的关系。

        :param pg_client: PostgreSQL 异步客户端实例
        :param rel_id: 关系ID（整数）
        :param graph_id: 知识图谱ID（可选）
        :return: None
        """
        # 根据 graph_id 是否为 None 构建 WHERE 条件
        if graph_id is not None:
            cypher = """
            MATCH (a:KnowledgePoint {graph_id: :graph_id})-[r]->(b:KnowledgePoint {graph_id: :graph_id})
            WHERE id(r) = :rel_id
            DELETE r
            """
            params = {"rel_id": rel_id, "graph_id": graph_id}
        else:
            cypher = """
            MATCH ()-[r]->() WHERE id(r) = :rel_id
            DELETE r
            """
            params = {"rel_id": rel_id}

        await pg_client.execute_cypher(graph_name=_GRAPH_NAME, cypher_stmt=cypher, params=params)

    @staticmethod
    async def update_relationship(
        pg_client: AsyncPostgresqlClient,
        rel_id: int,
        relation_type: str | None = None,
        confidence: float | None = None,
        description: str | None = None,
        graph_id: int | None = None,
    ) -> KnowledgeRelationshipRecord | None:
        """更新指定关系的属性，不改变起点和终点。

        说明：AGE/Neo4j 关系类型不可原地修改，若类型变化则创建同端点新关系并删除旧关系。

        :param pg_client: PostgreSQL 异步客户端实例
        :param rel_id: 关系ID（整数）
        :param relation_type: 新关系类型（可选）
        :param confidence: 新置信度（可选）
        :param description: 新关系描述（可选）
        :return: 更新后的关系记录，不存在返回 None
        """
        existing = await SyllabusGraphMapper.get_relationship_by_id(pg_client, rel_id, graph_id)
        if not existing:
            return None

        target_type = normalize_relationship_name(relation_type or existing.type)
        target_confidence = existing.confidence if confidence is None else confidence
        target_description = existing.description if description is None else description

        if target_type == existing.type:
            cypher = """
            MATCH ()-[r]->() WHERE id(r) = :rel_id
            SET r.confidence = :confidence,
                r.description = :description
            RETURN id(r) AS id, type(r) AS type, :from_node_id AS from_node_id, :to_node_id AS to_node_id,
                   r.confidence AS confidence, r.description AS description
            """
            results = await pg_client.execute_cypher(
                graph_name=_GRAPH_NAME,
                cypher_stmt=cypher,
                cols=["id", "type", "from_node_id", "to_node_id", "confidence", "description"],
                params={
                    "rel_id": rel_id,
                    "from_node_id": int(existing.from_node_id),
                    "to_node_id": int(existing.to_node_id),
                    "confidence": target_confidence,
                    "description": target_description,
                },
            )
        else:
            cypher = f"""
            MATCH (a)-[r]->(b) WHERE id(r) = :rel_id
            CREATE (a)-[new_rel:{target_type} {{
                confidence: :confidence,
                description: :description
            }}]->(b)
            DELETE r
            RETURN id(new_rel) AS id, type(new_rel) AS type, id(a) AS from_node_id, id(b) AS to_node_id,
                   new_rel.confidence AS confidence, new_rel.description AS description
            """
            results = await pg_client.execute_cypher(
                graph_name=_GRAPH_NAME,
                cypher_stmt=cypher,
                cols=["id", "type", "from_node_id", "to_node_id", "confidence", "description"],
                params={
                    "rel_id": rel_id,
                    "confidence": target_confidence,
                    "description": target_description,
                },
            )

        if not results:
            return None

        row = results[0]
        return KnowledgeRelationshipRecord.model_validate(
            {
                "id": str(row["id"]),
                "type": normalize_relationship_name(row.get("type")),
                "from_node_id": str(row["from_node_id"]),
                "to_node_id": str(row["to_node_id"]),
                "confidence": row.get("confidence"),
                "description": row.get("description"),
            }
        )

    @staticmethod
    async def get_relationship_by_id(
        pg_client: AsyncPostgresqlClient, rel_id: int, graph_id: int | None = None
    ) -> KnowledgeRelationshipRecord | None:
        """查询指定 ID 的关系详情。

        :param pg_client: PostgreSQL 异步客户端实例
        :param rel_id: 关系ID（整数）
        :param graph_id: 知识图谱ID（可选）
        :return: 包含 id/type/from_node_id/to_node_id/confidence 的字典，未找到返回 None
        """
        # 根据 graph_id 是否为 None 构建 WHERE 条件
        if graph_id is not None:
            cypher = """
            MATCH (a:KnowledgePoint {graph_id: :graph_id})-[r]->(b:KnowledgePoint {graph_id: :graph_id})
            WHERE id(r) = :rel_id
            RETURN id(r) AS id, type(r) AS type, id(a) AS from_node_id, id(b) AS to_node_id,
                r.confidence AS confidence, r.description AS description
            """
            params = {"rel_id": rel_id, "graph_id": graph_id}
        else:
            cypher = """
            MATCH (a)-[r]->(b) WHERE id(r) = :rel_id
            RETURN id(r) AS id, type(r) AS type, id(a) AS from_node_id, id(b) AS to_node_id,
                r.confidence AS confidence, r.description AS description
            """
            params = {"rel_id": rel_id}

        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["id", "type", "from_node_id", "to_node_id", "confidence", "description"],
            params=params,
        )
        if not results:
            return None
        row = results[0]
        return KnowledgeRelationshipRecord.model_validate(
            {
                "id": str(row["id"]),
                "type": normalize_relationship_name(row.get("type")),
                "from_node_id": str(row["from_node_id"]),
                "to_node_id": str(row["to_node_id"]),
                "confidence": row.get("confidence"),
                "description": row.get("description"),
            }
        )

    # ========================================================================
    # 批量操作
    # ========================================================================

    @staticmethod
    async def delete_graph_nodes(pg_client: AsyncPostgresqlClient, course_id: int, graph_id: int) -> None:
        """删除指定图谱的所有知识点节点（级联删除关系）。

        :param pg_client: PostgreSQL 异步客户端实例
        :param course_id: 课程ID
        :param graph_id: 知识图谱ID
        :return: None
        """
        cypher = """
        MATCH (n:KnowledgePoint {course_id: :course_id, graph_id: :graph_id})
        DETACH DELETE n
        """
        await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME, cypher_stmt=cypher, params={"course_id": course_id, "graph_id": graph_id}
        )

    # ========================================================================
    # 图谱查询
    # ========================================================================

    @staticmethod
    async def get_graph_nodes(
        pg_client: AsyncPostgresqlClient, course_id: int, graph_id: int | None = None
    ) -> list[KnowledgePointRecord]:
        """获取课程的知识点节点。

        :param pg_client: PostgreSQL 异步客户端实例
        :param course_id: 课程ID
        :param graph_id: 知识图谱ID（可选，为 None 时兼容旧数据）
        :return: 节点列表
        """
        if graph_id is not None:
            cypher = """
            MATCH (n:KnowledgePoint {course_id: :course_id, graph_id: :graph_id})
            RETURN id(n) AS id, n.course_id AS course_id, n.graph_id AS graph_id,
                   n.uuid AS uuid, n.title AS title, n.description AS description,
                   n.importance AS importance, n.source AS source,
                   n.create_time AS create_time, n.create_by AS create_by,
                   n.update_time AS update_time, n.update_by AS update_by
            """
        else:
            cypher = """
            MATCH (n:KnowledgePoint {course_id: :course_id})
            RETURN id(n) AS id, n.course_id AS course_id, n.graph_id AS graph_id,
                   n.uuid AS uuid, n.title AS title, n.description AS description,
                   n.importance AS importance, n.source AS source,
                   n.create_time AS create_time, n.create_by AS create_by,
                   n.update_time AS update_time, n.update_by AS update_by
            """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=[
                "id",
                "course_id",
                "graph_id",
                "uuid",
                "title",
                "description",
                "importance",
                "source",
                "create_time",
                "create_by",
                "update_time",
                "update_by",
            ],
            params={"course_id": course_id, "graph_id": graph_id},
        )
        return [KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in results]

    @staticmethod
    async def get_graph_relationships(
        pg_client: AsyncPostgresqlClient, course_id: int, graph_id: int | None = None
    ) -> list[KnowledgeRelationshipRecord]:
        """获取课程的所有关系。

        :param pg_client: PostgreSQL 异步客户端实例
        :param course_id: 课程ID
        :param graph_id: 知识图谱ID（可选，为 None 时兼容旧数据）
        :return: 关系列表
        """
        if graph_id is not None:
            cypher = """
            MATCH (a:KnowledgePoint {course_id: :course_id, graph_id: :graph_id})
                  -[r]->(b:KnowledgePoint {course_id: :course_id, graph_id: :graph_id})
             RETURN id(r) AS id, type(r) AS type, id(a) AS from_id, id(b) AS to_id,
                 r.confidence AS confidence, r.description AS description
            """
        else:
            cypher = """
            MATCH (a:KnowledgePoint {course_id: :course_id})-[r]->(b:KnowledgePoint {course_id: :course_id})
             RETURN id(r) AS id, type(r) AS type, id(a) AS from_id, id(b) AS to_id,
                 r.confidence AS confidence, r.description AS description
            """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["id", "type", "from_id", "to_id", "confidence", "description"],
            params={"course_id": course_id, "graph_id": graph_id},
        )
        return [
            KnowledgeRelationshipRecord.model_validate(
                {
                    "id": str(row["id"]),
                    "type": normalize_relationship_name(row.get("type")),
                    "from_node_id": str(row["from_id"]),
                    "to_node_id": str(row["to_id"]),
                    "confidence": row.get("confidence"),
                    "description": row.get("description"),
                }
            )
            for row in results
        ]

    @staticmethod
    async def search_nodes(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        keyword: str,
        limit: int = 20,
        graph_id: int | None = None,
    ) -> list[KnowledgePointRecord]:
        """按关键词搜索知识点（基于标题模糊匹配）。

        :param pg_client: PostgreSQL 异步客户端实例
        :param course_id: 课程ID
        :param keyword: 搜索关键词
        :param limit: 返回结果上限
        :param graph_id: 知识图谱ID（可选）
        :return: 匹配的节点列表
        """
        graph_filter = ", graph_id: :graph_id" if graph_id is not None else ""
        # AGE 不原生支持 CONTAINS，使用 toLower 做大小写不敏感包含匹配
        cypher = f"""
        MATCH (n:KnowledgePoint {{course_id: :course_id{graph_filter}}})
        WHERE toLower(n.title) CONTAINS toLower(:keyword)
        RETURN id(n) AS id, n.course_id AS course_id, n.graph_id AS graph_id,
               n.uuid AS uuid, n.title AS title, n.description AS description,
               n.importance AS importance, n.source AS source,
               n.create_time AS create_time, n.create_by AS create_by,
               n.update_time AS update_time, n.update_by AS update_by
        LIMIT {limit}
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=[
                "id",
                "course_id",
                "graph_id",
                "uuid",
                "title",
                "description",
                "importance",
                "source",
                "create_time",
                "create_by",
                "update_time",
                "update_by",
            ],
            params={"course_id": course_id, "keyword": keyword, "graph_id": graph_id},
        )
        return [KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in results]

    @staticmethod
    async def search_nodes_by_chapter_embedding(
        pg_client: AsyncPostgresqlClient,
        course_id: int,
        query_embedding: list[float],
        chapter_limit: int = 40,
        node_limit: int = 20,
        graph_id: int | None = None,
    ) -> list[KnowledgePointRecord]:
        """通过章节向量召回知识点。

        检索流程：
        1) 在 edu_chapter.embedding 上按向量距离召回章节
        2) 通过 edu_knowledge_node_chapter 关联到知识点 UUID
        3) 从 AGE 图中读取对应知识点节点

        :raises ValueError: 当向量维度不匹配或参数超出范围时
        """
        # 输入验证
        if not query_embedding:
            return []
        if len(query_embedding) != _EMBEDDING_DIM:
            logger.warning(f"Invalid embedding dimension: expected {_EMBEDDING_DIM}, got {len(query_embedding)}")
            return []
        if not (1 <= chapter_limit <= _MAX_CHAPTER_LIMIT):
            raise ValueError(f"chapter_limit must be between 1 and {_MAX_CHAPTER_LIMIT}, got {chapter_limit}")
        if not (1 <= node_limit <= _MAX_NODE_LIMIT):
            raise ValueError(f"node_limit must be between 1 and {_MAX_NODE_LIMIT}, got {node_limit}")

        async with pg_client.session_context() as session:
            chapter_distance = EduChapter.embedding.cosine_distance(query_embedding)

            top_chapters_subquery = (
                select(
                    EduChapter.chapter_id.label("chapter_id"),
                    chapter_distance.label("distance"),
                )
                .where(
                    EduChapter.course_id == course_id,
                    EduChapter.status == SystemConstants.Status.NORMAL,
                    EduChapter.embedding.is_not(None),
                )
                .order_by(chapter_distance.asc())
                .limit(chapter_limit)
                .subquery("top_chapters")
            )

            # CTE: 先计算每个 (node_id, chapter_id) 组合的距离和相关性
            # 然后使用窗口函数为每个 node_id 选择最佳 chapter
            node_chapter_cte = (
                select(
                    EduKnowledgeNodeChapter.node_id.label("node_id"),
                    top_chapters_subquery.c.distance.label("distance"),
                    func.coalesce(EduKnowledgeNodeChapter.relevance_score, 0).label("relevance_score"),
                    # 窗口函数：为每个 node_id 的记录按 (distance ASC, relevance DESC) 排序并编号
                    func.row_number()
                    .over(
                        partition_by=EduKnowledgeNodeChapter.node_id,
                        order_by=(
                            top_chapters_subquery.c.distance.asc(),
                            func.coalesce(EduKnowledgeNodeChapter.relevance_score, 0).desc(),
                        ),
                    )
                    .label("rn"),
                )
                .join(
                    top_chapters_subquery,
                    top_chapters_subquery.c.chapter_id == EduKnowledgeNodeChapter.chapter_id,
                )
                .where(EduKnowledgeNodeChapter.status == SystemConstants.Status.NORMAL)
                .cte("node_chapter_ranked")
            )

            # 只选择每个 node_id 的最佳记录 (rn = 1)，然后按综合分数排序
            best_match_subquery = (
                select(node_chapter_cte.c.node_id, node_chapter_cte.c.distance, node_chapter_cte.c.relevance_score)
                .select_from(node_chapter_cte)
                .where(node_chapter_cte.c.rn == 1)
                .subquery("best_match")
            )

            node_rank_stmt = (
                select(best_match_subquery.c.node_id)
                .select_from(best_match_subquery)
                .order_by(best_match_subquery.c.distance.asc(), best_match_subquery.c.relevance_score.desc())
                .limit(node_limit)
            )

            node_rank_rows = await session.execute(node_rank_stmt)
            ordered_node_uuids = [str(node_id) for node_id in node_rank_rows.scalars().all()]

        if not ordered_node_uuids:
            return []

        graph_filter = " AND n.graph_id = :graph_id" if graph_id is not None else ""
        cypher = f"""
        MATCH (n:KnowledgePoint {{course_id: :course_id}})
        WHERE n.uuid IN :node_uuids{graph_filter}
        RETURN id(n) AS id, n.course_id AS course_id, n.graph_id AS graph_id,
               n.uuid AS uuid, n.title AS title, n.description AS description,
               n.importance AS importance, n.source AS source,
               n.create_time AS create_time, n.create_by AS create_by,
               n.update_time AS update_time, n.update_by AS update_by
        """
        node_rows = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=[
                "id",
                "course_id",
                "graph_id",
                "uuid",
                "title",
                "description",
                "importance",
                "source",
                "create_time",
                "create_by",
                "update_time",
                "update_by",
            ],
            params={"course_id": course_id, "node_uuids": ordered_node_uuids, "graph_id": graph_id},
        )
        node_by_uuid = {
            str(row["uuid"]): KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in node_rows
        }

        # 检查缺失的 UUID 并记录日志
        missing_uuids = [uuid_ for uuid_ in ordered_node_uuids if uuid_ not in node_by_uuid]
        if missing_uuids:
            sample = missing_uuids[:5]
            elli = "..." if len(missing_uuids) > 5 else ""
            logger.warning(f"Found {len(missing_uuids)} node UUIDs in relational DB but not in graph: {sample}{elli}")

        return [node_by_uuid[uuid_] for uuid_ in ordered_node_uuids if uuid_ in node_by_uuid]

    @staticmethod
    def build_nvl_graph_data(
        nodes: list[KnowledgePointRecord], relationships: list[KnowledgeRelationshipRecord]
    ) -> NvlGraphDataVO:
        """将图谱实体转换为 NVL 可视化模型。"""
        return NvlGraphDataVO.model_validate(
            {
                "nodes": [
                    NvlNodeVO(
                        id=node.id,
                        labels=["KnowledgePoint"],
                        properties=NvlNodePropertiesVO.model_validate(
                            {
                                "title": node.title,
                                "description": node.description,
                                "importance": node.importance,
                                "source": node.source,
                                "uuid": node.uuid,
                            }
                        ),
                    ).model_dump(by_alias=True)
                    for node in nodes
                ],
                "relationships": [
                    NvlRelationshipVO.model_validate(
                        {
                            "id": relationship.id,
                            "type": relationship.type,
                            "from": relationship.from_node_id,
                            "to": relationship.to_node_id,
                            "properties": NvlRelationshipPropertiesVO.model_validate(
                                {
                                    "confidence": relationship.confidence,
                                    "description": relationship.description,
                                }
                            ).model_dump(),
                        }
                    ).model_dump(by_alias=True)
                    for relationship in relationships
                ],
                "total_nodes": len(nodes),
                "total_relationships": len(relationships),
            }
        )

    # ========================================================================
    # 辅助方法
    # ========================================================================

    @staticmethod
    async def get_top_nodes(
        pg_client: AsyncPostgresqlClient, course_id: int, limit: int = 10, graph_id: int | None = None
    ) -> tuple[list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """获取课程的顶层节点（入度为0的节点，代表没有前置依赖的知识点）及其之间的关系。

        :param pg_client: PostgreSQL 异步客户端实例
        :param course_id: 课程ID
        :param limit: 返回节点数量限制
        :param graph_id: 知识图谱ID（可选）
        :return: (顶层节点列表, 节点间关系列表)
        """
        if graph_id is not None:
            cypher = """
            MATCH (n:KnowledgePoint {course_id: :course_id, graph_id: :graph_id})
            WHERE NOT exists((n)<-[]-())
            RETURN id(n) AS id, n.course_id AS course_id, n.graph_id AS graph_id,
                   n.uuid AS uuid, n.title AS title, n.description AS description,
                   n.importance AS importance, n.source AS source,
                   n.create_time AS create_time, n.create_by AS create_by,
                   n.update_time AS update_time, n.update_by AS update_by
            LIMIT :limit
            """
        else:
            cypher = """
            MATCH (n:KnowledgePoint {course_id: :course_id})
            WHERE NOT exists((n)<-[]-())
            RETURN id(n) AS id, n.course_id AS course_id, n.graph_id AS graph_id,
                   n.uuid AS uuid, n.title AS title, n.description AS description,
                   n.importance AS importance, n.source AS source,
                   n.create_time AS create_time, n.create_by AS create_by,
                   n.update_time AS update_time, n.update_by AS update_by
            LIMIT :limit
            """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=[
                "id",
                "course_id",
                "graph_id",
                "uuid",
                "title",
                "description",
                "importance",
                "source",
                "create_time",
                "create_by",
                "update_time",
                "update_by",
            ],
            params={"course_id": course_id, "limit": limit, "graph_id": graph_id},
        )
        nodes = [KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in results]

        # 查询顶层节点之间的关系
        relationships: list[KnowledgeRelationshipRecord] = []
        if len(nodes) >= 2:
            node_ids = [int(n.id) for n in nodes]
            rel_cypher = """
            MATCH (a:KnowledgePoint)-[r]->(b:KnowledgePoint)
            WHERE id(a) IN :node_ids AND id(b) IN :node_ids
            RETURN id(r) AS id, type(r) AS type,
                   id(a) AS from_id, id(b) AS to_id,
                   r.confidence AS confidence, r.description AS description
            """
            rel_results = await pg_client.execute_cypher(
                graph_name=_GRAPH_NAME,
                cypher_stmt=rel_cypher,
                cols=["id", "type", "from_id", "to_id", "confidence", "description"],
                params={"node_ids": node_ids},
            )
            relationships = [
                KnowledgeRelationshipRecord.model_validate(
                    {
                        "id": str(row["id"]),
                        "type": normalize_relationship_name(row.get("type")),
                        "from_node_id": str(row["from_id"]),
                        "to_node_id": str(row["to_id"]),
                        "confidence": row.get("confidence"),
                        "description": row.get("description"),
                    }
                )
                for row in rel_results
            ]

        return nodes, relationships

    @staticmethod
    async def get_node_neighbors(
        pg_client: AsyncPostgresqlClient,
        node_id: str,
        depth: int = 1,
        limit: int = 20,
        direction: str = "both",
        graph_id: int | None = None,
    ) -> tuple[list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """获取指定节点的邻居节点和关系。

        :param pg_client: PostgreSQL 异步客户端实例
        :param node_id: 节点ID
        :param depth: 查询深度（1=直接邻居，2=两跳邻居）
        :param limit: 每层返回的节点数量限制
        :param direction: 关系方向（in/out/both）
        :param graph_id: 知识图谱ID（可选）
        :return: (节点列表, 关系列表)
        """
        # 根据方向构建关系模式
        if direction == "in":
            rel_pattern = f"<-[*1..{depth}]-"
        elif direction == "out":
            rel_pattern = f"-[*1..{depth}]->"
        else:
            rel_pattern = f"-[*1..{depth}]-"

        # 根据 graph_id 是否为 None 构建 WHERE 条件
        graph_filter = " AND neighbor.graph_id = :graph_id" if graph_id is not None else ""
        cypher = f"""
        MATCH (center:KnowledgePoint) WHERE id(center) = :node_id
        MATCH (center){rel_pattern}(neighbor:KnowledgePoint)
        WHERE true{graph_filter}
        RETURN DISTINCT id(neighbor) AS id, neighbor.course_id AS course_id, neighbor.graph_id AS graph_id,
               neighbor.uuid AS uuid, neighbor.title AS title, neighbor.description AS description,
               neighbor.importance AS importance, neighbor.source AS source,
               neighbor.create_time AS create_time, neighbor.create_by AS create_by,
               neighbor.update_time AS update_time, neighbor.update_by AS update_by
        LIMIT :limit
        """

        # 查询邻居节点
        params = {"node_id": int(node_id), "limit": limit}
        if graph_id is not None:
            params["graph_id"] = graph_id

        neighbor_results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=[
                "id",
                "course_id",
                "graph_id",
                "uuid",
                "title",
                "description",
                "importance",
                "source",
                "create_time",
                "create_by",
                "update_time",
                "update_by",
            ],
            params=params,
        )
        neighbor_nodes = [
            KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in neighbor_results
        ]

        # 查询中心节点与邻居节点之间的关系
        neighbor_ids = [n.id for n in neighbor_nodes]
        relationships = []

        if neighbor_ids:
            # 构建关系查询的 graph_id 过滤条件
            rel_graph_filter = ""
            rel_params = {"node_id": int(node_id), "neighbor_ids": [int(nid) for nid in neighbor_ids]}
            if graph_id is not None:
                # 需要验证中心节点和邻居节点都属于同一个 graph_id
                rel_graph_filter = " AND center.graph_id = :graph_id"
                rel_params["graph_id"] = graph_id

            if direction == "in":
                rel_cypher = f"""
                MATCH (center:KnowledgePoint) WHERE id(center) = :node_id{rel_graph_filter}
                MATCH (neighbor)-[r]->(center)
                WHERE id(neighbor) IN :neighbor_ids
                RETURN id(r) AS id, type(r) AS type, id(neighbor) AS from_id, id(center) AS to_id,
                       r.confidence AS confidence, r.description AS description
                """
            elif direction == "out":
                rel_cypher = f"""
                MATCH (center:KnowledgePoint) WHERE id(center) = :node_id{rel_graph_filter}
                MATCH (center)-[r]->(neighbor)
                WHERE id(neighbor) IN :neighbor_ids
                RETURN id(r) AS id, type(r) AS type, id(center) AS from_id, id(neighbor) AS to_id,
                       r.confidence AS confidence, r.description AS description
                """
            else:
                rel_cypher = f"""
                MATCH (center:KnowledgePoint) WHERE id(center) = :node_id{rel_graph_filter}
                MATCH (center)-[r]-(neighbor)
                WHERE id(neighbor) IN :neighbor_ids
                RETURN id(r) AS id, type(r) AS type,
                       CASE WHEN startNode(r) = center THEN id(center) ELSE id(neighbor) END AS from_id,
                       CASE WHEN startNode(r) = center THEN id(neighbor) ELSE id(center) END AS to_id,
                       r.confidence AS confidence, r.description AS description
                """

            rel_results = await pg_client.execute_cypher(
                graph_name=_GRAPH_NAME,
                cypher_stmt=rel_cypher,
                cols=["id", "type", "from_id", "to_id", "confidence", "description"],
                params=rel_params,
            )
            relationships = [
                KnowledgeRelationshipRecord.model_validate(
                    {
                        "id": str(row["id"]),
                        "type": normalize_relationship_name(row.get("type")),
                        "from_node_id": str(row["from_id"]),
                        "to_node_id": str(row["to_id"]),
                        "confidence": row.get("confidence"),
                        "description": row.get("description"),
                    }
                )
                for row in rel_results
            ]

            # 查询邻居节点之间的关系（邻居之间的边）
            if len(neighbor_ids) >= 2:
                int_neighbor_ids = [int(nid) for nid in neighbor_ids]
                neighbor_rel_params = {"neighbor_ids": int_neighbor_ids}
                neighbor_rel_graph_filter = ""

                if graph_id is not None:
                    neighbor_rel_graph_filter = " WHERE a.graph_id = :graph_id AND b.graph_id = :graph_id"
                    neighbor_rel_params["graph_id"] = graph_id

                neighbor_rel_cypher = f"""
                MATCH (a:KnowledgePoint)-[r]->(b:KnowledgePoint)
                WHERE id(a) IN :neighbor_ids AND id(b) IN :neighbor_ids{neighbor_rel_graph_filter}
                RETURN id(r) AS id, type(r) AS type,
                       id(a) AS from_id, id(b) AS to_id,
                       r.confidence AS confidence, r.description AS description
                """
                neighbor_rel_results = await pg_client.execute_cypher(
                    graph_name=_GRAPH_NAME,
                    cypher_stmt=neighbor_rel_cypher,
                    cols=["id", "type", "from_id", "to_id", "confidence", "description"],
                    params=neighbor_rel_params,
                )
                existing_rel_ids = {rel.id for rel in relationships}
                for row in neighbor_rel_results:
                    rel_id = str(row["id"])
                    if rel_id not in existing_rel_ids:
                        relationships.append(
                            KnowledgeRelationshipRecord.model_validate(
                                {
                                    "id": rel_id,
                                    "type": normalize_relationship_name(row.get("type")),
                                    "from_node_id": str(row["from_id"]),
                                    "to_node_id": str(row["to_id"]),
                                    "confidence": row.get("confidence"),
                                    "description": row.get("description"),
                                }
                            )
                        )
                        existing_rel_ids.add(rel_id)

        return neighbor_nodes, relationships

    @staticmethod
    def _build_cypher_query(
        operation: str,
        node_label: str | None = None,
        match_conditions: dict[str, Any] | None = None,
        set_properties: dict[str, Any] | None = None,
        create_properties: dict[str, Any] | None = None,
        return_clause: str | None = None,
        where_clause: str | None = None,
    ) -> str:
        """快速组装 Cypher 查询语句。

        支持 MATCH/CREATE/UPDATE/DELETE 操作模式。

        :param operation: 操作类型（MATCH/CREATE/MERGE/DELETE）
        :param node_label: 节点标签（如 KnowledgePoint）
        :param match_conditions: MATCH 条件字典
        :param set_properties: SET 属性字典（用于 UPDATE）
        :param create_properties: CREATE 属性字典
        :param return_clause: RETURN 子句（如 "id(n)"）
        :param where_clause: WHERE 子句（字符串）
        :return: 组装好的 Cypher 查询语句

        Example:
            >>> SyllabusGraphMapper._build_cypher_query(
            ...     operation="MATCH",
            ...     node_label="KnowledgePoint",
            ...     match_conditions={"course_id": 1},
            ...     return_clause="n"
            ... )
            'MATCH (n:KnowledgePoint {course_id: $course_id}) RETURN n'
        """
        clauses = []

        if operation == "MATCH":
            if node_label:
                match_part = f"(n:{node_label}"
                if match_conditions:
                    props = ", ".join(f"{k}: :{k}" for k in match_conditions)
                    match_part += f" {{{props}}}"
                match_part += ")"
                clauses.append(f"MATCH {match_part}")
            if where_clause:
                clauses.append(f"WHERE {where_clause}")
            if return_clause:
                clauses.append(f"RETURN {return_clause}")

        elif operation == "CREATE":
            if node_label and create_properties:
                props = ", ".join(f"{k}: :{k}" for k in create_properties)
                clauses.append(f"CREATE (n:{node_label} {{{props}}})")
                if return_clause:
                    clauses.append(f"RETURN {return_clause}")

        elif operation == "UPDATE":
            if node_label:
                match_part = f"(n:{node_label}"
                if match_conditions:
                    props = ", ".join(f"{k}: :{k}" for k in match_conditions)
                    match_part += f" {{{props}}}"
                match_part += ")"
                clauses.append(f"MATCH {match_part}")
            if set_properties:
                set_items = ", ".join(f"n.{k} = :{k}" for k in set_properties)
                clauses.append(f"SET {set_items}")
            if return_clause:
                clauses.append(f"RETURN {return_clause}")

        elif operation == "DELETE":
            if node_label:
                match_part = f"(n:{node_label}"
                if match_conditions:
                    props = ", ".join(f"{k}: :{k}" for k in match_conditions)
                    match_part += f" {{{props}}}"
                match_part += ")"
                clauses.append(f"MATCH {match_part}")
            if where_clause:
                clauses.append(f"WHERE {where_clause}")
            clauses.append("DETACH DELETE n")

        return " ".join(clauses)
