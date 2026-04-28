"""大纲图谱相关异常

包含大纲图谱（SKG - Syllabus Knowledge Graph）相关的异常定义，
包含基类 SyllabusGraphException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class SyllabusGraphException(ServiceException):
    """大纲图谱异常基类"""

    def __init__(self, error_code: str = ErrorCode.SYLLABUS_GRAPH_NODE_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class KnowledgeNodeNotFoundException(SyllabusGraphException):
    """知识点节点不存在"""

    def __init__(self, node_id: str = None, message: str = None, **kwargs):
        if node_id and message is None:
            message = f"知识点节点 {node_id} 不存在"

        super().__init__(
            error_code=ErrorCode.SYLLABUS_GRAPH_NODE_NOT_FOUND.value, message=message, node_id=node_id, **kwargs
        )


class KnowledgeNodeCreateFailedException(SyllabusGraphException):
    """知识点节点创建失败"""

    def __init__(self, title: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"知识点节点创建失败: {title}" if title else "知识点节点创建失败"

        super().__init__(
            error_code=ErrorCode.SYLLABUS_GRAPH_NODE_CREATE_FAILED.value, message=message, title=title, **kwargs
        )


class KnowledgeRelationshipNotFoundException(SyllabusGraphException):
    """知识点关系不存在"""

    def __init__(self, rel_id: str = None, message: str = None, **kwargs):
        if rel_id and message is None:
            message = f"知识点关系 {rel_id} 不存在"

        super().__init__(
            error_code=ErrorCode.SYLLABUS_GRAPH_RELATIONSHIP_NOT_FOUND.value, message=message, rel_id=rel_id, **kwargs
        )


class KnowledgeRelationshipCreateFailedException(SyllabusGraphException):
    """知识点关系创建失败"""

    def __init__(self, source_id: str = None, target_id: str = None, message: str = None, **kwargs):
        if message is None:
            if source_id and target_id:
                message = f"知识点关系创建失败: {source_id} -> {target_id}"
            else:
                message = "知识点关系创建失败"

        super().__init__(
            error_code=ErrorCode.SYLLABUS_GRAPH_RELATIONSHIP_CREATE_FAILED.value,
            message=message,
            source_id=source_id,
            target_id=target_id,
            **kwargs,
        )


# 导出所有异常类
__all__ = [
    "KnowledgeNodeCreateFailedException",
    "KnowledgeNodeNotFoundException",
    "KnowledgeRelationshipCreateFailedException",
    "KnowledgeRelationshipNotFoundException",
    "SyllabusGraphException",
]
