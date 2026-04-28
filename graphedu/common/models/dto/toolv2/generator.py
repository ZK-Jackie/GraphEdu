"""代码生成器 DTO 模型

本模块定义了代码生成器相关的数据传输对象（请求验证模型），包括：

- GenTableQueryDTO: 代码生成业务表查询 DTO
- GenDbTableQueryDTO: 数据库表查询 DTO
- GenTableCreateDTO: 创建代码生成业务表 DTO
- GenTableUpdateDTO: 更新代码生成业务表 DTO
- GenTableImportDTO: 导入代码生成业务表 DTO
- GenTableColumnUpdateDTO: 更新代码生成业务表字段 DTO
- GenTableParamsDTO: 代码生成业务表参数 DTO（树表等特殊配置）
- GenTableDeleteDTO: 删除代码生成业务表 DTO
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery

# ============================================================================
# 代码生成业务表相关 DTO
# ============================================================================


class GenTableQueryDTO(PageQuery):
    """代码生成业务表查询 DTO

    用于查询已导入的代码生成业务表列表

    Attributes:
        table_name: 表名称（模糊查询）
        table_comment: 表描述（模糊查询）
        begin_time: 创建开始时间
        end_time: 创建结束时间
    """

    table_name: str | None = Field(default=None, description="表名称")
    table_comment: str | None = Field(default=None, description="表描述")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class GenDbTableQueryDTO(PageQuery):
    """数据库表查询 DTO

    用于查询数据库中未导入的表列表

    Attributes:
        table_name: 表名称（模糊查询）
        table_comment: 表描述（模糊查询）
        begin_time: 创建开始时间
        end_time: 创建结束时间
    """

    table_name: str | None = Field(default=None, description="表名称")
    table_comment: str | None = Field(default=None, description="表描述")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class GenTableCreateDTO(DTO):
    """创建代码生成业务表 DTO

    用于管理员导入数据库表到代码生成器

    Attributes:
        table_name: 表名称
        table_comment: 表描述
        class_name: 实体类名称
        tpl_category: 使用的模板（crud单表 tree树表 sub主子表）
        tpl_web_type: 前端模板类型（element-ui element-plus ant-design-vue）
        package_name: 生成包路径
        module_name: 生成模块名
        business_name: 生成业务名
        function_name: 生成功能名
        function_author: 生成功能作者
        gen_type: 生成代码方式（0zip压缩包 1自定义路径）
        gen_path: 生成路径
    """

    table_name: str = Field(description="表名称")
    table_comment: str = Field(description="表描述")
    class_name: str = Field(description="实体类名称")
    tpl_category: Literal["crud", "tree", "sub"] = Field(default="crud", description="使用的模板")
    tpl_web_type: Literal["element-ui", "element-plus", "ant-design-vue"] = Field(
        default="ant-design-vue", description="前端模板类型"
    )
    package_name: str = Field(description="生成包路径")
    module_name: str = Field(description="生成模块名")
    business_name: str = Field(description="生成业务名")
    function_name: str = Field(description="生成功能名")
    function_author: str = Field(description="生成功能作者")
    gen_type: Literal["0", "1"] = Field(default="0", description="生成代码方式（0zip压缩包 1自定义路径）")
    gen_path: str = Field(default="/", description="生成路径")
    sub_table_name: str | None = Field(default=None, description="关联子表的表名")
    sub_table_fk_name: str | None = Field(default=None, description="子表关联的外键名")
    remark: str | None = Field(default=None, description="备注")


class GenTableUpdateDTO(DTO):
    """更新代码生成业务表 DTO

    用于管理员更新代码生成业务表的配置

    Attributes:
        table_id: 业务表ID
        table_name: 表名称
        table_comment: 表描述
        class_name: 实体类名称
        tpl_category: 使用的模板（crud单表 tree树表 sub主子表）
        tpl_web_type: 前端模板类型
        package_name: 生成包路径
        module_name: 生成模块名
        business_name: 生成业务名
        function_name: 生成功能名
        function_author: 生成功能作者
        gen_type: 生成代码方式（0zip压缩包 1自定义路径）
        gen_path: 生成路径
        columns: 字段列表
        params: 其他参数（树表相关）
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
    gen_type: Literal["0", "1"] = Field(default="0", description="生成代码方式（0zip压缩包 1自定义路径）")
    gen_path: str = Field(default="/", description="生成路径")
    sub_table_name: str | None = Field(default=None, description="关联子表的表名")
    sub_table_fk_name: str | None = Field(default=None, description="子表关联的外键名")
    remark: str | None = Field(default=None, description="备注")
    columns: list["GenTableColumnUpdateDTO"] = Field(default_factory=list, description="字段列表")
    params: "GenTableParamsDTO | None" = Field(default=None, description="其他参数")


class GenTableParamsDTO(DTO):
    """代码生成业务表参数 DTO

    用于存储树表等特殊表的参数配置

    Attributes:
        tree_code: 树编码字段
        tree_parent_code: 树父编码字段
        tree_name: 树名称字段
        parent_menu_id: 上级菜单ID
        parent_menu_name: 上级菜单名称
    """

    tree_code: str | None = Field(default=None, description="树编码字段")
    tree_parent_code: str | None = Field(default=None, description="树父编码字段")
    tree_name: str | None = Field(default=None, description="树名称字段")
    parent_menu_id: int | None = Field(default=None, description="上级菜单ID")
    parent_menu_name: str | None = Field(default=None, description="上级菜单名称")


class GenTableDeleteDTO(DTO):
    """删除代码生成业务表 DTO

    Attributes:
        table_ids: 业务表ID列表（逗号分隔）
    """

    table_ids: str = Field(description="业务表ID列表（逗号分隔）")


class GenTableImportDTO(DTO):
    """导入代码生成业务表 DTO

    Attributes:
        table_names: 表名称列表（逗号分隔）
    """

    table_names: str = Field(description="表名称列表（逗号分隔）")


# ============================================================================
# 代码生成业务表字段相关 DTO
# ============================================================================


class GenTableColumnUpdateDTO(DTO):
    """更新代码生成业务表字段 DTO

    Attributes:
        column_id: 字段ID
        table_id: 业务表ID
        column_name: 列名称
        column_comment: 列描述
        column_type: 列类型
        python_type: PYTHON类型
        python_field: PYTHON字段名
        is_pk: 是否主键（1是）
        is_increment: 是否自增（1是）
        is_required: 是否必填（1是）
        is_unique: 是否唯一（1是）
        is_insert: 是否为插入字段（1是）
        is_edit: 是否编辑字段（1是）
        is_list: 是否列表字段（1是）
        is_query: 是否查询字段（1是）
        query_type: 查询方式
        html_type: 显示类型
        dict_type: 字典类型
        sort: 排序
    """

    column_id: int | None = Field(default=None, description="字段ID")
    table_id: int | None = Field(default=None, description="业务表ID")
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
    query_type: str = Field(default="EQ", description="查询方式（等于、不等于、大于、小于、范围）")
    html_type: str = Field(default="input", description="显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）")
    dict_type: str = Field(default="", description="字典类型")
    sort: int = Field(description="排序")
