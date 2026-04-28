"""部门管理 Mapper 层"""

from collections.abc import Sequence
import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.systemv2.dept import DeptQueryDTO
from graphedu.common.models.orm.system import SysDept, SysUser, SysUserDept

logger = logging.getLogger(__name__)


class DeptMapper:
    """部门数据访问层"""

    @staticmethod
    async def get_by_id(dept_id: int, db_session: AsyncSession) -> SysDept | None:
        """根据部门ID获取部门信息

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: 部门信息
        """
        result = await db_session.execute(
            select(SysDept).where(SysDept.dept_id == dept_id, SysDept.status != SystemConstants.Status.DELETED)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_dept_list(
        query_params: DeptQueryDTO | None, data_scope_sql: str, db_session: AsyncSession
    ) -> Sequence[SysDept]:
        """获取部门列表

        :param query_params: 查询参数字典
        :param data_scope_sql: 数据权限SQL
        :param db_session: 数据库会话
        :return: 部门列表
        """
        stmt = select(SysDept).where(SysDept.status != SystemConstants.Status.DELETED, eval(data_scope_sql))
        # 应用查询参数过滤
        if query_params:
            if query_params.dept_id is not None:
                stmt = stmt.where(SysDept.dept_id == query_params.dept_id)
            if query_params.dept_name:
                stmt = stmt.where(SysDept.dept_name.ilike(f"%{query_params.dept_name}%"))
            if query_params.parent_id is not None:
                # 查询父部门及其子部门
                stmt = stmt.where(SysDept.parent_id == query_params.parent_id)
            if query_params.status:
                stmt = stmt.where(SysDept.status == query_params.status)
        result = await db_session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_dept_children(dept_id: int, db_session: AsyncSession) -> Sequence[SysDept]:
        """获取指定部门的所有子部门列表

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: 子部门列表
        """
        result = await db_session.execute(
            select(SysDept)
            .where(SysDept.parent_id == dept_id, SysDept.status != SystemConstants.Status.DELETED)
            .order_by(SysDept.sort_order, SysDept.dept_name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_dept_exclude_children(
        dept_id: int, data_scope_sql: str, db_session: AsyncSession
    ) -> Sequence[SysDept]:
        """获取排除指定部门及其子部门的部门列表（用于编辑时选择父部门）

        :param dept_id: 要排除的部门ID
        :param data_scope_sql: 数据权限SQL
        :param db_session: 数据库会话
        :return: 部门列表
        """
        # 首先获取要排除的部门及其所有子部门的ID
        dept_ids_to_exclude = await DeptMapper.get_dept_and_children_ids_r(dept_id, db_session)

        result = await db_session.execute(
            select(SysDept)
            .where(
                SysDept.status != SystemConstants.Status.DELETED,
                SysDept.dept_id.notin_(dept_ids_to_exclude),
                SysDept.status == SystemConstants.Status.NORMAL,
                eval(data_scope_sql),
            )
            .order_by(SysDept.sort_order, SysDept.dept_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_dept_and_children_ids_r(dept_id: int, db_session: AsyncSession):
        """获取部门及其所有子部门的ID列表

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: 部门ID列表
        """
        dept_ids = [dept_id]

        async def get_children_recursive(parent_id: int):
            result = await db_session.execute(
                select(SysDept.dept_id).where(
                    SysDept.parent_id == parent_id, SysDept.status != SystemConstants.Status.DELETED
                )
            )
            child_ids = result.scalars().all()
            for child_id in child_ids:
                dept_ids.append(child_id)
                await get_children_recursive(child_id)

        await get_children_recursive(dept_id)
        return dept_ids

    @staticmethod
    async def check_dept_name_unique(
        dept_name: str, parent_id: int, dept_id: int | None, db_session: AsyncSession
    ) -> bool:
        """检查部门名称是否唯一（同一父部门下不能有重名）

        :param dept_name: 部门名称
        :param parent_id: 父部门ID
        :param dept_id: 部门ID（编辑时传入，新增时为None）
        :param db_session: 数据库会话
        :return: True表示唯一，False表示重复
        """
        stmt = select(SysDept).where(
            SysDept.dept_name == dept_name,
            SysDept.parent_id == parent_id,
            SysDept.status != SystemConstants.Status.DELETED,
        )

        if dept_id is not None:
            stmt = stmt.where(SysDept.dept_id != dept_id)

        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def check_dept_key_unique(dept_key: str, dept_id: int | None, db_session: AsyncSession) -> bool:
        """检查部门编码是否唯一

        :param dept_key: 部门编码
        :param dept_id: 部门ID（编辑时传入，新增时为None）
        :param db_session: 数据库会话
        :return: True表示唯一，False表示重复
        """
        stmt = select(SysDept).where(SysDept.dept_key == dept_key, SysDept.status != SystemConstants.Status.DELETED)

        if dept_id is not None:
            stmt = stmt.where(SysDept.dept_id != dept_id)

        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def has_child_depts(dept_id: int, db_session: AsyncSession) -> bool:
        """检查部门是否有子部门

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: True表示有子部门，False表示没有
        """
        result = await db_session.execute(
            select(func.count(SysDept.dept_id)).where(
                SysDept.parent_id == dept_id, SysDept.status != SystemConstants.Status.DELETED
            )
        )
        count = result.scalar()
        return (count or 0) > 0

    @staticmethod
    async def count_normal_child_depts(dept_id: int, db_session: AsyncSession) -> int:
        """统计正常状态的子部门数量

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: 正常状态的子部门数量
        """
        result = await db_session.execute(
            select(func.count(SysDept.dept_id)).where(
                SysDept.parent_id == dept_id,
                SysDept.status == SystemConstants.Status.NORMAL,
                SysDept.status != SystemConstants.Status.DELETED,
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def has_users(dept_id: int, db_session: AsyncSession) -> bool:
        """检查部门是否有关联用户

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: True表示有用户，False表示没有
        """
        result = await db_session.execute(select(func.count(SysUserDept.user_id)).where(SysUserDept.dept_id == dept_id))
        count = result.scalar()
        return (count or 0) > 0

    @staticmethod
    async def add_dept(dept, db_session: AsyncSession):
        """新增部门

        :param dept: 部门ORM对象
        :param db_session: 数据库会话
        :return: 新增的部门对象
        """
        db_session.add(dept)
        await db_session.flush()
        await db_session.refresh(dept)
        return dept

    @staticmethod
    async def update_dept(dept, db_session: AsyncSession):
        """更新部门信息

        :param dept: 部门ORM对象
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.merge(dept)
        await db_session.flush()

    @staticmethod
    async def delete_dept(dept_id: int, db_session: AsyncSession) -> None:
        """删除部门

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(delete(SysDept).where(SysDept.dept_id == dept_id))
        await db_session.flush()

    @staticmethod
    async def update_dept_status(dept_id: int, status: str, db_session: AsyncSession):
        """更新部门状态

        :param dept_id: 部门ID
        :param status: 状态
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(update(SysDept).where(SysDept.dept_id == dept_id).values(status=status))
        await db_session.flush()

    @staticmethod
    async def add_user_dept(user_id: int, dept_id: int, db_session: AsyncSession):
        """添加用户部门关联

        :param user_id: 用户ID
        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: None
        """
        user_dept = SysUserDept(user_id=user_id, dept_id=dept_id)
        db_session.add(user_dept)
        await db_session.flush()

    @staticmethod
    async def delete_user_depts(user_id: int, db_session: AsyncSession):
        """删除用户的所有部门关联

        :param user_id: 用户ID
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(delete(SysUserDept).where(SysUserDept.user_id == user_id))
        await db_session.flush()

    @staticmethod
    async def get_dept_users(dept_id: int, db_session: AsyncSession) -> Sequence[tuple[SysUser, SysUserDept]]:
        """获取部门关联的用户列表

        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: (用户, 用户部门关联) 元组列表
        """
        result = await db_session.execute(
            select(SysUser, SysUserDept)
            .join(SysUserDept, SysUser.user_id == SysUserDept.user_id)
            .where(
                SysUserDept.dept_id == dept_id,
                SysUser.status != SystemConstants.Status.DELETED,
            )
            .order_by(SysUser.user_id)
        )
        return result.all()

    @staticmethod
    async def remove_user_from_dept(user_id: int, dept_id: int, db_session: AsyncSession) -> None:
        """移除用户的部门关联

        :param user_id: 用户ID
        :param dept_id: 部门ID
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(
            delete(SysUserDept).where(SysUserDept.user_id == user_id, SysUserDept.dept_id == dept_id)
        )
        await db_session.flush()
