"""功能权限管理服务模块。

该模块提供功能权限（菜单/按钮）的增删改查功能，支持树形结构展示。

职责：
1. 处理 DTO 到 ORM 的转换（创建/更新时）。
2. 组装 VO 返回（查询时）。
3. 处理业务逻辑。
"""

from datetime import datetime
import logging
from typing import TYPE_CHECKING

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.function import (
    FunctionAssignedToRoleException,
    FunctionCreateFailedException,
    FunctionDeleteFailedException,
    FunctionExternalLinkInvalidException,
    FunctionHasChildrenException,
    FunctionNameAlreadyExistsException,
    FunctionNotFoundException,
    FunctionParentItselfException,
    FunctionUpdateFailedException,
)
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants
from graphedu.common.models.dto.systemv2.function import (
    FunctionCreateDTO,
    FunctionQueryDTO,
    FunctionUpdateDTO,
)
from graphedu.common.models.orm.system import SysFunction, SysRoleFunction
from graphedu.common.models.vo.systemv2.function import (
    FunctionDetailVO,
    FunctionTreeBriefVO,
    FunctionTreeVO,
    RoleFunctionTreeVO,
)
from graphedu.mapper.system.function import FunctionMapper
from graphedu.mapper.system.role import RoleMapper

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _build_function_tree(function_list: list[SysFunction], parent_id: int = 0) -> list[FunctionTreeVO]:
    """将功能列表转换为树形结构。

    Args:
        function_list: 功能列表。
        parent_id: 父功能 ID。

    Returns:
        list[FunctionTreeVO]: 功能树形列表。
    """
    tree = []
    for func in function_list:
        if func.parent_id == parent_id:
            children = _build_function_tree(function_list, func.function_id)
            node = FunctionTreeVO(
                function_id=func.function_id,
                function_name=func.function_name,
                parent_id=func.parent_id,
                function_key=func.function_key,
                function_type=func.function_type,
                route_path=func.route_path,
                route_cache=func.route_cache,
                route_external=func.route_external,
                component=func.component,
                layout_component=func.layout_component,
                icon=func.icon,
                sort_order=func.sort_order,
                visible=func.visible,
                status=func.status,
                scene=func.scene,
                create_time=func.create_time,
                children=children if children else [],
                has_children=bool(children),
            )
            tree.append(node)
    return tree


def _build_function_brief_tree(function_list: list[SysFunction], parent_id: int = 0) -> list[FunctionTreeBriefVO]:
    """将功能列表转换为简要树形结构（用于下拉选择）。

    Args:
        function_list: 功能列表。
        parent_id: 父功能 ID。

    Returns:
        list[FunctionTreeBriefVO]: 功能简要树形列表。
    """
    tree = []
    for func in function_list:
        if func.parent_id == parent_id:
            children = _build_function_brief_tree(function_list, func.function_id)
            node = FunctionTreeBriefVO(
                function_id=func.function_id,
                function_name=func.function_name,
                parent_id=func.parent_id,
                function_type=func.function_type,
                children=children if children else [],
            )
            tree.append(node)
    return tree


class FunctionService:
    """功能权限管理服务类。

    提供功能权限（菜单/按钮）的增删改查功能，支持树形结构展示和角色权限分配。
    """

    @staticmethod
    async def get_function_tree(query_db: AsyncSession, query_params: FunctionQueryDTO) -> list[FunctionTreeVO]:
        """获取功能树形列表。

        Args:
            query_db: 数据库会话。
            query_params: 查询参数。

        Returns:
            list[FunctionTreeVO]: 功能树形列表。
        """
        function_list = await FunctionMapper.get_function_list(query_params, query_db)
        return _build_function_tree(list(function_list))

    @staticmethod
    async def get_function_tree_for_select(query_db: AsyncSession, parent_id: int = 0) -> list[FunctionTreeBriefVO]:
        """获取功能树（用于下拉选择）。

        Args:
            query_db: 数据库会话。
            parent_id: 父功能 ID。

        Returns:
            list[FunctionTreeBriefVO]: 功能简要树形列表（完整树形结构，包含嵌套的 children）。
        """
        # 获取所有功能列表（不限制 parent_id）
        function_list = await FunctionMapper.get_function_list(FunctionQueryDTO(), query_db)
        # 使用 _build_function_brief_tree 构建完整的树形结构
        return _build_function_brief_tree(list(function_list), parent_id)

    @staticmethod
    async def get_function_tree_lazy(
        query_db: AsyncSession, parent_id: int = 0, scene: str | None = None
    ) -> list[FunctionTreeVO]:
        """获取功能树（异步加载模式，只返回指定父级的直接子节点）。

        Args:
            query_db: 数据库会话。
            parent_id: 父功能 ID（0 表示顶层）。
            scene: 应用场景（可选，过滤功能列表）。

        Returns:
            list[FunctionTreeVO]: 功能列表（扁平，带 hasChildren 标记）。
        """
        # 获取指定父级的直接子节点
        function_list = await FunctionMapper.get_function_children(parent_id, scene, query_db)
        result = []
        for func in function_list:
            # 检查是否有子节点
            has_children = await FunctionMapper.has_children(func.function_id, query_db)
            node = FunctionTreeVO(
                function_id=func.function_id,
                function_name=func.function_name,
                parent_id=func.parent_id,
                function_key=func.function_key,
                function_type=func.function_type,
                route_path=func.route_path,
                route_cache=func.route_cache,
                route_external=func.route_external,
                component=func.component,
                layout_component=func.layout_component,
                icon=func.icon,
                sort_order=func.sort_order,
                visible=func.visible,
                status=func.status,
                scene=func.scene,
                create_time=func.create_time,
                has_children=has_children,
                children=[] if has_children else None,
                # 异步模式下返回 None 或 []，前端根据 children 情况决定是否需要加载 children
            )
            result.append(node)
        return result

    @staticmethod
    async def get_role_function_tree(
        query_db: AsyncSession, current_user: CurrentUser, role_id: int
    ) -> RoleFunctionTreeVO:
        """获取角色功能树（用于角色分配权限）。

        Args:
            query_db: 数据库会话。
            current_user: 当前用户。
            role_id: 角色 ID。

        Returns:
            RoleFunctionTreeVO: 包含功能树和已选中功能 ID 列表的 VO。
        """
        if not current_user.detail.user or not current_user.detail.roles or not current_user.detail.user.user_id:
            return RoleFunctionTreeVO()
        # 获取所有功能树
        function_list = await FunctionMapper.get_function_list_for_tree_by_user_roles(
            current_user.detail.role_ids, query_db
        )
        function_tree = _build_function_tree(list(function_list))
        # 获取角色已关联的功能ID列表
        checked_ids = await RoleMapper.get_role_function_ids(role_id, query_db)

        return RoleFunctionTreeVO(checked_ids=list(checked_ids), function_trees=function_tree)

    @staticmethod
    async def get_function_detail(query_db: AsyncSession, function_id: int) -> FunctionDetailVO | None:
        """获取功能详细信息。

        Args:
            query_db: 数据库会话。
            function_id: 功能 ID。

        Returns:
            FunctionDetailVO | None: 功能详细信息 VO。

        Raises:
            FunctionNotFoundException: 功能不存在时抛出。
        """
        function = await FunctionMapper.get_by_id(function_id, query_db)
        if not function:
            raise FunctionNotFoundException(function_id=function_id)
        # ORM -> VO 转换
        return FunctionDetailVO.model_validate(function)

    @staticmethod
    async def add_function(
        query_db: AsyncSession,
        function_dto: FunctionCreateDTO,
        current_user: CurrentUser,
        redis_session: AsyncRedis | None = None,
    ) -> None:
        """新增功能。

        Args:
            query_db: 数据库会话。
            function_dto: 功能 DTO。
            current_user: 当前用户。
            redis_session: Redis 会话（可选，用于缓存失效）

        Raises:
            FunctionNameAlreadyExistsException: 功能名称已存在。
            FunctionExternalLinkInvalidException: 外链格式无效。
            FunctionCreateFailedException: 功能创建失败。
        """
        # 检查功能名称唯一性（同一父级下）
        is_unique = await FunctionMapper.check_function_name_unique(
            function_dto.function_name, function_dto.parent_id, None, query_db
        )
        if not is_unique:
            raise FunctionNameAlreadyExistsException(function_name=function_dto.function_name)

        # 如果是外链，检查路径格式
        if function_dto.route_external == SystemConstants.Status.YES and function_dto.route_path:  # noqa: SIM102
            if not function_dto.route_path.startswith(("http://", "https://")):
                raise FunctionExternalLinkInvalidException(function_name=function_dto.function_name)

        # DTO → ORM (使用 model_dump)
        new_function = SysFunction(
            **function_dto.model_dump(),
            create_by=current_user.detail.user.user_id if current_user.detail.user else None,
            create_time=datetime.now(),
            update_by=current_user.detail.user.user_id if current_user.detail.user else None,
            update_time=datetime.now(),
        )

        try:
            # 新增功能
            await FunctionMapper.add_function(new_function, query_db)
            logger.info(f"新增功能成功: {function_dto.function_name}")
        except Exception as e:
            raise FunctionCreateFailedException from e

        # 清除所有角色的菜单/路由缓存（功能新增会影响所有角色）
        if redis_session:
            from graphedu.security.auth import SecurityService

            await SecurityService.invalidate_all_role_cache(
                redis_session=redis_session,
            )

    @staticmethod
    async def update_function(
        query_db: AsyncSession,
        function_dto: FunctionUpdateDTO,
        current_user: CurrentUser,
        redis_session: AsyncRedis | None = None,
    ) -> FunctionDetailVO:
        """更新功能信息。

        Args:
            query_db: 数据库会话。
            function_dto: 功能 DTO。
            current_user: 当前用户。
            redis_session: Redis 会话（可选，用于缓存失效）

        Returns:
            FunctionDetailVO: 更新后的功能详细信息 VO。

        Raises:
            FunctionNotFoundException: 功能不存在。
            FunctionNameAlreadyExistsException: 功能名称已存在。
            FunctionParentItselfException: 不能将自己设为父功能。
            FunctionExternalLinkInvalidException: 外链格式无效。
            FunctionUpdateFailedException: 功能更新失败。
        """
        # 检查功能是否存在
        existing_function = await FunctionMapper.get_by_id(function_dto.function_id, query_db)
        if not existing_function:
            raise FunctionNotFoundException(function_id=function_dto.function_id)

        # 检查功能名称唯一性（如果修改了名称）
        if function_dto.function_name and function_dto.function_name != existing_function.function_name:
            parent_id = function_dto.parent_id if function_dto.parent_id is not None else existing_function.parent_id
            is_unique = await FunctionMapper.check_function_name_unique(
                function_dto.function_name, parent_id, function_dto.function_id, query_db
            )
            if not is_unique:
                raise FunctionNameAlreadyExistsException(function_name=function_dto.function_name)

        # 检查是否将父功能设置为自己
        if function_dto.parent_id is not None and function_dto.parent_id == function_dto.function_id:
            raise FunctionParentItselfException

        # 如果是外链，检查路径格式
        route_external = (
            function_dto.route_external if function_dto.route_external else existing_function.route_external
        )
        route_path = function_dto.route_path if function_dto.route_path else existing_function.route_path
        if (
            route_external == SystemConstants.Status.YES
            and route_path
            and not route_path.startswith(("http://", "https://"))
        ):
            raise FunctionExternalLinkInvalidException

        # DTO -> ORM 转换（更新提供的字段）
        update_dict = function_dto.model_dump(exclude_unset=True, exclude={"function_id"})
        for key, value in update_dict.items():
            if hasattr(existing_function, key):
                setattr(existing_function, key, value)

        existing_function.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        existing_function.update_time = datetime.now()

        try:
            # 更新功能
            await FunctionMapper.update_function(existing_function, query_db)
            logger.info(f"更新功能成功: {function_dto.function_id}")
        except Exception as e:
            raise FunctionUpdateFailedException from e

        # 精确清除缓存：只清除拥有该功能的角色 + 超级管理员
        if redis_session:
            from graphedu.security.auth import SecurityService

            # 查询拥有该功能的角色ID列表
            result = await query_db.execute(
                select(SysRoleFunction.role_id).where(SysRoleFunction.function_id == existing_function.function_id)
            )
            affected_role_ids = set(result.scalars().all())
            # 加上超级管理员（role_id=0）
            affected_role_ids.add(0)

            await SecurityService.invalidate_role_cache(
                role_ids=affected_role_ids,
                redis_session=redis_session,
            )

        # 返回更新后的功能 VO
        return FunctionDetailVO.model_validate(existing_function)

    @staticmethod
    async def delete_function(
        query_db: AsyncSession,
        current_user: CurrentUser,
        function_ids: list[int],
        redis_session: AsyncRedis | None = None,
    ) -> None:
        """删除功能。

        Args:
            query_db: 数据库会话。
            current_user: 当前用户。
            function_ids: 功能 ID 列表。
            redis_session: Redis 会话（可选，用于缓存失效）

        Raises:
            FunctionNotFoundException: 功能不存在。
            FunctionHasChildrenException: 功能有子功能。
            FunctionAssignedToRoleException: 功能已分配给角色。
            FunctionDeleteFailedException: 功能删除失败。
        """
        # 收集需要清除缓存的场景
        scenes_to_clear = set()

        for function_id in function_ids:
            # 检查功能是否存在
            function = await FunctionMapper.get_by_id(function_id, query_db)
            if not function:
                raise FunctionNotFoundException(function_id=function_id)

            # 收集场景信息用于缓存失效
            if function.scene:
                scenes_to_clear.add(function.scene)

            # 检查是否有子功能
            has_children = await FunctionMapper.has_children(function_id, query_db)
            if has_children:
                raise FunctionHasChildrenException(function_name=function.function_name)

            # 检查是否被角色使用
            is_used = await FunctionMapper.check_function_exist_role(function_id, query_db)
            if is_used:
                raise FunctionAssignedToRoleException(function_name=function.function_name)

            # 删除功能
            function.status = SystemConstants.Status.DELETED
            function.update_time = datetime.now()
            function.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            try:
                await FunctionMapper.update_function(function, query_db)
                logger.info(f"删除功能成功: {function_id}")
            except Exception as e:
                raise FunctionDeleteFailedException from e

        # 只清除超级管理员缓存（删除前已确保功能未被普通角色使用）
        if redis_session:
            from graphedu.security.auth import SecurityService

            await SecurityService.invalidate_role_cache(
                role_ids=[0],  # 只清除超级管理员
                redis_session=redis_session,
            )
