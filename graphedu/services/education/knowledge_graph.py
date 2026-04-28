"""知识图谱管理服务模块

该模块提供知识图谱信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑（包括 AGE 图谱操作的编排）。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.graphrag_task import GraphRAGIndexNotBuiltException
from graphedu.common.exceptions.services.education.knowledge_graph import (
    KnowledgeGraphCourseNotFoundException,
    KnowledgeGraphIdListEmptyException,
    KnowledgeGraphNameAlreadyExistsException,
    KnowledgeGraphNotFoundException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto import (
    KnowledgeExtractionRequestDTO,
    KnowledgeGraphCreateDTO,
    KnowledgeGraphQueryDTO,
    KnowledgeGraphUpdateDTO,
    KnowledgePointCreateDTO,
    KnowledgePointUpdateDTO,
    KnowledgeRelationshipCreateDTO,
    KnowledgeRelationshipUpdateDTO,
    SaveExtractionRequestDTO,
)
from graphedu.common.models.dto.educationv2.knowledge_graph import AutoGenerateRequestDTO, NodeNeighborsQueryDTO
from graphedu.common.models.orm.education import EduCourse, EduKnowledgeGraph
from graphedu.common.models.orm.knowledge_graph import KnowledgeRelationshipPayload
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.educationv2.knowledge_graph import (
    AutoGenerateSubmitVO,
    GraphRelationshipCreatedVO,
    GraphRelationshipDetailVO,
    KnowledgeExtractionResultVO,
    KnowledgeGraphDetailVO,
    KnowledgeGraphListVO,
    KnowledgePointDraftVO,
    KnowledgePointVO,
    KnowledgeRelationshipDraftVO,
    NodeNeighborsVO,
    NvlGraphDataVO,
    NvlNodePropertiesVO,
    NvlNodeVO,
    NvlRelationshipPropertiesVO,
    NvlRelationshipVO,
    TopNodesVO,
)
from graphedu.common.resource import AioS3Client
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient
from graphedu.mapper.education.graphrag_task import GraphRAGTaskMapper
from graphedu.mapper.education.knowledge_graph import KnowledgeGraphMapper
from graphedu.mapper.education.syllabus_graph import SyllabusGraphMapper

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_knowledge_graph_orm_to_list_vo(
    knowledge_graph_orm: EduKnowledgeGraph, course_name: str | None = None, course_cover: str | None = None
) -> KnowledgeGraphListVO:
    """将知识图谱 ORM 对象转换为 KnowledgeGraphListVO。

    Args:
        knowledge_graph_orm: 知识图谱 ORM 对象。
        course_name: 课程名称（可选）。
        course_cover: 课程封面URL（可选）。

    Returns:
        KnowledgeGraphListVO: 知识图谱列表项 VO。
    """
    return KnowledgeGraphListVO(
        graph_id=knowledge_graph_orm.graph_id,
        course_id=knowledge_graph_orm.course_id,
        graph_name=knowledge_graph_orm.graph_name,
        graph_database=knowledge_graph_orm.graph_database,
        version=knowledge_graph_orm.version,
        total_nodes=knowledge_graph_orm.total_nodes,
        total_relationships=knowledge_graph_orm.total_relationships,
        build_method=knowledge_graph_orm.build_method,
        status=knowledge_graph_orm.status,
        is_draft=knowledge_graph_orm.is_draft,
        task_status=knowledge_graph_orm.task_status,
        create_time=knowledge_graph_orm.create_time,
        last_extended=knowledge_graph_orm.last_extended,
        course_name=course_name,
        course_cover=course_cover,
    )


def _convert_knowledge_graph_orm_to_detail_vo(
    knowledge_graph_orm: EduKnowledgeGraph, course_orm: EduCourse | None = None
) -> KnowledgeGraphDetailVO:
    """将知识图谱 ORM 对象转换为 KnowledgeGraphDetailVO。

    Args:
        knowledge_graph_orm: 知识图谱 ORM 对象。
        course_orm: 课程 ORM 对象（可选）。

    Returns:
        KnowledgeGraphDetailVO: 知识图谱详细信息 VO。
    """
    course_name = course_orm.course_name if course_orm else None

    return KnowledgeGraphDetailVO(
        graph_id=knowledge_graph_orm.graph_id,
        course_id=knowledge_graph_orm.course_id,
        graph_name=knowledge_graph_orm.graph_name,
        graph_database=knowledge_graph_orm.graph_database,
        version=knowledge_graph_orm.version,
        description=knowledge_graph_orm.description,
        total_nodes=knowledge_graph_orm.total_nodes,
        total_relationships=knowledge_graph_orm.total_relationships,
        node_type_stats=knowledge_graph_orm.node_type_stats,
        relationship_type_stats=knowledge_graph_orm.relationship_type_stats,
        average_degree=float(knowledge_graph_orm.average_degree) if knowledge_graph_orm.average_degree else None,
        connectivity_score=(
            float(knowledge_graph_orm.connectivity_score) if knowledge_graph_orm.connectivity_score else None
        ),
        build_method=knowledge_graph_orm.build_method,
        build_info=knowledge_graph_orm.build_info,
        last_extended=knowledge_graph_orm.last_extended,
        status=knowledge_graph_orm.status,
        is_draft=knowledge_graph_orm.is_draft,
        task_status=knowledge_graph_orm.task_status,
        create_by=knowledge_graph_orm.create_by,
        create_time=knowledge_graph_orm.create_time,
        update_by=knowledge_graph_orm.update_by,
        update_time=knowledge_graph_orm.update_time,
        course_name=course_name,
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_graph_name_exists(course_id: int, graph_name: str, query_db: AsyncSession) -> bool:
    """校验知识图谱名称是否存在。

    Args:
        course_id: 课程ID。
        graph_name: 图谱名称。
        query_db: 数据库会话。

    Returns:
        bool: 图谱名称是否存在。
    """
    return await KnowledgeGraphMapper.is_graph_name_exists_for_course(course_id, graph_name, query_db)


async def _check_graph_name_unique_for_update(
    graph_id: int, course_id: int, graph_name: str, query_db: AsyncSession
) -> bool:
    """校验图谱名称是否唯一（编辑时用）。

    Args:
        graph_id: 知识图谱 ID。
        course_id: 课程ID。
        graph_name: 图谱名称。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在）。
    """
    if not graph_name:
        return False
    existing_graph = await KnowledgeGraphMapper.get_knowledge_graph_by_name_for_unique_check(
        course_id, graph_name, query_db
    )
    return existing_graph is not None and existing_graph.graph_id != graph_id


# ============================================================================
# KnowledgeGraphService 类
# ============================================================================


class KnowledgeGraphService:
    """知识图谱管理服务类

    提供知识图谱的增删改查功能。
    """

    @staticmethod
    async def add_knowledge_graph(
        query_db: AsyncSession, graph_data: KnowledgeGraphCreateDTO, current_user: CurrentUser | None
    ) -> KnowledgeGraphDetailVO:
        """新增知识图谱信息。

        Args:
            query_db: 数据库会话。
            graph_data: 新增知识图谱 DTO。
            current_user: 当前登录用户。

        Returns:
            KnowledgeGraphDetailVO: 创建成功的知识图谱 VO。

        Raises:
            KnowledgeGraphCourseNotFoundException: 对应的课程不存在。
            KnowledgeGraphNameAlreadyExistsException: 图谱名称已存在。
        """
        # 1. 校验课程是否存在
        if not await KnowledgeGraphMapper.is_course_exists(graph_data.course_id, query_db):
            raise KnowledgeGraphCourseNotFoundException(course_id=graph_data.course_id)

        # 2. 校验图谱名称唯一性（同一课程下）
        if await _check_graph_name_exists(graph_data.course_id, graph_data.graph_name, query_db):
            raise KnowledgeGraphNameAlreadyExistsException(graph_name=graph_data.graph_name)

        # 3. DTO → ORM
        new_graph = EduKnowledgeGraph(
            **graph_data.model_dump(),
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
            create_time=datetime.now(),
            total_nodes=0,
            total_relationships=0,
        )

        # 4. 新增知识图谱
        await KnowledgeGraphMapper.add_knowledge_graph(new_graph, query_db)

        logger.info(f"新增知识图谱成功: {graph_data.graph_name}")

        # 5. 返回创建后的知识图谱 VO
        course_orm = await KnowledgeGraphMapper.get_course_by_id(graph_data.course_id, query_db)
        return _convert_knowledge_graph_orm_to_detail_vo(new_graph, course_orm)

    @staticmethod
    async def update_knowledge_graph(
        query_db: AsyncSession, graph_data: KnowledgeGraphUpdateDTO, current_user: CurrentUser
    ) -> KnowledgeGraphDetailVO:
        """更新知识图谱信息。

        Args:
            query_db: 数据库会话。
            graph_data: 更新知识图谱 DTO。
            current_user: 当前登录用户。

        Returns:
            KnowledgeGraphDetailVO: 更新后的知识图谱 VO.

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
            KnowledgeGraphNameAlreadyExistsException: 图谱名称已存在。
        """
        # 1. 获取目标知识图谱
        target_graph = await KnowledgeGraphMapper.get_by_id(graph_data.graph_id, query_db)
        if target_graph is None:
            raise KnowledgeGraphNotFoundException(graph_id=graph_data.graph_id)

        # 2. 如果更新了课程，校验课程是否存在
        if (
            graph_data.course_id is not None
            and graph_data.course_id != target_graph.course_id
            and not await KnowledgeGraphMapper.is_course_exists(graph_data.course_id, query_db)
        ):
            raise KnowledgeGraphCourseNotFoundException(course_id=graph_data.course_id)

        # 3. 唯一性校验（使用目标知识图谱的数据进行对比）
        course_id_to_check = graph_data.course_id if graph_data.course_id is not None else target_graph.course_id
        if (
            graph_data.graph_name is not None
            and graph_data.graph_name != target_graph.graph_name
            and await _check_graph_name_unique_for_update(
                graph_data.graph_id, course_id_to_check, graph_data.graph_name, query_db
            )
        ):
            raise KnowledgeGraphNameAlreadyExistsException(graph_name=graph_data.graph_name)

        # 4. 更新目标知识图谱
        update_data = graph_data.model_dump(exclude_unset=True, exclude={"graph_id"})
        for field, value in update_data.items():
            setattr(target_graph, field, value)

        target_graph.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_graph.update_time = datetime.now()

        await KnowledgeGraphMapper.update(target_graph, query_db)

        # 获取关联课程
        course_orm = await KnowledgeGraphMapper.get_course_by_id(target_graph.course_id, query_db)

        # 5. 返回更新后的知识图谱 VO
        return _convert_knowledge_graph_orm_to_detail_vo(target_graph, course_orm)

    @staticmethod
    async def list_knowledge_graph(
        query_db: AsyncSession, query_object: KnowledgeGraphQueryDTO
    ) -> PageResponse[KnowledgeGraphListVO]:
        """获取知识图谱列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[KnowledgeGraphListVO]: 分页结果。
        """
        rows, total = await KnowledgeGraphMapper.get_knowledge_graph_list(query_db, query_object)

        # 将 ORM 对象转换为 KnowledgeGraphListVO
        graph_list = []
        for row in rows:
            graph_orm = row[0]
            course_orm = row[1]
            course_name = course_orm.course_name if course_orm else None
            course_cover = str(course_orm.cover_file_id) if course_orm and course_orm.cover_file_id else None
            graph_list.append(_convert_knowledge_graph_orm_to_list_vo(graph_orm, course_name, course_cover))

        return PageResponse(rows=graph_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def delete_knowledge_graph(
        query_db: AsyncSession, graph_id_list: list[int], current_user: CurrentUser
    ) -> None:
        """删除知识图谱信息（批量）。

        Args:
            query_db: 数据库会话。
            graph_id_list: 知识图谱 ID 列表。
            current_user: 当前用户。

        Raises:
            KnowledgeGraphIdListEmptyException: 知识图谱 ID 列表为空。
        """
        if not graph_id_list:
            raise KnowledgeGraphIdListEmptyException

        for graph_id in graph_id_list:
            graph = await KnowledgeGraphMapper.get_by_id(graph_id, query_db)
            if graph:
                # 软删除知识图谱（令 status 为 2）
                graph.status = SystemConstants.Status.DELETED
                graph.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                graph.update_time = datetime.now()
                await KnowledgeGraphMapper.update(graph, query_db)

        logger.info(f"删除知识图谱成功: {graph_id_list}")

    @staticmethod
    async def change_knowledge_graph_status(
        query_db: AsyncSession, graph_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改知识图谱状态。

        Args:
            query_db: 数据库会话。
            graph_id: 知识图谱 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        graph = await KnowledgeGraphMapper.get_by_id(graph_id, query_db)
        if not graph:
            raise KnowledgeGraphNotFoundException(graph_id=graph_id)

        graph.status = status
        graph.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        graph.update_time = datetime.now()
        await KnowledgeGraphMapper.update(graph, query_db)
        logger.info(f"修改知识图谱状态成功: {graph_id}")

    @staticmethod
    async def get_knowledge_graph_detail(query_db: AsyncSession, graph_id: int) -> KnowledgeGraphDetailVO | None:
        """获取知识图谱详细信息。

        Args:
            query_db: 数据库会话。
            graph_id: 知识图谱 ID。

        Returns:
            KnowledgeGraphDetailVO | None: 知识图谱详细信息 VO。
        """
        graph = await KnowledgeGraphMapper.get_by_id_with_course(graph_id, query_db)
        if not graph[0]:
            return None

        graph_orm, course_orm = graph
        detail_vo = _convert_knowledge_graph_orm_to_detail_vo(graph_orm, course_orm)

        # 注入 Celery 实时进度（仅 pending/processing 状态时查询）
        if detail_vo and detail_vo.task_status in ("pending", "processing"):
            from celery.result import AsyncResult

            from graphedu.workers.celery import celery_app

            celery_task = AsyncResult(str(graph_id), app=celery_app)
            if celery_task.state == "PROGRESS" and isinstance(celery_task.info, dict):
                bi = dict(detail_vo.build_info or {})
                bi["progress_percent"] = celery_task.info.get("percent", 0)
                bi["progress_step"] = celery_task.info.get("step", "")
                detail_vo.build_info = bi

        return detail_vo

    # =========================================================================
    # Phase 4 — AGE 图谱操作（编排 SyllabusGraphService + Mapper）
    # =========================================================================

    @staticmethod
    async def _get_graph_or_raise(graph_id: int, query_db: AsyncSession) -> EduKnowledgeGraph:
        """根据图谱 ID 查询 ORM 对象，不存在则抛出异常。

        Args:
            graph_id: 知识图谱 ID。
            query_db: 数据库会话。

        Returns:
            EduKnowledgeGraph: 知识图谱 ORM 对象。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        graph = await KnowledgeGraphMapper.get_by_id(graph_id, query_db)
        if not graph:
            raise KnowledgeGraphNotFoundException(graph_id=graph_id)
        return graph

    @staticmethod
    async def extract_knowledge_points(
        graph_id: int,
        extract_req: KnowledgeExtractionRequestDTO,
        query_db: AsyncSession,
        s3_client: AioS3Client,
    ) -> KnowledgeExtractionResultVO:
        """使用 LLM 从文档/提纲提取知识点草稿（未入库，需确认后保存）。

        支持三种模式：markdown（解析文档）、skeleton（教师提纲）、combined（合并）。

        Args:
            graph_id: 知识图谱 ID（用于校验图谱存在性）
            extract_req: 提取请求 DTO
            query_db: 数据库会话
            s3_client: S3 客户端

        Returns:
            KnowledgeExtractionResultVO: 提取结果（草稿，未持久化）。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.dependency_inference import DependencyInferenceService
        from graphedu.services.education.knowledge_extraction import KnowledgeExtractionService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)

        mode = extract_req.mode
        if mode == "markdown":
            extraction = await KnowledgeExtractionService.extract_from_markdown(
                extract_req.document_id, query_db, s3_client
            )
        elif mode == "skeleton":
            extraction = KnowledgeExtractionService.extract_from_skeleton(extract_req.skeleton_text or "")
        else:
            extraction = await KnowledgeExtractionService.extract_combined(
                extract_req.document_id, extract_req.skeleton_text or "", query_db, s3_client
            )

        titles = [p.title for p in extraction.points]
        dep_result = await DependencyInferenceService.infer_dependencies(titles)

        draft_points = [
            KnowledgePointDraftVO(
                title=p.title,
                description=p.description,
                importance=p.importance,
                confidence=p.confidence,
                source=p.source,
            )
            for p in extraction.points
        ]
        draft_rels = [
            KnowledgeRelationshipDraftVO(
                source_title=r.source_title,
                target_title=r.target_title,
                relation_type=r.relation_type,
                confidence=r.confidence,
            )
            for r in dep_result.relationships
        ]

        return KnowledgeExtractionResultVO(
            points=draft_points,
            relationships=draft_rels,
            mode=extraction.mode,
            total_points=len(draft_points),
            total_relationships=len(draft_rels),
        )

    @staticmethod
    async def save_extraction(
        graph_id: int,
        save_req: SaveExtractionRequestDTO,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
        current_user: CurrentUser | None = None,
    ) -> NvlGraphDataVO:
        """将教师审核确认后的知识点和关系批量写入图数据库，并更新图谱统计数据。

        Args:
            graph_id: 知识图谱 ID。
            save_req: 保存请求 DTO（含审核后的 points + relationships）。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端（用于 AGE 操作）
            current_user: 当前用户对象

        Returns:
            NvlGraphDataVO: 写入后的图谱 NVL 数据。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.dependency_inference import KnowledgeRelationshipBO
        from graphedu.services.education.knowledge_extraction import KnowledgePointBO
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        graph_orm = await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        course_id = graph_orm.course_id

        points_bo = [
            KnowledgePointBO(
                title=p.title,
                description=p.description,
                importance=p.importance,
                confidence=1.0,
                source="manual",
            )
            for p in save_req.points
        ]
        rels_bo = [
            KnowledgeRelationshipBO(
                source_title=r.source_title,
                target_title=r.target_title,
                relation_type=r.relation_type,
                confidence=r.confidence,
                description=r.description,
            )
            for r in save_req.relationships
        ]

        operator_id = (
            current_user.detail.user.user_id
            if current_user and current_user.detail and current_user.detail.user
            else None
        )
        stats = await SyllabusGraphService.save_graph_from_extraction(
            pg_client,
            course_id,
            points_bo,
            rels_bo,
            operator_id=operator_id,
            graph_id=graph_id,
        )

        # 更新图谱统计字段
        graph_orm.total_nodes = stats.node_count
        graph_orm.total_relationships = stats.rel_count
        await KnowledgeGraphMapper.update(graph_orm, query_db)

        return await SyllabusGraphService.get_graph_nvl_data(pg_client, course_id, graph_id)

    @staticmethod
    async def get_graph_nvl_data(
        graph_id: int,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> NvlGraphDataVO:
        """获取图谱 NVL 可视化格式数据（节点 + 关系）。

        Args:
            graph_id: 知识图谱 ID。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Returns:
            NvlGraphDataVO: NVL 可视化数据。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        graph_orm = await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        return await SyllabusGraphService.get_graph_nvl_data(pg_client, graph_orm.course_id, graph_id)

    @staticmethod
    async def search_graph_nodes(
        graph_id: int,
        keyword: str,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> list[KnowledgePointVO]:
        """按关键词搜索图谱中的知识点节点（标题模糊匹配）。

        Args:
            graph_id: 知识图谱 ID。
            keyword: 搜索关键词。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Returns:
            list[KnowledgePointVO]: 匹配的知识点列表。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        graph_orm = await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        nodes = await SyllabusGraphService.search_nodes(pg_client, graph_orm.course_id, keyword, graph_id=graph_id)
        return [KnowledgePointVO.model_validate(node.model_dump()) for node in nodes]

    @staticmethod
    async def create_graph_node(
        graph_id: int,
        node_data: KnowledgePointCreateDTO,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
        current_user: CurrentUser | None = None,
    ) -> KnowledgePointVO:
        """手动创建知识点节点。

        Args:
            graph_id: 知识图谱 ID。
            node_data: 节点创建 DTO。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。
            current_user: 当前用户对象（用于记录操作人）。

        Returns:
            KnowledgePointVO: 创建成功的知识点 VO。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        graph_orm = await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        operator_id = (
            current_user.detail.user.user_id
            if current_user and current_user.detail and current_user.detail.user
            else None
        )
        node = await SyllabusGraphService.create_knowledge_point(
            pg_client,
            course_id=graph_orm.course_id,
            title=node_data.title,
            description=node_data.description,
            importance=node_data.importance,
            source=node_data.source,
            create_by=operator_id,
            graph_id=graph_id,
        )
        return KnowledgePointVO.model_validate(node.model_dump())

    @staticmethod
    async def update_graph_node(
        graph_id: int,
        node_id: str,
        node_data: KnowledgePointUpdateDTO,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
        current_user: CurrentUser | None = None,
    ) -> None:
        """修改知识点节点属性。

        Args:
            graph_id: 知识图谱 ID（校验图谱存在性）。
            node_id: 节点 ID。
            node_data: 节点更新 DTO。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。
            current_user: 当前用户对象。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        operator_id = (
            current_user.detail.user.user_id
            if current_user and current_user.detail and current_user.detail.user
            else None
        )
        await SyllabusGraphService.update_knowledge_point(
            pg_client,
            node_id=node_id,
            title=node_data.title,
            description=node_data.description,
            importance=node_data.importance,
            update_by=operator_id,
        )

    @staticmethod
    async def delete_graph_node(
        graph_id: int,
        node_id: str,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> None:
        """删除知识点节点（级联删除关系）。

        Args:
            graph_id: 知识图谱 ID（校验图谱存在性）。
            node_id: 节点 ID。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        await SyllabusGraphService.delete_knowledge_point(pg_client, node_id)

    @staticmethod
    async def create_graph_relationship(
        graph_id: int,
        rel_data: KnowledgeRelationshipCreateDTO,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> GraphRelationshipCreatedVO:
        """在两个知识点之间创建关系（RELATED_TO / PRIOR_TO / SUBTOPIC_OF）。

        Args:
            graph_id: 知识图谱 ID（校验图谱存在性）。
            rel_data: 关系创建 DTO。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Returns:
            dict: 包含 rel_id 的字典。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        payload = KnowledgeRelationshipPayload.model_validate(
            {
                "from_node_id": rel_data.source_id,
                "to_node_id": rel_data.target_id,
                "type": rel_data.relation_type,
                "confidence": rel_data.confidence,
                "description": rel_data.description,
                "graph_id": graph_id,
            }
        )
        rel_id = await SyllabusGraphService.create_relationship(
            pg_client,
            source_id=payload.from_node_id,
            target_id=payload.to_node_id,
            relation_type=payload.type,
            confidence=payload.confidence or 1.0,
            description=payload.description,
            graph_id=payload.graph_id,
        )
        return GraphRelationshipCreatedVO(rel_id=rel_id)

    @staticmethod
    async def delete_graph_relationship(
        graph_id: int,
        rel_id: str,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> None:
        """删除图谱关系。

        Args:
            graph_id: 知识图谱 ID（校验图谱存在性）。
            rel_id: 关系 ID。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        await SyllabusGraphService.delete_relationship(pg_client, rel_id, graph_id)

    @staticmethod
    async def update_graph_relationship(
        graph_id: int,
        rel_id: str,
        rel_data: KnowledgeRelationshipUpdateDTO,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> GraphRelationshipDetailVO:
        """更新图谱关系属性，不允许变更源节点与目标节点。"""
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        result = await SyllabusGraphService.update_relationship(
            pg_client=pg_client,
            rel_id=rel_id,
            relation_type=rel_data.relation_type,
            confidence=rel_data.confidence,
            description=rel_data.description,
            graph_id=graph_id,
        )
        return GraphRelationshipDetailVO.model_validate(
            {
                "rel_id": result.id,
                "rel_type": result.type,
                "from_node_id": result.from_node_id,
                "to_node_id": result.to_node_id,
                "confidence": result.confidence,
                "description": result.description,
            }
        )

    @staticmethod
    async def get_graph_relationship(
        graph_id: int,
        rel_id: str,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> GraphRelationshipDetailVO:
        """查询图谱关系详情。

        Args:
            graph_id: 知识图谱 ID（校验图谱存在性）。
            rel_id: 关系 ID。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
            KnowledgeRelationshipNotFoundException: 关系不存在。
        """
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        result = await SyllabusGraphService.get_relationship_by_id(pg_client, rel_id, graph_id)
        return GraphRelationshipDetailVO.model_validate(
            {
                "rel_id": result.id,
                "rel_type": result.type,
                "from_node_id": result.from_node_id,
                "to_node_id": result.to_node_id,
                "confidence": result.confidence,
                "description": result.description,
            }
        )

    @staticmethod
    async def get_graph_top_nodes(
        graph_id: int,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
        limit: int = 10,
    ) -> TopNodesVO:
        """获取知识图谱的顶层节点（入度为0的节点）及节点间关系。

        Args:
            graph_id: 知识图谱 ID。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。
            limit: 返回节点数量限制。

        Returns:
            TopNodesVO: 顶层节点列表 VO。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        graph_orm = await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        nodes, relationships = await SyllabusGraphMapper.get_top_nodes(pg_client, graph_orm.course_id, limit, graph_id)

        # 转换为 NvlNodeVO
        nvl_nodes = [
            NvlNodeVO(
                id=node.id,
                labels=["KnowledgePoint"],
                properties=NvlNodePropertiesVO.model_validate(
                    {
                        "title": node.title,
                        "description": node.description,
                        "importance": node.importance,
                        "source": node.source,
                    }
                ),
            ).model_dump(by_alias=True)
            for node in nodes
        ]

        # 转换为 NvlRelationshipVO
        nvl_relationships = [
            NvlRelationshipVO(
                id=rel.id,
                type=rel.type,
                from_=rel.from_node_id,
                to=rel.to_node_id,
                properties=NvlRelationshipPropertiesVO.model_validate(
                    {
                        "confidence": rel.confidence,
                        "description": rel.description,
                    }
                ),
            ).model_dump(by_alias=True)
            for rel in relationships
        ]

        return TopNodesVO(nodes=nvl_nodes, relationships=nvl_relationships, total=len(nvl_nodes))

    @staticmethod
    async def get_node_neighbors(
        graph_id: int,
        node_id: str,
        query_dto: NodeNeighborsQueryDTO,
        query_db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> NodeNeighborsVO:
        """获取指定节点的邻居节点和关系。

        Args:
            graph_id: 知识图谱 ID（校验图谱存在性）。
            node_id: 节点 ID。
            query_dto: 查询参数 DTO。
            query_db: 数据库会话。
            pg_client: PostgreSQL 客户端。

        Returns:
            NodeNeighborsVO: 节点邻居查询结果 VO。

        Raises:
            KnowledgeGraphNotFoundException: 知识图谱不存在。
        """
        await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)

        neighbor_nodes, relationships = await SyllabusGraphMapper.get_node_neighbors(
            pg_client,
            node_id,
            depth=query_dto.depth,
            limit=query_dto.limit,
            direction=query_dto.direction,
        )

        # 转换为 NvlNodeVO
        nvl_nodes = [
            NvlNodeVO(
                id=node.id,
                labels=["KnowledgePoint"],
                properties=NvlNodePropertiesVO.model_validate(
                    {
                        "title": node.title,
                        "description": node.description,
                        "importance": node.importance,
                        "source": node.source,
                    }
                ),
            ).model_dump(by_alias=True)
            for node in neighbor_nodes
        ]

        # 转换为 NvlRelationshipVO
        nvl_relationships = [
            NvlRelationshipVO(
                id=rel.id,
                type=rel.type,
                from_=rel.from_node_id,
                to=rel.to_node_id,
                properties=NvlRelationshipPropertiesVO.model_validate(
                    {
                        "confidence": rel.confidence,
                        "description": rel.description,
                    }
                ),
            ).model_dump(by_alias=True)
            for rel in relationships
        ]

        return NodeNeighborsVO(
            center_node_id=node_id,
            nodes=nvl_nodes,
            relationships=nvl_relationships,
            depth=query_dto.depth,
            total_nodes=len(nvl_nodes),
            total_relationships=len(nvl_relationships),
        )

    @staticmethod
    async def submit_auto_generate(
        dto: AutoGenerateRequestDTO,
        query_db: AsyncSession,
        current_user: CurrentUser,
    ) -> AutoGenerateSubmitVO:
        """提交异步自动生成知识图谱任务。

        先创建 edu_knowledge_graph 记录（task_status=pending），再派发 Celery 任务。
        重量级操作（GraphRAG 调用、AGE 写入）由 Celery Worker 异步完成。
        """
        # 1. 前置校验
        if not await KnowledgeGraphMapper.is_course_exists(dto.course_id, query_db):
            raise KnowledgeGraphCourseNotFoundException(course_id=dto.course_id)
        course = await KnowledgeGraphMapper.get_course_by_id(dto.course_id, query_db)
        if course is None:
            raise KnowledgeGraphCourseNotFoundException(course_id=dto.course_id)

        enabled_task = await GraphRAGTaskMapper.get_enabled_task_for_course(dto.course_id, query_db)
        if enabled_task is None:
            raise GraphRAGIndexNotBuiltException(course_id=dto.course_id)

        # 2. 创建图谱记录（pending 状态）
        graph_name = dto.graph_name or f"{course.course_name} - 可视化知识图谱"
        new_graph = EduKnowledgeGraph(
            course_id=dto.course_id,
            graph_name=graph_name,
            graph_database="edu_knowledge_graph",
            build_method="graphrag_assisted",
            build_info={"auto_generated": True},
            is_draft="Y",
            task_status="pending",
            status=SystemConstants.Status.NORMAL,
            create_by=(
                current_user.detail.user.user_id
                if current_user and current_user.detail and current_user.detail.user
                else None
            ),
        )
        new_graph = await KnowledgeGraphMapper.add_knowledge_graph(new_graph, query_db)
        await query_db.flush()

        # 3. 派发 Celery 异步任务
        from graphedu.workers.knowledge_graph_tasks import auto_generate_knowledge_graph

        user_id = (
            current_user.detail.user.user_id
            if current_user and current_user.detail and current_user.detail.user
            else None
        )
        auto_generate_knowledge_graph.apply_async(
            kwargs={
                "course_id": dto.course_id,
                "graph_id": new_graph.graph_id,
                "graph_name": graph_name,
                "user_id": user_id,
            },
            task_id=str(new_graph.graph_id),
        )

        logger.info(
            "已提交异步知识图谱生成任务: graph_id=%d, course_id=%d",
            new_graph.graph_id,
            dto.course_id,
        )

        return AutoGenerateSubmitVO(
            graph_id=new_graph.graph_id,
            task_status="pending",
        )

    @staticmethod
    async def confirm_graph(
        graph_id: int,
        query_db: AsyncSession,
        current_user: CurrentUser,
    ) -> KnowledgeGraphDetailVO:
        """将草稿知识图谱转正（is_draft='Y' -> 'N'）。"""
        from graphedu.common.exceptions.services.education.knowledge_graph import (
            KnowledgeGraphChangeStatusFailedException,
        )

        graph = await KnowledgeGraphService._get_graph_or_raise(graph_id, query_db)
        if graph.is_draft != "Y":
            raise KnowledgeGraphChangeStatusFailedException(message="该知识图谱不是草稿状态")

        graph.is_draft = "N"
        graph.update_by = current_user.detail.user.user_id
        await query_db.flush()

        course_orm = await KnowledgeGraphMapper.get_course_by_id(course_id=graph.course_id, db_session=query_db)

        return _convert_knowledge_graph_orm_to_detail_vo(graph, course_orm)
