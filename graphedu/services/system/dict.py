"""字典管理服务模块。

该模块提供字典类型和字典数据的管理功能，支持缓存的初始化和刷新。

职责：
1. 处理业务逻辑。
2. DTO 到 ORM 的转换。
3. 组装 VO 返回。
"""

from datetime import datetime
import json
import logging

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions import (
    DictDataAlreadyExistsException,
    DictDataCreateFailedException,
    DictDataDeleteFailedException,
    DictDataIdListEmptyException,
    DictDataNotFoundException,
    DictDataUpdateFailedException,
    DictTypeAlreadyExistsException,
    DictTypeCreateFailedException,
    DictTypeDeleteFailedException,
    DictTypeHasDataException,
    DictTypeIdListEmptyException,
    DictTypeNotFoundException,
    DictTypeUpdateFailedException,
)
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import RedisConstants
from graphedu.common.models.dto.systemv2.dict import (
    DictDataCreateDTO,
    DictDataQueryDTO,
    DictDataUpdateDTO,
    DictTypeCreateDTO,
    DictTypeQueryDTO,
    DictTypeUpdateDTO,
)
from graphedu.common.models.orm import SysDictData, SysDictType
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.systemv2.dict import (
    DictDataDetailVO,
    DictDataListVO,
    DictDataSimpleVO,
    DictTypeDetailVO,
    DictTypeListVO,
)
from graphedu.mapper.system.dict import DictDataMapper, DictTypeMapper

logger = logging.getLogger(__name__)


async def _update_cache_for_type(query_db: AsyncSession, redis_session: AsyncRedis, dict_type: str) -> None:
    """更新指定字典类型的缓存。

    Args:
        query_db: 数据库会话。
        redis_session: Redis 客户端。
        dict_type: 字典类型。
    """
    dict_data_list = await DictDataMapper.get_list_by_type(dict_type, query_db)

    dict_data = [DictDataSimpleVO.model_validate(item).model_dump() for item in dict_data_list]

    await redis_session.set(f"{RedisConstants.Common.DICT_TYPE}:{dict_type}", json.dumps(dict_data, ensure_ascii=False))


class DictTypeService:
    """字典类型管理服务类。

    提供字典类型的增删改查功能，支持缓存管理。
    """

    @staticmethod
    async def get_dict_type_list(
        query_db: AsyncSession, query_object: DictTypeQueryDTO
    ) -> PageResponse[DictTypeListVO]:
        """获取字典类型列表。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[DictTypeListVO]: 分页结果。
        """
        rows, total = await DictTypeMapper.get_list(query_object, query_db)
        return PageResponse(
            rows=[DictTypeListVO.model_validate(item) for item in rows],
            total=total,
            page=query_object.page,
            size=query_object.size,
        )

    @staticmethod
    async def check_dict_type_unique(query_db: AsyncSession, dict_type: str, dict_id: int | None = None) -> bool:
        """校验字典类型是否唯一。

        Args:
            query_db: 数据库会话。
            dict_type: 字典类型。
            dict_id: 字典 ID（编辑时传入）。

        Returns:
            bool: True 表示唯一，False 表示不唯一。
        """
        existing_dict = await DictTypeMapper.get_by_dict_type(dict_type, query_db)
        return not (existing_dict and (dict_id is None or existing_dict.dict_id != dict_id))

    @staticmethod
    async def add_dict_type(
        query_db: AsyncSession,
        redis_session: AsyncRedis,
        dict_type_data: DictTypeCreateDTO,
        current_user: CurrentUser,
    ) -> None:
        """新增字典类型。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            dict_type_data: 新增字典类型 DTO。
            current_user: 当前用户。

        Raises:
            DictTypeAlreadyExistsException: 字典类型已存在。
            DictTypeCreateFailedException: 字典类型创建失败。
        """
        # 校验唯一性
        if not await DictTypeService.check_dict_type_unique(query_db, dict_type_data.dict_type):
            raise DictTypeAlreadyExistsException(dict_type=dict_type_data.dict_type, dict_name=dict_type_data.dict_name)

        # DTO -> ORM
        new_dict_type = SysDictType(
            dict_name=dict_type_data.dict_name,
            dict_type=dict_type_data.dict_type,
            status=dict_type_data.status,
            remark=dict_type_data.remark,
            create_by=current_user.detail.user.user_id if current_user.detail.user else None,
            create_time=datetime.now(),
            update_by=current_user.detail.user.user_id if current_user.detail.user else None,
            update_time=datetime.now(),
        )

        try:
            await DictTypeMapper.add(new_dict_type, query_db)
            # 初始化空的字典数据缓存
            await redis_session.set(
                f"{RedisConstants.Common.DICT_TYPE}:{dict_type_data.dict_type}", json.dumps([], ensure_ascii=False)
            )
            logger.info(f"新增字典类型成功: {dict_type_data.dict_name}")
        except Exception as e:
            raise DictTypeCreateFailedException(dict_name=dict_type_data.dict_name) from e

    @staticmethod
    async def update_dict_type(
        query_db: AsyncSession,
        redis_session: AsyncRedis,
        updated_dto: DictTypeUpdateDTO,
        current_user: CurrentUser,
    ) -> None:
        """编辑字典类型。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            updated_dto: 编辑字典类型 DTO。
            current_user: 当前用户。

        Raises:
            DictTypeNotFoundException: 字典类型不存在。
            DictTypeAlreadyExistsException: 字典类型已存在。
            DictTypeUpdateFailedException: 字典类型更新失败。
        """
        # 获取原始数据
        origin_orm = await DictTypeMapper.get_by_id(updated_dto.dict_id, query_db)
        if not origin_orm:
            raise DictTypeNotFoundException(dict_id=updated_dto.dict_id)

        # 校验唯一性
        if updated_dto.dict_type and updated_dto.dict_type != origin_orm.dict_type:  # noqa: SIM102
            if not await DictTypeService.check_dict_type_unique(query_db, updated_dto.dict_type, updated_dto.dict_id):
                raise DictTypeAlreadyExistsException(
                    dict_type=updated_dto.dict_type, dict_name=updated_dto.dict_name or origin_orm.dict_name
                )

        # 如果字典类型的类型字段发生变化，需要更新关联的字典数据
        old_dict_type = origin_orm.dict_type
        type_changed = updated_dto.dict_type and updated_dto.dict_type != old_dict_type
        if type_changed and updated_dto.dict_type:
            await DictDataMapper.update_type_by_old_type(old_dict_type, updated_dto.dict_type, query_db)

        # DTO -> ORM，直接应用于原 ORM 上
        updated_dict = updated_dto.model_dump(exclude_unset=True)
        for field, value in updated_dict.items():
            setattr(origin_orm, field, value)
        origin_orm.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        origin_orm.update_time = datetime.now()

        # 更新字典类型
        try:
            await DictTypeMapper.update(origin_orm, query_db)
            # 更新缓存
            if type_changed:
                # 删除旧的缓存键
                old_key = f"{RedisConstants.Common.DICT_TYPE}:{old_dict_type}"
                await redis_session.delete(old_key)
            # 设置新的或更新后的缓存键
            final_dict_type = updated_dto.dict_type if (type_changed and updated_dto.dict_type) else old_dict_type
            await _update_cache_for_type(query_db, redis_session, final_dict_type)
            logger.info(f"更新字典类型成功: {updated_dto.dict_id}")
        except Exception as e:
            raise DictTypeUpdateFailedException(dict_id=updated_dto.dict_id) from e

    @staticmethod
    async def delete_dict_type(query_db: AsyncSession, redis_session: AsyncRedis, delete_id_list: list[int]) -> None:
        """删除字典类型。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            delete_id_list: 删除的字典类型 ID 列表。

        Raises:
            DictTypeIdListEmptyException: 字典类型 ID 列表为空。
            DictTypeNotFoundException: 字典类型不存在。
            DictTypeHasDataException: 字典类型已分配字典数据。
            DictTypeDeleteFailedException: 字典类型删除失败。
        """
        # 校验数据
        if not delete_id_list:
            raise DictTypeIdListEmptyException

        delete_cache_keys = []
        for dict_id in delete_id_list:
            # 检查字典类型是否存在
            dict_type_info = await DictTypeMapper.get_by_id(dict_id, query_db)
            if not dict_type_info:
                raise DictTypeNotFoundException(dict_id=dict_id)

            # 检查是否已分配字典数据
            count = await DictDataMapper.count_by_type(dict_type_info.dict_type, query_db)
            if count > 0:
                raise DictTypeHasDataException(dict_name=dict_type_info.dict_name, dict_type=dict_type_info.dict_type)

            # 执行删除操作（真删除）
            try:
                await DictTypeMapper.delete(dict_id, query_db)
                delete_cache_keys.append(f"{RedisConstants.Common.DICT_TYPE}:{dict_type_info.dict_type}")
            except Exception as e:
                raise DictTypeDeleteFailedException(dict_id=dict_id) from e

        # 删除缓存
        if delete_cache_keys:
            await redis_session.delete(*delete_cache_keys)

        logger.info(f"删除字典类型成功: {delete_id_list}")

    @staticmethod
    async def get_dict_type_detail(query_db: AsyncSession, dict_id: int) -> DictTypeDetailVO | None:
        """获取字典类型详细信息。

        Args:
            query_db: 数据库会话。
            dict_id: 字典类型 ID。

        Returns:
            DictTypeDetailVO | None: 字典类型详细信息 VO。

        Raises:
            DictTypeNotFoundException: 字典类型不存在。
        """
        dict_type = await DictTypeMapper.get_by_id(dict_id, query_db)
        if not dict_type:
            raise DictTypeNotFoundException(dict_id=dict_id)
        return DictTypeDetailVO.model_validate(dict_type)

    @staticmethod
    async def refresh_cache(query_db: AsyncSession, redis_session: AsyncRedis) -> None:
        """刷新字典缓存。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
        """
        await DictDataService.init_cache(query_db, redis_session)
        logger.info("刷新字典缓存成功")

    @staticmethod
    async def get_dict_type_options(query_db: AsyncSession) -> list[DictTypeListVO]:
        """获取字典类型选项列表（用于下拉框等场景）

        Args:
            query_db: 数据库会话。

        Returns:
            list[DictTypeListVO]: 字典类型选项列表。
        """
        dict_type_list = await DictTypeMapper.get_all(query_db)
        return [DictTypeListVO.model_validate(item) for item in dict_type_list]


class DictDataService:
    """字典数据管理服务类。

    提供字典数据的增删改查功能，支持缓存管理。
    """

    @staticmethod
    async def get_dict_data_list(
        query_db: AsyncSession, query_object: DictDataQueryDTO
    ) -> PageResponse[DictDataListVO]:
        """获取字典数据列表。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[DictDataListVO]: 分页结果。
        """
        rows, total = await DictDataMapper.get_list(query_object, query_db)
        dict_data_list_result = [DictDataListVO.model_validate(item) for item in rows]

        return PageResponse(rows=dict_data_list_result, total=total, page=query_object.page, size=query_object.size)

    @staticmethod
    async def get_dict_data_by_type(query_db: AsyncSession, dict_type: str) -> list[DictDataSimpleVO]:
        """根据字典类型获取字典数据列表。

        Args:
            query_db: 数据库会话。
            dict_type: 字典类型。

        Returns:
            list[DictDataSimpleVO]: 字典数据简化 VO 列表。
        """
        dict_data_list = await DictDataMapper.get_list_by_type(dict_type, query_db)
        return [DictDataSimpleVO.model_validate(item) for item in dict_data_list]

    @staticmethod
    async def get_dict_data_from_cache(
        query_db: AsyncSession, redis_session: AsyncRedis, dict_type: str
    ) -> list[DictDataSimpleVO]:
        """从缓存获取字典数据列表（缓存不存在时从数据库加载）。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            dict_type: 字典类型。

        Returns:
            list[DictDataSimpleVO]: 字典数据列表 VO。
        """
        # 先从缓存获取
        dict_data_str = await redis_session.get(f"{RedisConstants.Common.DICT_TYPE}:{dict_type}")
        if dict_data_str:
            result: list[dict] = json.loads(dict_data_str)
            return [DictDataSimpleVO.model_validate(item) for item in result]

        # 缓存不存在，从数据库加载
        dict_data_list = await DictDataMapper.get_list_by_type(dict_type, query_db)

        # 转换为简化 VO
        dict_data = [DictDataSimpleVO.model_validate(item).model_dump() for item in dict_data_list]

        # 更新缓存
        await redis_session.set(
            f"{RedisConstants.Common.DICT_TYPE}:{dict_type}", json.dumps(dict_data, ensure_ascii=False)
        )

        return [DictDataSimpleVO.model_validate(item) for item in dict_data_list]

    @staticmethod
    async def init_cache(query_db: AsyncSession, redis_session: AsyncRedis) -> None:
        """初始化字典缓存。

        删除所有字典缓存并重新加载所有启用的字典类型数据到缓存。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
        """
        # 删除所有字典缓存
        keys = await redis_session.keys(f"{RedisConstants.Common.DICT_TYPE}:*")
        if keys:
            await redis_session.delete(*keys)

        # 获取所有字典类型，只缓存正常状态的
        dict_type_list = await DictTypeMapper.get_all_enabled(query_db)

        # 缓存每个字典类型的数据
        for dict_type_obj in dict_type_list:
            # 获取字典数据列表
            dict_data_list = await DictDataMapper.get_list_by_type(dict_type_obj.dict_type, query_db)

            # 转换为简化VO
            dict_data = [DictDataSimpleVO.model_validate(item).model_dump() for item in dict_data_list]

            await redis_session.set(
                f"{RedisConstants.Common.DICT_TYPE}:{dict_type_obj.dict_type}",
                json.dumps(dict_data, ensure_ascii=False),
            )
        logger.info("初始化字典缓存成功")

    @staticmethod
    async def check_dict_data_unique(
        query_db: AsyncSession, dict_type: str, dict_value: str, dict_code: int | None = None
    ) -> bool:
        """校验字典数据是否唯一。

        Args:
            query_db: 数据库会话。
            dict_type: 字典类型。
            dict_value: 字典值。
            dict_code: 字典编码（编辑时传入）。

        Returns:
            bool: True 表示唯一，False 表示不唯一。
        """
        existing_dict = await DictDataMapper.get_by_type_and_value(dict_type, dict_value, query_db)
        return not (existing_dict and (dict_code is None or existing_dict.dict_code != dict_code))

    @staticmethod
    async def add_dict_data(
        query_db: AsyncSession, redis_session: AsyncRedis, dict_data: DictDataCreateDTO, current_user: CurrentUser
    ) -> None:
        """新增字典数据。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            dict_data: 新增字典数据 DTO。
            current_user: 当前用户。

        Raises:
            DictDataAlreadyExistsException: 字典数据已存在。
            DictDataCreateFailedException: 字典数据创建失败。
        """
        # 校验唯一性
        if not await DictDataService.check_dict_data_unique(query_db, dict_data.dict_type, dict_data.dict_value):
            raise DictDataAlreadyExistsException(
                dict_type=dict_data.dict_type, dict_value=dict_data.dict_value, dict_label=dict_data.dict_label
            )

        # DTO -> ORM
        new_object = SysDictData(**dict_data.model_dump())
        new_object.create_by = current_user.detail.user.user_id if current_user.detail.user else None
        new_object.create_time = datetime.now()
        new_object.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        new_object.update_time = datetime.now()

        try:
            await DictDataMapper.add(new_object, query_db)
            # 更新缓存
            await _update_cache_for_type(query_db, redis_session, dict_data.dict_type)
            logger.info(f"新增字典数据成功: {dict_data.dict_label}")
        except Exception as e:
            raise DictDataCreateFailedException(dict_label=dict_data.dict_label) from e

    @staticmethod
    async def update_dict_data(
        query_db: AsyncSession, redis_session: AsyncRedis, dict_data: DictDataUpdateDTO, current_user: CurrentUser
    ) -> None:
        """编辑字典数据。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            dict_data: 编辑字典数据 DTO。
            current_user: 当前用户。

        Raises:
            DictDataNotFoundException: 字典数据不存在。
            DictDataAlreadyExistsException: 字典数据已存在。
            DictDataUpdateFailedException: 字典数据更新失败。
        """
        # 获取原始数据
        origin_orm = await DictDataMapper.get_by_id(dict_data.dict_code, query_db)
        if not origin_orm:
            raise DictDataNotFoundException(dict_code=dict_data.dict_code)

        # 获取实际的字典类型（优先使用更新值，其次使用原始值）
        actual_dict_type = dict_data.dict_type or origin_orm.dict_type

        # 校验唯一性（只有当值真正改变时才校验）
        if (
            dict_data.dict_value is not None
            and dict_data.dict_value != origin_orm.dict_value
            and not await DictDataService.check_dict_data_unique(
                query_db, actual_dict_type, dict_data.dict_value, dict_data.dict_code
            )
        ):
            raise DictDataAlreadyExistsException(
                dict_type=actual_dict_type,
                dict_value=dict_data.dict_value,
                dict_label=dict_data.dict_label or origin_orm.dict_label,
            )

        # DTO -> ORM，直接应用于原 ORM 上
        updated_dict = dict_data.model_dump(exclude_unset=True)
        for field, value in updated_dict.items():
            setattr(origin_orm, field, value)
        origin_orm.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        origin_orm.update_time = datetime.now()

        try:
            await DictDataMapper.update(origin_orm, query_db)
            # 更新缓存
            await _update_cache_for_type(query_db, redis_session, dict_data.dict_type or origin_orm.dict_type)
            logger.info(f"更新字典数据成功: {dict_data.dict_code}")
        except Exception as e:
            raise DictDataUpdateFailedException(dict_code=dict_data.dict_code) from e

    @staticmethod
    async def delete_dict_data(query_db: AsyncSession, redis_session: AsyncRedis, delete_ids: list[int]) -> None:
        """删除字典数据。

        Args:
            query_db: 数据库会话。
            redis_session: Redis 客户端。
            delete_ids: 删除字典数据 ID 列表。

        Raises:
            DictDataIdListEmptyException: 字典数据 ID 列表为空。
            DictDataNotFoundException: 字典数据不存在。
            DictDataDeleteFailedException: 字典数据删除失败。
        """
        if not delete_ids:
            raise DictDataIdListEmptyException

        # 第一阶段：批量查询并验证所有字典数据是否存在，并收集需要更新缓存的类型
        affected_dict_types = set()
        for delete_id in delete_ids:
            dict_data = await DictDataMapper.get_by_id(delete_id, query_db)
            if not dict_data:
                raise DictDataNotFoundException(dict_code=delete_id)
            affected_dict_types.add(dict_data.dict_type)

        # 第二阶段：逐一执行删除操作
        for delete_id in delete_ids:
            try:
                await DictDataMapper.delete(delete_id, query_db)
            except Exception as e:
                raise DictDataDeleteFailedException(dict_code=delete_id) from e

        # 第三阶段：更新所有受影响的字典类型的缓存
        for dict_type in affected_dict_types:
            await _update_cache_for_type(query_db, redis_session, dict_type)

        logger.info(f"删除字典数据成功: {delete_ids}")

    @staticmethod
    async def get_dict_data_detail(query_db: AsyncSession, dict_code: int) -> DictDataDetailVO | None:
        """获取字典数据详细信息。

        Args:
            query_db: 数据库会话。
            dict_code: 字典数据编码。

        Returns:
            DictDataDetailVO | None: 字典数据详细信息 VO。

        Raises:
            DictDataNotFoundException: 字典数据不存在。
        """
        dict_data = await DictDataMapper.get_by_id(dict_code, query_db)
        if not dict_data:
            raise DictDataNotFoundException(dict_code=dict_code)
        return DictDataDetailVO.model_validate(dict_data)
