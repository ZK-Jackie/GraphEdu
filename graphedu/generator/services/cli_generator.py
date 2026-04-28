"""CLI 代码生成器服务

职责：
1. 直接从 PostgreSQL information_schema 读取表结构（无需依赖 gen_table）
2. 构建 Jinja2 模板上下文
3. 渲染模板并将生成的代码写入文件系统

与 CodeGeneratorService 的区别：
- CodeGeneratorService  使用 gen_table/gen_table_column ORM 表（Web 界面导入后生成）
- CliCodeGenerator       直接查询数据库表结构，适合命令行快速生成，无需先导入表
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from graphedu.common.models.vo.toolv2.generator import GenTableColumnVO, GenTableDetailVO
from graphedu.generator.core.gen_util import GenConstant, GenUtils
from graphedu.generator.core.template_util import TemplateInitializer, TemplateUtils

logger = logging.getLogger(__name__)


# ============================================================================
# PostgreSQL 表元数据查询
# ============================================================================

_TABLE_COMMENT_SQL = """
SELECT
    c.relname AS table_name,
    COALESCE(obj_description(c.oid), '') AS table_comment
FROM
    pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE
    n.nspname = 'public'
    AND c.relkind = 'r'
    AND c.relname = :table_name
"""

_COLUMN_SQL = """
SELECT
    col.column_name,
    col.ordinal_position                                        AS sort,
    col.data_type,
    col.udt_name,
    col.character_maximum_length,
    col.numeric_precision,
    col.numeric_scale,
    CASE WHEN col.is_nullable = 'NO' THEN '1' ELSE '0' END     AS is_required,
    CASE WHEN pk.column_name IS NOT NULL  THEN '1' ELSE '0' END AS is_pk,
    '0'                                                         AS is_increment,
    COALESCE(pgd.description, '')                               AS column_comment
FROM
    information_schema.columns col
    LEFT JOIN (
        SELECT kcu.column_name
        FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc
                ON  kcu.table_schema    = tc.table_schema
                AND kcu.table_name      = tc.table_name
                AND kcu.constraint_name = tc.constraint_name
                AND tc.constraint_type  = 'PRIMARY KEY'
        WHERE kcu.table_schema = 'public'
          AND kcu.table_name   = :table_name
    ) pk ON pk.column_name = col.column_name
    LEFT JOIN pg_catalog.pg_statio_all_tables st
           ON st.schemaname = col.table_schema
          AND st.relname    = col.table_name
    LEFT JOIN pg_catalog.pg_description pgd
           ON pgd.objoid    = st.relid
          AND pgd.objsubid  = col.ordinal_position
WHERE
    col.table_schema = 'public'
    AND col.table_name = :table_name
ORDER BY
    col.ordinal_position
"""


# ============================================================================
# SQLAlchemy 类型计算
# ============================================================================


def _get_sa_type_str(
    data_type: str,
    char_max_len: int | None = None,
    numeric_precision: int | None = None,
    numeric_scale: int | None = None,
) -> str:
    """计算该列使用的 SQLAlchemy 类型字符串（含参数）"""
    return GenUtils.get_sa_type_str(data_type, char_max_len, numeric_precision, numeric_scale)


def _collect_sa_imports(columns_ctx: list[dict[str, Any]]) -> list[str]:
    """从列上下文中收集需要 import 的 SQLAlchemy 类型名（去参数、去重）"""
    types: set[str] = set()
    for col in columns_ctx:
        sa_type = col.get("saType", "String")
        # 取类型名称（去掉括号及内容）
        base = sa_type.split("(")[0]
        types.add(base)

    # 分离 PostgreSQL 方言类型（JSONB）
    dialect_types = {"JSONB"}
    return sorted(types - dialect_types)


# ============================================================================
# 列上下文构建
# ============================================================================


def _build_column_ctx(
    column_name: str,
    data_type: str,
    udt_name: str,
    char_max_len: int | None,
    numeric_precision: int | None,
    numeric_scale: int | None,
    is_required: str,
    is_pk: str,
    is_increment: str,
    column_comment: str,
    sort: int,
) -> dict[str, Any]:
    """从 information_schema 原始数据构建模板列上下文字典"""
    # 获取 Python 类型
    python_type = GenConstant.DB_TO_PYTHON_TYPE_MAPPING.get(data_type.lower(), "str")

    # SQLAlchemy 类型字符串
    sa_type = _get_sa_type_str(data_type, char_max_len, numeric_precision, numeric_scale)

    # 派生属性
    python_field = GenUtils.to_snake_case(column_name)
    cap_python_field = python_field[0].upper() + python_field[1:] if python_field else None
    super_column = python_field in (GenConstant.BASE_ENTITY + GenConstant.TREE_ENTITY)

    # 通过 init_column_field 获取 is_insert/is_edit/is_list/is_query/html_type/query_type
    col_info = GenUtils.init_column_field(
        column_name=column_name,
        column_type=data_type,
        column_comment=column_comment or None,
        is_pk=is_pk,
        is_increment=is_increment,
        is_required=is_required,
    )

    ctx: dict[str, Any] = {
        # 原始列信息（camelCase，与 Jinja2 模板变量名对应）
        "columnName": column_name,
        "columnComment": column_comment or "",
        "columnType": data_type,
        "udtName": udt_name,
        "characterMaximumLength": char_max_len,
        "numericPrecision": numeric_precision,
        "numericScale": numeric_scale,
        # Python 字段信息
        "pythonField": python_field,
        "pythonType": python_type,
        "capPythonField": cap_python_field,
        # 标志位（全部为 "0"/"1" 字符串，兼容模板中的 == '1' 比较）
        "isPk": is_pk,
        "isIncrement": is_increment,
        "isRequired": is_required,
        "isInsert": col_info.get("is_insert", "0"),
        "isEdit": col_info.get("is_edit", "0"),
        "isList": col_info.get("is_list", "0"),
        "isQuery": col_info.get("is_query", "0"),
        # 模板 bool-style 字段（用 "0"/"1" 而不是 True/False）
        "pk": is_pk,
        "increment": is_increment,
        "required": is_required,
        "unique": "0",
        "insert": col_info.get("is_insert", "0"),
        "edit": col_info.get("is_edit", "0"),
        "list": col_info.get("is_list", "0"),
        "query": col_info.get("is_query", "0"),
        # 其他
        "queryType": col_info.get("query_type", GenConstant.QUERY_EQ),
        "htmlType": col_info.get("html_type", GenConstant.HTML_INPUT),
        "dictType": "",
        "sort": sort,
        # 辅助字段
        "superColumn": "1" if super_column else "0",
        "usableColumn": "0",
        # SQLAlchemy 相关（用于 ORM 模板）
        "saType": sa_type,
    }
    return ctx


# ============================================================================
# 表元数据查询
# ============================================================================


async def _fetch_table_info(table_name: str, db_session: AsyncSession) -> dict[str, Any] | None:
    """查询表的基本信息（名称、注释）"""
    result = await db_session.execute(text(_TABLE_COMMENT_SQL).bindparams(table_name=table_name))
    row = result.fetchone()
    return dict(row._mapping) if row else None


async def _fetch_columns(table_name: str, db_session: AsyncSession) -> list[dict[str, Any]]:
    """查询表的所有列信息"""
    result = await db_session.execute(text(_COLUMN_SQL).bindparams(table_name=table_name))
    rows = result.fetchall()
    return [dict(r._mapping) for r in rows]


# ============================================================================
# 上下文构建
# ============================================================================


def _build_gen_table_detail(
    table_name: str,
    table_comment: str,
    columns_raw: list[dict[str, Any]],
    module_name: str,
    domain_name: str,
    class_name: str,
    business_name: str,
    package_name: str = "graphedu",
    function_author: str = "graphedu",
) -> tuple[GenTableDetailVO, list[dict[str, Any]]]:
    """根据数据库原始数据构建 GenTableDetailVO 以及列上下文字典列表"""
    columns_ctx: list[dict[str, Any]] = []
    column_vos: list[GenTableColumnVO] = []
    pk_column_vo: GenTableColumnVO | None = None

    for i, raw in enumerate(columns_raw):
        col_name: str = raw.get("column_name", "")
        data_type: str = raw.get("data_type", "text")
        udt_name: str = raw.get("udt_name", data_type)
        char_max_len: int | None = raw.get("character_maximum_length")
        num_precision: int | None = raw.get("numeric_precision")
        num_scale: int | None = raw.get("numeric_scale")
        is_required: str = raw.get("is_required", "0")
        is_pk: str = raw.get("is_pk", "0")
        is_increment: str = raw.get("is_increment", "0")
        col_comment: str = raw.get("column_comment", "") or ""
        sort: int = raw.get("sort", i + 1) or (i + 1)

        # 构建列 ctx dict
        col_ctx = _build_column_ctx(
            column_name=col_name,
            data_type=data_type,
            udt_name=udt_name,
            char_max_len=char_max_len,
            numeric_precision=num_precision,
            numeric_scale=num_scale,
            is_required=is_required,
            is_pk=is_pk,
            is_increment=is_increment,
            column_comment=col_comment,
            sort=sort,
        )
        columns_ctx.append(col_ctx)

        # 同时构建 VO 对象供 GenTableDetailVO 使用
        python_type = GenConstant.DB_TO_PYTHON_TYPE_MAPPING.get(data_type.lower(), "str")
        python_field = GenUtils.to_snake_case(col_name)
        cap_pf = python_field[0].upper() + python_field[1:] if python_field else None
        col_info = GenUtils.init_column_field(
            column_name=col_name,
            column_type=data_type,
            column_comment=col_comment or None,
            is_pk=is_pk,
            is_increment=is_increment,
            is_required=is_required,
        )
        col_vo = GenTableColumnVO(
            column_id=i + 1,
            table_id=0,
            column_name=col_name,
            column_comment=col_comment or None,
            column_type=data_type,
            python_type=python_type,
            python_field=python_field,
            is_pk=is_pk,
            is_increment=is_increment,
            is_required=is_required,
            is_unique="0",
            is_insert=col_info.get("is_insert", "0"),
            is_edit=col_info.get("is_edit", "0"),
            is_list=col_info.get("is_list", "0"),
            is_query=col_info.get("is_query", "0"),
            query_type=col_info.get("query_type", "EQ"),
            html_type=col_info.get("html_type", "input"),
            dict_type="",
            sort=sort,
            pk=(is_pk == "1"),
            increment=(is_increment == "1"),
            required=(is_required == "1"),
            unique=False,
            insert=(col_info.get("is_insert", "0") == "1"),
            edit=(col_info.get("is_edit", "0") == "1"),
            list=(col_info.get("is_list", "0") == "1"),
            query=(col_info.get("is_query", "0") == "1"),
            cap_python_field=cap_pf,
            super_column=(python_field in (GenConstant.BASE_ENTITY + GenConstant.TREE_ENTITY)),
            usable_column=False,
        )
        column_vos.append(col_vo)
        if is_pk == "1" and pk_column_vo is None:
            pk_column_vo = col_vo

    if pk_column_vo is None and column_vos:
        pk_column_vo = column_vos[0]

    function_name = table_comment.replace("表", "").replace("管理", "").strip() or business_name

    gen_table_detail = GenTableDetailVO(
        table_id=0,
        table_name=table_name,
        table_comment=table_comment,
        class_name=class_name,
        tpl_category=GenConstant.TPL_CRUD,
        tpl_web_type=GenConstant.TPL_WEB_ANT_DESIGN_VUE,
        package_name=package_name,
        module_name=module_name,
        business_name=business_name,
        function_name=function_name,
        function_author=function_author,
        gen_type="0",
        gen_path="/",
        columns=column_vos,
        pk_column=pk_column_vo,
        sub_table=None,
        sub=False,
        tree=False,
        crud=True,
    )

    return gen_table_detail, columns_ctx


# ============================================================================
# 文件写入
# ============================================================================


def _write_file(file_path: str, content: str, output_root: str, overwrite: bool = False) -> bool:
    """将渲染好的内容写入文件。

    Args:
        file_path: 相对路径（来自 get_file_name）
        content: 文件内容
        output_root: 输出根目录
        overwrite: 是否覆盖已有文件

    Returns:
        True 表示写入成功，False 表示跳过
    """
    # 将 "backend/graphedu/..." 转换为实际输出路径
    if file_path.startswith("backend/"):
        rel = file_path[len("backend/") :]
    elif file_path.startswith("frontend/"):
        rel = file_path  # 保留 frontend/ 前缀，放入 output_root
    else:
        rel = file_path

    target = Path(output_root) / rel
    if target.exists() and not overwrite:
        logger.warning("文件已存在，跳过（使用 --overwrite 强制覆盖）：%s", target)
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    logger.info("已生成：%s", target)
    return True


# ============================================================================
# 核心生成函数
# ============================================================================


async def _generate_async(
    table_name: str,
    module_name: str,
    templates: list[str],
    extra_context: dict[str, Any],
    output_root: str,
    overwrite: bool,
    db_url: str,
    package_name: str = "graphedu",
    function_author: str = "graphedu",
) -> list[str]:
    """异步核心生成逻辑，返回生成的文件路径列表"""
    engine = create_async_engine(db_url, echo=False)
    generated: list[str] = []

    try:
        async with engine.begin() as conn:
            session = AsyncSession(bind=conn)
            async with session:
                # 1. 查询表信息
                table_info = await _fetch_table_info(table_name, session)
                if table_info is None:
                    raise ValueError(f"数据库中不存在表：{table_name}")

                table_comment: str = table_info.get("table_comment", "") or ""

                # 2. 查询列信息
                columns_raw = await _fetch_columns(table_name, session)
                if not columns_raw:
                    raise ValueError(f"表 {table_name} 没有列信息")

                # 3. 推断命名体系
                domain_name = GenUtils.get_domain_from_table(table_name)
                class_name = extra_context.get("className_override") or GenUtils.to_pascal_case(module_name)
                orm_class_name = GenUtils.to_pascal_case(table_name)
                business_name = module_name

                # 4. 构建 GenTableDetailVO 和列上下文字典
                gen_table_detail, columns_ctx = _build_gen_table_detail(
                    table_name=table_name,
                    table_comment=table_comment,
                    columns_raw=columns_raw,
                    module_name=domain_name,
                    domain_name=domain_name,
                    class_name=class_name,
                    business_name=business_name,
                    package_name=package_name,
                    function_author=function_author,
                )

                # 5. 通过 TemplateUtils 准备基础上下文（已转为 camelCase 字典）
                context = TemplateUtils.prepare_context(gen_table_detail)

                # 6. 覆盖/追加 CLI 专用上下文变量
                context["ormClassName"] = orm_class_name  # 完整 ORM 类名（如 EduCourse）
                context["domainName"] = domain_name  # 领域名（如 education）
                # 将 saType 注入到每个列 ctx 中
                for col_ctx, col_raw_ctx in zip(context["columns"], columns_ctx, strict=False):
                    col_ctx["saType"] = col_raw_ctx["saType"]

                # 7. 计算 ORM 模板所需的 SA imports
                sa_imports = _collect_sa_imports(context["columns"])
                has_jsonb = "JSONB" in {col.get("saType", "").split("(")[0] for col in context["columns"]}
                context["saImports"] = sa_imports
                context["hasJsonb"] = has_jsonb

                # 8. 合并额外上下文
                context.update({k: v for k, v in extra_context.items() if not k.startswith("className_override")})

                # 9. 初始化 Jinja2 环境并渲染模板
                env = TemplateInitializer.init_jinja2()

                for tpl_name in templates:
                    try:
                        tpl = env.get_template(tpl_name)
                        rendered = tpl.render(**context)
                    except Exception as exc:
                        logger.error("模板渲染失败 [%s]: %s", tpl_name, exc)
                        continue

                    file_rel = TemplateUtils.get_file_name(tpl_name, gen_table_detail)
                    if not file_rel:
                        logger.warning("无法确定模板 %s 的输出路径，跳过", tpl_name)
                        continue

                    if _write_file(file_rel, rendered, output_root, overwrite):
                        generated.append(str(Path(output_root) / file_rel.lstrip("backend/").lstrip("frontend/")))  # noqa: B005

    finally:
        await engine.dispose()

    return generated


# ============================================================================
# 公开 API
# ============================================================================


def generate_model(
    table_name: str,
    module_name: str | None = None,
    output_root: str = ".",
    overwrite: bool = False,
    config_file: str = "dev.config.yaml",
) -> list[str]:
    """生成 ORM 实体模型（从数据库表结构）

    使用示例::

        from graphedu.generator.services.cli_generator import generate_model
        generate_model("edu_course")
        generate_model("edu_course", module_name="course", output_root="graphedu")

    Args:
        table_name:   数据库表名，例如 "edu_course"
        module_name:  模块名（文件名），默认从表名提取（去掉前缀）
        output_root:  输出根目录，默认为当前目录
        overwrite:    是否覆盖已有文件
        config_file:  配置文件路径，默认 "dev.config.yaml"

    Returns:
        已写入的文件路径列表
    """
    from graphedu.common.config.manager import load_config

    config = load_config(config_file)

    db_url = config.datasource.postgresql.get_sa_async_dsn()

    if module_name is None:
        module_name = GenUtils.get_module_from_table(table_name)

    # 只生成 ORM 模板
    templates = ["python/orm.py.jinja2"]

    # 对 generate_model，ClassName 使用完整表名（EduCourse）
    extra_context = {
        "className_override": GenUtils.to_pascal_case(table_name),
    }

    return asyncio.run(
        _generate_async(
            table_name=table_name,
            module_name=module_name,
            templates=templates,
            extra_context=extra_context,
            output_root=output_root,
            overwrite=overwrite,
            db_url=db_url,
        )
    )


def generate_crud(
    module_name: str,
    table_name: str | None = None,
    output_root: str = ".",
    overwrite: bool = False,
    with_api: bool = True,
    with_service: bool = True,
    with_mapper: bool = True,
    config_file: str = "dev.config.yaml",
) -> list[str]:
    """生成完整 CRUD 代码（mapper / service / api / dto / vo）

    使用示例::

        from graphedu.generator.services.cli_generator import generate_crud
        generate_crud("course")
        generate_crud("student", table_name="edu_student")
        generate_crud("teacher", with_api=False)

    Args:
        module_name:  模块名，例如 "course"、"student"
        table_name:   数据库表名，默认为 "edu_{module_name}"
        output_root:  输出根目录
        overwrite:    是否覆盖已有文件
        with_api:     是否生成 API Controller 层
        with_service: 是否生成 Service 层
        with_mapper:  是否生成 Mapper 层
        config_file:  配置文件路径

    Returns:
        已写入的文件路径列表
    """
    from graphedu.common.config.manager import load_config

    config = load_config(config_file)

    db_url = config.datasource.postgresql.get_sa_async_dsn()

    if table_name is None:
        table_name = f"edu_{module_name}"

    # 构建模板列表
    templates: list[str] = [
        "python/dto.py.jinja2",
        "python/vo.py.jinja2",
    ]
    if with_mapper:
        templates.append("python/mapper.py.jinja2")
    if with_service:
        templates.append("python/service.py.jinja2")
    if with_api:
        templates.append("python/api.py.jinja2")

    # CRUD 中 ClassName = PascalCase(module_name)，不加前缀
    extra_context: dict[str, Any] = {}  # 不设置 className_override，让默认逻辑用 module_name

    return asyncio.run(
        _generate_async(
            table_name=table_name,
            module_name=module_name,
            templates=templates,
            extra_context=extra_context,
            output_root=output_root,
            overwrite=overwrite,
            db_url=db_url,
        )
    )
