"""VO (View Objects) 基类模块

提供所有VO类的统一基类和配置。
"""

from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, TypedDict

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from starlette import status as HttpStatus
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse, Response, StreamingResponse


class VO(BaseModel):
    """VO 基类

    统一配置所有 VO 类的通用行为：
    - from_attributes=True: 支持从 ORM 对象创建
    - alias_generator=to_camel: 自动生成驼峰命名的别名（user_id -> userId）
    - populate_by_name=True: 允许使用字段名或别名进行验证（validate_by_name 在 Pydantic v2 中的名称）
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)


class ResponseType[T](VO):
    """统一响应格式（Pydantic BaseModel，支持 FastAPI 文档生成）

    Attributes:
        code: HTTP 状态码
        msg: 响应消息
        data: 响应数据
        time: 响应时间
    """

    code: int = Field(description="HTTP 状态码")
    msg: str = Field(description="响应消息")
    data: T = Field(description="响应数据")
    time: datetime = Field(description="响应时间")


class Empty(TypedDict):
    """空 TypedDict，用于无额外参数的场景"""


class PageResponse[T](VO):
    """分页响应结果

    用于返回分页数据

    Attributes:
        rows: 当前页数据列表
        page: 当前页码
        size: 每页数量
        total: 总记录数
    """

    rows: list[T] = Field(default_factory=list, description="当前页数据列表")
    page: int | None = Field(default=None, description="当前页码")
    size: int | None = Field(default=None, description="每页数量")
    total: int = Field(default=0, description="总记录数")


class DeleteResultItem[T: int | str](VO):
    """批量删除结果项

    用于表示单个项目的删除结果。
    """

    target_id: T = Field(description="目标 ID（可以是 int 或 str 类型）")
    success: bool = Field(description="是否删除成功")
    error: str | None = Field(default=None, description="错误信息（如果删除失败）")


class BatchDeleteResponse[T: int | str](VO):
    """批量删除响应模型

    用于返回批量操作的汇总结果，包括成功数量、失败数量和详细结果列表。

    Attributes:
        success_count: 成功删除的数量
        fail_count: 删除失败的数量
        total_count: 总操作数量
        results: 详细结果列表

    Example:
        >>> response = DeleteResponse[int](
        ...     success_count=2,
        ...     fail_count=1,
        ...     results=[
        ...         DeleteResultItem(target_id=1, success=True, error=None),
        ...         DeleteResultItem(target_id=2, success=True, error=None),
        ...         DeleteResultItem(target_id=3, success=False, error="记录不存在"),
        ...     ]
        ... )
    """

    success_count: int = Field(description="成功删除的数量", ge=0)
    fail_count: int = Field(description="删除失败的数量", ge=0)
    total_count: int = Field(description="总操作数量", ge=0)
    results: list[DeleteResultItem[T]] = Field(description="详细结果列表")

    @classmethod
    def from_results(cls, results: list[DeleteResultItem[T]]) -> "BatchDeleteResponse[T]":
        """从结果列表创建响应对象

        Args:
            results: 删除结果列表

        Returns:
            BatchDeleteResponse: 包含统计信息的响应对象
        """
        success_count = sum(1 for result in results if result.success)
        fail_count = len(results) - success_count

        return cls(
            success_count=success_count,
            fail_count=fail_count,
            total_count=len(results),
            results=results,
        )


class ResponseUtil:
    """响应工具类

    提供统一的 HTTP 响应方法，包括：
    - success: 成功响应 (200)
    - fail: 失败响应 (500)
    - unauthorized: 未认证响应 (401)
    - forbidden: 未授权响应 (403)
    - error: 错误响应 (500)
    - streaming: 流式响应
    """

    @classmethod
    def success(
        cls,
        msg: str = "操作成功",
        data: BaseModel | Sequence[BaseModel] | None = None,
        model_exclude: set[str] | None = None,
        model_include: set[str] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        """成功响应方法，数据模型一定 by_alias=True

        :param msg: 可选，自定义成功响应信息
        :param data: 可选，成功响应结果中属性为data的值
        :param model_exclude: 可选，成功响应结果中，需要排除的字段集合
        :param model_include: 可选，成功响应结果中，需要包含的字段集合
        :param headers: 可选，响应头信息
        :param media_type: 可选，响应结果媒体类型
        :param background: 可选，响应返回后执行的后台任务
        :return: 成功响应结果
        """
        result = ResponseType(
            code=HttpStatus.HTTP_200_OK,
            msg=msg,
            data=data,
            time=datetime.now(UTC),
        )

        return JSONResponse(
            status_code=HttpStatus.HTTP_200_OK,
            content=jsonable_encoder(result, exclude=model_exclude, include=model_include),
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def fail(
        cls,
        msg: str = "操作失败",
        data: Any | None = None,
        model_exclude: set[str] | None = None,
        model_include: set[str] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        """失败响应方法，数据模型一定 by_alias=True

        :param msg: 可选，自定义失败响应信息
        :param data: 可选，失败响应结果中属性为data的值
        :param model_exclude: 可选，成功响应结果中，需要排除的字段集合
        :param model_include: 可选，成功响应结果中，需要包含的字段集合
        :param headers: 可选，响应头信息
        :param media_type: 可选，响应结果媒体类型
        :param background: 可选，响应返回后执行的后台任务
        :return: 失败响应结果
        """
        result = ResponseType(
            code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=msg,
            data=data,
            time=datetime.now(UTC),
        )

        return JSONResponse(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(result, exclude=model_exclude, include=model_include),
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def unauthorized(
        cls,
        msg: str = "登录信息已过期，访问系统资源失败",
        data: Any | None = None,
        model_exclude: set[str] | None = None,
        model_include: set[str] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        """未认证响应方法，数据模型一定 by_alias=True

        :param msg: 可选，自定义未认证响应信息
        :param data: 可选，未认证响应结果中属性为data的值
        :param model_exclude: 可选，成功响应结果中，需要排除的字段集合
        :param model_include: 可选，成功响应结果中，需要包含的字段集合
        :param headers: 可选，响应头信息
        :param media_type: 可选，响应结果媒体类型
        :param background: 可选，响应返回后执行的后台任务
        :return: 未认证响应结果
        """
        result = ResponseType(
            code=HttpStatus.HTTP_401_UNAUTHORIZED,
            msg=msg,
            data=data,
            time=datetime.now(UTC),
        )

        return JSONResponse(
            status_code=HttpStatus.HTTP_401_UNAUTHORIZED,
            content=jsonable_encoder(result, exclude=model_exclude, include=model_include),
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def forbidden(
        cls,
        msg: str = "该用户无此接口权限",
        data: Any | None = None,
        model_exclude: set[str] | None = None,
        model_include: set[str] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        """未授权响应方法，数据模型一定 by_alias=True

        :param msg: 可选，自定义未授权响应信息
        :param data: 可选，未授权响应结果中属性为data的值
        :param model_exclude: 可选，成功响应结果中，需要排除的字段集合
        :param model_include: 可选，成功响应结果中，需要包含的字段集合
        :param headers: 可选，响应头信息
        :param media_type: 可选，响应结果媒体类型
        :param background: 可选，响应返回后执行的后台任务
        :return: 未授权响应结果
        """
        result = ResponseType(
            code=HttpStatus.HTTP_403_FORBIDDEN,
            msg=msg,
            data=data,
            time=datetime.now(UTC),
        )

        return JSONResponse(
            status_code=HttpStatus.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(result, exclude=model_exclude, include=model_include),
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def error(
        cls,
        msg: str = "接口异常",
        data: Any | None = None,
        model_exclude: set[str] | None = None,
        model_include: set[str] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        """错误响应方法，数据模型一定 by_alias=True

        :param msg: 可选，自定义错误响应信息
        :param data: 可选，错误响应结果中属性为data的值
        :param model_exclude: 可选，成功响应结果中，需要排除的字段集合
        :param model_include: 可选，成功响应结果中，需要包含的字段集合
        :param headers: 可选，响应头信息
        :param media_type: 可选，响应结果媒体类型
        :param background: 可选，响应返回后执行的后台任务
        :return: 错误响应结果
        """
        result = ResponseType(
            code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=msg,
            data=data,
            time=datetime.now(UTC),
        )

        return JSONResponse(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(result, exclude=model_exclude, include=model_include),
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def streaming(
        cls,
        *,
        data: AsyncIterable[str | bytes] | Iterable[str | bytes] = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> Response:
        """流式响应方法，数据模型一定 by_alias=True

        :param data: 流式传输的内容
        :param headers: 可选，响应头信息
        :param media_type: 可选，响应结果媒体类型
        :param background: 可选，响应返回后执行的后台任务
        :return: 流式响应结果
        """
        return StreamingResponse(
            status_code=HttpStatus.HTTP_200_OK,
            content=data,
            headers=headers,
            media_type=media_type,
            background=background,
        )
