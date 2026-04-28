"""学习路径 Mapper 层。

负责对 Apache AGE 图数据库中 LearningPlan 节点和 PLAN_STEP 关系的数据访问操作。
"""

import logging

from graphedu.common import get_config
from graphedu.common.models.orm.knowledge_graph import (
    KnowledgePointRecord,
    KnowledgeRelationshipRecord,
    LearningPlan,
    LearningPlanRecord,
    normalize_relationship_name,
)
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient

logger = logging.getLogger(__name__)
_GRAPH_NAME = get_config().datasource.age.visualized_graph_name

# 学习路径节点标签
_PLAN_LABEL = "LearningPlan"
_PLAN_STEP_REL = "PLAN_STEP"


class LearningPathMapper:
    """学习路径数据访问层。

    在 AGE 图中管理 LearningPlan 节点和 PLAN_STEP 关系。
    """

    # ========================================================================
    # 计划 CRUD
    # ========================================================================

    @staticmethod
    async def create_plan(
        pg_client: AsyncPostgresqlClient,
        plan: LearningPlan,
    ) -> str | None:
        """在 AGE 图中创建一个 LearningPlan 节点。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan: 学习计划实体
        :return: 节点 ID，失败返回 None
        """
        cypher = """
            CREATE (p:LearningPlan {
                plan_id: :plan_id,
                student_id: :student_id,
                course_id: :course_id,
                title: :title,
                status: :status,
                session_id: :session_id,
                create_time: :create_time
            })
            RETURN id(p)
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["node_id"],
            params={
                "plan_id": str(plan.node_id),
                "student_id": plan.student_id,
                "course_id": plan.course_id,
                "title": plan.title,
                "status": plan.status,
                "session_id": plan.session_id,
                "create_time": plan.create_time.isoformat(),
            },
        )
        if not results:
            return None
        node_id = results[0].get("node_id")
        return str(node_id) if node_id is not None else None

    @staticmethod
    async def get_student_plans(
        pg_client: AsyncPostgresqlClient,
        student_id: int,
        course_id: int,
    ) -> list[LearningPlanRecord]:
        """查询学生的所有学习计划。

        :param pg_client: PostgreSQL 异步客户端实例
        :param student_id: 学生 ID
        :param course_id: 课程 ID
        :return: 学习计划列表
        """
        cypher = """
        MATCH (p:LearningPlan {student_id: :student_id, course_id: :course_id})
        RETURN id(p) AS id, p.plan_id AS plan_id, p.student_id AS student_id,
               p.course_id AS course_id, p.title AS title, p.status AS status,
               p.session_id AS session_id, p.create_time AS create_time
        ORDER BY p.create_time DESC
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["id", "plan_id", "student_id", "course_id", "title", "status", "session_id", "create_time"],
            params={"student_id": student_id, "course_id": course_id},
        )
        return [
            LearningPlanRecord.model_validate(
                {
                    "id": str(row["id"]),
                    "plan_id": str(row["plan_id"]),
                    "student_id": row["student_id"],
                    "course_id": row["course_id"],
                    "title": row["title"],
                    "status": row["status"],
                    "session_id": row["session_id"],
                    "create_time": row["create_time"],
                }
            )
            for row in results
        ]

    @staticmethod
    async def get_plan_by_plan_id(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
    ) -> LearningPlanRecord | None:
        """按 plan_id UUID 查询学习计划。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :return: 学习计划记录，不存在返回 None
        """
        cypher = """
        MATCH (p:LearningPlan {plan_id: :plan_id})
        RETURN id(p) AS id, p.plan_id AS plan_id, p.student_id AS student_id,
               p.course_id AS course_id, p.title AS title, p.status AS status,
               p.session_id AS session_id, p.create_time AS create_time
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["id", "plan_id", "student_id", "course_id", "title", "status", "session_id", "create_time"],
            params={"plan_id": plan_uuid},
        )
        if not results:
            return None
        row = results[0]
        return LearningPlanRecord.model_validate(
            {
                "id": str(row["id"]),
                "plan_id": str(row["plan_id"]),
                "student_id": row["student_id"],
                "course_id": row["course_id"],
                "title": row["title"],
                "status": row["status"],
                "session_id": row["session_id"],
                "create_time": row["create_time"],
            }
        )

    @staticmethod
    async def update_plan_status(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
        status: str,
    ) -> bool:
        """更新学习计划状态。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :param status: 新状态（active/completed/archived）
        :return: 是否更新成功
        """
        cypher = """
        MATCH (p:LearningPlan {plan_id: :plan_id})
        SET p.status = :status
        RETURN id(p)
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["node_id"],
            params={"plan_id": plan_uuid, "status": status},
        )
        return bool(results)

    @staticmethod
    async def delete_plan(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
    ) -> None:
        """删除学习计划节点及其 PLAN_STEP 关系。

        先删除该计划的所有 PLAN_STEP 关系，再删除 LearningPlan 节点。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        """
        # 1. 删除该计划的所有 PLAN_STEP 关系
        cypher_del_steps = """
        MATCH ()-[r:PLAN_STEP {plan_id: :plan_id}]->()
        DELETE r
        """
        await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher_del_steps,
            params={"plan_id": plan_uuid},
        )

        # 2. 删除 LearningPlan 节点
        cypher_del_plan = """
        MATCH (p:LearningPlan {plan_id: :plan_id})
        DETACH DELETE p
        """
        await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher_del_plan,
            params={"plan_id": plan_uuid},
        )

    # ========================================================================
    # 计划步骤（PLAN_STEP 关系）
    # ========================================================================

    @staticmethod
    async def create_plan_steps(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
        edges: list[tuple[str, str, int]],
    ) -> int:
        """批量创建 PLAN_STEP 关系（UNWIND 单次写入）。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :param edges: 边列表，每项为 (from_node_id, to_node_id, step_order)
        :return: 创建的关系数量
        """
        if not edges:
            return 0

        # 将边列表转为 [[from_id, to_id, step_order], ...] 的嵌套列表
        edge_list = [[int(from_id), int(to_id), step_order] for from_id, to_id, step_order in edges]

        cypher = """
        UNWIND :edges AS edge
        MATCH (a:KnowledgePoint), (b:KnowledgePoint)
        WHERE id(a) = edge[0] AND id(b) = edge[1]
        CREATE (a)-[r:PLAN_STEP {plan_id: :plan_id, step_order: edge[2]}]->(b)
        RETURN id(r) AS rel_id
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["rel_id"],
            params={"plan_id": plan_uuid, "edges": edge_list},
        )
        return len(results)

    @staticmethod
    async def get_plan_graph(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
    ) -> tuple[list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """获取某个计划对应的知识点子图（通过 PLAN_STEP 关系展开）。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :return: (知识点节点列表, 知识点间关系列表)
        """
        # 1. 获取计划涉及的所有知识点节点
        cypher_nodes = """
        MATCH ()-[r:PLAN_STEP {plan_id: :plan_id}]->(kp:KnowledgePoint)
        WITH DISTINCT kp
        RETURN id(kp) AS id, kp.course_id AS course_id, kp.uuid AS uuid,
               kp.title AS title, kp.description AS description,
               kp.importance AS importance, kp.source AS source,
               kp.create_time AS create_time, kp.create_by AS create_by,
               kp.update_time AS update_time, kp.update_by AS update_by
        """
        node_results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher_nodes,
            cols=[
                "id",
                "course_id",
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
            params={"plan_id": plan_uuid},
        )
        nodes = [KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in node_results]

        if not nodes:
            return [], []

        # 2. 获取这些知识点之间已存在的 PRIOR_TO 关系（展示先修链）
        node_ids = [int(n.id) for n in nodes]
        cypher_rels = """
        MATCH (a:KnowledgePoint)-[r]->(b:KnowledgePoint)
        WHERE id(a) IN :node_ids AND id(b) IN :node_ids
          AND type(r) IN ['PRIOR_TO', 'RELATED_TO', 'SUBTOPIC_OF']
        RETURN id(r) AS id, type(r) AS type, id(a) AS from_id, id(b) AS to_id,
               r.confidence AS confidence, r.description AS description
        """
        rel_results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher_rels,
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
    async def get_plan_node_uuids(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
    ) -> list[str]:
        """获取某个计划内所有知识点的 UUID 列表。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :return: UUID 字符串列表
        """
        cypher = """
        MATCH ()-[r:PLAN_STEP {plan_id: :plan_id}]->(kp:KnowledgePoint)
        WITH DISTINCT kp
        RETURN kp.uuid AS uuid
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["uuid"],
            params={"plan_id": plan_uuid},
        )
        return [str(row["uuid"]) for row in results if row.get("uuid")]

    @staticmethod
    async def create_plan_leaf_steps(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
        target_node_ids: list[str],
    ) -> int:
        """为无先修关系的目标知识点创建叶子步骤（UNWIND 单次写入）。

        从 LearningPlan 节点直接创建 PLAN_STEP 关系到每个目标知识点。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :param target_node_ids: 目标知识点 AGE ID 列表
        :return: 创建的关系数量
        """
        if not target_node_ids:
            return 0

        # [[node_id, step_order], ...]
        leaf_list = [[int(node_id), idx] for idx, node_id in enumerate(target_node_ids)]

        cypher = """
        UNWIND :leaves AS leaf
        MATCH (p:LearningPlan {plan_id: :plan_id}), (kp:KnowledgePoint)
        WHERE id(kp) = leaf[0]
        CREATE (p)-[r:PLAN_STEP {plan_id: :plan_id, step_order: leaf[1]}]->(kp)
        RETURN id(r) AS rel_id
        """
        results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher,
            cols=["rel_id"],
            params={"plan_id": plan_uuid, "leaves": leaf_list},
        )
        return len(results)

    # ========================================================================
    # 先修链回溯（核心方法）
    # ========================================================================

    @staticmethod
    async def get_prior_chain(
        pg_client: AsyncPostgresqlClient,
        target_node_ids: list[str],
    ) -> tuple[list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """沿 PRIOR_TO 关系回溯目标节点的所有前驱节点。

        返回目标节点 + 所有前驱节点，以及它们之间的 PRIOR_TO 关系。
        注意 PRIOR_TO 方向：A-[:PRIOR_TO]->B 表示 A 是 B 的前置知识点。
        因此回溯前驱使用 <-[:PRIOR_TO*]- 方向。

        :param pg_client: PostgreSQL 异步客户端实例
        :param target_node_ids: 目标知识点的 AGE ID 列表
        :return: (节点列表, PRIOR_TO 关系列表)
        """
        int_ids = [int(nid) for nid in target_node_ids]

        # 1. 回溯所有前驱节点（包括目标节点自身）
        # PRIOR_TO 方向：A-[:PRIOR_TO]->B，即 B 的前驱是 A
        # 要找 B 的所有前驱：从 B 沿 <-[:PRIOR_TO*]- 方向遍历
        cypher_nodes = """
        MATCH (target:KnowledgePoint)
        WHERE id(target) IN :target_ids
        OPTIONAL MATCH path = (target)<-[:PRIOR_TO*1..]-(pre:KnowledgePoint)
        WITH collect(DISTINCT target) + collect(DISTINCT pre) AS all_nodes
        UNWIND all_nodes AS n
        WITH DISTINCT n
        RETURN id(n) AS id, n.course_id AS course_id, n.uuid AS uuid,
               n.title AS title, n.description AS description,
               n.importance AS importance, n.source AS source,
               n.create_time AS create_time, n.create_by AS create_by,
               n.update_time AS update_time, n.update_by AS update_by
        """
        node_results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher_nodes,
            cols=[
                "id",
                "course_id",
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
            params={"target_ids": int_ids},
        )
        nodes = [KnowledgePointRecord.model_validate({**row, "id": str(row["id"])}) for row in node_results]

        if not nodes:
            return [], []

        # 2. 获取这些节点之间的 PRIOR_TO 关系
        node_int_ids = [int(n.id) for n in nodes]
        cypher_rels = """
        MATCH (a:KnowledgePoint)-[r:PRIOR_TO]->(b:KnowledgePoint)
        WHERE id(a) IN :node_ids AND id(b) IN :node_ids
        RETURN id(r) AS id, type(r) AS type, id(a) AS from_id, id(b) AS to_id,
               r.confidence AS confidence, r.description AS description
        """
        rel_results = await pg_client.execute_cypher(
            graph_name=_GRAPH_NAME,
            cypher_stmt=cypher_rels,
            cols=["id", "type", "from_id", "to_id", "confidence", "description"],
            params={"node_ids": node_int_ids},
        )
        relationships = [
            KnowledgeRelationshipRecord.model_validate(
                {
                    "id": str(row["id"]),
                    "type": "PRIOR_TO",
                    "from_node_id": str(row["from_id"]),
                    "to_node_id": str(row["to_id"]),
                    "confidence": row.get("confidence"),
                    "description": row.get("description"),
                }
            )
            for row in rel_results
        ]

        return nodes, relationships
