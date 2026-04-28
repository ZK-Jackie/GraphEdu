"""知识图谱管理 Mapper 层

负责知识图谱数据的访问操作，包括知识图谱信息的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto import KnowledgeGraphQueryDTO
from graphedu.common.models.orm.education import EduCourse, EduKnowledgeGraph


class KnowledgeGraphMapper:
    """知识图谱数据访问层

    提供知识图谱信息的 CRUD 操作。
    """

    @staticmethod
    async def add_knowledge_graph(
        knowledge_graph_info: EduKnowledgeGraph, db_session: AsyncSession
    ) -> EduKnowledgeGraph:
        """添加知识图谱

        :param db_session: 数据库会话
        :param knowledge_graph_info: 知识图谱信息
        :return: 知识图谱对象
        """
        db_session.add(knowledge_graph_info)
        await db_session.flush()
        return knowledge_graph_info

    @staticmethod
    async def get_by_id(graph_id: int, db_session: AsyncSession) -> EduKnowledgeGraph | None:
        """根据图谱ID查询知识图谱信息

        :param db_session: 数据库会话
        :param graph_id: 图谱ID
        :return: 知识图谱对象
        """
        stmt = select(EduKnowledgeGraph).where(
            EduKnowledgeGraph.graph_id == graph_id, EduKnowledgeGraph.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_id_with_course(
        graph_id: int, db_session: AsyncSession
    ) -> tuple[EduKnowledgeGraph | None, EduCourse | None]:
        """根据图谱ID查询知识图谱信息（包含关联课程）

        :param db_session: 数据库会话
        :param graph_id: 图谱ID
        :return: (EduKnowledgeGraph, EduCourse | None) 元组
        """
        stmt = (
            select(EduKnowledgeGraph, EduCourse)
            .outerjoin(
                EduCourse,
                and_(
                    EduKnowledgeGraph.course_id == EduCourse.course_id,
                    EduCourse.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(
                EduKnowledgeGraph.graph_id == graph_id,
                EduKnowledgeGraph.status != SystemConstants.Status.DELETED,
            )
        )
        row = (await db_session.execute(stmt)).first()
        if row is None:
            return None, None
        return row[0], row[1]

    @staticmethod
    async def is_graph_name_exists_for_course(course_id: int, graph_name: str, db_session: AsyncSession) -> bool:
        """校验同一课程下的图谱名称是否存在

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :param graph_name: 图谱名称
        :return: 是否存在
        """
        stmt = select(EduKnowledgeGraph).where(
            EduKnowledgeGraph.status != SystemConstants.Status.DELETED,
            EduKnowledgeGraph.course_id == course_id,
            EduKnowledgeGraph.graph_name == graph_name,
        )
        graph = (await db_session.execute(stmt)).scalars().first()
        return graph is not None

    @staticmethod
    async def get_knowledge_graph_by_name_for_unique_check(
        course_id: int, graph_name: str, db_session: AsyncSession
    ) -> EduKnowledgeGraph | None:
        """根据课程ID和图谱名称查询知识图谱（用于唯一性校验）

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :param graph_name: 图谱名称
        :return: 知识图谱对象
        """
        stmt = select(EduKnowledgeGraph).where(
            EduKnowledgeGraph.status != SystemConstants.Status.DELETED,
            EduKnowledgeGraph.course_id == course_id,
            EduKnowledgeGraph.graph_name == graph_name,
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_knowledge_graph_list(
        db: AsyncSession, query_object: KnowledgeGraphQueryDTO
    ) -> tuple[Sequence[tuple[EduKnowledgeGraph, EduCourse | None]], int]:
        """根据查询参数获取知识图谱列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :return: (rows, total) 元组，rows为知识图谱列表，total为总数
        """
        # 构建基础查询条件
        base_conditions = [EduKnowledgeGraph.status != SystemConstants.Status.DELETED]

        if query_object.graph_id is not None:
            base_conditions.append(EduKnowledgeGraph.graph_id == query_object.graph_id)
        if query_object.course_id is not None:
            base_conditions.append(EduKnowledgeGraph.course_id == query_object.course_id)
        if query_object.graph_name:
            base_conditions.append(EduKnowledgeGraph.graph_name.like(f"%{query_object.graph_name}%"))
        if query_object.graph_database:
            base_conditions.append(EduKnowledgeGraph.graph_database.like(f"%{query_object.graph_database}%"))
        if query_object.build_method:
            base_conditions.append(EduKnowledgeGraph.build_method == query_object.build_method)
        if query_object.is_draft:
            base_conditions.append(EduKnowledgeGraph.is_draft == query_object.is_draft)
        if query_object.status:
            base_conditions.append(EduKnowledgeGraph.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduKnowledgeGraph.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建主查询（关联 edu_course 表获取课程信息）
        query = (
            select(EduKnowledgeGraph, EduCourse)
            .outerjoin(
                EduCourse,
                and_(
                    EduKnowledgeGraph.course_id == EduCourse.course_id,
                    EduCourse.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(and_(*base_conditions))
            .order_by(EduKnowledgeGraph.graph_id.desc())
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count(func.distinct(EduKnowledgeGraph.graph_id)))
            .select_from(EduKnowledgeGraph)
            .outerjoin(
                EduCourse,
                and_(
                    EduKnowledgeGraph.course_id == EduCourse.course_id,
                    EduCourse.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(and_(*base_conditions))
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页（当提供了 page 和 size 参数时才分页）
        if query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.all()

        return rows, total

    @staticmethod
    async def update(knowledge_graph: EduKnowledgeGraph, query_db: AsyncSession) -> None:
        """更新知识图谱信息

        :param query_db: 数据库会话
        :param knowledge_graph: 知识图谱信息
        :return: None
        """
        await query_db.merge(knowledge_graph)
        await query_db.flush()

    @staticmethod
    async def is_course_exists(course_id: int, db_session: AsyncSession) -> bool:
        """校验课程是否存在

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 是否存在
        """
        stmt = select(EduCourse).where(
            EduCourse.course_id == course_id, EduCourse.status != SystemConstants.Status.DELETED
        )
        course = (await db_session.execute(stmt)).scalars().first()
        return course is not None

    @staticmethod
    async def get_course_by_id(course_id: int, db_session: AsyncSession) -> EduCourse | None:
        """根据课程ID查询课程信息

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 课程对象
        """
        stmt = select(EduCourse).where(
            EduCourse.course_id == course_id, EduCourse.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()
