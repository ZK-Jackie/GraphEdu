"""日志管理 Mapper 层

职责：
1. 只处理ORM数据或基础数据类型（dict）
2. 不引入PO、DTO、VO等业务模型
3. 提供纯粹的数据访问接口
"""

from collections.abc import Sequence
import logging

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.systemv2.log import LoginLogQueryDTO, OperLogQueryDTO
from graphedu.common.models.orm.system import SysLogininfor, SysOperLog

logger = logging.getLogger(__name__)


class OperLogMapper:
    """操作日志数据访问层"""

    @staticmethod
    async def get_log_list(query_params: OperLogQueryDTO, db_session: AsyncSession) -> tuple[Sequence[SysOperLog], int]:
        """获取操作日志列表

        :param query_params: 查询参数DTO
        :param db_session: 数据库会话
        :return: 操作日志列表或分页结果
        """
        # 构建查询语句
        stmt = select(SysOperLog)

        # 添加过滤条件
        if query_params.title:
            stmt = stmt.where(SysOperLog.title.like(f"%{query_params.title}%"))
        if query_params.oper_name:
            stmt = stmt.where(SysOperLog.oper_name.like(f"%{query_params.oper_name}%"))
        if query_params.oper_ip:
            stmt = stmt.where(SysOperLog.oper_ip.like(f"%{query_params.oper_ip}%"))
        if query_params.business_type is not None:
            stmt = stmt.where(SysOperLog.business_type == query_params.business_type)
        if query_params.status is not None:
            stmt = stmt.where(SysOperLog.status == query_params.status)
        if query_params.begin_time and query_params.end_time:
            begin_datetime = query_params.begin_time.replace(hour=0, minute=0, second=0)
            end_datetime = query_params.end_time.replace(hour=23, minute=59, second=59)
            stmt = stmt.where(SysOperLog.oper_time.between(begin_datetime, end_datetime))

        # 获取总数
        total_query = select(func.count()).select_from(stmt.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.page
        page_size = query_params.size
        if page_num and page_size:
            stmt = stmt.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(stmt)
        return result.scalars().all(), total

    @staticmethod
    async def add_log(new_orm: SysOperLog, db_session: AsyncSession) -> None:
        """新增操作日志

        :param new_orm: 日志数据 ORM 对象
        :param db_session: 数据库会话
        """
        db_session.add(new_orm)
        await db_session.flush()

    @staticmethod
    async def delete_log(oper_id: int, db_session: AsyncSession) -> None:
        """删除操作日志，真实删除

        :param oper_id: 日志ID
        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysOperLog).where(SysOperLog.oper_id == oper_id))
        await db_session.flush()

    @staticmethod
    async def clear_logs(db_session: AsyncSession) -> None:
        """清空操作日志

        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysOperLog))
        await db_session.flush()

    @staticmethod
    async def get_log_by_id(oper_id: int, db_session: AsyncSession) -> SysOperLog | None:
        """根据操作日志ID获取详情

        :param oper_id: 操作日志ID
        :param db_session: 数据库会话
        :return: 操作日志 ORM 对象
        """
        stmt = select(SysOperLog).where(SysOperLog.oper_id == oper_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()


class LoginLogMapper:
    """登录日志数据访问层"""

    @staticmethod
    async def get_log_list(
        query_params: LoginLogQueryDTO, db_session: AsyncSession
    ) -> tuple[Sequence[SysLogininfor], int]:
        """获取登录日志列表

        :param query_params: 查询参数DTO
        :param db_session: 数据库会话
        :return: 登录日志列表和总数
        """
        # 构建查询语句
        stmt = select(SysLogininfor)

        # 添加过滤条件
        if query_params.ipaddr:
            stmt = stmt.where(SysLogininfor.ipaddr.like(f"%{query_params.ipaddr}%"))
        if query_params.user_name:
            stmt = stmt.where(SysLogininfor.user_name.like(f"%{query_params.user_name}%"))
        if query_params.status:
            stmt = stmt.where(SysLogininfor.status == query_params.status)
        if query_params.begin_time and query_params.end_time:
            begin_datetime = query_params.begin_time.replace(hour=0, minute=0, second=0)
            end_datetime = query_params.end_time.replace(hour=23, minute=59, second=59)
            stmt = stmt.where(SysLogininfor.login_time.between(begin_datetime, end_datetime))

        # 获取总数
        total_query = select(func.count()).select_from(stmt.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.page
        page_size = query_params.size
        if page_num and page_size:
            stmt = stmt.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(stmt)
        return result.scalars().all(), total

    @staticmethod
    async def add_log(new_orm: SysLogininfor, db_session: AsyncSession) -> None:
        """新增登录日志

        :param new_orm: 日志数据 ORM 对象
        :param db_session: 数据库会话
        """
        db_session.add(new_orm)
        await db_session.flush()

    @staticmethod
    async def delete_log(info_id: int, db_session: AsyncSession) -> None:
        """删除登录日志

        :param info_id: 日志ID
        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysLogininfor).where(SysLogininfor.info_id == info_id))
        await db_session.flush()

    @staticmethod
    async def clear_logs(db_session: AsyncSession) -> None:
        """清空登录日志

        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysLogininfor))
        await db_session.flush()
