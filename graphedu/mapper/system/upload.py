"""文件上传Mapper - 数据访问层
负责与数据库交互，提供文件信息的CRUD操作
"""

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.system import SysUpload


class UploadMapper:
    """文件上传Mapper - 数据访问层"""

    @staticmethod
    async def get_by_id(file_id: int, db: AsyncSession) -> SysUpload | None:
        """根据ID查询文件信息

        :param file_id: 文件ID
        :param db: 数据库会话
        :return: 文件信息对象，不存在则返回None
        """
        result = await db.execute(select(SysUpload).where(SysUpload.file_id == file_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def add_upload(upload_orm: SysUpload, db: AsyncSession) -> SysUpload:
        """添加文件记录

        :param upload_orm: 文件ORM对象
        :param db: 数据库会话
        :return: 添加后的文件对象（包含自增ID）
        """
        db.add(upload_orm)
        await db.flush()
        await db.refresh(upload_orm)
        return upload_orm

    @staticmethod
    async def update_counts(
        db: AsyncSession, file_id: int, view_count: bool = False, download_count: bool = False
    ) -> bool:
        """更新文件统计计数

        :param db: 数据库会话
        :param file_id: 文件ID
        :param view_count: 是否需要浏览次数 + 1
        :param download_count: 是否需要下载次数 + 1
        :return: 是否更新成功
        """
        # 构建更新表达式
        updates = {}
        if view_count:
            updates[SysUpload.view_count] = SysUpload.view_count + 1
        if download_count:
            updates[SysUpload.download_count] = SysUpload.download_count + 1

        if not updates:
            return False

        # 执行更新
        result: Any = await db.execute(update(SysUpload).where(SysUpload.file_id == file_id).values(**updates))
        await db.flush()
        return result.rowcount > 0  # type: ignore[attr-defined]

    @staticmethod
    async def get_by_ids(file_ids: list[int], db: AsyncSession) -> list[SysUpload]:
        """根据 ID 列表批量查询文件信息。

        :param file_ids: 文件 ID 列表。
        :param db: 数据库会话。
        :return: 文件信息列表。
        """
        if not file_ids:
            return []
        result = await db.execute(select(SysUpload).where(SysUpload.file_id.in_(file_ids)))
        return list(result.scalars().all())
