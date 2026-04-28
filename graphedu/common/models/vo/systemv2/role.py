"""角色管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo.base import VO


class RoleListVO(VO):
    """角色列表项 VO"""

    role_id: int = Field(description="角色ID")
    role_name: str = Field(description="角色名称")
    role_key: str = Field(description="角色标识")
    role_sort: int = Field(description="显示顺序")
    data_scope: str = Field(description="数据范围")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class RoleDetailVO(VO):
    """角色详细信息 VO，包含关联的功能权限"""

    role_id: int = Field(description="角色ID")
    role_name: str = Field(description="角色名称")
    role_key: str = Field(description="角色标识")
    role_sort: int = Field(description="显示顺序")
    data_scope: str = Field(description="数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人）")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")
    function_ids: list[int] | None = Field(default=None, description="已分配的功能权限ID列表")


class RoleSimpleVO(VO):
    """角色简要信息 VO"""

    role_id: int = Field(description="角色ID")
    role_name: str = Field(description="角色名称")
    role_key: str = Field(description="角色标识")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")


class RoleDeptVO(VO):
    """角色关联部门 VO"""

    checked_ids: list[int] = Field(default_factory=list, description="角色ID")
    # 自己去 dept 接口获取部门树
    # dept_ids: Optional[list[int]] = Field(default=None, description='已分配的部门ID列表')


# class RoleUserListVO(UserListVO):
#     """角色关联用户列表 VO"""
