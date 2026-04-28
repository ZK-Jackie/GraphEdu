"""代码生成器 Service 层

职责：
1. 处理代码生成器的业务逻辑
2. 调用 Mapper 层进行数据访问
3. 进行数据验证和异常处理
"""

from datetime import datetime
import json
import logging
from typing import Any

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.toolv2.generator import (
    GenDbTableQueryDTO,
    GenTableQueryDTO,
    GenTableUpdateDTO,
)
from graphedu.common.models.orm.generator import GenTable, GenTableColumn
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.toolv2.generator import (
    GenTableColumnVO,
    GenTableDetailVO,
    GenTableInfoVO,
    GenTableListVO,
)
from graphedu.generator.core.gen_util import GenConstant
from graphedu.mapper.tool.gen_table import GenTableColumnMapper, GenTableMapper

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_table_orm_to_list_vo(table_orm: GenTable) -> GenTableListVO:
    """将业务表 ORM 对象转换为 GenTableListVO。"""
    return GenTableListVO(
        table_id=table_orm.table_id,
        table_name=table_orm.table_name or "",
        table_comment=table_orm.table_comment or "",
        class_name=table_orm.class_name or "",
        tpl_category=table_orm.tpl_category or GenConstant.TPL_CRUD,
        tpl_web_type=table_orm.tpl_web_type or GenConstant.TPL_WEB_ANT_DESIGN_VUE,
        create_time=table_orm.create_time,
        update_time=table_orm.update_time,
    )


def _convert_table_orm_to_detail_vo(table_orm: GenTable) -> GenTableDetailVO:
    """将业务表 ORM 对象转换为 GenTableDetailVO。"""
    # 转换字段列表
    columns = []
    pk_column = None
    if table_orm.columns:
        for column_orm in table_orm.columns:
            column_vo = _convert_column_orm_to_vo(column_orm)
            columns.append(column_vo)
            if column_vo.pk:
                pk_column = column_vo

    # 设置模板类型标识
    tpl_category = table_orm.tpl_category or GenConstant.TPL_CRUD
    sub = tpl_category == GenConstant.TPL_SUB
    tree = tpl_category == GenConstant.TPL_TREE
    crud = tpl_category == GenConstant.TPL_CRUD

    # 解析 options 参数
    options = None
    tree_code = None
    tree_parent_code = None
    tree_name = None
    parent_menu_id = None
    parent_menu_name = None
    if table_orm.options:
        try:
            options = json.loads(table_orm.options)
            tree_code = options.get(GenConstant.TREE_CODE)
            tree_parent_code = options.get(GenConstant.TREE_PARENT_CODE)
            tree_name = options.get(GenConstant.TREE_NAME)
            parent_menu_id = options.get(GenConstant.PARENT_MENU_ID)
            parent_menu_name = options.get("parentMenuName")
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse options for table {table_orm.table_name}")

    return GenTableDetailVO(
        table_id=table_orm.table_id,
        table_name=table_orm.table_name or "",
        table_comment=table_orm.table_comment or "",
        class_name=table_orm.class_name or "",
        tpl_category=tpl_category,
        tpl_web_type=table_orm.tpl_web_type or GenConstant.TPL_WEB_ANT_DESIGN_VUE,
        package_name=table_orm.package_name or "",
        module_name=table_orm.module_name or "",
        business_name=table_orm.business_name or "",
        function_name=table_orm.function_name or "",
        function_author=table_orm.function_author or "",
        gen_type=table_orm.gen_type or "0",
        gen_path=table_orm.gen_path or "/",
        sub_table_name=table_orm.sub_table_name,
        sub_table_fk_name=table_orm.sub_table_fk_name,
        options=table_orm.options,
        create_by=table_orm.create_by,
        create_time=table_orm.create_time,
        update_by=table_orm.update_by,
        update_time=table_orm.update_time,
        remark=table_orm.remark,
        columns=columns,
        pk_column=pk_column,
        sub_table=None,
        tree_code=tree_code,
        tree_parent_code=tree_parent_code,
        tree_name=tree_name,
        parent_menu_id=parent_menu_id,
        parent_menu_name=parent_menu_name,
        sub=sub,
        tree=tree,
        crud=crud,
    )


def _convert_column_orm_to_vo(column_orm: GenTableColumn) -> GenTableColumnVO:
    """将字段 ORM 对象转换为 GenTableColumnVO。"""
    python_field = column_orm.python_field or ""
    cap_python_field = python_field[0].upper() + python_field[1:] if python_field else None

    # 判断是否为基类字段
    super_column = python_field in GenConstant.TREE_ENTITY + GenConstant.BASE_ENTITY
    usable_column = python_field in ["parentId", "orderNum", "remark"]

    return GenTableColumnVO(
        column_id=column_orm.column_id,
        table_id=column_orm.table_id,
        column_name=column_orm.column_name or "",
        column_comment=column_orm.column_comment,
        column_type=column_orm.column_type or "",
        python_type=column_orm.python_type or "",
        python_field=python_field,
        is_pk=column_orm.is_pk or "0",
        is_increment=column_orm.is_increment or "0",
        is_required=column_orm.is_required or "0",
        is_unique=column_orm.is_unique or "0",
        is_insert=column_orm.is_insert or "0",
        is_edit=column_orm.is_edit or "0",
        is_list=column_orm.is_list or "0",
        is_query=column_orm.is_query or "0",
        query_type=column_orm.query_type or "EQ",
        html_type=column_orm.html_type or "input",
        dict_type=column_orm.dict_type or "",
        sort=column_orm.sort or 0,
        create_by=column_orm.create_by,
        create_time=column_orm.create_time,
        update_by=column_orm.update_by,
        update_time=column_orm.update_time,
        pk=column_orm.is_pk == "1",
        increment=column_orm.is_increment == "1",
        required=column_orm.is_required == "1",
        unique=column_orm.is_unique == "1",
        insert=column_orm.is_insert == "1",
        edit=column_orm.is_edit == "1",
        list=column_orm.is_list == "1",
        query=column_orm.is_query == "1",
        cap_python_field=cap_python_field,
        super_column=super_column,
        usable_column=usable_column,
    )


def _convert_db_table_row_to_info_vo(row: Any) -> GenTableInfoVO:
    """将数据库表信息行转换为 GenTableInfoVO。"""
    return GenTableInfoVO(
        table_name=row.table_name or "",
        table_comment=row.table_comment,
        create_time=row.create_time,
        update_time=row.update_time,
    )


# ============================================================================
# CodeGeneratorService 类
# ============================================================================


class CodeGeneratorService:
    """代码生成服务类

    提供代码生成业务表的增删改查功能
    """

    @staticmethod
    async def get_table_list(query_db: AsyncSession, query_object: GenTableQueryDTO) -> PageResponse[GenTableListVO]:
        """获取代码生成业务表列表信息"""
        query_params = query_object.model_dump(exclude_none=True, exclude={"page", "size"})
        rows, total = await GenTableMapper.get_list(query_params, query_db)

        table_list = [_convert_table_orm_to_list_vo(row) for row in rows]

        return PageResponse(rows=table_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def get_db_table_list(
        query_db: AsyncSession, query_object: GenDbTableQueryDTO
    ) -> PageResponse[GenTableInfoVO]:
        """获取数据库表列表信息"""
        query_params = query_object.model_dump(exclude_none=True, exclude={"page", "size"})
        rows, total = await GenTableMapper.get_db_table_list(query_params, query_db)

        table_list = [_convert_db_table_row_to_info_vo(row) for row in rows]

        return PageResponse(rows=table_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def get_db_tables_by_names(query_db: AsyncSession, table_names: list[str]) -> list[GenTableInfoVO]:
        """根据表名称组获取数据库表信息"""
        db_tables = await GenTableMapper.get_db_tables_by_names(table_names, query_db)
        return [_convert_db_table_row_to_info_vo(row) for row in db_tables]

    @staticmethod
    async def import_tables(query_db: AsyncSession, table_names: list[str], current_user: CurrentUser) -> None:
        """导入表结构"""
        try:
            for table_name in table_names:
                existing_table = await GenTableMapper.get_by_name(table_name, query_db)
                if existing_table:
                    logger.warning(f"Table {table_name} already imported, skipping")
                    continue

                db_table_info = await GenTableMapper.get_db_table_info(table_name, query_db)
                if not db_table_info:
                    raise ServiceException(message=f"表 {table_name} 不存在")

                new_table = GenTable(
                    table_name=table_name,
                    table_comment=db_table_info.get("table_comment", ""),
                    class_name=_to_pascal_case(table_name),
                    tpl_category=GenConstant.TPL_CRUD,
                    tpl_web_type=GenConstant.TPL_WEB_ANT_DESIGN_VUE,
                    package_name="graphedu",
                    module_name="system",
                    business_name=_to_camel_case(table_name.replace("sys_", "")),
                    function_name=db_table_info.get("table_comment", table_name),
                    function_author=current_user.detail.user.user_name if current_user.detail.user else "System",
                    gen_type="0",
                    gen_path="/",
                    create_by=current_user.detail.user.user_name if current_user.detail.user else None,
                    create_time=datetime.now(),
                )
                added_table = await GenTableMapper.add(new_table, query_db)

                db_columns = await GenTableColumnMapper.get_db_columns_by_table_name(table_name, query_db)
                for db_column in db_columns:
                    column = GenTableColumn(
                        table_id=added_table.table_id,
                        column_name=db_column.column_name or "",
                        column_comment=db_column.column_comment,
                        column_type=db_column.column_type or "",
                        python_type=_map_sql_type_to_python(db_column.column_type or ""),
                        python_field=_to_snake_case(db_column.column_name or ""),
                        is_pk=db_column.is_pk or "0",
                        is_increment=db_column.is_increment or "0",
                        is_required=db_column.is_required or "0",
                        is_insert="1" if db_column.is_pk != "1" else "0",
                        is_edit="1" if db_column.is_pk != "1" else "0",
                        is_list="1",
                        is_query="0",
                        query_type="EQ",
                        html_type="input",
                        dict_type="",
                        sort=db_column.sort or 0,
                        create_by=current_user.detail.user.user_name if current_user.detail.user else None,
                        create_time=datetime.now(),
                    )
                    await GenTableColumnMapper.add(column, query_db)

            logger.info(f"导入表成功: {table_names}")
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"导入失败: {e!s}") from e

    @staticmethod
    async def update_table(query_db: AsyncSession, table_data: GenTableUpdateDTO, current_user: CurrentUser) -> None:
        """更新业务表信息"""
        try:
            table = await GenTableMapper.get_by_id(table_data.table_id, query_db)
            if not table:
                raise ServiceException(message="业务表不存在")

            update_data = table_data.model_dump(
                exclude_unset=True,
                exclude={"table_id", "columns", "params"},
                by_alias=True,
            )
            for field, value in update_data.items():
                setattr(table, field, value)

            table.update_by = current_user.detail.user.user_name if current_user.detail.user else None
            table.update_time = datetime.now()

            if table_data.params:
                params_dict = {
                    GenConstant.TREE_CODE: table_data.params.tree_code,
                    GenConstant.TREE_PARENT_CODE: table_data.params.tree_parent_code,
                    GenConstant.TREE_NAME: table_data.params.tree_name,
                    GenConstant.PARENT_MENU_ID: table_data.params.parent_menu_id,
                    "parentMenuName": table_data.params.parent_menu_name,
                }
                table.options = json.dumps(params_dict)

            await GenTableMapper.update(table, query_db)

            if table_data.columns:
                for column_data in table_data.columns:
                    column = await GenTableColumnMapper.get_by_id(column_data.column_id, query_db)
                    if column:
                        column_update_data = column_data.model_dump(
                            exclude_unset=True,
                            exclude={"column_id", "table_id"},
                            by_alias=True,
                        )
                        for field, value in column_update_data.items():
                            setattr(column, field, value)
                        column.update_by = current_user.detail.user.user_name if current_user.detail.user else None
                        column.update_time = datetime.now()
                        await GenTableColumnMapper.update(column, query_db)

            logger.info(f"更新业务表成功: {table.table_name}")
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"更新失败: {e!s}") from e

    @staticmethod
    async def delete_table(query_db: AsyncSession, table_ids: list[int], current_user: CurrentUser) -> None:
        """删除业务表信息"""
        if not table_ids:
            raise ServiceException(message="业务表 ID 列表不能为空")

        try:
            for table_id in table_ids:
                await GenTableMapper.delete(table_id, query_db)
            logger.info(f"删除业务表成功: {table_ids}")
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"删除失败: {e!s}") from e

    @staticmethod
    async def get_table_detail(query_db: AsyncSession, table_id: int) -> GenTableDetailVO:
        """获取业务表详细信息"""
        table = await GenTableMapper.get_by_id(table_id, query_db)
        if not table:
            raise ServiceException(message="业务表不存在")

        return _convert_table_orm_to_detail_vo(table)

    @staticmethod
    async def get_all_tables(query_db: AsyncSession) -> list[GenTableListVO]:
        """获取所有业务表信息"""
        tables = await GenTableMapper.get_all(query_db)
        return [_convert_table_orm_to_list_vo(table) for table in tables]

    @staticmethod
    async def sync_table(query_db: AsyncSession, table_name: str, current_user: CurrentUser) -> None:
        """同步数据库表结构"""
        try:
            table = await GenTableMapper.get_by_name(table_name, query_db)
            if not table:
                raise ServiceException(message=f"业务表 {table_name} 不存在")

            current_columns = await GenTableColumnMapper.get_list_by_table_id(table.table_id, query_db)
            column_map = {col.column_name: col for col in current_columns}

            db_columns = await GenTableColumnMapper.get_db_columns_by_table_name(table_name, query_db)
            if not db_columns:
                raise ServiceException(message=f"表 {table_name} 不存在或无字段")

            db_column_names = [col.column_name for col in db_columns]
            current_column_names = list(column_map.keys())

            for db_column in db_columns:
                column_name = db_column.column_name
                if column_name in column_map:
                    existing_column = column_map[column_name]
                    existing_column.column_type = db_column.column_type or ""
                    existing_column.python_type = _map_sql_type_to_python(db_column.column_type or "")
                    existing_column.is_pk = db_column.is_pk or "0"
                    existing_column.is_increment = db_column.is_increment or "0"
                    existing_column.is_required = db_column.is_required or "0"
                    existing_column.sort = db_column.sort or 0
                    existing_column.update_by = current_user.detail.user.user_name if current_user.detail.user else None
                    existing_column.update_time = datetime.now()
                    await GenTableColumnMapper.update(existing_column, query_db)
                else:
                    new_column = GenTableColumn(
                        table_id=table.table_id,
                        column_name=column_name or "",
                        column_comment=db_column.column_comment,
                        column_type=db_column.column_type or "",
                        python_type=_map_sql_type_to_python(db_column.column_type or ""),
                        python_field=_to_snake_case(column_name or ""),
                        is_pk=db_column.is_pk or "0",
                        is_increment=db_column.is_increment or "0",
                        is_required=db_column.is_required or "0",
                        is_insert="1" if db_column.is_pk != "1" else "0",
                        is_edit="1" if db_column.is_pk != "1" else "0",
                        is_list="1",
                        is_query="0",
                        query_type="EQ",
                        html_type="input",
                        dict_type="",
                        sort=db_column.sort or 0,
                        create_by=current_user.detail.user.user_name if current_user.detail.user else None,
                        create_time=datetime.now(),
                    )
                    await GenTableColumnMapper.add(new_column, query_db)

            for column_name in current_column_names:
                if column_name not in db_column_names:
                    column = column_map[column_name]
                    await GenTableColumnMapper.delete_by_column_id(column.column_id, query_db)

            logger.info(f"同步表结构成功: {table_name}")
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"同步失败: {e!s}") from e

    @staticmethod
    async def preview_code(query_db: AsyncSession, table_id: int) -> dict[str, str]:
        """预览生成代码"""
        try:
            from graphedu.generator.core import TemplateInitializer, TemplateUtils

            table = await GenTableMapper.get_by_id(table_id, query_db)
            if not table:
                raise ServiceException(message="业务表不存在")

            table_detail = _convert_table_orm_to_detail_vo(table)

            if table_detail.sub and table_detail.sub_table_name:
                sub_table = await GenTableMapper.get_by_name(table_detail.sub_table_name, query_db)
                if sub_table:
                    table_detail.sub_table = _convert_table_orm_to_detail_vo(sub_table)

            env = TemplateInitializer.init_jinja2()
            context = TemplateUtils.prepare_context(table_detail)
            template_list = TemplateUtils.get_template_list(table_detail.tpl_category, table_detail.tpl_web_type)

            preview_result = {}
            for template in template_list:
                try:
                    template_obj = env.get_template(template)
                    render_content = template_obj.render(**context)
                    preview_result[template] = render_content
                except Exception as e:
                    logger.warning(f"渲染模板 {template} 失败: {e}")
                    preview_result[template] = f"// 渲染失败: {e}"

            return preview_result
        except Exception as e:
            logger.error(f"预览代码失败: {e}")
            raise ServiceException(message=f"预览失败: {e!s}") from e

    @staticmethod
    async def generate_code(
        query_db: AsyncSession,
        table_name: str,
        current_user: CurrentUser,
        gen_path: str | None = None,
    ) -> str:
        """生成代码到本地路径"""
        try:
            import os
            from pathlib import Path

            from graphedu.generator.core import TemplateInitializer, TemplateUtils

            table = await GenTableMapper.get_by_name(table_name, query_db)
            if not table:
                raise ServiceException(message=f"业务表 {table_name} 不存在")

            table_detail = _convert_table_orm_to_detail_vo(table)

            if table_detail.sub and table_detail.sub_table_name:
                sub_table = await GenTableMapper.get_by_name(table_detail.sub_table_name, query_db)
                if sub_table:
                    table_detail.sub_table = _convert_table_orm_to_detail_vo(sub_table)

            env = TemplateInitializer.init_jinja2()
            context = TemplateUtils.prepare_context(table_detail)
            template_list = TemplateUtils.get_template_list(table_detail.tpl_category, table_detail.tpl_web_type)

            if gen_path and gen_path != "/":
                base_path = gen_path
            else:
                base_path = os.getcwd()

            for template in template_list:
                try:
                    template_obj = env.get_template(template)
                    render_content = template_obj.render(**context)
                    file_name = TemplateUtils.get_file_name(template, table_detail)
                    if not file_name:
                        continue

                    file_path = Path(base_path) / file_name
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                        await f.write(render_content)

                    logger.info(f"生成文件成功: {file_path}")
                except Exception as e:
                    logger.error(f"生成文件失败 {template}: {e}")

            return "生成代码成功"
        except Exception as e:
            logger.error(f"生成代码失败: {e}")
            raise ServiceException(message=f"生成失败: {e!s}") from e

    @staticmethod
    async def batch_generate_code(
        query_db: AsyncSession,
        table_names: list[str],
    ) -> bytes:
        """批量生成代码（ZIP 包）"""
        try:
            import io
            import zipfile

            from graphedu.generator.core import TemplateInitializer, TemplateUtils

            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for table_name in table_names:
                    table = await GenTableMapper.get_by_name(table_name, query_db)
                    if not table:
                        logger.warning(f"表 {table_name} 不存在，跳过")
                        continue

                    table_detail = _convert_table_orm_to_detail_vo(table)

                    if table_detail.sub and table_detail.sub_table_name:
                        sub_table = await GenTableMapper.get_by_name(table_detail.sub_table_name, query_db)
                        if sub_table:
                            table_detail.sub_table = _convert_table_orm_to_detail_vo(sub_table)

                    env = TemplateInitializer.init_jinja2()
                    context = TemplateUtils.prepare_context(table_detail)
                    template_list = TemplateUtils.get_template_list(
                        table_detail.tpl_category, table_detail.tpl_web_type
                    )

                    for template in template_list:
                        try:
                            template_obj = env.get_template(template)
                            render_content = template_obj.render(**context)
                            file_name = TemplateUtils.get_file_name(template, table_detail)
                            if not file_name:
                                continue
                            zip_file.writestr(file_name, render_content)
                        except Exception as e:
                            logger.error(f"生成文件失败 {template}: {e}")

            zip_data = zip_buffer.getvalue()
            zip_buffer.close()
            return zip_data
        except Exception as e:
            logger.error(f"批量生成代码失败: {e}")
            raise ServiceException(message=f"批量生成失败: {e!s}") from e


# ============================================================================
# 工具函数
# ============================================================================


def _to_pascal_case(snake_str: str) -> str:
    if not snake_str:
        return ""
    return "".join(x.title() for x in snake_str.split("_"))


def _to_camel_case(snake_str: str) -> str:
    if not snake_str:
        return ""
    pascal = _to_pascal_case(snake_str)
    return pascal[0].lower() + pascal[1:] if pascal else ""


def _to_snake_case(camel_str: str) -> str:
    if not camel_str:
        return ""
    result = [camel_str[0].lower()]
    for char in camel_str[1:]:
        if char.isupper():
            result.extend(["_", char.lower()])
        else:
            result.append(char)
    return "".join(result)


def _map_sql_type_to_python(sql_type: str) -> str:
    sql_type_upper = sql_type.upper()
    if "INT" in sql_type_upper:
        return "int"
    if "CHAR" in sql_type_upper or "TEXT" in sql_type_upper or "VARCHAR" in sql_type_upper:
        return "str"
    if "DATETIME" in sql_type_upper or "TIMESTAMP" in sql_type_upper:
        return "datetime"
    if (
        "DECIMAL" in sql_type_upper
        or "NUMERIC" in sql_type_upper
        or "FLOAT" in sql_type_upper
        or "DOUBLE" in sql_type_upper
    ):
        return "decimal"
    if "BIT" in sql_type_upper or "BOOL" in sql_type_upper:
        return "bool"
    return "str"
