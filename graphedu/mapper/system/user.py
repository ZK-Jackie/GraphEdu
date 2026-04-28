"""用户管理 Mapper 层

负责用户数据的访问操作，包括用户信息的增删改查、
用户角色关联、权限查询等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time
from typing import TypedDict

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.systemv2.user import UserQueryDTO
from graphedu.common.models.orm.education import EduStudent, EduTeacher
from graphedu.common.models.orm.system import (
    SysDept,
    SysFunction,
    SysRole,
    SysRoleFunction,
    SysUser,
    SysUserDept,
    SysUserRole,
)


class _UserDetailByIdResult(TypedDict):
    """用户详情查询结果类型定义"""

    user_basic_info: SysUser
    user_dept_info: Sequence[SysDept]
    user_role_info: Sequence[SysRole]
    user_function_info: Sequence[SysFunction]


class UserMapper:
    """用户数据访问层

    提供用户信息的 CRUD 操作以及用户角色、权限等相关查询功能。
    """

    @staticmethod
    async def add_user(user_info: SysUser, db_session: AsyncSession):
        """添加用户

        :param db_session: orm对象
        :param user_info: 用户信息
        :return: 用户对象
        """
        db_session.add(user_info)
        await db_session.flush()
        return user_info

    @staticmethod
    async def add_user_role(user_role: SysUserRole, db_session: AsyncSession) -> SysUserRole:
        """添加用户角色关联

        :param db_session: orm对象
        :param user_role: 用户角色信息
        :return: 用户角色对象
        """
        db_session.add(user_role)
        await db_session.flush()
        return user_role

    @staticmethod
    async def get_by_id(user_id: int, db_session: AsyncSession) -> SysUser | None:
        """根据用户ID查询用户信息

        :param db_session: orm对象
        :param user_id: 用户ID
        :return: 用户对象
        """
        stmt = select(SysUser).where(SysUser.user_id == user_id, SysUser.status != SystemConstants.Status.DELETED)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_username(user_name: str, db_session: AsyncSession) -> SysUser | None:
        """根据用户名查询用户信息

        :param db_session: orm对象
        :param user_name: 用户名
        :return: 用户对象
        """
        stmt = select(SysUser).where(SysUser.status == SystemConstants.Status.NORMAL, SysUser.user_name == user_name)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_phonenumber(phonenumber: str, db_session: AsyncSession) -> SysUser | None:
        """根据手机号查询用户信息

        :param db_session: orm对象
        :param phonenumber: 手机号
        :return: 用户对象
        """
        stmt = select(SysUser).where(
            SysUser.status == SystemConstants.Status.NORMAL, SysUser.phonenumber == phonenumber
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_email(email: str, db_session: AsyncSession) -> SysUser | None:
        """根据邮箱查询用户信息（用于登录等场景，只查询启用的用户）

        :param db_session: orm对象
        :param email: 邮箱
        :return: 用户对象
        """
        stmt = select(SysUser).where(SysUser.status == SystemConstants.Status.NORMAL, SysUser.email == email)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_user_by_username_for_unique_check(user_name: str, db_session: AsyncSession) -> SysUser | None:
        """根据用户名查询用户（用于唯一性校验，查询所有未删除的用户）

        :param db_session: orm对象
        :param user_name: 用户名
        :return: 用户对象
        """
        stmt = select(SysUser).where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_name == user_name)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_user_by_phonenumber_for_unique_check(phonenumber: str, db_session: AsyncSession) -> SysUser | None:
        """根据手机号查询用户（用于唯一性校验，查询所有未删除的用户）

        :param db_session: orm对象
        :param phonenumber: 手机号
        :return: 用户对象
        """
        stmt = select(SysUser).where(
            SysUser.status != SystemConstants.Status.DELETED, SysUser.phonenumber == phonenumber
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_user_by_email_for_unique_check(email: str, db_session: AsyncSession) -> SysUser | None:
        """根据邮箱查询用户（用于唯一性校验，查询所有未删除的用户）

        :param db_session: orm对象
        :param email: 邮箱
        :return: 用户对象
        """
        stmt = select(SysUser).where(SysUser.status != SystemConstants.Status.DELETED, SysUser.email == email)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_detail_by_id(user_id: int, db_session: AsyncSession) -> _UserDetailByIdResult:
        """根据用户ID查询用户信息

        :param db_session: orm对象
        :param user_id: 用户ID
        :return: 用户信息字典，包含 user_basic_info, user_dept_info, user_role_info, user_menu_info
        """
        query_user_basic_info = (
            (
                await db_session.execute(
                    select(SysUser)
                    .where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_id == user_id)
                    .distinct()
                )
            )
            .scalars()
            .first()
        )
        query_user_dept_info = (
            (
                await db_session.execute(
                    select(SysDept)
                    .select_from(SysUser)
                    .where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_id == user_id)
                    .join(SysUserDept, SysUser.user_id == SysUserDept.user_id, isouter=True)
                    .join(
                        SysDept,
                        and_(SysUserDept.dept_id == SysDept.dept_id, SysDept.status == SystemConstants.Status.NORMAL),
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        query_user_role_info = (
            (
                await db_session.execute(
                    select(SysRole)
                    .select_from(SysUser)
                    .where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_id == user_id)
                    .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                    .join(
                        SysRole,
                        and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == SystemConstants.Status.NORMAL),
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        role_key_list = [item.role_key for item in query_user_role_info]
        role_id_list = [item.role_id for item in query_user_role_info]

        # 处理用户角色为空的情况
        if not role_key_list:
            query_user_function_info = []
        elif any(role_id <= 10 for role_id in role_id_list):
            # 超级管理员拥有所有功能权限（role_id <= 10）
            query_user_function_info: Sequence[SysFunction] = (
                (
                    await db_session.execute(
                        select(SysFunction).where(SysFunction.status == SystemConstants.Status.NORMAL).distinct()
                    )
                )
                .scalars()
                .all()
            )
        else:
            # 普通用户根据角色查询功能权限
            query_user_function_info: Sequence[SysFunction] = (
                (
                    await db_session.execute(
                        select(SysFunction)
                        .select_from(SysUser)
                        .where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_id == user_id)
                        .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                        .join(
                            SysRole,
                            and_(
                                SysUserRole.role_id == SysRole.role_id, SysRole.status == SystemConstants.Status.NORMAL
                            ),
                            isouter=True,
                        )
                        .join(SysRoleFunction, SysRole.role_id == SysRoleFunction.role_id, isouter=True)
                        .join(
                            SysFunction,
                            and_(
                                SysRoleFunction.function_id == SysFunction.function_id,
                                SysFunction.status == SystemConstants.Status.NORMAL,
                            ),
                        )
                        .order_by(SysFunction.sort_order)
                        .distinct()
                    )
                )
                .scalars()
                .all()
            )
        await db_session.flush()
        return _UserDetailByIdResult(
            user_basic_info=query_user_basic_info,
            user_dept_info=query_user_dept_info,
            user_role_info=query_user_role_info,
            user_function_info=query_user_function_info,
        )

    @staticmethod
    async def is_username_exists(user_name: str, query_db: AsyncSession) -> bool:
        """校验用户名是否存在

        :param query_db: orm对象
        :param user_name: 用户名
        :return: 是否存在
        """
        stmt = select(SysUser).where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_name == user_name)
        user = (await query_db.execute(stmt)).scalars().first()
        return user is not None

    @staticmethod
    async def is_phonenumber_exists(phonenumber: str, query_db: AsyncSession) -> bool:
        """校验手机号是否存在

        :param query_db: orm对象
        :param phonenumber: 手机号
        :return: 是否存在
        """
        stmt = select(SysUser).where(
            SysUser.status != SystemConstants.Status.DELETED, SysUser.phonenumber == phonenumber
        )
        user = (await query_db.execute(stmt)).scalars().first()
        return user is not None

    @staticmethod
    async def is_email_exists(email: str, query_db: AsyncSession) -> bool:
        """校验邮箱是否存在

        :param query_db: orm对象
        :param email: 邮箱
        :return: 是否存在
        """
        stmt = select(SysUser).where(SysUser.status != SystemConstants.Status.DELETED, SysUser.email == email)
        user = (await query_db.execute(stmt)).scalars().first()
        return user is not None

    @staticmethod
    async def get_user_list(
        db: AsyncSession, query_object: UserQueryDTO, data_scope_sql: str, is_page: bool = False
    ) -> tuple[
        Sequence[tuple[SysUser | None, SysDept | None, SysUserDept | None, EduStudent | None, EduTeacher | None]],
        int,
    ]:
        """根据查询参数获取用户列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句（警告：使用eval存在安全风险）
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为用户列表（含部门、学生、教师信息），total为总数
        """
        # 构建部门过滤条件（使用递归CTE查询所有子孙部门）
        dept_filter = None
        if query_object.dept_ids:
            # 创建递归CTE获取所有子孙部门
            dept_cte = (
                select(SysDept.dept_id)
                .where(and_(SysDept.dept_id.in_(query_object.dept_ids)))
                .cte(name="dept_tree", recursive=True)
            )
            # 递归查询子部门
            dept_recursive = select(SysDept.dept_id).where(and_(SysDept.parent_id == dept_cte.c.dept_id))
            # 组合成递归CTE
            dept_cte = dept_cte.union_all(dept_recursive)
            # 构建部门过滤子查询
            dept_filter = select(SysUserDept.user_id).where(SysUserDept.dept_id.in_(select(dept_cte))).scalar_subquery()

        # 构建角色过滤条件
        role_filter = None
        if query_object.role_ids:
            role_filter = (
                select(SysUserRole.user_id).where(SysUserRole.role_id.in_(query_object.role_ids)).scalar_subquery()
            )

        # 构建基础查询条件
        base_conditions = [SysUser.status != SystemConstants.Status.DELETED]  # 必须未删除

        if query_object.user_id is not None:
            base_conditions.append(SysUser.user_id == query_object.user_id)
        if query_object.user_name:
            base_conditions.append(SysUser.user_name.like(f"%{query_object.user_name}%"))
        if query_object.nick_name:
            base_conditions.append(SysUser.nick_name.like(f"%{query_object.nick_name}%"))
        if query_object.email:
            base_conditions.append(SysUser.email.like(f"%{query_object.email}%"))
        if query_object.phonenumber:
            base_conditions.append(SysUser.phonenumber.like(f"%{query_object.phonenumber}%"))
        if query_object.status:
            base_conditions.append(SysUser.status == query_object.status)
        if query_object.user_types:
            base_conditions.append(SysUser.user_type.in_(query_object.user_types))
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                SysUser.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 添加部门过滤条件
        if dept_filter is not None:
            base_conditions.append(SysUser.user_id.in_(dept_filter))

        # 添加角色过滤条件
        if role_filter is not None:
            base_conditions.append(SysUser.user_id.in_(role_filter))

        # 添加数据权限过滤条件（警告：eval存在严重安全风险，建议重构为安全的实现方式）
        if data_scope_sql:
            base_conditions.append(eval(data_scope_sql))

        # 构建主查询
        query = (
            select(SysUser, SysDept, SysUserDept, EduStudent, EduTeacher)
            .join(
                SysUserDept,
                SysUser.user_id == SysUserDept.user_id,
                isouter=False,  # INNER JOIN：只查询有部门关联的用户
            )
            .join(
                SysDept,
                and_(SysUserDept.dept_id == SysDept.dept_id, SysDept.status == SystemConstants.Status.NORMAL),
                isouter=True,  # LEFT JOIN：部门可能被禁用或删除
            )
            .join(
                EduStudent,
                and_(SysUser.user_id == EduStudent.student_id, EduStudent.status != SystemConstants.Status.DELETED),
                isouter=True,  # LEFT JOIN：学生信息可选
            )
            .join(
                EduTeacher,
                and_(SysUser.user_id == EduTeacher.teacher_id, EduTeacher.status != SystemConstants.Status.DELETED),
                isouter=True,  # LEFT JOIN：教师信息可选
            )
            .where(and_(*base_conditions))
            .order_by(SysUser.user_id)
            .distinct()
        )

        # 获取总数（统计不重复的user_id）
        count_query = (
            select(func.count(func.distinct(SysUser.user_id)))
            .select_from(SysUser)
            .join(
                SysUserDept,
                SysUser.user_id == SysUserDept.user_id,
                isouter=False,
            )
            .join(
                SysDept,
                and_(SysUserDept.dept_id == SysDept.dept_id, SysDept.status == SystemConstants.Status.NORMAL),
                isouter=True,
            )
            .where(and_(*base_conditions))
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.all()

        return rows, total

    @staticmethod
    async def delete_user_role_by_user_id(user_id: int, db_session: AsyncSession) -> None:
        """根据用户ID删除用户角色关联

        :param db_session: orm对象
        :param user_id: 用户ID
        :return: None
        """
        stmt = delete(SysUserRole).where(SysUserRole.user_id == user_id)
        await db_session.execute(stmt)

    @staticmethod
    async def update(user_info: SysUser, query_db: AsyncSession) -> None:
        """更新用户信息

        :param query_db: orm对象
        :param user_info: 用户信息（PO对象或ORM对象）
        :return: 用户对象
        """
        await query_db.merge(user_info)
        await query_db.flush()

    @staticmethod
    async def check_is_admin_by_user_id(user_id: int, query_db: AsyncSession) -> bool:
        """检查用户是否为超级管理员

        超级管理员定义：用户拥有 role_id <= 10 的角色

        :param query_db: orm对象
        :param user_id: 用户ID
        :return: 是否为超级管理员
        """
        stmt = (
            select(SysRole)
            .select_from(SysUser)
            .where(SysUser.status != SystemConstants.Status.DELETED, SysUser.user_id == user_id, SysRole.role_id <= 10)
            .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
            .join(
                SysRole,
                and_(SysUserRole.role_id == SysRole.role_id),
                isouter=True,
            )
        )
        role = (await query_db.execute(stmt)).scalars().first()

        return role is not None

    @staticmethod
    async def get_available_for_student(db: AsyncSession) -> Sequence[SysUser]:
        """获取可以关联学生的用户列表（未在 edu_student 表中存在的正常状态用户）

        Args:
            db: 数据库会话。

        Returns:
            Sequence[SysUser]: 可关联学生的用户列表。
        """
        stmt = (
            select(SysUser)
            .outerjoin(EduStudent, SysUser.user_id == EduStudent.student_id)
            .where(EduStudent.student_id.is_(None))
            .where(SysUser.status == SystemConstants.Status.NORMAL)
            .order_by(SysUser.user_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
