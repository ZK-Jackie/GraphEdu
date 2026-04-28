"""部门管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo.base import VO


class DeptTreeVO(VO):
    """部门树节点 VO"""

    dept_id: int = Field(description="部门ID")
    dept_name: str = Field(description="部门名称")
    parent_id: int = Field(description="父部门ID")
    dept_key: str = Field(description="部门编码")
    leader: str | None = Field(default=None, description="负责人")
    phone: str | None = Field(default=None, description="联系电话")
    email: str | None = Field(default=None, description="联系邮箱")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    sort_order: int = Field(description="显示顺序")
    create_time: datetime | None = Field(default=None, description="创建时间")
    has_children: bool = Field(default=False, description="是否有子部门")
    children: list["DeptTreeVO"] | None = Field(default=None, description="子部门列表，一般推荐自己组装")


class DeptDetailVO(VO):
    """部门详细信息 VO"""

    dept_id: int = Field(description="部门ID")
    parent_id: int = Field(description="父部门ID")
    dept_name: str = Field(description="部门名称")
    dept_key: str = Field(description="部门编码")
    leader: str | None = Field(default=None, description="负责人")
    phone: str | None = Field(default=None, description="联系电话")
    email: str | None = Field(default=None, description="联系邮箱")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    sort_order: int = Field(description="显示顺序")
    create_by: int | None = Field(default=None, description="创建者ID")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者ID")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class DeptSimpleVO(VO):
    """部门简要信息 VO"""

    dept_id: int = Field(description="部门ID")
    dept_name: str = Field(description="部门名称")
    dept_key: str = Field(description="部门编码")
    parent_id: int = Field(description="父部门ID")


class DeptInfoVO(VO):
    """部门信息 VO (用于列表展示)"""

    dept_id: int = Field(description="部门ID")
    parent_id: int = Field(description="父部门ID")
    dept_name: str = Field(description="部门名称")
    dept_key: str = Field(description="部门编码")
    leader: str | None = Field(default=None, description="负责人")
    phone: str | None = Field(default=None, description="联系电话")
    email: str | None = Field(default=None, description="联系邮箱")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    sort_order: int = Field(description="显示顺序")
    create_time: datetime | None = Field(default=None, description="创建时间")
    remark: str | None = Field(default=None, description="备注")


# 更新前向引用
DeptTreeVO.model_rebuild()
