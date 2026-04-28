"""角色管理服务模块。

该模块提供角色和角色权限分配的管理功能。

职责：
1. 处理 DTO 到 ORM 的转换（创建/更新时）。
2. 组装 VO 返回（查询时）。
3. 处理业务逻辑。
"""

import asyncio
from datetime import datetime
import logging

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.role import (
    RoleAuthorizeUsersFailedException,
    RoleChangeAdminStatusForbiddenException,
    RoleCreateFailedException,
    RoleDeleteAdminForbiddenException,
    RoleDeleteFailedException,
    RoleHasUsersException,
    RoleIdListEmptyException,
    RoleKeyAlreadyExistsException,
    RoleModifyAdminForbiddenException,
    RoleNameAlreadyExistsException,
    RoleNoPermissionException,
    RoleNotFoundException,
    RoleRevokeUsersBatchFailedException,
    RoleRevokeUsersFailedException,
    RoleUpdateDataScopeFailedException,
    RoleUpdateFailedException,
)
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants
from graphedu.common.models.dto.systemv2.role import (
    RoleCreateDTO,
    RoleDatascopeChangeDTO,
    RoleQueryDTO,
    RoleUpdateDTO,
    RoleUserQueryDTO,
)
from graphedu.common.models.orm.system import SysRole
from graphedu.common.models.vo import UserListVO
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.systemv2.role import RoleDetailVO, RoleListVO
from graphedu.mapper.system.role import RoleMapper

logger = logging.getLogger(__name__)


class RoleService:
    """角色管理服务类。

    提供角色的增删改查功能，支持角色权限分配和用户授权管理。
    """

    @staticmethod
    async def get_role_list(query_db: AsyncSession, page_query: RoleQueryDTO) -> PageResponse[RoleListVO]:
        """获取角色列表。

        Args:
            query_db: 数据库会话。
            page_query: 查询参数。

        Returns:
            PageResponse[RoleListVO]: 分页结果。
        """
        rows, total = await RoleMapper.get_role_list(page_query, query_db)

        # ORM -> VO 转换
        role_list = [RoleListVO.model_validate(role) for role in rows]

        return PageResponse(page=page_query.page, size=page_query.size, rows=role_list, total=total)

    @staticmethod
    async def get_role_detail(query_db: AsyncSession, role_id: int) -> RoleDetailVO | None:
        """获取角色详细信息（含功能权限）。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。

        Returns:
            RoleDetailVO | None: 角色详细信息 VO，不存在返回 None。
        """
        role = await RoleMapper.get_by_id(role_id, query_db)
        if not role:
            return None

        # 获取角色关联的功能权限ID列表
        function_ids = await RoleMapper.get_role_function_ids(role_id, query_db)

        # ORM -> VO 转换，附加 function_ids
        return RoleDetailVO(
            role_id=role.role_id,
            role_name=role.role_name,
            role_key=role.role_key,
            data_scope=role.data_scope,
            status=role.status,
            create_by=role.create_by,
            create_time=role.create_time,
            update_by=role.update_by,
            update_time=role.update_time,
            remark=role.remark,
            function_ids=list(function_ids),
            role_sort=role.role_sort,
        )

    @staticmethod
    async def add_role(query_db: AsyncSession, role_dto: RoleCreateDTO, current_user: CurrentUser) -> RoleDetailVO:
        """新增角色。

        Args:
            query_db: 数据库会话。
            role_dto: 角色 DTO。
            current_user: 当前用户。

        Returns:
            RoleDetailVO: 创建的角色详细信息 VO。

        Raises:
            RoleNameAlreadyExistsException: 角色名称已存在。
            RoleKeyAlreadyExistsException: 角色标识已存在。
            RoleCreateFailedException: 角色创建失败。
        """
        # 检查角色名称唯一性
        is_unique = await RoleMapper.check_role_name_unique(role_dto.role_name, None, query_db)
        if not is_unique:
            raise RoleNameAlreadyExistsException(role_name=role_dto.role_name)

        # 检查角色标识唯一性
        is_unique = await RoleMapper.check_role_key_unique(role_dto.role_key, None, query_db)
        if not is_unique:
            raise RoleKeyAlreadyExistsException(role_key=role_dto.role_key, role_name=role_dto.role_name)

        # DTO -> ORM 转换
        new_role = SysRole(
            role_name=role_dto.role_name,
            role_key=role_dto.role_key,
            role_sort=role_dto.role_sort,
            data_scope=role_dto.data_scope,
            status=role_dto.status,
            remark=role_dto.remark,
            create_by=current_user.detail.user.user_id if current_user.detail.user else None,
            create_time=datetime.now(),
            update_by=current_user.detail.user.user_id if current_user.detail.user else None,
            update_time=datetime.now(),
        )

        try:
            # 新增角色
            added_role = await RoleMapper.add_role(new_role, query_db)
        except Exception as e:
            raise RoleCreateFailedException from e

        # 关联功能权限
        if role_dto.function_ids:
            await asyncio.gather(
                *[
                    RoleMapper.add_role_function(added_role.role_id, function_id, query_db)
                    for function_id in role_dto.function_ids
                ]
            )
        logger.info(f"新增角色成功: {role_dto.role_name}")

        # 返回创建的角色 VO
        return RoleDetailVO(
            role_id=added_role.role_id,
            role_name=added_role.role_name,
            role_key=added_role.role_key,
            role_sort=added_role.role_sort,
            data_scope=added_role.data_scope,
            status=added_role.status,
            create_by=added_role.create_by,
            create_time=added_role.create_time,
            update_by=added_role.update_by,
            update_time=added_role.update_time,
            remark=added_role.remark,
            function_ids=role_dto.function_ids,
        )

    @staticmethod
    async def update_role(
        query_db: AsyncSession,
        role_dto: RoleUpdateDTO,
        current_user: CurrentUser,
        redis_session: AsyncRedis | None = None,
    ) -> RoleDetailVO:
        """更新角色信息。

        Args:
            query_db: 数据库会话。
            role_dto: 角色 DTO。
            current_user: 当前用户。
            redis_session: Redis 会话（可选，用于缓存失效）

        Returns:
            RoleDetailVO: 更新后的角色详细信息 VO。

        Raises:
            RoleNotFoundException: 角色不存在。
            RoleModifyAdminForbiddenException: 不允许修改管理员角色。
            RoleNameAlreadyExistsException: 角色名称已存在。
            RoleKeyAlreadyExistsException: 角色标识已存在。
            RoleUpdateFailedException: 角色更新失败。
        """
        # 检查角色是否存在
        existing_role = await RoleMapper.get_by_id(role_dto.role_id, query_db)
        if not existing_role:
            raise RoleNotFoundException(role_id=role_dto.role_id)

        # 检查是否为超级管理员角色（role_id <= 10）
        if existing_role.role_id <= 10:
            raise RoleModifyAdminForbiddenException

        # 检查角色名称唯一性（只有当值真正改变时才校验）
        if role_dto.role_name is not None and role_dto.role_name != existing_role.role_name:
            is_unique = await RoleMapper.check_role_name_unique(role_dto.role_name, role_dto.role_id, query_db)
            if not is_unique:
                raise RoleNameAlreadyExistsException(role_name=role_dto.role_name)

        # 检查角色标识唯一性（只有当值真正改变时才校验）
        if role_dto.role_key is not None and role_dto.role_key != existing_role.role_key:
            is_unique = await RoleMapper.check_role_key_unique(role_dto.role_key, role_dto.role_id, query_db)
            if not is_unique:
                raise RoleKeyAlreadyExistsException(role_key=role_dto.role_key)

        # 检查是否更新了功能权限
        function_ids_changed = role_dto.function_ids is not None

        # DTO -> ORM 转换（更新提供的字段）
        if role_dto.role_name:
            existing_role.role_name = role_dto.role_name
        if role_dto.role_key:
            existing_role.role_key = role_dto.role_key
        if role_dto.role_sort is not None:
            existing_role.role_sort = role_dto.role_sort
        if role_dto.data_scope:
            existing_role.data_scope = role_dto.data_scope
        if role_dto.status is not None:
            existing_role.status = role_dto.status
        if role_dto.remark is not None:
            existing_role.remark = role_dto.remark
        existing_role.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        existing_role.update_time = datetime.now()

        try:
            await RoleMapper.update_role(existing_role, query_db)
        except Exception as e:
            raise RoleUpdateFailedException from e

        # 更新功能权限关联
        function_ids = role_dto.function_ids
        if function_ids is not None:
            # 删除旧的权限关联
            await RoleMapper.delete_role_functions(role_dto.role_id, query_db)
            # 添加新的权限关联
            await asyncio.gather(
                *[RoleMapper.add_role_function(role_dto.role_id, function_id, query_db) for function_id in function_ids]
            )
        else:
            # 如果没有提供 function_ids，则获取现有的
            function_ids = await RoleMapper.get_role_function_ids(role_dto.role_id, query_db)

        logger.info(f"更新角色成功: {existing_role.role_name}")

        # 如果功能权限有变更，清除缓存
        if function_ids_changed and redis_session:
            from graphedu.security.auth import SecurityService

            await SecurityService.invalidate_role_cache(
                role_ids=[role_dto.role_id],
                redis_session=redis_session,
            )

        # 返回更新后的角色 VO
        return RoleDetailVO(
            role_id=existing_role.role_id,
            role_name=existing_role.role_name,
            role_key=existing_role.role_key,
            role_sort=existing_role.role_sort,
            data_scope=existing_role.data_scope,
            status=existing_role.status,
            create_by=existing_role.create_by,
            create_time=existing_role.create_time,
            update_by=existing_role.update_by,
            update_time=existing_role.update_time,
            remark=existing_role.remark,
            function_ids=function_ids,
        )

    @staticmethod
    async def delete_role(query_db: AsyncSession, role_id_list: list[int], current_user: CurrentUser) -> None:
        """删除角色（批量）。

        Args:
            query_db: 数据库会话。
            role_id_list: 角色 ID 列表。
            current_user: 当前用户。

        Raises:
            RoleIdListEmptyException: 角色 ID 列表为空。
            RoleNotFoundException: 角色不存在。
            RoleDeleteAdminForbiddenException: 不允许删除管理员角色。
            RoleHasUsersException: 角色有关联用户。
            RoleDeleteFailedException: 角色删除失败。
        """
        if not role_id_list:
            raise RoleIdListEmptyException

        for role_id in role_id_list:
            # 检查角色是否存在
            role = await RoleMapper.get_by_id(role_id, query_db)
            if not role:
                raise RoleNotFoundException(role_id=role_id)

            # 检查是否为超级管理员角色（role_id <= 10）
            if role.role_id <= 10:
                raise RoleDeleteAdminForbiddenException

            # 检查是否有关联用户
            has_users = await RoleMapper.has_users(role_id, query_db)
            if has_users:
                raise RoleHasUsersException(role_name=role.role_name)

            # 删除角色
            role.status = SystemConstants.Status.DELETED
            role.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            role.update_time = datetime.now()
            try:
                await asyncio.gather(
                    # 删除角色功能权限关联
                    RoleMapper.delete_role_functions(role_id, query_db),
                    # 删除角色部门关联
                    RoleMapper.delete_role_depts(role_id, query_db),
                    # 删除用户角色关联
                    RoleMapper.delete_user_roles_by_role_id(role_id, query_db),
                    # 软删除角色
                    RoleMapper.update_role(role, query_db),
                )
                logger.info(f"删除角色: {role.role_name}")
            except Exception as e:
                raise RoleDeleteFailedException from e

    @staticmethod
    async def change_role_status(
        query_db: AsyncSession, role_id: int, status: str, current_user: CurrentUser
    ) -> RoleDetailVO:
        """修改角色状态。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。
            status: 新状态（'0' 正常，'1' 停用）。
            current_user: 当前用户。

        Returns:
            RoleDetailVO: 更新后的角色详细信息 VO。

        Raises:
            RoleNotFoundException: 角色不存在。
            RoleChangeAdminStatusForbiddenException: 不允许修改管理员状态。
            RoleUpdateFailedException: 角色状态修改失败。
        """
        role = await RoleMapper.get_by_id(role_id, query_db)
        if not role:
            raise RoleNotFoundException(role_id=role_id)

        # 检查是否为超级管理员角色（role_id <= 10）
        if role.role_id <= 10:
            raise RoleChangeAdminStatusForbiddenException

        role.status = status
        role.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        role.update_time = datetime.now()

        try:
            await RoleMapper.update_role(role, query_db)
        except Exception as e:
            raise RoleUpdateFailedException from e

        # 获取功能权限ID列表
        function_ids = await RoleMapper.get_role_function_ids(role_id, query_db)

        # 返回更新后的角色 VO
        return RoleDetailVO(
            role_id=role.role_id,
            role_name=role.role_name,
            role_key=role.role_key,
            role_sort=role.role_sort,
            data_scope=role.data_scope,
            status=role.status,
            create_by=role.create_by,
            create_time=role.create_time,
            update_by=role.update_by,
            update_time=role.update_time,
            remark=role.remark,
            function_ids=list(function_ids),
        )

    @staticmethod
    async def get_role_dept_ids(query_db: AsyncSession, role_id: int) -> list[int]:
        """获取角色已分配的部门 ID 列表。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。

        Returns:
            list[int]: 部门 ID 列表。
        """
        return await RoleMapper.get_role_dept_ids(role_id, query_db)

    @staticmethod
    async def check_role_data_scope(query_db: AsyncSession, role_id: int, data_scope_sql: str) -> None:
        """检查角色数据权限。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。
            data_scope_sql: 数据权限 SQL。

        Raises:
            RoleNotFoundException: 角色不存在。
            RoleNoPermissionException: 无权限。
        """
        role = await RoleMapper.get_by_id(role_id, query_db)
        if not role:
            raise RoleNotFoundException(role_id=role_id)

        # 如果data_scope_sql为空或者为'True'，说明当前用户是管理员或有全部权限
        if not data_scope_sql or data_scope_sql == "True":
            return

        # 检查角色是否在当前用户的数据权限范围内
        # 这里的data_scope_sql已经包含了完整的WHERE条件
        check_query = text(f"SELECT 1 FROM sys_role WHERE role_id = {role_id} AND ({data_scope_sql}) LIMIT 1")
        result = await query_db.execute(check_query)
        if not result.scalar():
            raise RoleNoPermissionException(role_id=role_id)

    @staticmethod
    async def get_role_allocated_user_list(
        query_db: AsyncSession, query_object: RoleUserQueryDTO, data_scope_sql: str
    ) -> PageResponse[UserListVO]:
        """获取角色已分配的用户列表（分页）。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数。
            data_scope_sql: 数据权限 SQL。

        Returns:
            PageResponse[UserListVO]: 分页结果。
        """
        rows, total = await RoleMapper.get_role_allocated_users(query_object, data_scope_sql, query_db)

        # ORM -> dict 转换（用户列表）
        user_list = [UserListVO.model_validate(user) for user in rows]

        return PageResponse(page=query_object.page, size=query_object.size, total=total or 0, rows=user_list)

    @staticmethod
    async def get_role_unallocated_user_list(
        query_db: AsyncSession, query_object: RoleUserQueryDTO, data_scope_sql: str
    ) -> PageResponse[UserListVO]:
        """获取角色未分配的用户列表（分页）。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数。
            data_scope_sql: 数据权限 SQL。

        Returns:
            PageResponse[UserListVO]: 分页结果。
        """
        rows, total = await RoleMapper.get_role_unallocated_users(query_object, data_scope_sql, query_db)

        # ORM -> dict 转换（用户列表）
        user_list = [UserListVO.model_validate(user) for user in rows]

        return PageResponse(page=query_object.page, size=query_object.size, total=total or 0, rows=user_list)

    @staticmethod
    async def add_role_users(query_db: AsyncSession, role_id: int, user_id_list: list[int], current_user: CurrentUser):
        """批量授权用户到角色。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。
            user_id_list: 用户 ID 列表。
            current_user: 当前用户。

        Raises:
            RoleNotFoundException: 角色不存在。
            RoleAuthorizeUsersFailedException: 批量授权失败。
        """
        role = await RoleMapper.get_by_id(role_id, query_db)
        if not role:
            raise RoleNotFoundException(role_id=role_id)

        try:
            for user_id in user_id_list:
                # 检查是否已经关联
                existing = await RoleMapper.check_user_role_exists(user_id, role_id, query_db)
                if not existing:
                    await RoleMapper.add_user_role(user_id, role_id, query_db)
            logger.info(f"批量授权 {len(user_id_list)} 个用户到角色ID {role_id}")
        except Exception as e:
            raise RoleAuthorizeUsersFailedException(reason=str(e)) from e

    @staticmethod
    async def remove_role_user(query_db: AsyncSession, role_id: int, user_id: int, current_user: CurrentUser):
        """取消单个用户的角色授权。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。
            user_id: 用户 ID。
            current_user: 当前用户。

        Raises:
            RoleRevokeUsersFailedException: 取消授权失败。
        """
        try:
            await RoleMapper.delete_user_role(user_id, role_id, query_db)
            logger.info(f"取消用户ID {user_id} 的角色ID {role_id} 授权")
        except Exception as e:
            raise RoleRevokeUsersFailedException(reason=str(e)) from e

    @staticmethod
    async def remove_role_users(
        query_db: AsyncSession, role_id: int, user_id_list: list[int], current_user: CurrentUser
    ):
        """批量取消用户的角色授权。

        Args:
            query_db: 数据库会话。
            role_id: 角色 ID。
            user_id_list: 用户 ID 列表。
            current_user: 当前用户。

        Raises:
            RoleRevokeUsersBatchFailedException: 批量取消授权失败。
        """
        try:
            for user_id in user_id_list:
                await RoleMapper.delete_user_role(user_id, role_id, query_db)

            logger.info(f"批量取消 {len(user_id_list)} 个用户的角色ID {role_id} 授权")
        except Exception as e:
            raise RoleRevokeUsersBatchFailedException(reason=str(e)) from e

    @staticmethod
    async def update_role_data_scope(
        query_db: AsyncSession, update_object: RoleDatascopeChangeDTO, current_user: CurrentUser
    ) -> RoleDetailVO:
        """修改角色数据权限范围。

        Args:
            query_db: 数据库会话。
            update_object: 角色数据权限修改 DTO。
            current_user: 当前用户。

        Returns:
            RoleDetailVO: 更新后的角色详细信息 VO。

        Raises:
            RoleNotFoundException: 角色不存在。
            RoleUpdateDataScopeFailedException: 角色数据权限范围修改失败。
        """
        # 检查角色是否存在
        role = await RoleMapper.get_by_id(update_object.role_id, query_db)
        if not role:
            raise RoleNotFoundException(role_id=update_object.role_id)

        # DTO -> ORM 转换
        role.data_scope = update_object.data_scope
        role.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        role.update_time = datetime.now()

        try:
            await RoleMapper.update_role(role, query_db)
        except Exception as e:
            raise RoleUpdateDataScopeFailedException(reason=str(e)) from e

        # 删除旧的角色部门关联
        await RoleMapper.delete_role_depts(role.role_id, query_db)

        if update_object.dept_ids and update_object.data_scope == SystemConstants.Datascope.CUSTOM:
            dept_ids = update_object.dept_ids
            await asyncio.gather(*[RoleMapper.add_role_dept(role.role_id, dept_id, query_db) for dept_id in dept_ids])
        logger.info(f"修改角色ID {role.role_id} 的数据权限范围成功，关联部门数: {len(update_object.dept_ids)}")

        # 获取功能权限ID列表
        function_ids = await RoleMapper.get_role_function_ids(role.role_id, query_db)

        # 返回更新后的角色 VO
        return RoleDetailVO(
            role_id=role.role_id,
            role_name=role.role_name,
            role_key=role.role_key,
            role_sort=role.role_sort,
            data_scope=role.data_scope,
            status=role.status,
            create_by=role.create_by,
            create_time=role.create_time,
            update_by=role.update_by,
            update_time=role.update_time,
            remark=role.remark,
            function_ids=list(function_ids),
        )
