"""Pagination utility functions.

This module provides utilities for paginating data, including both
in-memory list pagination and database query pagination.
"""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.vo.base import PageResponse
from graphedu.common.utils.strings import SqlalchemyUtil


class PageUtil:
    """Pagination utility class.

    Provides methods for paginating both in-memory lists and database queries.
    """

    @classmethod
    def get_page_obj(cls, data_list: list, page_num: int, page_size: int):
        """Paginate a data list and return the paginated result.

        Args:
            data_list: Original data list.
            page_num: Current page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            PageResponse object containing paginated data.
        """
        # 计算起始索引和结束索引
        start = (page_num - 1) * page_size
        end = page_num * page_size

        # 根据计算得到的起始索引和结束索引对数据列表进行切片
        paginated_data = data_list[start:end]

        return PageResponse(rows=paginated_data, page=page_num, size=page_size, total=len(data_list))

    @staticmethod
    async def paginate(db: AsyncSession, query: Select, page_num: int, page_size: int, is_page: bool = False):
        """Paginate a SQLAlchemy query and return the paginated result.

        Args:
            db: SQLAlchemy async session.
            query: SQLAlchemy Select query statement.
            page_num: Current page number (1-indexed).
            page_size: Number of items per page.
            is_page: Whether to enable pagination.

        Returns:
            PageResponse object containing paginated data if is_page is True,
            otherwise returns all data as a list.
        """
        if is_page:
            total = (await db.execute(select(func.count("*")).select_from(query.subquery()))).scalar()
            query_result = await db.execute(query.offset((page_num - 1) * page_size).limit(page_size))
            paginated_data = []
            for row in query_result:
                if row and len(row) == 1:
                    paginated_data.append(row[0])
                else:
                    paginated_data.append(row)
            result = PageResponse(
                rows=SqlalchemyUtil.serialize_result(paginated_data), page=page_num, size=page_size, total=total
            )
        else:
            query_result = await db.execute(query)
            no_paginated_data = []
            for row in query_result:
                if row and len(row) == 1:
                    no_paginated_data.append(row[0])
                else:
                    no_paginated_data.append(row)
            result = SqlalchemyUtil.serialize_result(no_paginated_data)

        return result


def get_page_obj(data_list: list, page_num: int, page_size: int):
    """Paginate a data list and return the paginated result.

    Args:
        data_list: Original data list.
        page_num: Current page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        PageResponse object containing paginated data.
    """
    # 计算起始索引和结束索引
    start = (page_num - 1) * page_size
    end = page_num * page_size

    # 根据计算得到的起始索引和结束索引对数据列表进行切片
    paginated_data = data_list[start:end]

    return PageResponse(rows=paginated_data, page=page_num, size=page_size, total=len(data_list))
