"""字典管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo.base import VO

# ============================================================================
# 字典类型相关 VO
# ============================================================================


class DictTypeListVO(VO):
    """字典类型列表项 VO"""

    dict_id: int = Field(description="字典主键")
    dict_name: str = Field(description="字典名称")
    dict_type: str = Field(description="字典类型")
    status: str = Field(description="字典类型数据状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")
    remark: str | None = Field(default=None, description="备注")


class DictTypeDetailVO(VO):
    """字典类型详情 VO"""

    dict_id: int = Field(description="字典主键")
    dict_name: str = Field(description="字典名称")
    dict_type: str = Field(description="字典类型")
    status: str = Field(description="字典类型数据状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


# ============================================================================
# 字典数据相关 VO
# ============================================================================


class DictDataListVO(VO):
    """字典数据列表项 VO"""

    dict_code: int = Field(description="字典编码")
    dict_sort: int = Field(description="字典排序")
    dict_label: str = Field(description="字典标签")
    dict_value: str = Field(description="字典键值")
    dict_type: str = Field(description="字典类型")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str = Field(description="颜色主题（success | processing | error | warning | default）")
    icon: str | None = Field(default=None, description="图标（Ant Design Vue图标名称）")
    bordered: str = Field(default="N", description="是否带边框（Y是 N否）")
    is_default: str = Field(description="是否默认（Y是 N否）")
    status: str = Field(description="字典值数据状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")
    remark: str | None = Field(default=None, description="备注")


class DictDataDetailVO(VO):
    """字典数据详情 VO"""

    dict_code: int = Field(description="字典编码")
    dict_sort: int = Field(description="字典排序")
    dict_label: str = Field(description="字典标签")
    dict_value: str = Field(description="字典键值")
    dict_type: str = Field(description="字典类型")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str = Field(description="颜色主题（success | processing | error | warning | default）")
    icon: str | None = Field(default=None, description="图标（Ant Design Vue图标名称）")
    bordered: str = Field(default="N", description="是否带边框（Y是 N否）")
    is_default: str = Field(description="是否默认（Y是 N否）")
    status: str = Field(description="字典值数据状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class DictDataSimpleVO(VO):
    """字典数据简化 VO（用于下拉框等场景）"""

    dict_label: str = Field(description="字典标签")
    dict_value: str = Field(description="字典键值")
    style: dict | None = Field(default=None, description="样式属性（JSONB格式）")
    color: str = Field(description="颜色主题（success | processing | error | warning | default）")
    icon: str | None = Field(default=None, description="图标（Ant Design Vue图标名称）")
    bordered: str = Field(default="N", description="是否带边框（Y是 N否）")
