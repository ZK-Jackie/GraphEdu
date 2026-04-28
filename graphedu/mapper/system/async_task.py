"""通用异步任务 Mapper 层

负责异步任务数据的访问操作，包括任务的增删改查、状态更新等。
"""

from collections.abc import Sequence

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.systemv2.async_task import AsyncTaskQueryDTO
from graphedu.common.models.orm.system import SysAsyncTask


class AsyncTaskMapper:
    """通用异步任务数据访问层。"""

    @staticmethod
    async def insert(task: SysAsyncTask, db: AsyncSession) -> SysAsyncTask:
        """插入任务记录。"""
        db.add(task)
        await db.flush()
        return task

    @staticmethod
    async def get_by_id(task_id: int, db: AsyncSession) -> SysAsyncTask | None:
        """根据任务ID查询任务。"""
        stmt = select(SysAsyncTask).where(SysAsyncTask.task_id == task_id)
        return (await db.execute(stmt)).scalars().first()

    @staticmethod
    async def update(task: SysAsyncTask, db: AsyncSession) -> SysAsyncTask:
        """更新任务记录。"""
        await db.flush()
        return task

    @staticmethod
    async def update_fields(task_id: int, db: AsyncSession, **kwargs) -> None:
        """按字段更新任务（不加载完整 ORM 对象）。"""
        if not kwargs:
            return
        stmt = update(SysAsyncTask).where(SysAsyncTask.task_id == task_id).values(**kwargs)
        await db.execute(stmt)
        await db.flush()

    @staticmethod
    async def list_by_query(
        query: AsyncTaskQueryDTO,
        db: AsyncSession,
        user_id: int | None = None,
    ) -> tuple[Sequence[SysAsyncTask], int]:
        """分页查询异步任务列表。

        Args:
            query: 查询条件
            db: 数据库会话
            user_id: 可选，按用户过滤

        Returns:
            (rows, total)
        """
        conditions = [SysAsyncTask.status == "0"]

        if query.task_type:
            conditions.append(SysAsyncTask.task_type == query.task_type)
        if query.task_status:
            conditions.append(SysAsyncTask.task_status == query.task_status)
        if query.begin_time:
            conditions.append(SysAsyncTask.create_time >= query.begin_time)
        if query.end_time:
            conditions.append(SysAsyncTask.create_time <= query.end_time)
        if user_id is not None:
            conditions.append(SysAsyncTask.user_id == user_id)

        where = and_(*conditions)

        # 总数
        count_stmt = select(func.count()).select_from(SysAsyncTask).where(where)
        total = (await db.execute(count_stmt)).scalar() or 0

        # 分页数据
        page_num = query.page or 1
        page_size = query.size or 10
        data_stmt = (
            select(SysAsyncTask)
            .where(where)
            .order_by(SysAsyncTask.create_time.desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        rows = (await db.execute(data_stmt)).scalars().all()

        return rows, total
