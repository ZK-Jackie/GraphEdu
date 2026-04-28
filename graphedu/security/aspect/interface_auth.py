"""接口权限校验模块

本模块提供基于权限标识和角色的接口访问控制功能。

核心类：
- CheckUserInterfacePermit: 基于权限标识的接口校验类
- CheckRoleInterfaceAuth: 基于角色标识的接口校验类

使用方式：
```python
from fastapi import APIRouter, Depends
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit, CheckRoleInterfaceAuth

router = APIRouter()

# 方式1：基于权限标识校验（单个权限）
@router.post("/user/add")
async def add_user(
    _: None = Depends(CheckUserInterfacePermit("system:user:add"))
):
    pass

# 方式2：基于权限标识校验（多个权限，满足其一即可）
@router.post("/user/edit")
async def edit_user(
    _: None = Depends(CheckUserInterfacePermit(["system:user:edit", "system:user:update"]))
):
    pass

# 方式3：基于权限标识校验（多个权限，需全部满足）
@router.delete("/user/delete")
async def delete_user(
    _: None = Depends(CheckUserInterfacePermit(["system:user:delete", "system:user:remove"], is_strict=True))
):
    pass

# 方式4：基于角色标识校验
@router.get("/admin/settings")
async def get_admin_settings(
    _: None = Depends(CheckRoleInterfaceAuth("admin"))
):
    pass
```

权限规则：
- 管理员用户（拥有 admin 角色）具有通配符权限 "*:*:*"，可访问所有接口
- 普通用户根据其角色所分配的权限标识进行访问控制
- 校验失败时抛出 NoInterfacePermissionException 异常
"""

from fastapi import Depends

from graphedu.common.exceptions.services.system.auth import NoInterfacePermissionException
from graphedu.common.models.bo import CurrentUser
from graphedu.security.auth import SecurityService


class CheckUserInterfacePermit:
    """校验当前用户是否具有相应的接口权限

    基于权限标识进行接口访问控制，支持单个权限、多个权限（OR/AND）模式。
    """

    def __init__(self, perm: str | list, is_strict: bool = False):
        """初始化权限校验器

        Args:
            perm: 权限标识，可以是字符串或字符串列表
            is_strict: 当权限为列表时，是否启用严格模式
                - False（默认）：满足任一权限即可通过（OR 逻辑）
                - True：需要满足所有权限才通过（AND 逻辑）
        """
        self.perm = perm
        self.is_strict = is_strict

    def __call__(self, current_user: CurrentUser = Depends(SecurityService.get_current_user)):
        """执行权限校验

        Args:
            current_user: 当前用户信息对象

        Returns:
            bool: 校验通过返回 True

        Raises:
            NoInterfacePermissionException: 当用户不具有相应权限时
        """
        user_auth_list = current_user.permissions
        if "*:*:*" in user_auth_list:
            return True
        if isinstance(self.perm, str) and self._match_permission(self.perm, user_auth_list):
            return True
        if isinstance(self.perm, list):
            if self.is_strict and all(self._match_permission(p, user_auth_list) for p in self.perm):
                return True
            if not self.is_strict and any(self._match_permission(p, user_auth_list) for p in self.perm):
                return True
        raise NoInterfacePermissionException

    @staticmethod
    def _match_permission(perm_str: str, user_auth_list: list[str]) -> bool:
        """检查用户是否拥有指定权限，支持场景前缀匹配

        匹配规则：
        1. 精确匹配：perm_str 直接存在于权限列表中
        2. 场景前缀匹配：perm_str 为 3 段格式（如 system:user:list），
           用户权限为 4 段格式（如 admin:system:user:list），
           通过后缀匹配自动关联

        Examples:
            _match_permission("system:user:list", ["admin:system:user:list"]) -> True
            _match_permission("admin:system:user:list", ["admin:system:user:list"]) -> True
        """
        if perm_str in user_auth_list:
            return True
        suffix = ":" + perm_str
        return any(p.endswith(suffix) for p in user_auth_list)


class CheckRoleInterfaceAuth:
    """根据角色校验当前用户是否具有相应的接口权限

    基于角色标识进行接口访问控制，支持单个角色、多个角色（OR/AND）模式。
    """

    def __init__(self, role_key: str | list, is_strict: bool = False):
        """初始化角色权限校验器

        Args:
            role_key: 角色标识，可以是字符串或字符串列表
            is_strict: 当角色为列表时，是否启用严格模式
                - False（默认）：满足任一角色即可通过（OR 逻辑）
                - True：需要满足所有角色才通过（AND 逻辑）
        """
        self.role_key = role_key
        self.is_strict = is_strict

    def __call__(self, current_user: CurrentUser = Depends(SecurityService.get_current_user)):
        """执行角色权限校验

        Args:
            current_user: 当前用户信息对象

        Returns:
            bool: 校验通过返回 True

        Raises:
            NoInterfacePermissionException: 当用户不具有相应角色时
        """
        user_role_list = current_user.detail.roles
        user_role_key_list = [role.role_key for role in user_role_list]
        if isinstance(self.role_key, str) and self.role_key in user_role_key_list:
            return True
        if isinstance(self.role_key, list):
            if self.is_strict:
                if all(role_key_str in user_role_key_list for role_key_str in self.role_key):
                    return True
            else:
                if any(role_key_str in user_role_key_list for role_key_str in self.role_key):
                    return True
        raise NoInterfacePermissionException
