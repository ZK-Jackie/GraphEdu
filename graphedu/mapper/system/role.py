"""角色管理 Mapper 层"""

from collections.abc import Sequence
import logging

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.systemv2.role import RoleQueryDTO, RoleUserQueryDTO
from graphedu.common.models.orm import SysUserDept
from graphedu.common.models.orm.system import SysDept, SysRole, SysRoleDept, SysRoleFunction, SysUser, SysUserRole

logger = logging.getLogger(__name__)


class RoleMapper:
    """角色数据访问层"""

    @staticmethod
    async def get_by_id(role_id: int, db_session: AsyncSession) -> SysRole | None:
        """根据角色ID获取角色信息

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: 角色信息
        """
        result = await db_session.execute(select(SysRole).where(SysRole.role_id == role_id, SysRole.status != "2"))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_role_key(role_key: str, db_session: AsyncSession) -> SysRole | None:
        """根据角色标识获取角色信息

        :param role_key: 角色标识
        :param db_session: 数据库会话
        :return: 角色信息
        """
        result = await db_session.execute(select(SysRole).where(SysRole.role_key == role_key, SysRole.status != "2"))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_role_name(role_name: str, db_session: AsyncSession) -> SysRole | None:
        """根据角色名称获取角色信息

        :param role_name: 角色名称
        :param db_session: 数据库会话
        :return: 角色信息
        """
        result = await db_session.execute(select(SysRole).where(SysRole.role_name == role_name, SysRole.status != "2"))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_role_list(query_params: RoleQueryDTO, db_session: AsyncSession) -> tuple[Sequence[SysRole], int]:
        """获取角色列表（支持分页）

        :param query_params: 查询参数字典
        :param db_session: 数据库会话
        :return: 角色列表和总数
        """
        stmt = select(SysRole).where(SysRole.status != "2")

        if query_params.role_name:
            stmt = stmt.where(SysRole.role_name.like(f"%{query_params.role_name}%"))
        if query_params.role_key:
            stmt = stmt.where(SysRole.role_key.like(f"%{query_params.role_key}%"))
        if query_params.status:
            stmt = stmt.where(SysRole.status == query_params.status)

        stmt = stmt.order_by(SysRole.role_id)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db_session.execute(count_stmt)
        total: int = total_result.scalar()

        # 分页
        page = query_params.page
        size = query_params.size
        if page and size:
            offset = (page - 1) * size
            stmt = stmt.offset(offset).limit(size)

        result = await db_session.execute(stmt)
        rows: Sequence[SysRole] = result.scalars().all()

        return rows, total

    @staticmethod
    async def check_role_name_unique(role_name: str, role_id: int | None, db_session: AsyncSession) -> bool:
        """检查角色名称是否唯一

        :param role_name: 角色名称
        :param role_id: 角色ID（编辑时传入，新增时为None）
        :param db_session: 数据库会话
        :return: True表示唯一，False表示重复
        """
        stmt = select(SysRole).where(SysRole.role_name == role_name, SysRole.status != "2")

        if role_id is not None:
            stmt = stmt.where(SysRole.role_id != role_id)

        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def check_role_key_unique(role_key: str, role_id: int | None, db_session: AsyncSession) -> bool:
        """检查角色标识是否唯一

        :param role_key: 角色标识
        :param role_id: 角色ID（编辑时传入，新增时为None）
        :param db_session: 数据库会话
        :return: True表示唯一，False表示重复
        """
        stmt = select(SysRole).where(SysRole.role_key == role_key, SysRole.status != "2")

        if role_id is not None:
            stmt = stmt.where(SysRole.role_id != role_id)

        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()
        return existing is None

    @staticmethod
    async def has_users(role_id: int, db_session: AsyncSession) -> bool:
        """检查角色是否有关联用户

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: True表示有用户，False表示没有
        """
        result = await db_session.execute(select(func.count(SysUserRole.user_id)).where(SysUserRole.role_id == role_id))
        count = result.scalar()
        return (count or 0) > 0

    @staticmethod
    async def add_role(role: SysRole, db_session: AsyncSession):
        """新增角色

        :param role: 角色ORM对象
        :param db_session: 数据库会话
        :return: 新增的角色对象
        """
        db_session.add(role)
        await db_session.flush()
        await db_session.refresh(role)
        return role

    @staticmethod
    async def update_role(role: SysRole, db_session: AsyncSession):
        """更新角色信息

        :param role: 角色ORM对象
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.merge(role)
        await db_session.flush()

    @staticmethod
    async def delete_role(role_id: int, db_session: AsyncSession):
        """删除角色

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(delete(SysRole).where(SysRole.role_id == role_id))
        await db_session.flush()

    @staticmethod
    async def get_role_function_ids(role_id: int, db_session: AsyncSession) -> Sequence[int]:
        """获取角色关联的功能权限ID列表

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: 功能权限ID列表
        """
        result = await db_session.execute(select(SysRoleFunction.function_id).where(SysRoleFunction.role_id == role_id))
        return result.scalars().all()

    @staticmethod
    async def add_role_function(role_id: int, function_id: int, db_session: AsyncSession):
        """新增角色功能权限关联

        :param role_id: 角色ID
        :param function_id: 功能权限ID
        :param db_session: 数据库会话
        :return: None
        """
        role_function = SysRoleFunction(role_id=role_id, function_id=function_id)
        db_session.add(role_function)
        await db_session.flush()

    @staticmethod
    async def delete_role_functions(role_id: int, db_session: AsyncSession):
        """删除角色的所有功能权限关联

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(delete(SysRoleFunction).where(SysRoleFunction.role_id == role_id))
        await db_session.flush()

    @staticmethod
    async def delete_user_roles_by_role_id(role_id: int, db_session: AsyncSession):
        """删除角色的所有用户关联

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: None
        """
        await db_session.execute(delete(SysUserRole).where(SysUserRole.role_id == role_id))
        await db_session.flush()

    @staticmethod
    async def get_role_allocated_users(
        query_params: RoleUserQueryDTO, data_scope_sql: str | None, db_session: AsyncSession
    ) -> tuple[list[SysUser], int | None]:
        """获取角色已分配的用户列表（分页）

        :param query_params: 查询参数
        :param data_scope_sql: 数据权限 SQL 片段
        :param db_session: 数据库会话
        :return: (用户列表, 总数)
        """
        query = (
            select(SysUser)
            .join(SysUserDept, SysUser.user_id == SysUserDept.user_id, isouter=True)
            .join(SysDept, SysUserDept.dept_id == SysDept.dept_id, isouter=True)
            .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
            .join(SysRole, SysUserRole.role_id == SysRole.role_id, isouter=True)
            .where(SysUserRole.role_id == query_params.role_id, SysUser.status != "2", eval(data_scope_sql))
        )

        if query_params.user_name:
            query = query.where(SysUser.user_name.like(f"%{query_params.user_name}%"))
        if query_params.phonenumber:
            query = query.where(SysUser.phonenumber.like(f"%{query_params.phonenumber}%"))

        # 获取总数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.page
        page_size = query_params.size
        if page_num and page_size:
            query = query.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_role_unallocated_users(
        query_params: RoleUserQueryDTO, data_scope_sql: str | None, db_session: AsyncSession
    ) -> tuple[list, int | None]:
        """获取角色未分配的用户列表（分页）

        :param query_params: 查询参数
        :param db_session: 数据库会话
        :param data_scope_sql: 数据权限 SQL 片段
        :return: (用户列表, 总数)
        """
        query = (
            select(SysUser, SysDept.dept_id, SysDept.dept_name)
            .join(SysUserDept, SysUser.user_id == SysUserDept.user_id, isouter=True)
            .join(SysDept, SysUserDept.dept_id == SysDept.dept_id, isouter=True)
            .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
            .join(SysRole, SysUserRole.role_id == SysRole.role_id, isouter=True)
            .where(SysRole.role_id != query_params.role_id, SysUser.status != "2", eval(data_scope_sql))
        )

        if query_params.user_name:
            query = query.where(SysUser.user_name.like(f"%{query_params.user_name}%"))
        if query_params.phonenumber:
            query = query.where(SysUser.phonenumber.like(f"%{query_params.phonenumber}%"))

        # 获取总数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.page
        page_size = query_params.size
        if page_num and page_size:
            query = query.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def check_user_role_exists(user_id: int, role_id: int, db_session: AsyncSession) -> bool:
        """检查用户角色关联是否存在

        :param user_id: 用户ID
        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: 是否存在
        """
        query = select(SysUserRole).where(SysUserRole.user_id == user_id, SysUserRole.role_id == role_id)
        result = await db_session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def add_user_role(user_id: int, role_id: int, db_session: AsyncSession):
        """添加用户角色关联

        :param user_id: 用户ID
        :param role_id: 角色ID
        :param db_session: 数据库会话
        """
        user_role = SysUserRole(user_id=user_id, role_id=role_id)
        db_session.add(user_role)
        await db_session.flush()

    @staticmethod
    async def delete_user_role(user_id: int, role_id: int, db_session: AsyncSession):
        """删除用户角色关联

        :param user_id: 用户ID
        :param role_id: 角色ID
        :param db_session: 数据库会话
        """
        await db_session.execute(
            delete(SysUserRole).where(SysUserRole.user_id == user_id, SysUserRole.role_id == role_id)
        )
        await db_session.flush()

    @staticmethod
    async def get_role_dept_ids(role_id: int, db_session: AsyncSession) -> list[int]:
        """获取角色已分配的部门ID列表

        :param role_id: 角色ID
        :param db_session: 数据库会话
        :return: 部门ID列表
        """
        query = select(SysRoleDept.dept_id).where(SysRoleDept.role_id == role_id)
        result = await db_session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_role_depts(role_id: int, db_session: AsyncSession):
        """删除角色的所有部门关联

        :param role_id: 角色ID
        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysRoleDept).where(SysRoleDept.role_id == role_id))
        await db_session.flush()

    @staticmethod
    async def add_role_dept(role_id: int, dept_id: int, db_session: AsyncSession):
        """添加角色部门关联

        :param role_id: 角色ID
        :param dept_id: 部门ID
        :param db_session: 数据库会话
        """
        role_dept = SysRoleDept(role_id=role_id, dept_id=dept_id)
        db_session.add(role_dept)
        await db_session.flush()
