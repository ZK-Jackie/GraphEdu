"""代码生成器 VO 模型（View Objects - 响应模型）

本模块定义了代码生成器相关的 API 响应数据结构，包括：

- GenTableInfoVO: 数据库表简要信息 VO
- GenTableColumnVO: 代码生成业务表字段 VO
- GenTableListVO: 代码生成业务表列表项 VO
- GenTableDetailVO: 代码生成业务表详细信息 VO
- GenCodePreviewVO: 代码预览结果 VO
- GenTableEditInfoVO: 代码生成业务表编辑信息 VO
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.vo.base import VO

# ============================================================================
# 代码生成业务表相关 VO
# ============================================================================


class GenTableInfoVO(VO):
    """数据库表简要信息 VO

    用于显示数据库中未导入的表列表
    """

    table_name: str = Field(description="表名称")
    table_comment: str | None = Field(default=None, description="表描述")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_time: datetime | None = Field(default=None, description="更新时间")


class GenTableColumnVO(VO):
    """代码生成业务表字段 VO

    用于显示代码生成业务表的字段信息
    """

    column_id: int = Field(description="字段ID")
    table_id: int = Field(description="业务表ID")
    column_name: str = Field(description="列名称")
    column_comment: str | None = Field(default=None, description="列描述")
    column_type: str = Field(description="列类型")
    python_type: str = Field(description="PYTHON类型")
    python_field: str = Field(description="PYTHON字段名")
    is_pk: str = Field(default="0", description="是否主键（1是）")
    is_increment: str = Field(default="0", description="是否自增（1是）")
    is_required: str = Field(default="0", description="是否必填（1是）")
    is_unique: str = Field(default="0", description="是否唯一（1是）")
    is_insert: str = Field(default="0", description="是否为插入字段（1是）")
    is_edit: str = Field(default="0", description="是否编辑字段（1是）")
    is_list: str = Field(default="0", description="是否列表字段（1是）")
    is_query: str = Field(default="0", description="是否查询字段（1是）")
    query_type: str = Field(default="EQ", description="查询方式")
    html_type: str = Field(default="input", description="显示类型")
    dict_type: str = Field(default="", description="字典类型")
    sort: int = Field(description="排序")
    create_by: str | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: str | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")

    # 布尔类型字段（方便前端使用）
    pk: bool = Field(default=False, description="是否主键")
    increment: bool = Field(default=False, description="是否自增")
    required: bool = Field(default=False, description="是否必填")
    unique: bool = Field(default=False, description="是否唯一")
    insert: bool = Field(default=False, description="是否为插入字段")
    edit: bool = Field(default=False, description="是否编辑字段")
    list: bool = Field(default=False, description="是否列表字段")
    query: bool = Field(default=False, description="是否查询字段")

    # 首字母大写的字段名（用于代码生成）
    cap_python_field: str | None = Field(default=None, description="字段首字母大写形式")

    # 是否为基类字段
    super_column: bool = Field(default=False, description="是否为基类字段")
    usable_column: bool = Field(default=False, description="是否为基类字段白名单")


class GenTableListVO(VO):
    """代码生成业务表列表项 VO

    用于显示已导入的代码生成业务表列表
    """

    table_id: int = Field(description="业务表ID")
    table_name: str = Field(description="表名称")
    table_comment: str = Field(description="表描述")
    class_name: str = Field(description="实体类名称")
    tpl_category: str = Field(default="crud", description="使用的模板")
    tpl_web_type: str = Field(default="ant-design-vue", description="前端模板类型")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_time: datetime | None = Field(default=None, description="更新时间")


class GenTableDetailVO(VO):
    """代码生成业务表详细信息 VO

    用于显示单个业务表的详细信息
    """

    table_id: int = Field(description="业务表ID")
    table_name: str = Field(description="表名称")
    table_comment: str = Field(description="表描述")
    class_name: str = Field(description="实体类名称")
    tpl_category: Literal["crud", "tree", "sub"] = Field(description="使用的模板")
    tpl_web_type: Literal["element-ui", "element-plus", "ant-design-vue"] = Field(description="前端模板类型")
    package_name: str = Field(description="生成包路径")
    module_name: str = Field(description="生成模块名")
    business_name: str = Field(description="生成业务名")
    function_name: str = Field(description="生成功能名")
    function_author: str = Field(description="生成功能作者")
    gen_type: Literal["0", "1"] = Field(default="0", description="生成代码方式")
    gen_path: str = Field(default="/", description="生成路径")
    sub_table_name: str | None = Field(default=None, description="关联子表的表名")
    sub_table_fk_name: str | None = Field(default=None, description="子表关联的外键名")
    options: str | None = Field(default=None, description="其它生成选项（JSON格式）")
    create_by: str | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: str | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")

    # 关联信息
    columns: list[GenTableColumnVO] = Field(default_factory=list, description="字段列表")
    pk_column: GenTableColumnVO | None = Field(default=None, description="主键信息")
    sub_table: GenTableDetailVO | None = Field(default=None, description="子表信息")

    # 树表相关字段
    tree_code: str | None = Field(default=None, description="树编码字段")
    tree_parent_code: str | None = Field(default=None, description="树父编码字段")
    tree_name: str | None = Field(default=None, description="树名称字段")
    parent_menu_id: int | None = Field(default=None, description="上级菜单ID")
    parent_menu_name: str | None = Field(default=None, description="上级菜单名称")

    # 模板类型标识
    sub: bool = Field(default=False, description="是否为子表")
    tree: bool = Field(default=False, description="是否为树表")
    crud: bool = Field(default=False, description="是否为单表")


# ============================================================================
# 代码预览相关 VO
# ============================================================================


class GenCodePreviewVO(VO):
    """代码预览结果 VO

    用于返回代码预览的结果
    """

    file_name: str = Field(description="文件名")
    file_path: str = Field(description="文件路径")
    content: str = Field(description="文件内容")


class GenTableEditInfoVO(VO):
    """代码生成业务表编辑信息 VO

    用于返回编辑业务表时需要的完整信息
    """

    info: GenTableDetailVO = Field(description="业务表详细信息")
    rows: list[GenTableColumnVO] = Field(description="字段列表")
    tables: list[GenTableListVO] = Field(description="所有业务表列表")
