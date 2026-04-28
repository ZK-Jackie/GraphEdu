"""部门管理相关 DTO 模型 (Data Transfer Objects - 请求参数验证)"""

from typing import Literal

from pydantic import EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

from graphedu.common.models.dto.base import DTO

# ============================================================================
# 查询相关 DTO
# ============================================================================


class DeptQueryDTO(DTO):
    """部门查询 DTO (用于列表查询)

    用于查询部门列表，支持多条件查询

    Attributes:
        dept_id: 部门 ID
        dept_name: 部门名称（模糊查询）
        parent_id: 父部门 ID，0 或 None 表示根节点
        status: 部门状态（0正常 1停用）
    """

    dept_id: int | None = Field(default=None, description="部门ID")
    dept_name: str | None = Field(default=None, description="部门名称（模糊查询）")
    parent_id: int | None = Field(default=None, description="父部门ID，0或None表示根节点")
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")


# ============================================================================
# 创建/更新相关 DTO
# ============================================================================
class DeptCreateDTO(DTO):
    """创建部门 DTO (用于新增部门)

    用于创建新的部门

    Attributes:
        parent_id: 父部门 ID（0表示根节点）
        dept_name: 部门名称
        dept_key: 部门编码（唯一标识）
        leader: 负责人（可选）
        phone: 联系电话（可选）
        email: 联系邮箱（可选）
        status: 部门状态（0正常 1停用）
        sort_order: 显示顺序
        remark: 备注（可选）
    """

    parent_id: int = Field(default=0, description="父部门ID（0表示根节点）")
    dept_name: str = Field(description="部门名称", min_length=1, max_length=64)
    dept_key: str = Field(description="部门编码（唯一标识）", min_length=1, max_length=64)
    leader: str | None = Field(default=None, description="负责人", max_length=32)
    phone: PhoneNumber | None = Field(default=None, description="联系电话", max_length=16)
    email: EmailStr | None = Field(default=None, description="联系邮箱", max_length=64)
    status: Literal["0", "1"] = Field(default="0", description="对照sys_data_status（0正常 1停用）")
    sort_order: int = Field(default=0, description="显示顺序")
    remark: str | None = Field(default=None, description="备注", max_length=500)


class DeptUpdateDTO(DTO):
    """更新部门 DTO (用于修改部门信息)

    用于更新部门信息

    Attributes:
        dept_id: 部门 ID
        parent_id: 父部门 ID（可选）
        dept_name: 部门名称（可选）
        dept_key: 部门编码（可选）
        leader: 负责人（可选）
        phone: 联系电话（可选）
        email: 联系邮箱（可选）
        status: 部门状态（可选）
        sort_order: 显示顺序（可选）
        remark: 备注（可选）
    """

    dept_id: int = Field(description="部门ID")
    parent_id: int | None = Field(default=None, description="父部门ID")
    dept_name: str | None = Field(default=None, description="部门名称", max_length=64)
    dept_key: str | None = Field(default=None, description="部门编码", max_length=64)
    leader: str | None = Field(default=None, description="负责人", max_length=32)
    phone: PhoneNumber | None = Field(default=None, description="联系电话", max_length=16)
    email: EmailStr | None = Field(default=None, description="联系邮箱", max_length=64)
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    sort_order: int | None = Field(default=None, description="显示顺序")
    remark: str | None = Field(default=None, description="备注", max_length=500)


class DeptStatusChangeDTO(DTO):
    """修改部门状态 DTO (用于启用/停用部门)

    用于启用或停用部门

    Attributes:
        dept_id: 部门 ID
        status: 部门状态（0正常 1停用）
    """

    dept_id: int = Field(description="部门ID")
    status: Literal["0", "1"] = Field(description="对照sys_data_status（0正常 1停用）")
