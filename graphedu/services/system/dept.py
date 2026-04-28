"""部门管理 Service 层

职责：
1. 接收 DTO，转换为 ORM 对象
2. 处理业务逻辑
3. 将 ORM 对象转换为 VO 返回
"""

from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.dept import (
    DeptCreateFailedException,
    DeptDeleteFailedException,
    DeptHasActiveChildrenException,
    DeptHasChildrenException,
    DeptHasUsersException,
    DeptIdListEmptyException,
    DeptKeyAlreadyExistsException,
    DeptNameAlreadyExistsException,
    DeptNoPermissionException,
    DeptNotFoundException,
    DeptParentCycleException,
    DeptParentDisabledException,
    DeptParentItselfException,
    DeptParentNotFoundException,
    DeptUpdateFailedException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.systemv2.dept import DeptCreateDTO, DeptQueryDTO, DeptUpdateDTO
from graphedu.common.models.orm.system import SysDept
from graphedu.common.models.vo.systemv2.dept import DeptDetailVO, DeptTreeVO
from graphedu.common.models.vo.systemv2.user import UserListVO
from graphedu.mapper.system.dept import DeptMapper

logger = logging.getLogger(__name__)


def _convert_orm_to_tree_vo(dept: SysDept, children: list[DeptTreeVO] | None = None) -> DeptTreeVO:
    """将 ORM 对象转换为 DeptTreeVO。

    Args:
        dept: ORM 部门对象。
        children: 子部门列表。

    Returns:
        DeptTreeVO: 部门树形视图对象。
    """
    return DeptTreeVO(
        dept_id=dept.dept_id,
        dept_name=dept.dept_name,
        parent_id=dept.parent_id,
        dept_key=dept.dept_key,
        leader=dept.leader,
        phone=dept.phone,
        email=dept.email,
        status=dept.status,
        sort_order=dept.sort_order,
        create_time=dept.create_time,
        children=children,
    )


def _build_dept_tree(dept_list: list[SysDept], parent_id: int = 0) -> list[DeptTreeVO]:
    """将部门列表转换为树形结构。

    Args:
        dept_list: 部门 ORM 列表。
        parent_id: 父部门 ID。

    Returns:
        list[DeptTreeVO]: 部门树形列表。
    """
    tree = []
    for dept in dept_list:
        if dept.parent_id == parent_id:
            children = _build_dept_tree(dept_list, dept.dept_id)
            node = _convert_orm_to_tree_vo(dept, children if children else None)
            tree.append(node)
    return tree


class DeptService:
    """部门管理服务类。

    提供部门的增删改查功能，支持部门树形结构展示和管理。
    """

    @staticmethod
    async def get_dept_children(query_db: AsyncSession, data_scope_sql: str, parent_id: int = 0) -> list[DeptTreeVO]:
        """根据父部门 ID 获取子部门列表。

        用于自行构建树形结构或异步获取部门树。

        Args:
            query_db: 数据库会话。
            data_scope_sql: 数据权限 SQL。
            parent_id: 父部门 ID。

        Returns:
            list[DeptTreeVO]: 给定父部门 ID 的子部门列表。
        """
        # 获取子部门列表
        dept_list = await DeptMapper.get_dept_list(DeptQueryDTO(parent_id=parent_id), data_scope_sql, query_db)
        # 检查每个部门是否有子部门
        dept_vo_list = []
        for dept in dept_list:
            has_children = await DeptMapper.has_child_depts(dept.dept_id, query_db)
            dept_vo = DeptTreeVO.model_validate(dept)
            dept_vo.has_children = has_children
            # 叶子节点 children 设为 None，避免前端渲染展开箭头
            dept_vo.children = [] if has_children else None
            dept_vo_list.append(dept_vo)
        return dept_vo_list

    @staticmethod
    async def get_dept_tree(
        query_db: AsyncSession, query_params: DeptQueryDTO | None, data_scope_sql: str
    ) -> list[DeptTreeVO]:
        """获取完整部门树形列表。

        Args:
            query_db: 数据库会话。
            query_params: 查询参数 DTO。
            data_scope_sql: 数据权限 SQL。

        Returns:
            list[DeptTreeVO]: 部门树形列表 VO。
        """
        dept_list = await DeptMapper.get_dept_list(query_params, data_scope_sql, query_db)
        logger.debug(f"获取部门树形列表成功，共 {len(dept_list)} 条记录")
        return _build_dept_tree(list(dept_list))

    @staticmethod
    async def get_dept_exclude_tree(
        query_db: AsyncSession, exclude_dept_id: int, data_scope_sql: str
    ) -> list[DeptTreeVO]:
        """获取排除指定部门及其子部门的部门树。

        用于编辑时选择父部门，避免将父部门设为自己的子部门。

        Args:
            query_db: 数据库会话。
            exclude_dept_id: 要排除的部门 ID。
            data_scope_sql: 数据权限 SQL。

        Returns:
            list[DeptTreeVO]: 部门树形列表 VO。
        """
        dept_list = await DeptMapper.get_dept_exclude_children(exclude_dept_id, data_scope_sql, query_db)
        logger.debug(f"获取排除部门ID {exclude_dept_id} 的部门树成功，共 {len(dept_list)} 条记录")
        return _build_dept_tree(list(dept_list))

    @staticmethod
    async def get_dept_detail(query_db: AsyncSession, dept_id: int) -> DeptDetailVO | None:
        """获取部门详细信息。

        Args:
            query_db: 数据库会话。
            dept_id: 部门 ID。

        Returns:
            DeptDetailVO | None: 部门详细信息 VO，不存在返回 None。

        Raises:
            DeptNotFoundException: 部门不存在时抛出。
        """
        dept = await DeptMapper.get_by_id(dept_id, query_db)
        if not dept:
            raise DeptNotFoundException(dept_id=dept_id)
        # ORM → VO
        logger.debug(f"获取部门ID {dept_id} 详细信息成功")
        return DeptDetailVO.model_validate(dept)

    @staticmethod
    async def add_dept(
        query_db: AsyncSession, dept_data: DeptCreateDTO, current_user: CurrentUser
    ) -> DeptDetailVO | None:
        """新增部门。

        Args:
            query_db: 数据库会话。
            dept_data: 部门数据 DTO。
            current_user: 当前用户。

        Returns:
            DeptDetailVO | None: 创建成功的部门 VO。

        Raises:
            DeptNameAlreadyExistsException: 部门名称已存在。
            DeptKeyAlreadyExistsException: 部门编码已存在。
            DeptParentNotFoundException: 父部门不存在。
            DeptParentDisabledException: 父部门已停用。
            DeptCreateFailedException: 部门创建失败。
        """
        # 检查部门名称唯一性
        is_unique = await DeptMapper.check_dept_name_unique(dept_data.dept_name, dept_data.parent_id, None, query_db)
        if not is_unique:
            raise DeptNameAlreadyExistsException(dept_name=dept_data.dept_name, parent_id=dept_data.parent_id)

        # 检查部门编码唯一性
        is_unique = await DeptMapper.check_dept_key_unique(dept_data.dept_key, None, query_db)
        if not is_unique:
            raise DeptKeyAlreadyExistsException(dept_key=dept_data.dept_key, dept_name=dept_data.dept_name)

        # 检查父部门状态
        if dept_data.parent_id != 0:
            parent_dept = await DeptMapper.get_by_id(dept_data.parent_id, query_db)
            if not parent_dept:
                raise DeptParentNotFoundException(parent_id=dept_data.parent_id)
            if parent_dept.status == "1":
                raise DeptParentDisabledException(parent_name=parent_dept.dept_name)

        # DTO → ORM (使用 model_dump)
        new_dept = SysDept(
            **dept_data.model_dump(),
            create_by=current_user.detail.user.user_id if current_user.detail.user else None,
            create_time=datetime.now(),
            update_by=current_user.detail.user.user_id if current_user.detail.user else None,
            update_time=datetime.now(),
        )

        try:
            await DeptMapper.add_dept(new_dept, query_db)
            logger.info(f"新增部门成功: {dept_data.dept_name}")

            # 返回创建后的部门 VO
            return DeptDetailVO.model_validate(new_dept)
        except Exception as e:
            raise DeptCreateFailedException from e

    @staticmethod
    async def update_dept(
        query_db: AsyncSession, dept_data: DeptUpdateDTO, current_user: CurrentUser
    ) -> DeptDetailVO | None:
        """更新部门信息。

        Args:
            query_db: 数据库会话。
            dept_data: 部门数据 DTO。
            current_user: 当前用户。

        Returns:
            DeptDetailVO | None: 更新后的部门 VO。

        Raises:
            DeptNotFoundException: 部门不存在。
            DeptNameAlreadyExistsException: 部门名称已存在。
            DeptKeyAlreadyExistsException: 部门编码已存在。
            DeptParentItselfException: 不能将自己设为父部门。
            DeptParentNotFoundException: 父部门不存在。
            DeptParentCycleException: 不能将父部门设为自己的子部门。
            DeptHasActiveChildrenException: 有未停用的子部门。
            DeptUpdateFailedException: 部门更新失败。
        """
        # 检查部门是否存在
        existing_dept = await DeptMapper.get_by_id(dept_data.dept_id, query_db)
        if not existing_dept:
            raise DeptNotFoundException(dept_id=dept_data.dept_id)

        # 检查部门名称唯一性（只有当值真正改变时才校验）
        if dept_data.dept_name is not None and dept_data.dept_name != existing_dept.dept_name:
            parent_id = dept_data.parent_id if dept_data.parent_id is not None else existing_dept.parent_id
            is_unique = await DeptMapper.check_dept_name_unique(
                dept_data.dept_name, parent_id, dept_data.dept_id, query_db
            )
            if not is_unique:
                raise DeptNameAlreadyExistsException(dept_name=dept_data.dept_name, parent_id=parent_id)

        # 检查部门编码唯一性（只有当值真正改变时才校验）
        if dept_data.dept_key is not None and dept_data.dept_key != existing_dept.dept_key:
            is_unique = await DeptMapper.check_dept_key_unique(dept_data.dept_key, dept_data.dept_id, query_db)
            if not is_unique:
                raise DeptKeyAlreadyExistsException(dept_key=dept_data.dept_key)

        # 不能将自己设为父部门
        if dept_data.parent_id is not None and dept_data.parent_id == dept_data.dept_id:
            raise DeptParentItselfException

        # 检查父部门
        if dept_data.parent_id is not None and dept_data.parent_id != 0:
            parent_dept = await DeptMapper.get_by_id(dept_data.parent_id, query_db)
            if not parent_dept:
                raise DeptParentNotFoundException(parent_id=dept_data.parent_id)

            # 不能将父部门设为自己的子部门
            parent_ids = await DeptMapper.get_dept_and_children_ids_r(dept_data.dept_id, query_db)
            if dept_data.parent_id in parent_ids:
                raise DeptParentCycleException

        # 如果要停用部门，检查是否有未停用的子部门
        if dept_data.status == "1":
            normal_child_count = await DeptMapper.count_normal_child_depts(dept_data.dept_id, query_db)
            if normal_child_count > 0:
                raise DeptHasActiveChildrenException(dept_name=existing_dept.dept_name)

        # 使用 model_dump(exclude_unset=True) 只更新提供的字段
        update_data = dept_data.model_dump(exclude_unset=True, exclude={"dept_id"})
        for field, value in update_data.items():
            setattr(existing_dept, field, value)

        existing_dept.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        existing_dept.update_time = datetime.now()

        try:
            await DeptMapper.update_dept(existing_dept, query_db)
            logger.info(f"更新部门成功: {existing_dept.dept_name}")

            # 返回更新后的部门 VO
            return DeptDetailVO.model_validate(existing_dept)
        except Exception as e:
            raise DeptUpdateFailedException from e

    @staticmethod
    async def delete_dept(query_db: AsyncSession, dept_id_list: list[int], current_user: CurrentUser) -> None:
        """删除部门（批量）。

        Args:
            query_db: 数据库会话。
            dept_id_list: 部门 ID 列表。
            current_user: 当前用户。

        Raises:
            DeptIdListEmptyException: 部门 ID 列表为空。
            DeptNotFoundException: 部门不存在。
            DeptHasChildrenException: 部门有子部门。
            DeptHasUsersException: 部门有关联用户。
            DeptDeleteFailedException: 部门删除失败。
        """
        if not dept_id_list:
            raise DeptIdListEmptyException

        for dept_id in dept_id_list:
            # 检查部门是否存在
            dept = await DeptMapper.get_by_id(dept_id, query_db)
            if not dept:
                raise DeptNotFoundException(dept_id=dept_id)

            # 检查是否有子部门
            has_children = await DeptMapper.has_child_depts(dept_id, query_db)
            if has_children:
                raise DeptHasChildrenException(dept_name=dept.dept_name)

            # 检查是否有关联用户
            has_users = await DeptMapper.has_users(dept_id, query_db)
            if has_users:
                raise DeptHasUsersException(dept_name=dept.dept_name)

            # 删除部门
            dept.status = SystemConstants.Status.DELETED
            dept.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            dept.update_time = datetime.now()
            try:
                await DeptMapper.update_dept(dept, query_db)
                logger.info(f"删除部门: {dept.dept_name}")
            except Exception as e:
                raise DeptDeleteFailedException from e

    @staticmethod
    async def check_dept_data_scope(query_db: AsyncSession, dept_id: int, data_scope_sql: str) -> None:
        """检查部门数据权限。

        Args:
            query_db: 数据库会话。
            dept_id: 部门 ID。
            data_scope_sql: 数据权限 SQL。

        Raises:
            DeptNoPermissionException: 无数据权限时抛出。
        """
        dept_list = await DeptMapper.get_dept_list(DeptQueryDTO(dept_id=dept_id), data_scope_sql, query_db)
        if not dept_list:
            raise DeptNoPermissionException

    @staticmethod
    async def get_dept_users(query_db: AsyncSession, dept_id: int) -> list[UserListVO]:
        """获取部门关联的用户列表。

        Args:
            query_db: 数据库会话。
            dept_id: 部门 ID。

        Returns:
            list[UserListVO]: 用户列表 VO。
        """
        # 检查部门是否存在
        dept = await DeptMapper.get_by_id(dept_id, query_db)
        if not dept:
            raise DeptNotFoundException(dept_id=dept_id)

        # 获取部门关联的用户
        users = await DeptMapper.get_dept_users(dept_id, query_db)
        user_list = []
        for user, _user_dept in users:
            user_vo = UserListVO.model_validate(user)
            user_vo.dept_id = dept_id
            user_vo.dept_name = dept.dept_name
            user_list.append(user_vo)

        logger.debug(f"获取部门ID {dept_id} 的用户列表成功，共 {len(user_list)} 条记录")
        return user_list

    @staticmethod
    async def remove_user_from_dept(
        query_db: AsyncSession, dept_id: int, user_id: int, current_user: CurrentUser
    ) -> None:
        """移除用户的部门关联。

        Args:
            query_db: 数据库会话。
            dept_id: 部门 ID。
            user_id: 用户 ID。
            current_user: 当前用户。

        Raises:
            DeptNotFoundException: 部门不存在时抛出。
        """
        # 检查部门是否存在
        dept = await DeptMapper.get_by_id(dept_id, query_db)
        if not dept:
            raise DeptNotFoundException(dept_id=dept_id)

        # 移除用户部门关联
        await DeptMapper.remove_user_from_dept(user_id, dept_id, query_db)
        logger.info(f"移除用户ID {user_id} 与部门ID {dept_id} 的关联成功")
