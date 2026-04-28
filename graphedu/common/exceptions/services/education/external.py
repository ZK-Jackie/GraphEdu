"""外部服务相关异常"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class ExternalServiceException(ServiceException):
    """外部服务异常基类"""

    pass


class MinerUApiException(ExternalServiceException):
    """MinerU API 异常"""

    def __init__(self, message: str = "MinerU API 调用失败", **kwargs):
        super().__init__(error_code=ErrorCode.MINERU_API_ERROR, message=message, **kwargs)


class GraphRAGException(ExternalServiceException):
    """GraphRAG 异常"""

    def __init__(self, message: str = "GraphRAG 操作失败", **kwargs):
        super().__init__(error_code=ErrorCode.GRAPHRAG_ERROR, message=message, **kwargs)


__all__ = [
    "ExternalServiceException",
    "GraphRAGException",
    "MinerUApiException",
]
