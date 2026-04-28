"""全局异常处理器

处理FastAPI应用中的所有异常，返回统一格式的响应
"""

from datetime import UTC, datetime
import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from graphedu.common.exceptions.base import AppException
from graphedu.common.exceptions.services.base import ServiceException, ServiceWarning

logger = logging.getLogger(__name__)


def parse_accept_language(accept_language: str | None) -> str:
    """解析Accept-Language请求头，获取语言代码

    Args:
        accept_language: Accept-Language请求头的值

    Returns:
        语言代码 (zh_CN 或 en_US)，默认为 zh_CN
    """
    if not accept_language:
        return "zh_CN"

    # 解析语言列表（按权重排序）
    languages = [lang.split(";")[0].strip() for lang in accept_language.split(",")]
    primary_lang = languages[0].lower() if languages else ""

    # 映射到支持的语言
    if primary_lang.startswith("zh"):
        return "zh_CN"
    if primary_lang.startswith("en"):
        return "en_US"

    # 默认使用中文
    return "zh_CN"


def handle_exception(app: FastAPI):
    """注册全局异常处理器

    Args:
        app: FastAPI应用实例
    """

    @app.exception_handler(ServiceWarning)
    async def service_warning_handler(request: Request, exc: ServiceWarning):
        """处理服务警告（非错误）

        用于不需要中断流程的警告信息
        """
        logger.info(
            f"[WARNING] {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "code": 200,
                    "msg": exc.message,
                    "data": exc.data or {},
                    "time": datetime.now(UTC).isoformat(),
                    "warning": True,  # 标识这是一个警告
                }
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTPException

        这是FastAPI内置的HTTP异常
        """
        logger.warning(
            f"HTTP Exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {"code": exc.status_code, "msg": exc.detail, "data": {}, "time": datetime.now(UTC).isoformat()}
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证错误

        当请求体或参数验证失败时触发，返回友好的错误信息
        """
        # 提取第一个验证错误作为主要错误信息
        errors = exc.errors()
        first_error = errors[0] if errors else {}

        # 构建友好的错误消息
        field_path = " -> ".join(str(loc) for loc in first_error.get("loc", []))
        error_msg = first_error.get("msg", "验证失败")

        friendly_message = f"参数验证失败: {field_path} - {error_msg}"

        logger.warning(
            f"Request Validation Error: {friendly_message}",
            extra={
                "validation_errors": errors,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "code": 422,
                    "msg": friendly_message,
                    "data": {"errors": errors},
                    "time": datetime.now(UTC).isoformat(),
                }
            ),
        )

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        """处理所有ServiceException异常

        这些是业务异常，包含错误码和消息
        """
        # 解析Accept-Language请求头
        accept_language = request.headers.get("Accept-Language")
        locale = parse_accept_language(accept_language)

        # 获取本地化错误消息
        from graphedu.common.exceptions.services.codes import ErrorCode

        error_code_enum = ErrorCode(exc.error_code) if exc.error_code else None
        if error_code_enum:
            from graphedu.common.exceptions.messages import get_message

            localized_msg = get_message(error_code_enum, locale, **exc.kwargs)
        else:
            localized_msg = exc.message

        # 记录日志（warning级别，因为这是预期的业务异常）
        logger.warning(
            f"[{exc.error_code}] {localized_msg}",
            extra={
                "error_code": exc.error_code,
                "http_status": exc.http_status,
                "path": request.url.path,
                "method": request.method,
                "request_id": request.headers.get("X-Request-ID", "N/A"),
                "request_time": datetime.now(UTC).isoformat(),
                "locale": locale,
            },
        )

        # 返回统一格式的响应
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "code": exc.http_status,
                    "errorCode": exc.error_code,
                    "msg": localized_msg,
                    "data": exc.data or {},
                    "time": datetime.now(UTC).isoformat(),
                }
            ),
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理所有AppException异常

        这些是应用级异常，通常用于配置或环境错误
        """
        logger.error(
            f"App Exception: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {"code": 500, "msg": "系统错误，请稍后再试", "data": {}, "time": datetime.now(UTC).isoformat()}
            ),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_exception_handler(request: Request, exc):
        """处理Pydantic验证异常

        这是一个通用的Pydantic异常处理器
        """
        logger.warning(
            f"Pydantic Validation Error: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "code": 422,
                    "msg": "请求参数验证失败",
                    "data": {"errors": exc.errors()},
                    "time": datetime.now(UTC).isoformat(),
                }
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理所有未捕获的异常

        这是最后的异常处理器，捕获所有未被前面处理器处理的异常
        """
        # 记录完整的异常堆栈
        logger.exception(
            f"Unhandled exception: {type(exc).__name__}: {exc!s}",
            extra={
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            },
        )

        # 返回通用错误响应
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(
                {"code": 500, "msg": "系统错误，请稍后再试", "data": {}, "time": datetime.now(UTC).isoformat()}
            ),
        )
