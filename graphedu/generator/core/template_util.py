"""代码生成器模板工具类

职责：
1. 初始化 Jinja2 模板引擎
2. 准备模板上下文变量
3. 获取模板列表和文件名
4. 处理不同类型模板的上下文（树表、主子表等）
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from graphedu.common.models.vo.toolv2.generator import GenTableDetailVO
from graphedu.generator.core.gen_util import GenConstant, GenUtils


class TemplateInitializer:
    """模板引擎初始化类"""

    @classmethod
    def init_jinja2(cls) -> Environment:
        """初始化 Jinja2 模板引擎

        Returns:
            Jinja2 环境对象
        """
        # 获取模板目录：core/ 的上一级目录（generator/）下的 templates/
        current_dir = Path(__file__).parent.parent
        template_dir = current_dir / "templates"

        if not template_dir.exists():
            raise RuntimeError(f"模板目录不存在: {template_dir}")

        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 注册自定义过滤器
        env.filters.update(
            {
                "to_pascal": GenUtils.to_pascal_case,
                "to_camel": GenUtils.to_camel_case,
                "to_snake": GenUtils.to_snake_case,
            }
        )

        return env


class TemplateUtils:
    """模板工具类"""

    # 项目路径
    FRONTEND_PROJECT_PATH = "frontend"
    BACKEND_PROJECT_PATH = "backend"
    DEFAULT_PARENT_MENU_ID = "3"

    @classmethod
    def prepare_context(cls, gen_table: GenTableDetailVO) -> dict[str, Any]:
        """准备模板变量

        Args:
            gen_table: 生成表的配置信息

        Returns:
            模板上下文字典
        """
        class_name = gen_table.class_name
        module_name = gen_table.module_name
        business_name = gen_table.business_name
        package_name = gen_table.package_name
        tpl_category = gen_table.tpl_category
        function_name = gen_table.function_name

        # 获取主键列并转换为模板友好字典
        pk_column = gen_table.pk_column
        if not pk_column and gen_table.columns:
            pk_column = gen_table.columns[0]
        pk_column_ctx = cls._column_to_ctx(pk_column) if pk_column else {}

        # 转换所有列为模板友好字典
        columns_ctx = [cls._column_to_ctx(col) for col in (gen_table.columns or [])]

        # 收集列中使用的 Python 类型，用于模板中生成 import 语句
        column_types = list({col["pythonType"] for col in columns_ctx if col.get("pythonType")})

        context = {
            "tplCategory": tpl_category,
            "tableName": gen_table.table_name,
            "tableComment": gen_table.table_comment or "",
            "functionName": function_name if function_name else "【请填写功能名称】",
            "ClassName": class_name,
            "className": class_name[0].lower() + class_name[1:] if class_name else "",
            "moduleName": module_name,
            "BusinessName": business_name.capitalize() if business_name else "",
            "businessName": business_name,
            "basePackage": cls.get_package_prefix(package_name),
            "packageName": package_name,
            "author": gen_table.function_author or "System",
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pkColumn": pk_column_ctx,
            "columns": columns_ctx,
            "table": gen_table,
            "dicts": cls.get_dicts(gen_table),
            "columnTypes": column_types,
        }

        # 设置菜单、树形结构、子表的上下文
        cls.set_menu_context(context, gen_table)
        if tpl_category == GenConstant.TPL_TREE:
            cls.set_tree_context(context, gen_table)
        if tpl_category == GenConstant.TPL_SUB:
            cls.set_sub_context(context, gen_table)

        return context

    @classmethod
    def _column_to_ctx(cls, column: Any) -> dict[str, Any]:
        """将列对象（VO 或 dict）转换为模板可直接使用的 camelCase 字典

        模板变量说明：
        - 使用 camelCase 键名（如 pythonField、columnComment）
        - bool 型字段（pk/insert/edit/list/query 等）统一转为 "0"/"1" 字符串
          以兼容模板中的 ``column.insert == '1'`` 这类比较

        Args:
            column: GenTableColumnVO 实例或已有字典

        Returns:
            模板上下文字典（camelCase 键名）
        """
        from graphedu.common.models.vo.toolv2.generator import GenTableColumnVO

        if isinstance(column, GenTableColumnVO):
            # model_dump(by_alias=True) 利用 BaseVO.alias_generator=to_camel 生成 camelCase 键
            d = column.model_dump(by_alias=True)
        elif isinstance(column, dict):
            d = dict(column)
        else:
            d = {}

        # 将 bool 字段转换为 "0"/"1" 字符串，保持与模板 == '1' 比较的兼容性
        _bool_fields = [
            "pk",
            "increment",
            "required",
            "unique",
            "insert",
            "edit",
            "list",
            "query",
            "superColumn",
            "usableColumn",
        ]
        for field in _bool_fields:
            if field in d and isinstance(d[field], bool):
                d[field] = "1" if d[field] else "0"

        return d

    @classmethod
    def set_menu_context(cls, context: dict[str, Any], gen_table: GenTableDetailVO) -> None:
        """设置菜单上下文

        Args:
            context: 模板上下文字典
            gen_table: 生成表的配置信息
        """
        params_obj = cls._parse_options(gen_table)
        context["parentMenuId"] = cls.get_parent_menu_id(params_obj)

    @classmethod
    def set_tree_context(cls, context: dict[str, Any], gen_table: GenTableDetailVO) -> None:
        """设置树形结构上下文

        Args:
            context: 模板上下文字典
            gen_table: 生成表的配置信息
        """
        params_obj = cls._parse_options(gen_table)
        context["treeCode"] = cls.get_tree_code(params_obj)
        context["treeParentCode"] = cls.get_tree_parent_code(params_obj)
        context["treeName"] = cls.get_tree_name(params_obj)
        context["expandColumn"] = cls.get_expand_column(gen_table)

    @classmethod
    def set_sub_context(cls, context: dict[str, Any], gen_table: GenTableDetailVO) -> None:
        """设置子表上下文

        Args:
            context: 模板上下文字典
            gen_table: 生成表的配置信息
        """
        sub_table = gen_table.sub_table
        if not sub_table:
            return

        sub_table_name = gen_table.sub_table_name
        sub_table_fk_name = gen_table.sub_table_fk_name
        sub_class_name = sub_table.class_name
        sub_table_fk_class_name = GenUtils.to_camel_case(sub_table_fk_name)

        context["subTable"] = sub_table
        context["subTableName"] = sub_table_name
        context["subTableFkName"] = sub_table_fk_name
        context["subTableFkClassName"] = sub_table_fk_class_name
        context["subTableFkclassName"] = sub_table_fk_class_name.lower()
        context["subClassName"] = sub_class_name
        context["subclassName"] = sub_class_name.lower()

    @classmethod
    def _parse_options(cls, gen_table: GenTableDetailVO) -> dict[str, Any]:
        """解析 options 字段

        Args:
            gen_table: 生成表信息

        Returns:
            解析后的字典
        """
        if gen_table.options:
            try:
                return json.loads(gen_table.options)
            except json.JSONDecodeError:
                pass
        return {}

    @classmethod
    def get_template_list(cls, tpl_category: str, tpl_web_type: str) -> list[str]:
        """获取模板列表

        Args:
            tpl_category: 生成模板类型
            tpl_web_type: 前端类型

        Returns:
            模板列表
        """
        use_web_type = "vue"
        if tpl_web_type == "element-plus":
            use_web_type = "vue/v3"
        elif tpl_web_type == "ant-design-vue":
            use_web_type = "vue/antd"

        # 树表使用专用模板
        if tpl_category == GenConstant.TPL_TREE:
            templates = [
                "python/mapper-tree.py.jinja2",
                "python/service-tree.py.jinja2",
                "python/api-tree.py.jinja2",
                "python/dto.py.jinja2",
                "python/vo.py.jinja2",
                "sql/sql.jinja2",
                "typescript/api.ts.jinja2",
                "typescript/types.ts.jinja2",
                "locales/zh.json.jinja2",
                "locales/en.json.jinja2",
                f"{use_web_type}/index-tree.vue.jinja2",
            ]
        else:
            # CRUD 和子表使用通用模板
            templates = [
                "python/mapper.py.jinja2",
                "python/service.py.jinja2",
                "python/api.py.jinja2",
                "python/dto.py.jinja2",
                "python/vo.py.jinja2",
                "sql/sql.jinja2",
                "typescript/api.ts.jinja2",
                "locales/zh.json.jinja2",
                "locales/en.json.jinja2",
            ]

            if tpl_category == GenConstant.TPL_CRUD or tpl_category == GenConstant.TPL_SUB:
                templates.append(f"{use_web_type}/index.vue.jinja2")

        return templates

    @classmethod
    def get_file_name(cls, template: str, gen_table: GenTableDetailVO) -> str:
        """根据模板生成文件名

        Args:
            template: 模板名称
            gen_table: 生成表的配置信息

        Returns:
            生成的文件名（相对于项目根目录）
        """
        package_name = gen_table.package_name
        module_name = gen_table.module_name  # 例如 "education" 或 "system"
        business_name = gen_table.business_name  # 例如 "course" 或 "user"

        vue_path = cls.FRONTEND_PROJECT_PATH
        python_path = f"{cls.BACKEND_PROJECT_PATH}/{package_name.replace('.', '/')}"

        if "mapper.py.jinja2" in template:
            return f"{python_path}/mapper/{business_name}.py"
        if "service.py.jinja2" in template:
            return f"{python_path}/services/{module_name}/{business_name}.py"
        if "api.py.jinja2" in template:
            return f"{python_path}/api/services/{module_name}/{business_name}.py"
        if "dto.py.jinja2" in template:
            return f"{python_path}/common/models/dto/{business_name}.py"
        if "vo.py.jinja2" in template:
            return f"{python_path}/common/models/vo/{business_name}.py"
        if "orm.py.jinja2" in template:
            return f"{python_path}/common/models/orm/{business_name}.py"
        if "sql.jinja2" in template:
            return f"{cls.BACKEND_PROJECT_PATH}/sql/{business_name}_menu.sql"
        if "api.ts.jinja2" in template:
            return f"{vue_path}/src/api/{module_name}/{business_name}.ts"
        if "types.ts.jinja2" in template:
            return f"{vue_path}/src/types/api/{business_name}.ts"
        if "locales/zh.json.jinja2" in template:
            return f"{vue_path}/src/locales/{module_name}.{business_name}.zh.json"
        if "locales/en.json.jinja2" in template:
            return f"{vue_path}/src/locales/{module_name}.{business_name}.en.json"
        if "index.vue.jinja2" in template or "index-tree.vue.jinja2" in template:
            return f"{vue_path}/src/views/{module_name}/{business_name}/index.vue"

        return ""

    @classmethod
    def get_package_prefix(cls, package_name: str) -> str:
        """获取包前缀

        Args:
            package_name: 包名

        Returns:
            包前缀
        """
        last_dot = package_name.rfind(".")
        if last_dot > 0:
            return package_name[:last_dot]
        return package_name

    @classmethod
    def get_dicts(cls, gen_table: GenTableDetailVO) -> str:
        """获取字典列表

        Args:
            gen_table: 生成表的配置信息

        Returns:
            字典列表（逗号分隔）
        """
        columns = gen_table.columns or []
        dicts = set()
        cls.add_dicts(dicts, columns)
        if gen_table.sub_table:
            cls.add_dicts(dicts, gen_table.sub_table.columns or [])
        return ", ".join(dicts)

    @classmethod
    def add_dicts(cls, dicts: set[str], columns: list) -> None:
        """添加字典列表

        Args:
            dicts: 字典集合
            columns: 字段列表
        """
        for column in columns:
            if (
                not column.super_column
                and column.dict_type
                and column.html_type in [GenConstant.HTML_SELECT, GenConstant.HTML_RADIO, GenConstant.HTML_CHECKBOX]
            ):
                dicts.add(f"'{column.dict_type}'")

    @classmethod
    def get_permission_prefix(cls, module_name: str, business_name: str) -> str:
        """获取权限前缀

        Args:
            module_name: 模块名
            business_name: 业务名

        Returns:
            权限前缀
        """
        return f"{module_name}:{business_name}"

    @classmethod
    def get_parent_menu_id(cls, params_obj: dict[str, Any]) -> str:
        """获取上级菜单 ID

        Args:
            params_obj: 菜单参数字典

        Returns:
            上级菜单 ID
        """
        if params_obj and GenConstant.PARENT_MENU_ID in params_obj:
            return str(params_obj.get(GenConstant.PARENT_MENU_ID, cls.DEFAULT_PARENT_MENU_ID))
        return cls.DEFAULT_PARENT_MENU_ID

    @classmethod
    def get_tree_code(cls, params_obj: dict[str, Any]) -> str:
        """获取树编码

        Args:
            params_obj: 菜单参数字典

        Returns:
            树编码
        """
        if GenConstant.TREE_CODE in params_obj:
            return GenUtils.to_camel_case(params_obj.get(GenConstant.TREE_CODE, ""))
        return ""

    @classmethod
    def get_tree_parent_code(cls, params_obj: dict[str, Any]) -> str:
        """获取树父编码

        Args:
            params_obj: 菜单参数字典

        Returns:
            树父编码
        """
        if GenConstant.TREE_PARENT_CODE in params_obj:
            return GenUtils.to_camel_case(params_obj.get(GenConstant.TREE_PARENT_CODE, ""))
        return ""

    @classmethod
    def get_tree_name(cls, params_obj: dict[str, Any]) -> str:
        """获取树名称

        Args:
            params_obj: 菜单参数字典

        Returns:
            树名称
        """
        if GenConstant.TREE_NAME in params_obj:
            return GenUtils.to_camel_case(params_obj.get(GenConstant.TREE_NAME, ""))
        return ""

    @classmethod
    def get_expand_column(cls, gen_table: GenTableDetailVO) -> int:
        """获取展开列

        Args:
            gen_table: 生成表的配置信息

        Returns:
            展开列索引
        """
        params_obj = cls._parse_options(gen_table)
        tree_name = params_obj.get(GenConstant.TREE_NAME)
        if not tree_name:
            return 0

        num = 0
        for column in gen_table.columns or []:
            if column.list:
                num += 1
                if column.column_name == tree_name:
                    break
        return num
