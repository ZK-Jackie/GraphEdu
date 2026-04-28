"""角色管理相关 DTO 模型

职责：
1. 定义 API 请求验证的数据结构
2. 为 CRUD 操作设置不同的字段约束
"""

from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery

from .user import UserQueryDTO


class RoleQueryDTO(PageQuery):
    """角色查询 DTO

    用于查询角色列表，支持分页和多条件查询

    Attributes:
        role_name: 角色名称（模糊查询）
        role_key: 角色标识（模糊查询）
        status: 角色状态（0正常 1停用）
    """

    role_name: str | None = Field(default=None, description="角色名称（模糊查询）")
    role_key: str | None = Field(default=None, description="角色标识（模糊查询）")
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")


class RoleCreateDTO(DTO):
    """创建角色 DTO - 所有必填字段必须有值

    用于创建新角色

    Attributes:
        role_name: 角色名称
        role_key: 角色标识（student/teacher/admin）
        role_sort: 显示顺序
        data_scope: 数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人）
        status: 角色状态（0正常 1停用）
        remark: 备注（可选）
        function_ids: 功能权限 ID 列表（可选）
    """

    role_name: str = Field(description="角色名称", min_length=1, max_length=30)
    role_key: str = Field(description="角色标识（student/teacher/admin）", min_length=1, max_length=100)
    role_sort: int = Field(default=0, description="显示顺序", ge=0)
    data_scope: Literal["1", "2", "3", "4", "5"] = Field(
        default="1", description="数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人）"
    )
    status: Literal["0", "1"] = Field(default="0", description="对照sys_data_status（0正常 1停用）")
    remark: str | None = Field(default=None, description="备注", max_length=500)
    function_ids: list[int] | None = Field(default=None, description="功能权限ID列表")


class RoleUpdateDTO(DTO):
    """更新角色 DTO - 所有字段可选，仅更新提供的字段

    用于更新角色信息

    Attributes:
        role_id: 角色 ID
        role_name: 角色名称（可选）
        role_key: 角色标识（可选）
        role_sort: 显示顺序（可选）
        data_scope: 数据范围（可选）
        status: 角色状态（可选）
        remark: 备注（可选）
        function_ids: 功能权限 ID 列表（可选）
    """

    role_id: int = Field(description="角色ID")
    role_name: str | None = Field(default=None, description="角色名称", max_length=30)
    role_key: str | None = Field(default=None, description="角色标识", max_length=100)
    role_sort: int | None = Field(default=None, description="显示顺序", ge=0)
    data_scope: Literal["1", "2", "3", "4", "5"] | None = Field(
        default=None, description="数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人）"
    )
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    remark: str | None = Field(default=None, description="备注", max_length=500)
    function_ids: list[int] | None = Field(default=None, description="功能权限ID列表")


class RoleStatusChangeDTO(DTO):
    """修改角色状态 DTO - 仅包含状态字段

    用于启用或停用角色

    Attributes:
        role_id: 角色 ID
        status: 角色状态（0正常 1停用）
    """

    role_id: int = Field(description="角色ID")
    status: Literal["0", "1"] = Field(description="对照sys_data_status（0正常 1停用）")


class RoleDatascopeChangeDTO(DTO):
    """修改角色数据权限范围 DTO

    用于更新角色的数据权限范围

    Attributes:
        role_id: 角色 ID
        dept_ids: 部门 ID 列表
        data_scope: 数据范围（1：全部 2：自定 3：本部门 4：本部门及以下）
    """

    role_id: int = Field(description="角色ID")
    dept_ids: list[int] = Field(description="部门ID列表")
    data_scope: Literal["1", "2", "3", "4"] = Field(
        default="1", description="数据范围（1：全部 2：自定 3：本部门 4：本部门及以下）"
    )


class RoleUserQueryDTO(UserQueryDTO):
    """角色关联的用户查询 DTO

    用于查询某个角色下的所有用户

    Attributes:
        role_id: 角色 ID（精确查询）
    """

    role_id: int | None = Field(default=None, description="角色ID（精确查询）")
