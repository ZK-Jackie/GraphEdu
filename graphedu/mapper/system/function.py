"""功能权限管理 Mapper 层"""

from collections.abc import Sequence
from datetime import datetime
import logging

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.systemv2.function import FunctionQueryDTO
from graphedu.common.models.orm.system import SysFunction, SysRole, SysRoleFunction

logger = logging.getLogger(__name__)


class FunctionMapper:
    """功能权限数据访问层"""

    @staticmethod
    async def get_by_id(function_id: int, db_session: AsyncSession) -> SysFunction | None:
        """根据功能ID获取功能信息

        :param function_id: 功能ID
        :param db_session: 数据库会话
        :return: 功能信息
        """
        result = await db_session.execute(select(SysFunction).where(SysFunction.function_id == function_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_function_key(function_key: str, db_session: AsyncSession) -> SysFunction | None:
        """根据权限标识获取功能信息

        :param function_key: 权限标识
        :param db_session: 数据库会话
        :return: 功能信息
        """
        result = await db_session.execute(select(SysFunction).where(SysFunction.function_key == function_key))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_function_children(
        parent_id: int, scene: str | None, db_session: AsyncSession
    ) -> Sequence[SysFunction]:
        """获取指定父功能ID的子功能列表
        :param parent_id: 父功能ID
        :param scene: 应用场景 (web/admin/mobile)，如果提供则过滤该场景的功能
        :param db_session: 数据库会话
        :return: 父功能的子功能列表
        """
        scene_filter = SysFunction.scene == scene if scene else True
        result = await db_session.execute(
            select(SysFunction)
            .where(
                SysFunction.parent_id == parent_id, SysFunction.status != SystemConstants.Status.DELETED, scene_filter
            )
            .order_by(SysFunction.sort_order, SysFunction.function_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_function_list(query_params: FunctionQueryDTO, db_session: AsyncSession) -> Sequence[SysFunction]:
        """获取功能列表

        :param query_params: 查询参数字典
        :param db_session: 数据库会话
        :return: 功能列表
        """
        stmt = select(SysFunction).where(SysFunction.status != SystemConstants.Status.DELETED)
        if query_params:
            if query_params.function_name:
                stmt = stmt.where(SysFunction.function_name.like(f"%{query_params.function_name}%"))
            if query_params.status:
                stmt = stmt.where(SysFunction.status == query_params.status)
            if query_params.visible:
                stmt = stmt.where(SysFunction.visible == query_params.visible)
            if query_params.function_type:
                stmt = stmt.where(SysFunction.function_type == query_params.function_type)
            if query_params.scene:
                stmt = stmt.where(SysFunction.scene == query_params.scene)
        stmt = stmt.order_by(SysFunction.sort_order, SysFunction.function_id)

        result = await db_session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_function_list_for_tree_by_user_roles(
        role_ids: list[int], db_session: AsyncSession
    ) -> Sequence[SysFunction]:
        """根据用户角色信息获取功能树列表（用于菜单树展示）

        :param role_ids: 用户的角色ID列表
        :param db_session: 数据库会话
        :return: 功能列表
        """
        # 超级管理员定义：role_id <= 10 的角色，返回所有功能
        if any(role_id <= 10 for role_id in role_ids):
            result = await db_session.execute(
                select(SysFunction)
                .where(SysFunction.status == SystemConstants.Status.NORMAL)
                .order_by(SysFunction.sort_order, SysFunction.function_id)
            )
        else:
            # 普通用户，根据角色获取功能
            # 使用 role_ids 参数直接查询，避免从 SysUser 开始多表 JOIN
            result = await db_session.execute(
                select(SysFunction)
                .select_from(SysFunction)
                .join(SysRoleFunction, SysFunction.function_id == SysRoleFunction.function_id)
                .join(
                    SysRole,
                    and_(
                        SysRoleFunction.role_id == SysRole.role_id, SysRole.role_id.in_(role_ids), SysRole.status == "0"
                    ),
                )
                .where(SysFunction.status == SystemConstants.Status.NORMAL)
                .order_by(SysFunction.sort_order, SysFunction.function_id)
                .distinct()
            )

        return result.scalars().all()

    @staticmethod
    async def get_function_list_for_tree_by_user_roles_and_scene(
        role_ids: list[int], scene: str, db_session: AsyncSession
    ) -> Sequence[SysFunction]:
        """根据用户角色信息和场景获取功能树列表（用于菜单树展示）

        :param role_ids: 用户的角色ID列表
        :param scene: 应用场景 (web/admin/mobile)
        :param db_session: 数据库会话
        :return: 功能列表
        """
        # 超级管理员定义：role_id <= 10 的角色，返回该场景的所有功能
        if any(role_id <= 10 for role_id in role_ids):
            result = await db_session.execute(
                select(SysFunction)
                .where(
                    SysFunction.status == SystemConstants.Status.NORMAL,
                    SysFunction.scene == scene,
                )
                .order_by(SysFunction.sort_order, SysFunction.function_id)
            )
        else:
            # 普通用户，根据角色获取功能
            # 使用 role_ids 参数直接查询，避免从 SysUser 开始多表 JOIN
            result = await db_session.execute(
                select(SysFunction)
                .select_from(SysFunction)
                .join(SysRoleFunction, SysFunction.function_id == SysRoleFunction.function_id)
                .join(
                    SysRole,
                    and_(
                        SysRoleFunction.role_id == SysRole.role_id, SysRole.role_id.in_(role_ids), SysRole.status == "0"
                    ),
                )
                .where(
                    SysFunction.status == SystemConstants.Status.NORMAL,
                    SysFunction.scene == scene,
                )
                .order_by(SysFunction.sort_order, SysFunction.function_id)
                .distinct()
            )

        return result.scalars().all()

    @staticmethod
    async def check_function_name_unique(
        function_name: str, parent_id: int, function_id: int | None, db_session: AsyncSession
    ) -> bool:
        """检查功能名称是否唯一（同一父级下）

        :param function_name: 功能名称
        :param parent_id: 父功能ID
        :param function_id: 功能ID（编辑时传入，新增时为None）
        :param db_session: 数据库会话
        :return: True表示唯一，False表示重复
        """
        stmt = select(SysFunction).where(SysFunction.function_name == function_name, SysFunction.parent_id == parent_id)

        if function_id is not None:
            stmt = stmt.where(SysFunction.function_id != function_id)

        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def has_children(function_id: int, db_session: AsyncSession) -> bool:
        """检查功能是否有子功能

        :param function_id: 功能ID
        :param db_session: 数据库会话
        :return: True表示有子功能，False表示没有
        """
        result = await db_session.execute(
            select(func.count(SysFunction.function_id)).where(SysFunction.parent_id == function_id)
        )
        count = result.scalar()
        return (count or 0) > 0

    @staticmethod
    async def check_function_exist_role(function_id: int, db_session: AsyncSession) -> bool:
        """检查功能是否被角色使用

        :param function_id: 功能ID
        :param db_session: 数据库会话
        :return: True表示被使用，False表示未使用
        """
        result = await db_session.execute(
            select(func.count(SysRoleFunction.role_id)).where(SysRoleFunction.function_id == function_id)
        )
        count = result.scalar()
        return (count or 0) > 0

    @staticmethod
    async def add_function(function: SysFunction, db_session: AsyncSession) -> SysFunction:
        """新增功能

        :param function: 功能ORM对象
        :param db_session: 数据库会话
        :return: 新增的功能对象
        """
        db_session.add(function)
        await db_session.flush()
        await db_session.refresh(function)
        return function

    @staticmethod
    async def update_function(function: SysFunction, db_session: AsyncSession) -> None:
        """更新功能信息

        :param function: 功能ORM对象
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.merge(function)
        await db_session.flush()

    @staticmethod
    async def delete_function(
        function_id: int, update_by: int, update_time: datetime, db_session: AsyncSession
    ) -> None:
        """删除功能

        :param function_id: 功能ID
        :param update_by: 更新者ID
        :param update_time: 更新时间
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(
            update(SysFunction)
            .where(SysFunction.function_id == function_id)
            .values(status=SystemConstants.Status.DELETED, update_by=update_by, update_time=update_time)
        )
        await db_session.flush()

    @staticmethod
    async def get_function_and_children_ids(function_id: int, db_session: AsyncSession) -> list[int]:
        """递归获取功能及其所有子功能的ID列表

        :param function_id: 功能ID
        :param db_session: 数据库会话
        :return: 功能ID列表（包含自身和所有子孙功能）
        """
        function_ids = [function_id]

        # 查询直接子功能
        result = await db_session.execute(select(SysFunction.function_id).where(SysFunction.parent_id == function_id))
        children = result.scalars().all()

        # 递归获取每个子功能的子功能
        for child_id in children:
            child_ids = await FunctionMapper.get_function_and_children_ids(child_id, db_session)
            function_ids.extend(child_ids)

        return function_ids
