"""日志管理服务模块。

该模块提供操作日志和登录日志的管理功能。

职责：
1. 处理业务逻辑。
2. DTO 到 ORM 的转换。
3. 组装 VO 返回。
"""

import logging

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.auth import LoginUserNotLockedException
from graphedu.common.exceptions.services.system.log import (
    LogClearFailedException,
    LogCreateFailedException,
    LogDeleteFailedException,
    LogIdListEmptyException,
)
from graphedu.common.models.dto.systemv2.log import (
    LoginLogCreateDTO,
    LoginLogQueryDTO,
    OperLogCreateDTO,
    OperLogQueryDTO,
    UnlockUserDTO,
)
from graphedu.common.models.orm import SysLogininfor, SysOperLog
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.systemv2.log import LoginLogListVO, OperLogDetailVO, OperLogListVO
from graphedu.mapper.system.log import LoginLogMapper, OperLogMapper

logger = logging.getLogger(__name__)


class OperationLogService:
    """操作日志管理服务类。

    提供操作日志的查询、新增、删除和清空功能。
    """

    @staticmethod
    async def get_operation_log_list(
        query_db: AsyncSession, query_object: OperLogQueryDTO
    ) -> PageResponse[OperLogListVO]:
        """获取操作日志列表。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[OperLogListVO]: 操作日志分页结果。
        """
        operation_log_list_result, total = await OperLogMapper.get_log_list(query_object, query_db)
        vo_list = [OperLogListVO.model_validate(item) for item in operation_log_list_result]

        return PageResponse(
            rows=vo_list,
            page=query_object.page or 1,
            size=query_object.size or 10,
            total=total,
        )

    @staticmethod
    async def add_operation_log(query_db: AsyncSession, log_dto: OperLogCreateDTO) -> None:
        """新增操作日志。

        Args:
            query_db: 数据库会话。
            log_dto: 新增操作日志 DTO。

        Raises:
            LogCreateFailedException: 操作日志创建失败。
        """
        # DTO -> ORM
        new_orm = SysOperLog(**log_dto.model_dump())
        try:
            await OperLogMapper.add_log(new_orm, query_db)
            logger.info("新增操作日志成功")
        except Exception as e:
            raise LogCreateFailedException from e

    @staticmethod
    async def delete_operation_log(query_db: AsyncSession, delete_ids: list[int]) -> None:
        """删除操作日志（真删除）。

        Args:
            query_db: 数据库会话。
            delete_ids: 删除操作日志 ID 列表。

        Raises:
            LogIdListEmptyException: 日志 ID 列表为空。
            LogDeleteFailedException: 操作日志删除失败。
        """
        if not delete_ids:
            raise LogIdListEmptyException

        for oper_id in delete_ids:
            try:
                await OperLogMapper.delete_log(oper_id, query_db)
                logger.info(f"删除操作日志成功: {oper_id}")
            except Exception as e:
                raise LogDeleteFailedException from e

    @classmethod
    async def clear_operation_log(cls, query_db: AsyncSession) -> None:
        """清除操作日志。

        Args:
            query_db: 数据库会话。

        Raises:
            LogClearFailedException: 操作日志清空失败。
        """
        try:
            await OperLogMapper.clear_logs(query_db)
            logger.info("清除操作日志成功")
        except Exception as e:
            raise LogClearFailedException from e

    @staticmethod
    async def get_operation_log_detail(oper_id: int, query_db: AsyncSession) -> OperLogDetailVO | None:
        """获取操作日志详情。

        Args:
            oper_id: 操作日志ID。
            query_db: 数据库会话。

        Returns:
            OperLogDetailVO | None: 操作日志详情 VO，如果不存在则返回 None。
        """
        orm_result = await OperLogMapper.get_log_by_id(oper_id, query_db)
        if orm_result:
            return OperLogDetailVO.model_validate(orm_result)
        return None

    # @classmethod
    # async def export_operation_log_list(cls, redis_session: AsyncRedis, operation_log_list: List):
    #     """
    #     导出操作日志信息service
    #
    #     :param redis_session: Redis对象
    #     :param operation_log_list: 操作日志信息列表
    #     :return: 操作日志信息对应excel的二进制数据
    #     """
    #     # TODO: 实现导出功能，需要DictDataService和ExcelUtil
    #     # 创建一个映射字典，将英文键映射到中文键
    #     mapping_dict = {
    #         'oper_id': '日志编号',
    #         'title': '系统模块',
    #         'business_type': '操作类型',
    #         'method': '方法名称',
    #         'request_method': '请求方式',
    #         'oper_name': '操作人员',
    #         'dept_name': '部门名称',
    #         'oper_url': '请求URL',
    #         'oper_ip': '操作地址',
    #         'oper_location': '操作地点',
    #         'oper_param': '请求参数',
    #         'json_result': '返回参数',
    #         'status': '操作状态',
    #         'error_msg': '错误消息',
    #         'oper_time': '操作日期',
    #         'cost_time': '消耗时间（毫秒）',
    #     }
    #
    #     # 转换数据格式
    #     for item in operation_log_list:
    #         if hasattr(item, 'status'):
    #             item.status = '成功' if item.status == 0 else '失败'
    #
    #     # 这里需要实现Excel导出功能
    #     # binary_data = ExcelUtil.export_list2excel(operation_log_list, mapping_dict)
    #     # return binary_data
    #     raise NotImplementedError("Excel导出功能待实现")


class LoginLogService:
    """登录日志管理服务类。

    提供登录日志的查询、新增、删除、清空和用户解锁功能。
    """

    @staticmethod
    async def get_login_log_list(
        query_db: AsyncSession, query_object: LoginLogQueryDTO
    ) -> PageResponse[LoginLogListVO]:
        """获取登录日志列表。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[LoginLogListVO]: 登录日志分页结果。
        """
        login_log_list_result, total = await LoginLogMapper.get_log_list(query_object, query_db)
        vo_list = [LoginLogListVO.model_validate(item) for item in login_log_list_result]

        return PageResponse(
            rows=vo_list,
            page=query_object.page or 1,
            size=query_object.size or 10,
            total=total,
        )

    @staticmethod
    async def add_login_log(query_db: AsyncSession, log_dto: LoginLogCreateDTO) -> None:
        """新增登录日志。

        Args:
            query_db: 数据库会话。
            log_dto: 新增登录日志 DTO。

        Raises:
            LogCreateFailedException: 登录日志创建失败。
        """
        # DTO -> ORM
        new_orm = SysLogininfor(**log_dto.model_dump())
        try:
            await LoginLogMapper.add_log(new_orm, query_db)
            logger.info("新增登录日志成功")
        except Exception as e:
            raise LogCreateFailedException from e

    @staticmethod
    async def delete_login_log(query_db: AsyncSession, delete_ids: list[int]) -> None:
        """删除登录日志（真删除）。

        Args:
            query_db: 数据库会话。
            delete_ids: 删除登录日志 ID 列表。

        Raises:
            LogIdListEmptyException: 日志 ID 列表为空。
            LogDeleteFailedException: 登录日志删除失败。
        """
        if not delete_ids:
            raise LogIdListEmptyException

        for info_id in delete_ids:
            try:
                await LoginLogMapper.delete_log(info_id, query_db)
                logger.info(f"删除登录日志成功: {info_id}")
            except Exception as e:
                raise LogDeleteFailedException from e

    @staticmethod
    async def clear_login_log(query_db: AsyncSession) -> None:
        """清除登录日志。

        Args:
            query_db: 数据库会话。

        Raises:
            LogClearFailedException: 登录日志清空失败。
        """
        try:
            await LoginLogMapper.clear_logs(query_db)
            logger.info("清除登录日志成功")
        except Exception as e:
            raise LogClearFailedException from e

    @staticmethod
    async def unlock_user(redis_session: AsyncRedis, unlock_user: UnlockUserDTO) -> None:
        """解锁用户。

        Args:
            redis_session: Redis 客户端。
            unlock_user: 解锁用户 DTO。

        Raises:
            LoginUserNotLockedException: 用户未被锁定。
        """
        locked_user = await redis_session.get(f"account_lock:{unlock_user.user_name}")
        if locked_user:
            await redis_session.delete(f"account_lock:{unlock_user.user_name}")
            logger.info(f"解锁用户成功: {unlock_user.user_name}")
        else:
            raise LoginUserNotLockedException(username=unlock_user.user_name)

    # @classmethod
    # async def export_login_log_list(cls, login_log_list: List):
    #     """
    #     导出登录日志信息service
    #
    #     :param login_log_list: 登录日志信息列表
    #     :return: 登录日志信息对应excel的二进制数据
    #     """
    #     # TODO: 实现导出功能
    #     # 创建一个映射字典，将英文键映射到中文键
    #     mapping_dict = {
    #         'info_id': '访问编号',
    #         'user_name': '用户名称',
    #         'ipaddr': '登录地址',
    #         'login_location': '登录地点',
    #         'browser': '浏览器',
    #         'os': '操作系统',
    #         'status': '登录状态',
    #         'msg': '操作信息',
    #         'login_time': '登录日期',
    #     }
    #
    #     for item in login_log_list:
    #         if hasattr(item, 'status'):
    #             item.status = '成功' if item.status == '0' else '失败'
    #
    #     # binary_data = ExcelUtil.export_list2excel(login_log_list, mapping_dict)
    #     # return binary_data
    #     raise NotImplementedError("Excel导出功能待实现")
