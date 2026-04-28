"""DTO 基础模型和响应工具模块

本模块定义了：

- **DTO**: 所有 DTO 的基类，提供统一的配置（驼峰命名转换、别名验证）
- **ResponseType**: 统一响应格式模型，用于 FastAPI 文档生成
- **ResponseUtil**: 响应工具类，提供多种 HTTP 响应方法
"""

from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DTO(BaseModel):
    """DTO 基类

    所有数据传输对象的基类，提供统一的配置：

    - alias_generator: 使用驼峰命名转换（snake_case -> camelCase）
    - validate_by_alias: 同时验证别名和原始字段名
    - validate_by_name: 允许使用字段名进行验证
    """

    model_config = ConfigDict(alias_generator=to_camel, validate_by_alias=True, validate_by_name=True)


T = TypeVar("T")


class PageQuery(DTO):
    """分页查询参数基类

    用于所有需要分页的查询接口

    Attributes:
        page: 页码，从 1 开始，默认为 1
        size: 每页数量，默认为 10，最大为 100
    """

    page: int | None = Field(default=None, ge=1, description="页码，默认值为1")
    size: int | None = Field(default=None, ge=1, le=100, description="每页数量，默认值为10，最大值为100")
