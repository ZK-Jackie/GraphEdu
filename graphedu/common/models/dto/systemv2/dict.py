"""字典管理相关 DTO 模型"""

from datetime import datetime
import re
from typing import Literal

from pydantic import Field, field_validator

from graphedu.common.models.dto.base import DTO, PageQuery

# ============================================================================
# 字典类型相关 DTO
# ============================================================================


class DictTypeQueryDTO(PageQuery):
    """字典类型查询 DTO"""

    dict_name: str | None = Field(default=None, description="字典名称（模糊查询）")
    dict_type: str | None = Field(default=None, description="字典类型（模糊查询）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    begin_time: str | None = Field(default=None, description="开始时间（YYYY-MM-DD）")
    end_time: str | None = Field(default=None, description="结束时间（YYYY-MM-DD）")


class DictTypeCreateDTO(DTO):
    """创建字典类型 DTO"""

    dict_name: str = Field(description="字典名称", min_length=1, max_length=100)
    dict_type: str = Field(description="字典类型", min_length=1, max_length=100)
    status: Literal["0", "1"] = Field(default="0", description="对照sys_data_status（0正常 1停用）")
    remark: str | None = Field(default=None, description="备注", max_length=500)

    @field_validator("dict_type")
    @classmethod
    def validate_dict_type(cls, v: str) -> str:
        """验证字典类型格式：必须以字母开头，且只能为（小写字母，数字，下划线）"""
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("字典类型必须以字母开头，且只能为（小写字母，数字，下划线）")
        return v


class DictTypeUpdateDTO(DTO):
    """更新字典类型 DTO"""

    dict_id: int = Field(description="字典主键")
    dict_name: str | None = Field(default=None, description="字典名称", max_length=100)
    dict_type: str | None = Field(default=None, description="字典类型", max_length=100)
    status: Literal["0", "1"] | None = Field(default=None, description="状态")
    remark: str | None = Field(default=None, description="备注", max_length=500)

    @field_validator("dict_type")
    @classmethod
    def validate_dict_type(cls, v: str | None) -> str | None:
        """验证字典类型格式"""
        if v and not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("字典类型必须以字母开头，且只能为（小写字母，数字，下划线）")
        return v


class DictTypeDetailDTO(DTO):
    """字典类型详情 DTO"""

    dict_id: int = Field(description="字典主键")
    dict_name: str = Field(description="字典名称")
    dict_type: str = Field(description="字典类型")
    status: Literal["0", "1"] = Field(description="状态")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


# ============================================================================
# 字典数据相关 DTO
# ============================================================================


class DictDataQueryDTO(PageQuery):
    """字典数据查询 DTO"""

    dict_type: str | None = Field(default=None, description="字典类型（精确查询）")
    dict_label: str | None = Field(default=None, description="字典标签（模糊查询）")
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    begin_time: datetime | None = Field(default=None, description="开始时间（YYYY-MM-DD）")
    end_time: datetime | None = Field(default=None, description="结束时间（YYYY-MM-DD）")


class DictDataCreateDTO(DTO):
    """创建字典数据 DTO"""

    dict_label: str = Field(description="字典标签", min_length=1, max_length=100)
    dict_value: str = Field(description="字典键值", min_length=1, max_length=100)
    dict_type: str = Field(description="字典类型", min_length=1, max_length=100)
    dict_sort: int = Field(default=0, description="字典排序")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str = Field(
        default="default", description="颜色主题（success | processing | error | warning | default）", max_length=32
    )
    icon: str | None = Field(default=None, description="图标（Ant Design Vue图标名称）", max_length=64)
    bordered: Literal["Y", "N"] = Field(default="N", description="是否带边框（Y是 N否）")
    is_default: Literal["Y", "N"] = Field(default="N", description="是否默认（Y是 N否）")
    status: Literal["0", "1"] = Field(default="0", description="对照sys_data_status（0正常 1停用）")
    remark: str | None = Field(default=None, description="备注", max_length=500)


class DictDataUpdateDTO(DTO):
    """更新字典数据 DTO"""

    dict_code: int = Field(description="字典编码")
    dict_label: str | None = Field(default=None, description="字典标签", max_length=100)
    dict_value: str | None = Field(default=None, description="字典键值", max_length=100)
    dict_type: str | None = Field(default=None, description="字典类型", max_length=100)
    dict_sort: int | None = Field(default=None, description="字典排序")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str | None = Field(default=None, description="颜色主题", max_length=32)
    icon: str | None = Field(default=None, description="Ant Design Vue图标名称", max_length=64)
    bordered: Literal["Y", "N"] = Field(default="N", description="是否带边框（Y是 N否）")
    is_default: Literal["Y", "N"] | None = Field(default=None, description="是否默认")
    status: Literal["0", "1"] | None = Field(default=None, description="状态")
    remark: str | None = Field(default=None, description="备注", max_length=500)


class DictDataDetailDTO(DTO):
    """字典数据详情 DTO"""

    dict_code: int = Field(description="字典编码")
    dict_sort: int = Field(description="字典排序")
    dict_label: str = Field(description="字典标签")
    dict_value: str = Field(description="字典键值")
    dict_type: str = Field(description="字典类型")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str = Field(description="颜色主题（success | processing | error | warning | default）")
    icon: str | None = Field(default=None, description="图标（Ant Design Vue图标名称）")
    bordered: Literal["Y", "N"] = Field(default="N", description="是否带边框（Y是 N否）")
    is_default: Literal["Y", "N"] = Field(description="是否默认")
    status: Literal["0", "1"] = Field(description="状态")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class DictDataSimpleDTO(DTO):
    """字典数据简化 DTO（用于下拉框等场景）"""

    dict_label: str = Field(description="字典标签")
    dict_value: str = Field(description="字典键值")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str = Field(description="颜色主题（success | processing | error | warning | default）")
    icon: str | None = Field(default=None, description="图标（Ant Design Vue图标名称）")
    bordered: Literal["Y", "N"] = Field(default="N", description="是否带边框（Y是 N否）")
