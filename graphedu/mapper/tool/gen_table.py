"""代码生成器 Mapper 层

职责：
1. 只处理 ORM 数据或基础数据类型（dict、tuple）
2. 不引入 DTO、VO 等业务模型
3. 提供纯粹的数据访问接口
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from graphedu.common.models.orm.generator import GenTable, GenTableColumn

# ============================================================================
# 代码生成业务表 Mapper
# ============================================================================


class GenTableMapper:
    """代码生成业务表数据访问层"""

    @staticmethod
    async def get_by_id(table_id: int, db_session: AsyncSession) -> GenTable | None:
        """根据业务表 ID 获取业务表 ORM 对象

        Args:
            table_id: 业务表 ID
            db_session: 数据库会话

        Returns:
            业务表 ORM 对象或 None
        """
        stmt = select(GenTable).options(selectinload(GenTable.columns)).where(GenTable.table_id == table_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(table_name: str, db_session: AsyncSession) -> GenTable | None:
        """根据业务表名称获取业务表 ORM 对象

        Args:
            table_name: 业务表名称
            db_session: 数据库会话

        Returns:
            业务表 ORM 对象或 None
        """
        stmt = select(GenTable).options(selectinload(GenTable.columns)).where(GenTable.table_name == table_name)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db_session: AsyncSession) -> list[GenTable]:
        """获取所有业务表信息

        Args:
            db_session: 数据库会话

        Returns:
            所有业务表 ORM 对象列表
        """
        stmt = select(GenTable).options(selectinload(GenTable.columns))
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_imported_table_names(db_session: AsyncSession) -> list[str]:
        """获取已导入的业务表名称列表

        Args:
            db_session: 数据库会话

        Returns:
            已导入的业务表名称列表
        """
        stmt = select(GenTable.table_name)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_list(query_params: dict[str, Any], db_session: AsyncSession) -> tuple[Sequence[GenTable], int]:
        """获取业务表列表

        Args:
            query_params: 查询参数字典
            db_session: 数据库会话

        Returns:
            业务表 ORM 对象列表和总数
        """
        stmt = select(GenTable).options(selectinload(GenTable.columns)).distinct()

        # 添加过滤条件
        if query_params.get("table_name"):
            stmt = stmt.where(GenTable.table_name.like(f"%{query_params['table_name']}%"))
        if query_params.get("table_comment"):
            stmt = stmt.where(GenTable.table_comment.like(f"%{query_params['table_comment']}%"))
        if query_params.get("begin_time") and query_params.get("end_time"):
            begin_datetime = datetime.strptime(query_params["begin_time"], "%Y-%m-%d").replace(
                hour=0, minute=0, second=0
            )
            end_datetime = datetime.strptime(query_params["end_time"], "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            stmt = stmt.where(GenTable.create_time.between(begin_datetime, end_datetime))

        # 获取总数
        total_query = select(func.count()).select_from(stmt.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.get("page")
        page_size = query_params.get("size")
        if page_num and page_size:
            stmt = stmt.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(stmt)
        return result.scalars().all(), total

    @staticmethod
    async def get_db_table_list(query_params: dict[str, Any], db_session: AsyncSession) -> tuple[Sequence[Any], int]:
        """获取数据库中未导入的表列表

        Args:
            query_params: 查询参数字典
            db_session: 数据库会话

        Returns:
            数据库表信息列表和总数
        """
        # 使用 pg_class + obj_description() 正确查询 PostgreSQL 表注释
        query_sql = """
            SELECT
                c.relname                                        AS table_name,
                COALESCE(obj_description(c.oid, 'pg_class'), '') AS table_comment,
                NULL::timestamp                                   AS create_time,
                NULL::timestamp                                   AS update_time
            FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND c.relname NOT LIKE 'apscheduler_%'
              AND c.relname NOT LIKE 'gen_%'
              AND c.relname NOT IN (
                  SELECT table_name FROM gen_table
              )
        """

        # 添加过滤条件
        params = {}
        if query_params.get("table_name"):
            query_sql += " AND LOWER(c.relname) LIKE LOWER(:table_name)"
            params["table_name"] = f"%{query_params['table_name']}%"
        if query_params.get("table_comment"):
            query_sql += " AND LOWER(COALESCE(obj_description(c.oid, 'pg_class'), '')) LIKE LOWER(:table_comment)"
            params["table_comment"] = f"%{query_params['table_comment']}%"

        query_sql += " ORDER BY c.relname"

        # 先获取总数
        count_sql = f"SELECT COUNT(*) FROM ({query_sql}) AS subq"
        count_result = await db_session.execute(text(count_sql).bindparams(**params))
        total = count_result.scalar() or 0

        # 分页
        page_num = query_params.get("page")
        page_size = query_params.get("size")
        if page_num and page_size:
            query_sql += " LIMIT :limit OFFSET :offset"
            params["limit"] = page_size
            params["offset"] = (page_num - 1) * page_size

        result = await db_session.execute(text(query_sql).bindparams(**params))
        return result.fetchall(), total

    @staticmethod
    async def get_db_table_info(table_name: str, db_session: AsyncSession) -> dict[str, Any] | None:
        """获取数据库表的详细信息

        Args:
            table_name: 表名称
            db_session: 数据库会话

        Returns:
            表信息字典或 None
        """
        query_sql = """
            SELECT
                c.relname                                        AS table_name,
                COALESCE(obj_description(c.oid, 'pg_class'), '') AS table_comment,
                NULL::timestamp                                   AS create_time,
                NULL::timestamp                                   AS update_time
            FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND c.relname = :table_name
        """
        result = await db_session.execute(text(query_sql).bindparams(table_name=table_name))
        row = result.fetchone()
        return dict(row._mapping) if row else None

    @staticmethod
    async def get_db_tables_by_names(table_names: list[str], db_session: AsyncSession) -> Sequence[Any]:
        """根据表名称组获取数据库表信息

        Args:
            table_names: 表名称列表
            db_session: 数据库会话

        Returns:
            数据库表信息列表
        """
        if not table_names:
            return []

        query_sql = """
            SELECT
                c.relname                                        AS table_name,
                COALESCE(obj_description(c.oid, 'pg_class'), '') AS table_comment,
                NULL::timestamp                                   AS create_time,
                NULL::timestamp                                   AS update_time
            FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND c.relname NOT LIKE 'gen_%'
              AND c.relname = ANY(:table_names)
            ORDER BY c.relname
        """
        result = await db_session.execute(text(query_sql).bindparams(table_names=table_names))
        return result.fetchall()

    @staticmethod
    async def add(gen_table: GenTable, db_session: AsyncSession) -> GenTable:
        """新增业务表

        Args:
            gen_table: 业务表 ORM 对象
            db_session: 数据库会话

        Returns:
            新创建的业务表 ORM 对象
        """
        db_session.add(gen_table)
        await db_session.flush()
        await db_session.refresh(gen_table)
        return gen_table

    @staticmethod
    async def update(gen_table: GenTable, db_session: AsyncSession) -> None:
        """更新业务表

        Args:
            gen_table: 更新后的 ORM 实体
            db_session: 数据库会话
        """
        await db_session.merge(gen_table)
        await db_session.flush()

    @staticmethod
    async def delete(table_id: int, db_session: AsyncSession) -> None:
        """删除业务表

        Args:
            table_id: 业务表 ID
            db_session: 数据库会话
        """
        await db_session.execute(delete(GenTable).where(GenTable.table_id == table_id))


# ============================================================================
# 代码生成业务表字段 Mapper
# ============================================================================


class GenTableColumnMapper:
    """代码生成业务表字段数据访问层"""

    @staticmethod
    async def get_by_id(column_id: int, db_session: AsyncSession) -> GenTableColumn | None:
        """根据字段 ID 获取字段 ORM 对象

        Args:
            column_id: 字段 ID
            db_session: 数据库会话

        Returns:
            字段 ORM 对象或 None
        """
        stmt = select(GenTableColumn).where(GenTableColumn.column_id == column_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list_by_table_id(table_id: int, db_session: AsyncSession) -> list[GenTableColumn]:
        """根据业务表 ID 获取字段列表

        Args:
            table_id: 业务表 ID
            db_session: 数据库会话

        Returns:
            字段 ORM 对象列表
        """
        stmt = select(GenTableColumn).where(GenTableColumn.table_id == table_id).order_by(GenTableColumn.sort)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_db_columns_by_table_name(table_name: str, db_session: AsyncSession) -> Sequence[Any]:
        """根据表名称获取数据库表字段列表（PostgreSQL）

        Args:
            table_name: 表名称
            db_session: 数据库会话

        Returns:
            数据库表字段信息列表
        """
        query_sql = """
            SELECT
                col.column_name,
                CASE WHEN col.is_nullable = 'NO' THEN '1' ELSE '0' END AS is_required,
                CASE WHEN pk.column_name IS NOT NULL THEN '1' ELSE '0' END AS is_pk,
                col.ordinal_position AS sort,
                COALESCE(pgd.description, '') AS column_comment,
                '0' AS is_increment,
                col.data_type AS column_type
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
        result = await db_session.execute(text(query_sql).bindparams(table_name=table_name))
        return result.fetchall()

    @staticmethod
    async def add(gen_table_column: GenTableColumn, db_session: AsyncSession) -> GenTableColumn:
        """新增业务表字段

        Args:
            gen_table_column: 字段 ORM 对象
            db_session: 数据库会话

        Returns:
            新创建的字段 ORM 对象
        """
        db_session.add(gen_table_column)
        await db_session.flush()
        await db_session.refresh(gen_table_column)
        return gen_table_column

    @staticmethod
    async def update(gen_table_column: GenTableColumn, db_session: AsyncSession) -> None:
        """更新业务表字段

        Args:
            gen_table_column: 更新后的 ORM 实体
            db_session: 数据库会话
        """
        await db_session.merge(gen_table_column)
        await db_session.flush()

    @staticmethod
    async def delete_by_column_id(column_id: int, db_session: AsyncSession) -> None:
        """通过字段 ID 删除字段

        Args:
            column_id: 字段 ID
            db_session: 数据库会话
        """
        await db_session.execute(delete(GenTableColumn).where(GenTableColumn.column_id == column_id))

    @staticmethod
    async def delete_by_table_id(table_id: int, db_session: AsyncSession) -> None:
        """通过业务表 ID 删除所有关联字段

        Args:
            table_id: 业务表 ID
            db_session: 数据库会话
        """
        await db_session.execute(delete(GenTableColumn).where(GenTableColumn.table_id == table_id))
