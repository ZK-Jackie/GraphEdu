"""字典管理 Mapper 层

职责：
1. 只处理ORM数据或基础数据类型（dict）
2. 不引入PO、DTO、VO等业务模型
3. 提供纯粹的数据访问接口
"""

from collections.abc import Sequence
from datetime import datetime
import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.systemv2.dict import DictDataQueryDTO, DictTypeQueryDTO
from graphedu.common.models.orm.system import SysDictData, SysDictType

logger = logging.getLogger(__name__)


class DictTypeMapper:
    """字典类型数据访问层"""

    @staticmethod
    async def get_by_id(dict_id: int, db_session: AsyncSession) -> SysDictType | None:
        """根据字典类型ID获取字典类型ORM对象

        :param dict_id: 字典类型ID
        :param db_session: 数据库会话
        :return: 字典类型ORM对象或None
        """
        result = await db_session.execute(select(SysDictType).where(SysDictType.dict_id == dict_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_dict_type(dict_type: str, db_session: AsyncSession) -> SysDictType | None:
        """根据字典类型编码获取字典类型ORM对象

        :param dict_type: 字典类型编码
        :param db_session: 数据库会话
        :return: 字典类型ORM对象或None
        """
        result = await db_session.execute(select(SysDictType).where(SysDictType.dict_type == dict_type))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(query_params: DictTypeQueryDTO, db_session: AsyncSession) -> tuple[Sequence[SysDictType], int]:
        """获取字典类型列表

        :param query_params: 查询参数DTO
        :param db_session: 数据库会话
        :return: 字典类型列表或分页结果
        """
        stmt = select(SysDictType)

        # 添加过滤条件
        if query_params.dict_name:
            stmt = stmt.where(SysDictType.dict_name.like(f"%{query_params.dict_name}%"))
        if query_params.dict_type:
            stmt = stmt.where(SysDictType.dict_type.like(f"%{query_params.dict_type}%"))
        if query_params.status:
            stmt = stmt.where(SysDictType.status == query_params.status)
        if query_params.begin_time and query_params.end_time:
            begin_datetime = datetime.strptime(query_params.begin_time, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            end_datetime = datetime.strptime(query_params.end_time, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            stmt = stmt.where(SysDictType.create_time.between(begin_datetime, end_datetime))
        stmt = stmt.order_by(SysDictType.dict_id)

        # 获取总数
        total_query = select(func.count()).select_from(stmt.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.page
        page_size = query_params.size
        if page_num and page_size:
            stmt = stmt.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_all(db_session: AsyncSession) -> list[SysDictType]:
        """获取所有字典类型

        :param db_session: 数据库会话
        :return: 所有字典类型ORM对象列表
        """
        result = await db_session.execute(select(SysDictType))
        return list(result.scalars().all())

    @staticmethod
    async def get_all_enabled(db_session: AsyncSession) -> Sequence[SysDictType]:
        """获取所有启用状态的字典类型

        :param db_session: 数据库会话
        :return: 启用状态的字典类型ORM对象列表
        """
        result = await db_session.execute(
            select(SysDictType).where(SysDictType.status == "0").order_by(SysDictType.dict_id)
        )
        return result.scalars().all()

    @staticmethod
    async def add(new_object: SysDictType, db_session: AsyncSession) -> SysDictType:
        """新增字典类型

        :param new_object: 新字典类型ORM对象
        :param db_session: 数据库会话
        :return: 新创建的字典类型ORM对象
        """
        db_session.add(new_object)
        await db_session.flush()
        await db_session.refresh(new_object)
        return new_object

    @staticmethod
    async def update(updated_orm: SysDictType, db_session: AsyncSession) -> None:
        """更新字典类型

        :param updated_orm: 更新后的 ORM 实体
        :param db_session: 数据库会话
        """
        await db_session.merge(updated_orm)
        await db_session.flush()

    @staticmethod
    async def delete(dict_id: int, db_session: AsyncSession) -> None:
        """删除字典类型

        :param dict_id: 字典类型ID
        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysDictType).where(SysDictType.dict_id == dict_id))


class DictDataMapper:
    """字典数据数据访问层"""

    @staticmethod
    async def get_by_id(dict_code: int, db_session: AsyncSession) -> SysDictData | None:
        """根据字典编码获取字典数据ORM对象

        :param dict_code: 字典编码
        :param db_session: 数据库会话
        :return: 字典数据ORM对象或None
        """
        result = await db_session.execute(select(SysDictData).where(SysDictData.dict_code == dict_code))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_type_and_value(dict_type: str, dict_value: str, db_session: AsyncSession) -> SysDictData | None:
        """根据字典类型和字典值获取字典数据ORM对象

        :param dict_type: 字典类型
        :param dict_value: 字典值
        :param db_session: 数据库会话
        :return: 字典数据ORM对象或None
        """
        result = await db_session.execute(
            select(SysDictData).where(SysDictData.dict_type == dict_type, SysDictData.dict_value == dict_value)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list_by_type(dict_type: str, db_session: AsyncSession) -> Sequence[SysDictData]:
        """根据字典类型获取字典数据列表

        :param dict_type: 字典类型
        :param db_session: 数据库会话
        :return: 字典数据ORM对象列表
        """
        result = await db_session.execute(
            select(SysDictData)
            .where(SysDictData.dict_type == dict_type, SysDictData.status == "0")
            .order_by(SysDictData.dict_sort, SysDictData.dict_code)
        )
        return result.scalars().all()

    @staticmethod
    async def get_list(query_params: DictDataQueryDTO, db_session: AsyncSession) -> tuple[Sequence[SysDictData], int]:
        """获取字典数据列表

        :param query_params: 查询参数DTO
        :param db_session: 数据库会话
        :return: 字典数据列表或分页结果
        """
        stmt = select(SysDictData)

        # 添加过滤条件
        if query_params.dict_type:
            stmt = stmt.where(SysDictData.dict_type == query_params.dict_type)
        if query_params.dict_label:
            stmt = stmt.where(SysDictData.dict_label.like(f"%{query_params.dict_label}%"))
        if query_params.status:
            stmt = stmt.where(SysDictData.status == query_params.status)
        if query_params.begin_time and query_params.end_time:
            begin_datetime = query_params.begin_time.replace(hour=0, minute=0, second=0)
            end_datetime = query_params.end_time.replace(hour=23, minute=59, second=59)
            stmt = stmt.where(SysDictData.create_time.between(begin_datetime, end_datetime))
        stmt = stmt.order_by(SysDictData.dict_sort, SysDictData.dict_code)

        # 获取总数
        total_query = select(func.count()).select_from(stmt.subquery())
        total_result = await db_session.execute(total_query)
        total = total_result.scalar()

        # 分页
        page_num = query_params.page
        page_size = query_params.size
        if page_num and page_size:
            stmt = stmt.offset((page_num - 1) * page_size).limit(page_size)

        result = await db_session.execute(stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def count_by_type(dict_type: str, db_session: AsyncSession) -> int:
        """统计指定字典类型的字典数据数量

        :param dict_type: 字典类型
        :param db_session: 数据库会话
        :return: 数量
        """
        result = await db_session.execute(
            select(func.count(SysDictData.dict_code)).where(SysDictData.dict_type == dict_type)
        )
        return result.scalar()

    @staticmethod
    async def add(new_orm: SysDictData, db_session: AsyncSession) -> SysDictData:
        """新增字典数据

        :param new_orm: 新字典数据ORM对象
        :param db_session: 数据库会话
        :return: 新创建的字典数据ORM对象
        """
        db_session.add(new_orm)
        await db_session.flush()
        await db_session.refresh(new_orm)
        return new_orm

    @staticmethod
    async def update(updated_orm: SysDictData, db_session: AsyncSession) -> None:
        """更新字典数据

        :param updated_orm: 更新后的 ORM 实体
        :param db_session: 数据库会话
        """
        await db_session.merge(updated_orm)
        await db_session.flush()

    @staticmethod
    async def update_type_by_old_type(old_type: str, new_type: str, db_session: AsyncSession) -> None:
        """批量更新字典类型

        :param old_type: 旧字典类型
        :param new_type: 新字典类型
        :param db_session: 数据库会话
        """
        await db_session.execute(
            update(SysDictData).where(SysDictData.dict_type == old_type).values(dict_type=new_type)
        )

    @staticmethod
    async def delete(dict_code: int, db_session: AsyncSession) -> None:
        """删除字典数据

        :param dict_code: 字典编码
        :param db_session: 数据库会话
        """
        await db_session.execute(delete(SysDictData).where(SysDictData.dict_code == dict_code))
