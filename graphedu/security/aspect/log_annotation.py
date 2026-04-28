"""日志注解模块

本模块提供系统日志记录的装饰器功能，用于自动记录登录日志和操作日志。

核心类：
- SystemLog: 日志装饰器，用于自动记录方法调用的详细信息

辅助函数：
- extract_params_from_function_args: 从函数参数中智能提取请求参数
- get_ip_location: 查询 IP 归属区域（支持缓存）
- get_function_parameters_name_by_type: 获取函数指定类型的参数名称
- get_function_parameters_value_by_name: 获取函数指定参数的值

记录内容：
- 请求信息：请求方法、URL、IP 地址、归属地、请求参数（从函数参数提取）
- 用户信息：操作用户、部门、浏览器、操作系统
- 执行信息：执行方法、执行时间、耗时、响应结果
- 业务信息：业务类型、模块标题、操作状态、错误信息

日志类型：
- login: 登录日志，记录用户登录行为和结果
- operation: 操作日志，记录用户在系统中的业务操作

业务类型：
- OTHER: 其它
- INSERT: 新增
- UPDATE: 修改
- DELETE: 删除
- GRANT: 授权
- EXPORT: 导出
- IMPORT: 导入
- FORCE: 强退
- GENCODE: 生成代码
- CLEAN: 清空数据

使用方式：
```python
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.common.models.constants import BusinessType

# 记录登录日志
@SystemLog(title="用户登录", business_type=BusinessType.OTHER, log_type="login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    pass

# 记录操作日志
@SystemLog(title="用户管理", business_type=BusinessType.INSERT)
async def add_user(request: Request, user: UserCreateDTO):
    pass
```

注意事项：
- 请求参数从函数的 args/kwargs 中提取，避免过度消费请求体
- 自动排除 Request、数据库会话等非业务参数
- 支持 Pydantic 模型、字典、基本类型的自动序列化
- 登录日志会自动收集浏览器和操作系统信息
- 请求参数超过 2000 字符会被截断
- 来源于 API 文档的请求不会记录登录日志
- 操作日志会自动捕获 ServiceException 和 LoginException 并记录
"""

from collections.abc import Callable
from datetime import datetime
from functools import wraps
import inspect
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Literal, Protocol

from async_lru import alru_cache
from fastapi import Request
from fastapi.responses import JSONResponse, ORJSONResponse, UJSONResponse
import httpx
from pydantic import BaseModel
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse

from graphedu.common.config.manager import get_config
from graphedu.common.models.dto.systemv2.log import LoginLogCreateDTO, OperLogCreateDTO
from graphedu.common.resource import AsyncPostgresqlClient, AsyncRedisClient
from graphedu.common.resource.deps import get_db_client, get_redis_client
from graphedu.common.utils.app import is_in_openapi
from graphedu.common.utils.context import RequestManager
from graphedu.security.auth import SecurityService
from graphedu.services.system.log import LoginLogService, OperationLogService

logger = logging.getLogger(__name__)


class SystemLog:
    """系统日志装饰器

    自动记录系统登录日志和操作日志，包括请求信息、用户信息、
    执行信息和业务信息等。

    支持的日志类型：
    - login: 登录日志
    - operation: 操作日志
    """

    # 类常量：参数排除规则
    _EXCLUDE_PARAM_TYPES: tuple[type, ...] = (Request, AsyncSession, AsyncRedis)
    _EXCLUDE_PARAM_NAMES: set[str] = {"request", "db", "query_db", "session", "redis_session", "cache", "redis"}

    title: str
    business_type: str
    log_type: Literal["login", "operation"] | None
    exclude_params: set[str]

    db_client: AsyncPostgresqlClient | None = None
    redis_client: AsyncRedisClient | None = None

    def __init__(
        self,
        title: str,
        business_type: str,
        log_type: Literal["login", "operation"] | None = "operation",
        exclude_params: set[str] | None = None,
    ):
        """初始化日志装饰器

        Args:
            title: 当前日志装饰器装饰的模块标题
            business_type: 业务类型
                （OTHER 其它、INSERT 新增、UPDATE 修改、DELETE 删除、
                GRANT 授权、EXPORT 导出、IMPORT 导入、FORCE 强退、
                GENCODE 生成代码、CLEAN 清空数据）
            log_type: 日志类型
                - 'login': 登录日志
                - 'operation': 操作日志（默认）
            exclude_params: 需要排除记录的请求参数名称集合
        """
        self.title = title
        self.business_type = business_type
        self.log_type = log_type
        self.exclude_params = exclude_params or set()

    def __call__(self, func):
        """日志装饰器主体"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.db_client is None:
                self.db_client = await get_db_client()
            if self.redis_client is None:
                self.redis_client = await get_redis_client()
            # 1 获取函数信息
            # 1.1 获取被装饰函数的文件路径
            file_path = inspect.getfile(func)
            # 1.2 获取项目根路径
            project_root = os.getcwd()
            # 1.3 处理文件路径，去除项目根路径部分
            relative_path = str(Path(file_path).relative_to(project_root))[:-2].replace("\\", ".").replace("/", ".")
            # 1.4 获取当前被装饰函数所在路径
            func_path = f"{relative_path}{func.__name__}()"
            # 2 获取请求信息
            # 2.1 获取请求头、请求方法、请求url、请求ip及归属地等基本信息
            request = RequestManager.get_request()
            token = request.headers.get("Authorization")
            request_method = request.method
            operator_type = 0
            user_agent = request.headers.get("User-Agent")
            if "Windows" in user_agent or "Macintosh" in user_agent or "Linux" in user_agent:
                operator_type = 1
            if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
                operator_type = 2
            # 2.1.1 获取请求的url
            oper_url = request.url.path
            # 2.1.2 获取请求的ip及ip归属区域
            oper_ip = request.headers.get("X-Forwarded-For") or request.client.host
            oper_location = "内网IP"
            if get_config().system.location_query:
                oper_location = await get_ip_location(oper_ip)
            # 2.2 获取请求参数
            # 2.2.1 从函数参数中提取请求参数
            params = self.extract_params_from_function_args(func, *args, **kwargs)
            oper_param = json.dumps(params, ensure_ascii=False, default=str)
            # 日志表请求参数字段长度最大为2000，因此在此处判断长度
            if len(oper_param) > 2000:
                oper_param = "请求参数过长"
            # 2.2.2 添加路径参数
            if request.path_params:
                params.update({"path_params": request.path_params})
            # 获取操作时间
            oper_time = datetime.now()
            # 此处在登录之前向原始函数传递一些登录信息，用于监测在线用户的相关信息
            login_log = {}
            if self.log_type == "login":
                user_agent_info = parse(user_agent)
                browser = f"{user_agent_info.browser.family}"
                system_os = f"{user_agent_info.os.family}"
                if user_agent_info.browser.version != ():
                    browser += f" {user_agent_info.browser.version[0]}"
                if user_agent_info.os.version != ():
                    system_os += f" {user_agent_info.os.version[0]}"
                login_log = {
                    "ipaddr": oper_ip,
                    "loginLocation": oper_location,
                    "browser": browser,
                    "os": system_os,
                    "loginTime": oper_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                kwargs["form_data"].login_info = login_log
            # 3 调用原始函数
            start_time = time.time()
            # 3.1 调用原始函数
            result = await func(*args, **kwargs)
            # 3.2 获取请求耗时
            cost_time = float(time.time() - start_time) * 100
            # 3.3 根据响应结果的类型使用不同的方法获取响应结果参数
            # 判断请求是否来自api文档
            in_openapi = is_in_openapi(request.headers)
            if isinstance(result, (JSONResponse, ORJSONResponse, UJSONResponse)):
                result_dict = json.loads(str(result.body, "utf-8"))
            else:
                if in_openapi:
                    result_dict = {}
                else:
                    if result.status_code == 200:
                        result_dict = {"code": result.status_code, "message": "获取成功"}
                    else:
                        result_dict = {"code": result.status_code, "message": "获取失败"}
            json_result = json.dumps(result_dict, ensure_ascii=False)
            # 根据响应结果获取响应状态及异常信息
            status = 1
            error_msg = ""
            if result_dict.get("code") == 200:
                status = 0
            else:
                error_msg = result_dict.get("msg")
            # 根据日志类型向对应的日志表插入数据
            if self.log_type == "login":
                # 登录请求来自于api文档时不记录登录日志，其余情况则记录
                if in_openapi:
                    pass
                else:
                    user = kwargs.get("form_data")
                    user_name = user.username

                    login_log["login_time"] = oper_time
                    login_log["user_name"] = user_name
                    login_log["status"] = str(status)
                    login_log["msg"] = result_dict.get("msg")

                    async with self.db_client.session_context() as query_db:
                        await LoginLogService.add_login_log(query_db, LoginLogCreateDTO(**login_log))
            else:
                async with self.db_client.session_context() as query_db:
                    current_user = await SecurityService.get_current_user(
                        token, query_db, self.redis_client.get_redis()
                    )
                    oper_name = current_user.detail.user.user_name
                    dept_names = ",".join(
                        [dept.dept_name for dept in current_user.detail.depts if current_user.detail.depts]
                    )
                    operation_log = OperLogCreateDTO(
                        title=self.title,
                        business_type=self.business_type,
                        method=func_path,
                        request_method=request_method,
                        operator_type=operator_type,
                        oper_name=oper_name,
                        dept_name=dept_names,
                        oper_url=oper_url,
                        oper_ip=oper_ip,
                        oper_location=oper_location,
                        oper_param=oper_param,
                        json_result=json_result,
                        status=status,
                        error_msg=error_msg,
                        oper_time=oper_time,
                        cost_time=int(cost_time),
                    )
                    await OperationLogService.add_operation_log(query_db, operation_log)

            return result

        return wrapper

    def _should_exclude_param(
        self,
        param_name: str,
        param_value: Any,
        exclude_names: set[str],
        exclude_types: tuple[type, ...],
    ) -> bool:
        """判断参数是否应该被排除

        Args:
            param_name: 参数名
            param_value: 参数值
            exclude_names: 排除的参数名集合
            exclude_types: 排除的类型元组

        Returns:
            bool: True 表示应该排除
        """
        return param_name in exclude_names or param_value is None or isinstance(param_value, exclude_types)

    def extract_params_from_function_args(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        """从函数参数中提取请求参数

        智能识别函数参数中的数据对象（Pydantic 模型、字典等），
        过滤掉 Request、数据库会话等非业务参数。

        Args:
            func: 被装饰的函数对象
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            dict[str, Any]: 提取的请求参数字典
        """
        # 使用类常量作为排除规则
        exclude_types = self._EXCLUDE_PARAM_TYPES
        exclude_names = self._EXCLUDE_PARAM_NAMES
        exclude_params = self.exclude_params

        params: dict[str, Any] = {}

        try:
            # 获取函数签名并绑定参数
            sig = inspect.signature(func)
            bound_args: inspect.BoundArguments = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for param_name, param_value in bound_args.arguments.items():
                if self._should_exclude_param(param_name, param_value, exclude_names, exclude_types):
                    continue

                try:
                    # 递归过滤敏感字段（如密码、token 等）和类型
                    filtered_value = _recursive_filter_attr(param_value, exclude_params, exclude_types)
                    params[param_name] = filtered_value
                except Exception as e:
                    logger.warning(
                        f"Failed to filter parameter '{param_name}' (type: {type(param_value).__name__}): {e}",
                        exc_info=False,
                    )
                    params[param_name] = repr(param_value)

        except Exception as e:
            logger.warning(f"Failed to extract params from function '{func.__name__}': {e}", exc_info=False)

        return params


class _Dictable(Protocol):
    """可过滤的对象协议

    定义一个协议，表示具有 __dict__ 属性的对象，可以被递归过滤
    """

    __dict__: dict[str, Any]


# 定义类型别名（使用 Python 3.12+ type 语句）
type _FilterableBasic = BaseModel | _Dictable

type _FilterResult = dict[str, Any] | list[Any] | str | int | float | bool | None

type _Filterable = _FilterableBasic | list[_FilterableBasic] | dict[str, _FilterableBasic] | _FilterResult


def _recursive_filter_attr(
    d: _Filterable,
    exclude_fields: set[str],
    exclude_types: tuple[type, ...] = (),
) -> _FilterResult:
    """递归过滤字典中的指定字段和类型

    Args:
        d: 需要过滤
        exclude_fields: 需要排除的字段名称集合
        exclude_types: 需要排除的类型元组（如 Request, AsyncSession）

    Returns:
        _FilterResult: 过滤后的数据，如果值被排除则返回占位符字符串
    """
    # 先检查类型，如果是要排除的类型，返回占位符
    if isinstance(d, exclude_types):
        return f"<{type(d).__name__}>"

    if isinstance(d, list):
        return [_recursive_filter_attr(item, exclude_fields, exclude_types) for item in d]
    elif isinstance(d, dict):  # noqa: RET505
        return {
            k: _recursive_filter_attr(v, exclude_fields, exclude_types) for k, v in d.items() if k not in exclude_fields
        }
    elif hasattr(d, "__dict__"):
        return {
            k: _recursive_filter_attr(v, exclude_fields, exclude_types)
            for k, v in d.__dict__.items()
            if not k.startswith("_") and k not in exclude_fields
        }
    else:
        return d


@alru_cache(maxsize=256)
async def get_ip_location(oper_ip: str):
    """查询 IP 归属区域

    使用外部 API 查询 IP 地址的归属地，支持缓存。

    Args:
        oper_ip: 需要查询的 IP 地址

    Returns:
        str: IP 归属区域，查询失败返回 '未知'
    """
    if oper_ip in ["127.0.0.1", "localhost"]:
        return "本地"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # https://uapis.cn/docs/api-reference/get-network-ipinfo
            ip_result = await client.get(f"https://uapis.cn/api/v1/network/ipinfo?ip={oper_ip}&source=commercial")
            if ip_result.status_code == 200:
                data = ip_result.json()
                return data.get("region", "未知")
            return "未知"

    except Exception:
        return "未知"


def get_function_parameters_name_by_type(func: Callable, param_type: Any):
    """获取函数指定类型的参数名称

    Args:
        func: 目标函数对象
        param_type: 要查找的参数类型

    Returns:
        list[str]: 函数中指定类型的参数名称列表
    """
    # 获取函数的参数信息
    parameters = inspect.signature(func).parameters
    # 找到指定类型的参数名称
    parameters_name_list = []
    for name, param in parameters.items():
        if param.annotation == param_type:
            parameters_name_list.append(name)
    return parameters_name_list


def get_function_parameters_value_by_name(func: Callable, name: str, *args, **kwargs):
    """获取函数指定参数的值

    Args:
        func: 目标函数对象
        name: 参数名
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Any: 参数的值，如果参数不存在则返回 None
    """
    # 获取参数值
    bound_parameters = inspect.signature(func).bind(*args, **kwargs)
    bound_parameters.apply_defaults()
    return bound_parameters.arguments.get(name)
