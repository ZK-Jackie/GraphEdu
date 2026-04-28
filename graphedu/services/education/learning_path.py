"""学习路径推荐服务模块。

根据学生在 AI 聊天中表达的学习目标，利用知识图谱拓扑结构生成学习路径。

核心流程：
1. AI 提炼关键词 → 混合检索匹配目标知识节点
2. 沿 PRIOR_TO 关系回溯前驱链
3. 在 AGE 图中创建 LearningPlan 节点 + PLAN_STEP 关系
4. 返回子图数据供前端展示
"""

from datetime import UTC, datetime
import logging

from graphedu.common.models.bo.learning_path import LearningPathNodeProgressBO, LearningPathProgressBO
from graphedu.common.models.orm.knowledge_graph import (
    KnowledgePointRecord,
    KnowledgeRelationshipRecord,
    LearningPlan,
    LearningPlanRecord,
)
from graphedu.common.resource.deps import get_db_client
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient
from graphedu.common.utils.uuids import uuid7
from graphedu.mapper.education.learning_path import LearningPathMapper
from graphedu.mapper.education.study_analytics import StudyAnalyticsMapper
from graphedu.services.education.syllabus_graph import SyllabusGraphService

logger = logging.getLogger(__name__)


class LearningPathService:
    """学习路径推荐服务类。"""

    @staticmethod
    async def generate_path(
        pg_client: AsyncPostgresqlClient,
        student_id: int,
        course_id: int,
        keywords: list[str],
        title: str | None = None,
        session_id: int | None = None,
    ) -> tuple[LearningPlanRecord | None, list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """根据关键词生成学习路径。

        流程：
        1. 对每个关键词做混合检索，匹配目标知识节点
        2. 沿 PRIOR_TO 关系回溯所有前驱节点
        3. 在 AGE 中创建 LearningPlan + PLAN_STEP
        4. 返回计划信息 + 子图数据

        :param pg_client: PostgreSQL 异步客户端实例
        :param student_id: 学生 ID
        :param course_id: 课程 ID
        :param keywords: AI 提炼的关键词列表
        :param title: 计划标题（可选，自动生成则用关键词拼接）
        :param session_id: 聊天会话 ID（可选）
        :return: (计划记录, 知识点节点列表, 关系列表)
        """
        # 1. 混合检索匹配目标节点
        target_nodes: list[KnowledgePointRecord] = []
        seen_ids: set[str] = set()
        for kw in keywords:
            merged_nodes, _, _ = await SyllabusGraphService.search_nodes_hybrid(
                pg_client=pg_client,
                course_id=course_id,
                keyword=kw,
            )
            for node in merged_nodes:
                if node.id not in seen_ids:
                    target_nodes.append(node)
                    seen_ids.add(node.id)

        if not target_nodes:
            logger.warning("未匹配到任何目标知识节点: keywords=%s, course_id=%s", keywords, course_id)
            return None, [], []

        # 2. 回溯前驱链
        target_ids = [n.id for n in target_nodes]
        all_nodes, prior_rels = await LearningPathMapper.get_prior_chain(
            pg_client=pg_client,
            target_node_ids=target_ids,
        )

        if not all_nodes:
            all_nodes = target_nodes
            prior_rels = []

        logger.info(
            "学习路径回溯完成: 目标 %d 个, 前驱链共 %d 个节点, %d 条 PRIOR_TO 关系",
            len(target_nodes),
            len(all_nodes),
            len(prior_rels),
        )

        # 3. 创建 LearningPlan 节点
        plan_uuid = uuid7()
        plan_title = title or "、".join(keywords[:3]) + " 学习路径"
        plan = LearningPlan.model_validate(
            {
                "node_id": plan_uuid,
                "student_id": student_id,
                "course_id": course_id,
                "title": plan_title,
                "status": "active",
                "session_id": session_id,
                "create_time": datetime.now(UTC),
            }
        )

        plan_id = await LearningPathMapper.create_plan(pg_client=pg_client, plan=plan)
        if not plan_id:
            logger.error("创建学习计划节点失败: student_id=%s, course_id=%s", student_id, course_id)
            return None, all_nodes, prior_rels

        plan_record = LearningPlanRecord.model_validate(
            {
                "id": plan_id,
                "plan_id": str(plan_uuid),
                "student_id": student_id,
                "course_id": course_id,
                "title": plan_title,
                "status": "active",
                "session_id": session_id,
                "create_time": plan.create_time,
            }
        )

        # 4. 创建 PLAN_STEP 关系
        if prior_rels:
            # 有先修关系：从 PRIOR_TO 关系中提取边，按拓扑序排列
            node_order_map = _topological_order(all_nodes, prior_rels)
            edges: list[tuple[str, str, int]] = []
            for rel in prior_rels:
                from_order = node_order_map.get(rel.from_node_id, 0)
                edges.append((rel.from_node_id, rel.to_node_id, from_order))

            step_count = await LearningPathMapper.create_plan_steps(
                pg_client=pg_client,
                plan_uuid=str(plan_uuid),
                edges=edges,
            )
            logger.info("学习计划 %s 创建了 %d 个 PLAN_STEP 关系", plan_uuid, step_count)
        else:
            # 无先修关系：将每个目标节点作为叶子步骤（LearningPlan → KnowledgePoint）
            target_ids = [n.id for n in target_nodes]
            step_count = await LearningPathMapper.create_plan_leaf_steps(
                pg_client=pg_client,
                plan_uuid=str(plan_uuid),
                target_node_ids=target_ids,
            )
            logger.info(
                "学习计划 %s 无先修关系，将 %d 个目标节点作为叶子步骤写入",
                plan_uuid,
                step_count,
            )

        return plan_record, all_nodes, prior_rels

    @staticmethod
    async def get_student_plans(
        pg_client: AsyncPostgresqlClient,
        student_id: int,
        course_id: int,
    ) -> list[LearningPlanRecord]:
        """查询学生的所有学习计划。"""
        return await LearningPathMapper.get_student_plans(
            pg_client=pg_client,
            student_id=student_id,
            course_id=course_id,
        )

    @staticmethod
    async def get_plan_detail(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
    ) -> tuple[LearningPlanRecord | None, list[KnowledgePointRecord], list[KnowledgeRelationshipRecord]]:
        """获取学习计划详情（子图）。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :return: (计划记录, 节点列表, 关系列表)
        """
        plan = await LearningPathMapper.get_plan_by_plan_id(pg_client=pg_client, plan_uuid=plan_uuid)
        if not plan:
            return None, [], []

        nodes, rels = await LearningPathMapper.get_plan_graph(pg_client=pg_client, plan_uuid=plan_uuid)
        return plan, nodes, rels

    @staticmethod
    async def get_plan_progress(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
        student_id: int,
        course_id: int,
    ) -> LearningPathProgressBO:
        """计算学习计划完成进度。

        从 VStudentNodeProfile 视图获取每个知识点的最新掌握等级，
        medium 及以上视为已掌握。

        :param pg_client: PostgreSQL 异步客户端实例
        :param plan_uuid: 计划 UUID
        :param student_id: 学生 ID
        :param course_id: 课程 ID
        :return: 进度信息
        """
        # 1. 获取计划内的知识点 UUID
        node_uuids = await LearningPathMapper.get_plan_node_uuids(
            pg_client=pg_client,
            plan_uuid=plan_uuid,
        )

        if not node_uuids:
            return LearningPathProgressBO(total=0, mastered=0, progress_pct=0, details=[])

        # 2. 查询学生掌握度
        db_client = await get_db_client()
        async with db_client.session_context() as db_session:
            profiles = await StudyAnalyticsMapper.get_my_node_profile(
                student_id=student_id,
                course_id=course_id,
                db=db_session,
            )

        # 构建掌握度映射
        profile_map = {str(p.node_uuid): p for p in profiles}

        # 3. 计算进度
        mastered_levels = {"medium", "high"}
        mastered = 0
        details: list[LearningPathNodeProgressBO] = []
        for nuuid in node_uuids:
            profile = profile_map.get(nuuid)
            level = profile.latest_mastery_level if profile else "unknown"
            is_mastered = level in mastered_levels
            if is_mastered:
                mastered += 1
            details.append(
                LearningPathNodeProgressBO(
                    node_uuid=nuuid,
                    mastery_level=level,
                    mastery_score=float(profile.latest_mastery_score)
                    if profile and profile.latest_mastery_score
                    else None,
                    mastered=is_mastered,
                )
            )

        total = len(node_uuids)
        progress_pct = round(mastered / total * 100) if total > 0 else 0

        return LearningPathProgressBO(
            total=total,
            mastered=mastered,
            progress_pct=progress_pct,
            details=details,
        )

    @staticmethod
    async def update_plan_status(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
        status: str,
    ) -> bool:
        """更新学习计划状态。"""
        return await LearningPathMapper.update_plan_status(
            pg_client=pg_client,
            plan_uuid=plan_uuid,
            status=status,
        )

    @staticmethod
    async def delete_plan(
        pg_client: AsyncPostgresqlClient,
        plan_uuid: str,
    ) -> None:
        """删除学习计划。"""
        await LearningPathMapper.delete_plan(pg_client=pg_client, plan_uuid=plan_uuid)


def _topological_order(
    nodes: list[KnowledgePointRecord],
    relationships: list[KnowledgeRelationshipRecord],
) -> dict[str, int]:
    """对知识点做拓扑排序，返回 node_id → order 映射。

    基于先修关系（PRIOR_TO）的 DAG 排序，order 越小表示越基础。

    :param nodes: 节点列表
    :param relationships: PRIOR_TO 关系列表（from → to 表示 from 是 to 的前置）
    :return: {node_id: order}
    """
    node_ids = {n.id for n in nodes}

    # 计算入度（被多少个节点指向 = 有多少前置）
    in_degree: dict[str, int] = dict.fromkeys(node_ids, 0)
    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}

    for rel in relationships:
        if rel.from_node_id in node_ids and rel.to_node_id in node_ids:
            # from → to: from 是前置，to 有入度
            adj[rel.from_node_id].append(rel.to_node_id)
            in_degree[rel.to_node_id] = in_degree.get(rel.to_node_id, 0) + 1

    # BFS 拓扑排序
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order_map: dict[str, int] = {}
    current_order = 0

    while queue:
        # 按重要性排序，同层级先处理重要的
        queue.sort(key=lambda nid: next((n.importance or 3 for n in nodes if n.id == nid), 3), reverse=True)
        next_queue = []
        for nid in queue:
            order_map[nid] = current_order
            current_order += 1
            for neighbor in adj[nid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue

    # 处理环或未到达的节点
    for nid in node_ids:
        if nid not in order_map:
            order_map[nid] = current_order
            current_order += 1

    return order_map
