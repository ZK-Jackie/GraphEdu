"""定时任务管理服务模块。

该模块提供定时任务和任务执行日志的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
4. 与调度器交互。
"""

from datetime import datetime
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.job import (
    JobChangeStatusFailedException,
    JobConfigInvalidException,
    JobCreateFailedException,
    JobDeleteFailedException,
    JobExecuteFailedException,
    JobIdListEmptyException,
    JobLogClearFailedException,
    JobLogDeleteFailedException,
    JobLogIdListEmptyException,
    JobLogNotFoundException,
    JobNameAlreadyExistsException,
    JobNoPermissionException,
    JobNotFoundException,
    JobUpdateFailedException,
)
from graphedu.common.models.dto.toolv2.job import (
    JobCreateDTO,
    JobExecuteOnceDTO,
    JobLogQueryDTO,
    JobQueryDTO,
    JobStatusChangeDTO,
    JobUpdateDTO,
)
from graphedu.common.models.orm.system import SysJob
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.toolv2.job import JobDetailVO, JobExecuteResultVO, JobListVO, JobLogListVO
from graphedu.common.resource.modules.scheduler import AsyncSchedulerResource
from graphedu.jobs.job_executor import job_executor
from graphedu.mapper.system.job import JobLogMapper, JobMapper

logger = logging.getLogger(__name__)


# ============================================================================
# Webhook URL 生成工具
# ============================================================================


def generate_webhook_url(job_id: int, base_url: str) -> str:
    """生成外部 Webhook 触发 URL

    Args:
        job_id: 任务ID
        base_url: 基础 URL（从请求获取）

    Returns:
        Webhook 触发 URL
    """
    return f"{base_url}/webhook/job/{job_id}"


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_job_orm_to_list_vo(job_orm) -> JobListVO:
    """将任务 ORM 对象转换为 JobListVO。

    Args:
        job_orm: 任务 ORM 对象。

    Returns:
        JobListVO: 任务列表项 VO。
    """
    return JobListVO(
        job_id=job_orm.job_id,
        job_name=job_orm.job_name,
        job_group=job_orm.job_group,
        job_executor=job_orm.job_executor,
        invoke_target=job_orm.invoke_target,
        cron_expression=job_orm.cron_expression,
        misfire_policy=job_orm.misfire_policy,
        concurrent=job_orm.concurrent,
        status=job_orm.status,
        webhook_enabled=job_orm.webhook_enabled,
        create_time=job_orm.create_time,
        remark=job_orm.remark,
    )


def _convert_job_orm_to_detail_vo(job_orm, base_url: str | None = None) -> JobDetailVO:
    """将任务 ORM 对象转换为 JobDetailVO。

    Args:
        job_orm: 任务 ORM 对象。
        base_url: 基础 URL（可选，用于生成 Webhook 触发 URL）

    Returns:
        JobDetailVO: 任务详细信息 VO。
    """
    # 生成 Webhook 触发 URL（如果提供了 base_url）
    webhook_url_display = None
    if base_url:
        webhook_url_display = f"{base_url}/webhook/job/{job_orm.job_id}"

    return JobDetailVO(
        job_id=job_orm.job_id,
        job_name=job_orm.job_name,
        job_group=job_orm.job_group,
        job_executor=job_orm.job_executor,
        invoke_target=job_orm.invoke_target,
        job_args=job_orm.job_args,
        job_kwargs=job_orm.job_kwargs,
        cron_expression=job_orm.cron_expression,
        misfire_policy=job_orm.misfire_policy,
        concurrent=job_orm.concurrent,
        status=job_orm.status,
        webhook_enabled=job_orm.webhook_enabled,
        webhook_url=job_orm.webhook_url,
        webhook_secret=job_orm.webhook_secret,
        webhook_url_display=webhook_url_display,
        create_by=job_orm.create_by,
        create_time=job_orm.create_time,
        update_by=job_orm.update_by,
        update_time=job_orm.update_time,
        remark=job_orm.remark,
    )


def _convert_job_log_orm_to_list_vo(job_log_orm) -> JobLogListVO:
    """将任务日志 ORM 对象转换为 JobLogListVO。

    Args:
        job_log_orm: 任务日志 ORM 对象。

    Returns:
        JobLogListVO: 任务日志列表项 VO。
    """
    return JobLogListVO(
        job_log_id=job_log_orm.job_log_id,
        job_id=job_log_orm.job_id,
        job_name=job_log_orm.job_name,
        job_group=job_log_orm.job_group,
        invoke_target=job_log_orm.invoke_target,
        job_message=job_log_orm.job_message,
        status=job_log_orm.status,
        exception_info=job_log_orm.exception_info,
        create_time=job_log_orm.create_time,
    )


# ============================================================================
# 定时任务服务
# ============================================================================


class JobService:
    """定时任务业务逻辑层"""

    @staticmethod
    async def add_job(
        query_db: AsyncSession,
        scheduler: AsyncSchedulerResource,
        job_data: JobCreateDTO,
        current_user_id: int,
        base_url: str | None = None,
    ) -> JobDetailVO:
        """新增任务

        Args:
            query_db: 数据库会话
            scheduler: 调度器资源实例
            job_data: 任务创建数据
            current_user_id: 当前用户ID
            base_url: 基础 URL（可选，用于生成 Webhook 触发 URL）

        Returns:
            JobDetailVO: 任务详细信息

        Raises:
            JobNameAlreadyExistsException: 任务名称已存在
            JobCreateFailedException: 任务创建失败
        """
        # 1. 校验任务名称唯一性
        existing_job = await JobMapper.get_by_name(job_data.job_name, query_db)
        if existing_job:
            raise JobNameAlreadyExistsException(job_name=job_data.job_name)

        try:
            # 2. 创建 ORM 对象
            job_orm = SysJob(
                job_name=job_data.job_name,
                job_group=job_data.job_group,
                job_executor=job_data.job_executor,
                invoke_target=job_data.invoke_target,
                job_args=job_data.job_args,
                job_kwargs=job_data.job_kwargs,
                cron_expression=job_data.cron_expression,
                misfire_policy=job_data.misfire_policy,
                concurrent=job_data.concurrent,
                status=job_data.status,
                webhook_enabled=job_data.webhook_enabled,
                webhook_url=job_data.webhook_url,
                webhook_secret=job_data.webhook_secret,
                create_by=current_user_id,
                remark=job_data.remark,
            )

            # 3. 先 flush 到数据库获取 job_id（暂不提交事务）
            job_orm = await JobMapper.add_job(job_orm, query_db)

            # 4. 如果任务状态为正常，先添加到调度器（在 commit 之前，失败可回滚）
            if job_data.status == "0":
                await scheduler.add_job(
                    func=job_executor,
                    job_id=job_orm.job_id,
                    cron_expression=job_data.cron_expression,
                    executor_type=job_data.job_executor,
                    target=job_data.invoke_target,
                    args=job_data.job_args,
                    kwargs=job_data.job_kwargs,
                    misfire_policy=job_data.misfire_policy,
                    job_name=job_data.job_name,
                )

            # 5. 调度器操作成功后提交数据库
            await query_db.commit()

            logger.info(f"任务创建成功: job_id={job_orm.job_id}, job_name={job_data.job_name}")
            return _convert_job_orm_to_detail_vo(job_orm, base_url)

        except Exception as e:
            await query_db.rollback()
            logger.error(f"任务创建失败: job_name={job_data.job_name}, error={e}")
            raise JobCreateFailedException(job_name=job_data.job_name) from e

    @staticmethod
    async def update_job(
        query_db: AsyncSession,
        scheduler: AsyncSchedulerResource,
        job_data: JobUpdateDTO,
        current_user_id: int,
        base_url: str | None = None,
    ) -> JobDetailVO:
        """修改任务

        Args:
            query_db: 数据库会话
            scheduler: 调度器资源实例
            job_data: 任务更新数据
            current_user_id: 当前用户ID
            base_url: 基础 URL（可选，用于生成 Webhook 触发 URL）

        Returns:
            JobDetailVO: 任务详细信息

        Raises:
            JobNotFoundException: 任务不存在
            JobNameAlreadyExistsException: 任务名称已存在
            JobUpdateFailedException: 任务更新失败
        """
        # 1. 查询任务
        job_orm = await JobMapper.get_by_id(job_data.job_id, query_db)
        if not job_orm:
            raise JobNotFoundException(job_id=job_data.job_id)

        # 2. 校验任务名称唯一性
        if job_data.job_name and job_data.job_name != job_orm.job_name:
            existing_job = await JobMapper.is_job_name_exists(
                job_data.job_name, query_db, exclude_job_id=job_data.job_id
            )
            if existing_job:
                raise JobNameAlreadyExistsException(job_name=job_data.job_name)

        try:
            # 3. 先从调度器移除旧任务（失败则忽略，调度器中可能本不存在此任务）
            try:
                await scheduler.remove_job(job_data.job_id)
            except Exception as remove_err:
                logger.warning(
                    f"移除旧调度任务失败（可能已不存在于调度器中）: job_id={job_data.job_id}, error={remove_err}"
                )

            # 4. 更新 ORM 对象
            if job_data.job_name is not None:
                job_orm.job_name = job_data.job_name
            if job_data.job_group is not None:
                job_orm.job_group = job_data.job_group
            if job_data.job_executor is not None:
                job_orm.job_executor = job_data.job_executor
            if job_data.invoke_target is not None:
                job_orm.invoke_target = job_data.invoke_target
            if job_data.job_args is not None:
                job_orm.job_args = job_data.job_args
            if job_data.job_kwargs is not None:
                job_orm.job_kwargs = job_data.job_kwargs
            if job_data.cron_expression is not None:
                job_orm.cron_expression = job_data.cron_expression
            if job_data.misfire_policy is not None:
                job_orm.misfire_policy = job_data.misfire_policy
            if job_data.concurrent is not None:
                job_orm.concurrent = job_data.concurrent
            if job_data.status is not None:
                job_orm.status = job_data.status
            if job_data.webhook_enabled is not None:
                job_orm.webhook_enabled = job_data.webhook_enabled
            if job_data.webhook_url is not None:
                job_orm.webhook_url = job_data.webhook_url
            if job_data.webhook_secret is not None:
                job_orm.webhook_secret = job_data.webhook_secret
            if job_data.remark is not None:
                job_orm.remark = job_data.remark

            job_orm.update_by = current_user_id
            job_orm.update_time = datetime.now()

            # 5. flush 更新到数据库（暂不提交事务）
            await JobMapper.update(job_orm, query_db)

            # 6. 如果任务状态为正常，重新添加到调度器（在 commit 之前，失败可回滚）
            if job_orm.status == "0":
                await scheduler.add_job(
                    func=job_executor,
                    job_id=job_orm.job_id,
                    cron_expression=job_orm.cron_expression,
                    executor_type=job_orm.job_executor,
                    target=job_orm.invoke_target,
                    args=job_orm.job_args,
                    kwargs=job_orm.job_kwargs,
                    misfire_policy=job_orm.misfire_policy,
                    job_name=job_orm.job_name,
                )

            # 7. 所有操作成功后提交数据库
            await query_db.commit()

            logger.info(f"任务更新成功: job_id={job_orm.job_id}")
            return _convert_job_orm_to_detail_vo(job_orm, base_url)

        except Exception as e:
            await query_db.rollback()
            logger.error(f"任务更新失败: job_id={job_data.job_id}, error={e}")
            raise JobUpdateFailedException(job_id=job_data.job_id) from e

    @staticmethod
    async def delete_job(
        query_db: AsyncSession,
        scheduler: AsyncSchedulerResource,
        job_ids: list[int],
    ) -> None:
        """删除任务

        Args:
            query_db: 数据库会话
            scheduler: 调度器资源实例
            job_ids: 任务ID列表

        Raises:
            JobIdListEmptyException: 任务ID列表为空
            JobDeleteFailedException: 任务删除失败
        """
        if not job_ids:
            raise JobIdListEmptyException

        try:
            # 1. 从调度器移除任务（容错处理：任务可能已不在调度器中，如被暂停或不存在）
            for job_id in job_ids:
                try:
                    await scheduler.remove_job(job_id)
                except Exception as remove_err:
                    logger.warning(f"从调度器移除任务失败（可能已不存在）: job_id={job_id}, error={remove_err}")

            # 2. 删除数据库记录
            await JobMapper.delete_job(job_ids, query_db)
            await query_db.commit()

            logger.info(f"任务删除成功: job_ids={job_ids}")

        except Exception as e:
            await query_db.rollback()
            logger.error(f"任务删除失败: job_ids={job_ids}, error={e}")
            raise JobDeleteFailedException from e

    @staticmethod
    async def change_job_status(
        query_db: AsyncSession,
        scheduler: AsyncSchedulerResource,
        status_data: JobStatusChangeDTO,
        current_user_id: int,
    ) -> None:
        """修改任务状态

        Args:
            query_db: 数据库会话
            scheduler: 调度器资源实例
            status_data: 状态变更数据
            current_user_id: 当前用户ID

        Raises:
            JobNotFoundException: 任务不存在
            JobChangeStatusFailedException: 状态修改失败
        """
        # 1. 查询任务
        job_orm = await JobMapper.get_by_id(status_data.job_id, query_db)
        if not job_orm:
            raise JobNotFoundException(job_id=status_data.job_id)

        try:
            # 2. 先更新数据库（flush，未提交）
            job_orm.status = status_data.status
            job_orm.update_by = current_user_id
            job_orm.update_time = datetime.now()
            await JobMapper.update(job_orm, query_db)

            # 3. 根据状态变更操作调度器（在 commit 之前，失败可回滚 DB）
            if status_data.status == "1":
                # 暂停任务
                await scheduler.pause_job(status_data.job_id)
            elif status_data.status == "0":
                # 恢复任务
                await scheduler.resume_job(status_data.job_id)

            # 4. 调度器操作成功后提交 DB
            await query_db.commit()

            logger.info(f"任务状态修改成功: job_id={status_data.job_id}, status={status_data.status}")

        except Exception as e:
            await query_db.rollback()
            logger.error(f"任务状态修改失败: job_id={status_data.job_id}, error={e}")
            raise JobChangeStatusFailedException(job_id=status_data.job_id) from e

    @staticmethod
    async def execute_job_once(query_db: AsyncSession, execute_data: JobExecuteOnceDTO) -> JobExecuteResultVO:
        """立即执行一次任务

        Args:
            query_db: 数据库会话
            execute_data: 执行数据

        Returns:
            JobExecuteResultVO: 执行结果

        Raises:
            JobNotFoundException: 任务不存在
            JobExecuteFailedException: 任务执行失败
        """
        # 1. 查询任务
        job_orm = await JobMapper.get_by_id(execute_data.job_id, query_db)
        if not job_orm:
            raise JobNotFoundException(job_id=execute_data.job_id)

        try:
            # 2. 解析 DB 中存储的 JSON 参数并直接调用执行器
            args_list = json.loads(job_orm.job_args) if job_orm.job_args else []
            kwargs_dict = json.loads(job_orm.job_kwargs) if job_orm.job_kwargs else {}
            await job_executor(
                job_orm.job_id,
                job_orm.job_executor,
                job_orm.invoke_target,
                args_list,
                kwargs_dict,
            )

            logger.info(f"任务立即执行成功: job_id={execute_data.job_id}")
            return JobExecuteResultVO(
                job_id=job_orm.job_id,
                job_name=job_orm.job_name,
                status="0",
                message="任务执行成功",
            )

        except JobExecuteFailedException:
            raise  # 已经是自定义异常，直接传递
        except Exception as e:
            logger.error(f"任务立即执行失败: job_id={execute_data.job_id}, error={e}")
            raise JobExecuteFailedException(job_name=job_orm.job_name, reason=str(e)) from e

    @staticmethod
    async def list_job(query_db: AsyncSession, query_object: JobQueryDTO) -> PageResponse[JobListVO]:
        """获取任务列表（分页）

        Args:
            query_db: 数据库会话
            query_object: 查询参数对象

        Returns:
            PageResponse[JobListVO]: 任务列表分页结果
        """
        is_page = query_object.page is not None and query_object.size is not None
        rows, total = await JobMapper.get_job_list(query_db, query_object, is_page=is_page)

        return PageResponse(
            rows=[_convert_job_orm_to_list_vo(row) for row in rows],
            page=query_object.page,
            size=query_object.size,
            total=total,
        )

    @staticmethod
    async def get_job_detail(query_db: AsyncSession, job_id: int, base_url: str | None = None) -> JobDetailVO:
        """获取任务详情

        Args:
            query_db: 数据库会话
            job_id: 任务ID
            base_url: 基础 URL（可选，用于生成 Webhook 触发 URL）

        Returns:
            JobDetailVO: 任务详细信息

        Raises:
            JobNotFoundException: 任务不存在
        """
        job_orm = await JobMapper.get_by_id(job_id, query_db)
        if not job_orm:
            raise JobNotFoundException(job_id=job_id)

        return _convert_job_orm_to_detail_vo(job_orm, base_url)

    @staticmethod
    async def trigger_by_webhook(
        query_db: AsyncSession,
        job_id: int,
        webhook_secret: str | None,
        args: list | None = None,
        kwargs: dict | None = None,
    ) -> JobExecuteResultVO:
        """通过 Webhook 触发执行任务

        Args:
            query_db: 数据库会话
            job_id: 任务ID
            webhook_secret: 请求携带的 Webhook 密钥
            args: 额外传入的位置参数（可选）
            kwargs: 额外传入的关键字参数（可选）

        Returns:
            JobExecuteResultVO: 执行结果

        Raises:
            JobNotFoundException: 任务不存在
            JobConfigInvalidException: 任务未启用
            JobNoPermissionException: Webhook 密钥验证失败
            JobExecuteFailedException: 任务执行失败
        """
        # 1. 查询任务
        job_orm = await JobMapper.get_by_id(job_id, query_db)
        if not job_orm:
            raise JobNotFoundException(job_id=job_id)

        # 2. 验证任务状态（必须为正常运行）
        if job_orm.status != "0":
            raise JobConfigInvalidException(reason=f"任务 '{job_orm.job_name}' 未启用（当前状态为暂停）")

        # 3. 验证 Webhook 密钥（已配置密钥时必须匹配）
        if job_orm.webhook_enabled == "1" and job_orm.webhook_secret and webhook_secret != job_orm.webhook_secret:
            raise JobNoPermissionException(job_id=job_id)

        try:
            # 4. 直接调用执行器（将 Python 对象传入，内部会写入日志）
            await job_executor(
                job_orm.job_id,
                job_orm.job_executor,
                job_orm.invoke_target,
                args or [],
                kwargs or {},
            )

            logger.info(f"Webhook 触发任务成功: job_id={job_id}, job_name={job_orm.job_name}")
            return JobExecuteResultVO(
                job_id=job_orm.job_id,
                job_name=job_orm.job_name,
                status="0",
                message="任务触发成功",
            )

        except JobExecuteFailedException:
            raise  # 已经是自定义异常，直接传递
        except Exception as e:
            logger.error(f"Webhook 触发任务失败: job_id={job_id}, error={e}")
            raise JobExecuteFailedException(job_name=job_orm.job_name, reason=str(e)) from e

    @staticmethod
    async def trigger_by_webhook_name(
        query_db: AsyncSession,
        job_name: str,
        webhook_secret: str | None,
        args: list | None = None,
        kwargs: dict | None = None,
    ) -> JobExecuteResultVO:
        """通过任务名称触发 Webhook 执行

        Args:
            query_db: 数据库会话
            job_name: 任务名称
            webhook_secret: 请求携带的 Webhook 密钥
            args: 额外传入的位置参数（可选）
            kwargs: 额外传入的关键字参数（可选）

        Returns:
            JobExecuteResultVO: 执行结果

        Raises:
            JobNotFoundException: 任务不存在
        """
        job_orm = await JobMapper.get_by_name(job_name, query_db)
        if not job_orm:
            raise JobNotFoundException(message=f"任务名称 '{job_name}' 不存在")

        return await JobService.trigger_by_webhook(query_db, job_orm.job_id, webhook_secret, args, kwargs)


# ============================================================================
# 任务日志服务
# ============================================================================


class JobLogService:
    """任务执行日志业务逻辑层"""

    @staticmethod
    async def list_job_log(query_db: AsyncSession, query_object: JobLogQueryDTO) -> PageResponse[JobLogListVO]:
        """获取任务日志列表（分页）

        Args:
            query_db: 数据库会话
            query_object: 查询参数对象

        Returns:
            PageResponse[JobLogListVO]: 任务日志列表分页结果
        """
        is_page = query_object.page is not None and query_object.size is not None
        rows, total = await JobLogMapper.get_job_log_list(query_db, query_object, is_page=is_page)

        return PageResponse(
            rows=[_convert_job_log_orm_to_list_vo(row) for row in rows],
            page=query_object.page,
            size=query_object.size,
            total=total,
        )

    @staticmethod
    async def delete_job_log(query_db: AsyncSession, job_log_ids: list[int]) -> None:
        """删除任务日志

        Args:
            query_db: 数据库会话
            job_log_ids: 日志ID列表

        Raises:
            JobLogIdListEmptyException: 日志ID列表为空
            JobLogNotFoundException: 日志不存在
        """
        if not job_log_ids:
            raise JobLogIdListEmptyException

        # 验证日志是否存在
        for job_log_id in job_log_ids:
            job_log = await JobLogMapper.get_by_id(job_log_id, query_db)
            if not job_log:
                raise JobLogNotFoundException(job_log_id=job_log_id)

        try:
            await JobLogMapper.delete_job_log(job_log_ids, query_db)
            await query_db.commit()
            logger.info(f"任务日志删除成功: job_log_ids={job_log_ids}")
        except Exception as e:
            await query_db.rollback()
            logger.error(f"任务日志删除失败: job_log_ids={job_log_ids}, error={e}")
            raise JobLogDeleteFailedException from e

    @staticmethod
    async def clear_job_log(query_db: AsyncSession) -> None:
        """清空所有任务日志

        Args:
            query_db: 数据库会话
        """
        try:
            await JobLogMapper.clear_job_log(query_db)
            await query_db.commit()
            logger.info("任务日志清空成功")
        except Exception as e:
            await query_db.rollback()
            logger.error(f"任务日志清空失败: error={e}")
            raise JobLogClearFailedException from e
