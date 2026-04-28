"""定时任务管理 Mapper 层

负责定时任务数据的访问操作，包括任务信息的增删改查、
任务执行日志的查询等功能。
"""

from collections.abc import Sequence

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.toolv2.job import JobLogQueryDTO, JobQueryDTO
from graphedu.common.models.orm.system import SysJob, SysJobLog


class JobMapper:
    """定时任务数据访问层

    提供定时任务信息的 CRUD 操作以及任务执行日志等相关查询功能。
    """

    @staticmethod
    async def add_job(job_info: SysJob, db_session: AsyncSession):
        """添加定时任务

        :param db_session: orm对象
        :param job_info: 任务信息
        :return: 任务对象
        """
        db_session.add(job_info)
        await db_session.flush()
        return job_info

    @staticmethod
    async def get_by_id(job_id: int, db_session: AsyncSession) -> SysJob | None:
        """根据任务ID查询任务信息

        :param db_session: orm对象
        :param job_id: 任务ID
        :return: 任务对象
        """
        stmt = select(SysJob).where(SysJob.job_id == job_id)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_name(job_name: str, db_session: AsyncSession) -> SysJob | None:
        """根据任务名称查询任务信息

        :param db_session: orm对象
        :param job_name: 任务名称
        :return: 任务对象
        """
        stmt = select(SysJob).where(SysJob.job_name == job_name)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_job_list(
        db: AsyncSession, query_object: JobQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[SysJob], int]:
        """根据查询参数获取任务列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为任务列表，total为总数
        """
        # 构建基础查询条件
        conditions = []

        if query_object.job_name:
            conditions.append(SysJob.job_name.like(f"%{query_object.job_name}%"))
        if query_object.job_group:
            conditions.append(SysJob.job_group == query_object.job_group)
        if query_object.status:
            conditions.append(SysJob.status == query_object.status)
        if query_object.job_executor:
            conditions.append(SysJob.job_executor == query_object.job_executor)

        # 构建主查询
        query = select(SysJob).where(and_(*conditions)).order_by(SysJob.job_id)

        # 获取总数
        count_query = select(func.count(SysJob.job_id)).select_from(SysJob).where(and_(*conditions))
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
    async def update(job_info: SysJob, db_session: AsyncSession) -> None:
        """更新任务信息

        :param db_session: orm对象
        :param job_info: 任务信息（PO对象或ORM对象）
        :return: None
        """
        await db_session.merge(job_info)
        await db_session.flush()

    @staticmethod
    async def delete_job(job_ids: list[int], db_session: AsyncSession) -> None:
        """删除任务（批量）

        :param db_session: orm对象
        :param job_ids: 任务ID列表
        :return: None
        """
        stmt = delete(SysJob).where(SysJob.job_id.in_(job_ids))
        await db_session.execute(stmt)

    @staticmethod
    async def get_job_list_for_scheduler(db_session: AsyncSession) -> Sequence[SysJob]:
        """获取所有启用的任务（供调度器初始化）

        :param db_session: orm对象
        :return: 启用的任务列表
        """
        stmt = select(SysJob).where(SysJob.status == SystemConstants.Status.NORMAL).order_by(SysJob.job_id)
        result = await db_session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def is_job_name_exists(job_name: str, query_db: AsyncSession, exclude_job_id: int = None) -> bool:
        """校验任务名称是否存在

        :param query_db: orm对象
        :param job_name: 任务名称
        :param exclude_job_id: 排除的任务ID（用于更新场景）
        :return: 是否存在
        """
        conditions = [SysJob.job_name == job_name]
        if exclude_job_id is not None:
            conditions.append(SysJob.job_id != exclude_job_id)

        stmt = select(SysJob).where(and_(*conditions))
        job = (await query_db.execute(stmt)).scalars().first()
        return job is not None


class JobLogMapper:
    """任务执行日志数据访问层

    提供任务执行日志的查询、删除等功能。
    """

    @staticmethod
    async def add_log(job_log: SysJobLog, db_session: AsyncSession) -> None:
        """新增任务执行日志

        :param db_session: orm对象
        :param job_log: 日志对象
        :return: None
        """
        db_session.add(job_log)
        await db_session.flush()

    @staticmethod
    async def get_by_id(job_log_id: int, db_session: AsyncSession) -> SysJobLog | None:
        """根据日志ID查询日志信息

        :param db_session: orm对象
        :param job_log_id: 日志ID
        :return: 日志对象
        """
        stmt = select(SysJobLog).where(SysJobLog.job_log_id == job_log_id)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_job_log_list(
        db: AsyncSession, query_object: JobLogQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[SysJobLog], int]:
        """根据查询参数获取任务日志列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为日志列表，total为总数
        """
        # 构建基础查询条件
        conditions = []

        if query_object.job_id:
            conditions.append(SysJobLog.job_id == query_object.job_id)
        if query_object.job_name:
            conditions.append(SysJobLog.job_name.like(f"%{query_object.job_name}%"))
        if query_object.job_group:
            conditions.append(SysJobLog.job_group == query_object.job_group)
        if query_object.status:
            conditions.append(SysJobLog.status == query_object.status)

        # 构建主查询
        query = select(SysJobLog).where(and_(*conditions)).order_by(SysJobLog.create_time.desc())

        # 获取总数
        count_query = select(func.count(SysJobLog.job_log_id)).select_from(SysJobLog).where(and_(*conditions))
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
    async def delete_job_log(job_log_ids: list[int], db_session: AsyncSession) -> None:
        """删除任务日志（批量）

        :param db_session: orm对象
        :param job_log_ids: 日志ID列表
        :return: None
        """
        stmt = delete(SysJobLog).where(SysJobLog.job_log_id.in_(job_log_ids))
        await db_session.execute(stmt)

    @staticmethod
    async def clear_job_log(db_session: AsyncSession) -> None:
        """清空所有任务日志

        :param db_session: orm对象
        :return: None
        """
        stmt = delete(SysJobLog)
        await db_session.execute(stmt)

    @staticmethod
    async def clear_job_log_by_job_id(job_id: int, db_session: AsyncSession) -> None:
        """清空指定任务的所有日志

        :param db_session: orm对象
        :param job_id: 任务ID
        :return: None
        """
        stmt = delete(SysJobLog).where(SysJobLog.job_id == job_id)
        await db_session.execute(stmt)
