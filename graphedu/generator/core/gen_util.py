"""代码生成器工具类

职责：
1. 初始化表信息（类名、包名、模块名等）
2. 初始化字段信息（Python 类型、字段名、HTML 类型等）
3. 命名转换（下划线、驼峰、帕斯卡）
"""

from datetime import datetime
import re


class GenConstant:
    """代码生成器常量"""

    # 模板类型
    TPL_CRUD = "crud"
    TPL_TREE = "tree"
    TPL_SUB = "sub"

    # 前端模板类型
    TPL_WEB_ELEMENT_UI = "element-ui"
    TPL_WEB_ELEMENT_PLUS = "element-plus"
    TPL_WEB_ANT_DESIGN_VUE = "ant-design-vue"

    # 树表字段
    TREE_CODE = "treeCode"
    TREE_PARENT_CODE = "treeParentCode"
    TREE_NAME = "treeName"
    PARENT_MENU_ID = "parentMenuId"

    # 查询方式
    QUERY_EQ = "EQ"
    QUERY_NE = "NE"
    QUERY_GT = "GT"
    QUERY_GTE = "GTE"
    QUERY_LT = "LT"
    QUERY_LTE = "LTE"
    QUERY_LIKE = "LIKE"
    QUERY_BETWEEN = "BETWEEN"

    # HTML 类型
    HTML_INPUT = "input"
    HTML_TEXTAREA = "textarea"
    HTML_SELECT = "select"
    HTML_RADIO = "radio"
    HTML_CHECKBOX = "checkbox"
    HTML_DATETIME = "datetime"
    HTML_IMAGE_UPLOAD = "imageUpload"
    HTML_FILE_UPLOAD = "fileUpload"
    HTML_EDITOR = "editor"

    # 数据库类型
    COLUMNTYPE_STR = ["varchar", "char", "text"]
    COLUMNTYPE_TEXT = ["tinytext", "mediumtext", "longtext"]
    COLUMNTYPE_TIME = ["datetime", "timestamp", "date", "time"]
    COLUMNTYPE_NUMBER = ["int", "bigint", "float", "double", "decimal", "numeric"]

    # 不需要编辑的字段
    COLUMNNAME_NOT_EDIT = ["create_by", "create_time", "update_by", "update_time", "del_flag"]
    # 不在列表显示的字段
    COLUMNNAME_NOT_LIST = ["create_by", "update_by", "del_flag", "remark"]
    # 不在查询显示的字段
    COLUMNNAME_NOT_QUERY = [
        "id",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
        "del_flag",
        "remark",
        "parent_id",
    ]
    # 不需要添加显示的字段
    COLUMNNAME_NOT_ADD_SHOW = ["id", "parent_id", "del_flag"]

    # 基类字段（不需要生成，来自基类实体）
    BASE_ENTITY = ["create_by", "create_time", "update_by", "update_time", "remark"]
    # 树形基类字段
    TREE_ENTITY = ["parent_name", "parent_id", "order_num", "ancestors", "children"]

    # Python 类型映射（同时支持 MySQL 和 PostgreSQL 类型名）
    DB_TO_PYTHON_TYPE_MAPPING = {
        # 字符串类型（MySQL）
        "varchar": "str",
        "char": "str",
        "text": "str",
        "tinytext": "str",
        "mediumtext": "str",
        "longtext": "str",
        # 整数类型（MySQL）
        "int": "int",
        "tinyint": "int",
        "smallint": "int",
        "mediumint": "int",
        "bigint": "int",
        # 浮点类型（MySQL）
        "float": "float",
        "double": "float",
        # 精确小数
        "decimal": "Decimal",
        "numeric": "Decimal",
        # 时间类型（MySQL）
        "datetime": "datetime",
        "timestamp": "datetime",
        "date": "date",
        "time": "time",
        # 布尔类型（MySQL）
        "bit": "bool",
        "bool": "bool",
        # PostgreSQL 特有类型
        "character varying": "str",
        "character": "str",
        "integer": "int",
        "int2": "int",
        "int4": "int",
        "int8": "int",
        "int4range": "str",
        "int8range": "str",
        "float4": "float",
        "float8": "float",
        "boolean": "bool",
        "timestamp without time zone": "datetime",
        "timestamp with time zone": "datetime",
        "time without time zone": "time",
        "time with time zone": "time",
        "json": "dict",
        "jsonb": "dict",
        "uuid": "str",
        "bytea": "bytes",
    }

    # SQLAlchemy 类型字符串映射（用于 ORM 模板），key 为 data_type
    DB_TO_SA_TYPE = {
        # 字符串类型
        "varchar": "String",
        "character varying": "String",
        "char": "CHAR",
        "character": "CHAR",
        "text": "Text",
        "tinytext": "Text",
        "mediumtext": "Text",
        "longtext": "Text",
        # 整数类型
        "int": "Integer",
        "tinyint": "SmallInteger",
        "smallint": "SmallInteger",
        "mediumint": "Integer",
        "bigint": "BigInteger",
        "integer": "Integer",
        "int2": "SmallInteger",
        "int4": "Integer",
        "int8": "BigInteger",
        # 浮点类型
        "float": "Float",
        "double": "Float",
        "float4": "Float",
        "float8": "Float",
        # 精确小数
        "decimal": "Numeric",
        "numeric": "Numeric",
        # 布尔类型
        "bit": "Boolean",
        "bool": "Boolean",
        "boolean": "Boolean",
        # 时间类型
        "datetime": "TIMESTAMP",
        "timestamp": "TIMESTAMP",
        "timestamp without time zone": "TIMESTAMP",
        "timestamp with time zone": "TIMESTAMP",
        "date": "Date",
        "time": "Time",
        "time without time zone": "Time",
        "time with time zone": "Time",
        # JSON 类型
        "json": "JSON",
        "jsonb": "JSONB",
        # 其他
        "uuid": "String(36)",
        "bytea": "LargeBinary",
    }


class GenUtils:
    """代码生成器工具类"""

    @classmethod
    def init_table(
        cls,
        table_name: str,
        table_comment: str,
        oper_name: str | None = None,
        package_name: str = "graphedu",
        module_name: str = "system",
        function_author: str = "System",
    ) -> dict:
        """初始化表信息

        Args:
            table_name: 表名
            table_comment: 表注释
            oper_name: 操作人
            package_name: 包名
            module_name: 模块名
            function_author: 作者

        Returns:
            表信息字典
        """
        class_name = cls.convert_class_name(table_name)
        business_name = cls.get_business_name(table_name)
        function_name = cls.replace_text(table_comment)

        return {
            "table_name": table_name,
            "table_comment": table_comment,
            "class_name": class_name,
            "package_name": package_name,
            "module_name": module_name,
            "business_name": business_name,
            "function_name": function_name,
            "function_author": function_author,
            "create_by": oper_name,
            "create_time": datetime.now(),
            "update_by": oper_name,
            "update_time": datetime.now(),
        }

    @classmethod
    def init_column_field(
        cls,
        column_name: str,
        column_type: str,
        column_comment: str | None = None,
        is_pk: str = "0",
        is_increment: str = "0",
        is_required: str = "0",
        oper_name: str | None = None,
    ) -> dict:
        """初始化列属性字段

        Args:
            column_name: 列名
            column_type: 列类型
            column_comment: 列注释
            is_pk: 是否主键
            is_increment: 是否自增
            is_required: 是否必填
            oper_name: 操作人

        Returns:
            列信息字典
        """
        data_type = cls.get_db_type(column_type)
        python_field = cls.to_snake_case(column_name)
        python_type = GenConstant.DB_TO_PYTHON_TYPE_MAPPING.get(data_type, "str")

        column_info = {
            "column_name": column_name,
            "column_comment": column_comment,
            "column_type": column_type,
            "python_field": python_field,
            "python_type": python_type,
            "is_pk": is_pk,
            "is_increment": is_increment,
            "is_required": is_required,
            "query_type": GenConstant.QUERY_EQ,
            "create_by": oper_name,
            "create_time": datetime.now(),
            "update_by": oper_name,
            "update_time": datetime.now(),
        }

        # 设置 HTML 类型
        column_info["html_type"] = cls._get_html_type(column_type, column_name)

        # 插入字段（默认所有字段都需要插入）
        column_info["is_insert"] = "1" if is_pk != "1" else "0"

        # 编辑字段
        if column_name not in GenConstant.COLUMNNAME_NOT_EDIT and is_pk != "1":
            column_info["is_edit"] = "1"
        else:
            column_info["is_edit"] = "0"

        # 列表字段
        if column_name not in GenConstant.COLUMNNAME_NOT_LIST and is_pk != "1":
            column_info["is_list"] = "1"
        else:
            column_info["is_list"] = "0"

        # 查询字段
        if column_name not in GenConstant.COLUMNNAME_NOT_QUERY and is_pk != "1":
            column_info["is_query"] = "1"
        else:
            column_info["is_query"] = "0"

        # 查询字段类型
        if column_name.lower().endswith("name"):
            column_info["query_type"] = GenConstant.QUERY_LIKE

        # 状态字段设置单选框
        if column_name.lower().endswith("status"):
            column_info["html_type"] = GenConstant.HTML_RADIO
        # 类型&性别字段设置下拉框
        elif column_name.lower().endswith("type") or column_name.lower().endswith("sex"):
            column_info["html_type"] = GenConstant.HTML_SELECT
        # 图片字段设置图片上传控件
        elif column_name.lower().endswith("image"):
            column_info["html_type"] = GenConstant.HTML_IMAGE_UPLOAD
        # 文件字段设置文件上传控件
        elif column_name.lower().endswith("file"):
            column_info["html_type"] = GenConstant.HTML_FILE_UPLOAD
        # 内容字段设置富文本控件
        elif column_name.lower().endswith("content"):
            column_info["html_type"] = GenConstant.HTML_EDITOR

        return column_info

    @classmethod
    def _get_html_type(cls, column_type: str, column_name: str) -> str:
        """获取 HTML 类型

        Args:
            column_type: 列类型
            column_name: 列名

        Returns:
            HTML 类型
        """
        data_type = cls.get_db_type(column_type)

        # 字符串长度超过 500 设置为文本域
        if data_type in GenConstant.COLUMNTYPE_STR or data_type in GenConstant.COLUMNTYPE_TEXT:
            column_length = cls.get_column_length(column_type)
            if column_length >= 500 or data_type in GenConstant.COLUMNTYPE_TEXT:
                return GenConstant.HTML_TEXTAREA
            return GenConstant.HTML_INPUT
        if data_type in GenConstant.COLUMNTYPE_TIME:
            return GenConstant.HTML_DATETIME
        if data_type in GenConstant.COLUMNTYPE_NUMBER:
            return GenConstant.HTML_INPUT

        return GenConstant.HTML_INPUT

    @classmethod
    def get_module_name(cls, package_name: str) -> str:
        """获取模块名

        Args:
            package_name: 包名

        Returns:
            模块名
        """
        return package_name.split(".")[-1]

    @classmethod
    def get_business_name(cls, table_name: str) -> str:
        """获取业务名

        Args:
            table_name: 表名

        Returns:
            业务名
        """
        return table_name.split("_")[-1]

    @classmethod
    def convert_class_name(cls, table_name: str) -> str:
        """表名转换成 Python 类名

        Args:
            table_name: 表名

        Returns:
            Python 类名
        """
        return cls.to_pascal_case(table_name)

    @classmethod
    def replace_text(cls, text: str) -> str:
        """关键字替换

        Args:
            text: 需要被替换的字符串

        Returns:
            替换后的字符串
        """
        return re.sub(r"(?:表|系统)", "", text)

    @classmethod
    def get_db_type(cls, column_type: str) -> str:
        """获取数据库类型字段

        Args:
            column_type: 字段类型

        Returns:
            数据库类型
        """
        if "(" in column_type:
            return column_type.split("(")[0]
        return column_type

    @classmethod
    def get_column_length(cls, column_type: str) -> int:
        """获取字段长度

        Args:
            column_type: 字段类型

        Returns:
            字段长度
        """
        if "(" in column_type:
            length = column_type.split("(")[1].split(")")[0]
            try:
                return int(length)
            except ValueError:
                return 0
        return 0

    @classmethod
    def to_pascal_case(cls, snake_str: str) -> str:
        """将下划线命名转换为帕斯卡命名（PascalCase）

        Args:
            snake_str: 下划线命名字符串

        Returns:
            帕斯卡命名字符串
        """
        if not snake_str:
            return ""
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    @classmethod
    def to_camel_case(cls, snake_str: str) -> str:
        """将下划线命名转换为驼峰命名（camelCase）

        Args:
            snake_str: 下划线命名字符串

        Returns:
            驼峰命名字符串
        """
        if not snake_str:
            return ""
        pascal = cls.to_pascal_case(snake_str)
        return pascal[0].lower() + pascal[1:] if pascal else ""

    @classmethod
    def to_snake_case(cls, camel_str: str) -> str:
        """将驼峰命名转换为下划线命名（snake_case）

        Args:
            camel_str: 驼峰命名字符串

        Returns:
            下划线命名字符串
        """
        if not camel_str:
            return ""
        result = [camel_str[0].lower()]
        for char in camel_str[1:]:
            if char.isupper():
                result.extend(["_", char.lower()])
            else:
                result.append(char)
        return "".join(result)

    @classmethod
    def get_sa_type_str(
        cls,
        data_type: str,
        char_max_len: int | None = None,
        numeric_precision: int | None = None,
        numeric_scale: int | None = None,
    ) -> str:
        """获取 SQLAlchemy 类型字符串（含参数）

        Args:
            data_type: 数据库原始类型（来自 information_schema.columns.data_type）
            char_max_len: 字符长度（varchar/char 使用）
            numeric_precision: 精度（numeric/decimal 使用）
            numeric_scale: 小数位数

        Returns:
            SQLAlchemy 类型字符串，如 "String(255)", "Integer", "Numeric(10, 2)"
        """
        base_type = GenConstant.DB_TO_SA_TYPE.get(data_type.lower(), "String")

        if base_type in ("String", "CHAR") and char_max_len is not None:
            return f"{base_type}({char_max_len})"
        if base_type == "Numeric" and numeric_precision is not None:
            if numeric_scale is not None:
                return f"Numeric({numeric_precision}, {numeric_scale})"
            return f"Numeric({numeric_precision})"
        return base_type

    @classmethod
    def get_domain_from_table(cls, table_name: str) -> str:
        """从表名推断所属领域（模块）

        Args:
            table_name: 表名（如 edu_course, sys_user）

        Returns:
            领域名称（如 education, system, common）
        """
        if table_name.startswith("edu_"):
            return "education"
        if table_name.startswith("sys_"):
            return "system"
        return "common"

    @classmethod
    def get_module_from_table(cls, table_name: str) -> str:
        """从表名推断模块名（去除前缀后的最后一个下划线段）

        例如：edu_course → course，sys_user → user，edu_student_course → studentCourse

        Args:
            table_name: 表名

        Returns:
            camelCase 模块名
        """
        # 去除已知前缀
        for prefix in ("edu_", "sys_"):
            if table_name.startswith(prefix):
                rest = table_name[len(prefix) :]
                return cls.to_camel_case(rest)
        return cls.to_camel_case(table_name)
