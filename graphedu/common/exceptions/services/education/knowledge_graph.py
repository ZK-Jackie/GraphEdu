"""知识图谱相关异常

包含知识图谱管理相关的异常定义
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class KnowledgeGraphException(ServiceException):
    """知识图谱异常基类"""

    def __init__(self, error_code: str = ErrorCode.KNOWLEDGE_GRAPH_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class KnowledgeGraphNotFoundException(KnowledgeGraphException):
    """知识图谱不存在"""

    def __init__(self, graph_id: int = None, message: str = None, **kwargs):
        if graph_id and message is None:
            message = f"知识图谱ID {graph_id} 不存在"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_NOT_FOUND.value, message=message, graph_id=graph_id, **kwargs
        )


class KnowledgeGraphAlreadyExistsException(KnowledgeGraphException):
    """知识图谱已存在"""

    def __init__(self, graph_id: int = None, message: str = None, **kwargs):
        if graph_id and message is None:
            message = f"知识图谱ID {graph_id} 已存在"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_ALREADY_EXISTS.value, message=message, graph_id=graph_id, **kwargs
        )


class KnowledgeGraphNameAlreadyExistsException(KnowledgeGraphException):
    """知识图谱名称已存在"""

    def __init__(self, graph_name: str = None, message: str = None, **kwargs):
        if graph_name and message is None:
            message = f"知识图谱名称 '{graph_name}' 已存在"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_NAME_ALREADY_EXISTS.value,
            message=message,
            graph_name=graph_name,
            **kwargs,
        )


class KnowledgeGraphIdListEmptyException(KnowledgeGraphException):
    """知识图谱ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "知识图谱ID列表不能为空"

        super().__init__(error_code=ErrorCode.KNOWLEDGE_GRAPH_ID_LIST_EMPTY.value, message=message, **kwargs)


class KnowledgeGraphCreateFailedException(KnowledgeGraphException):
    """知识图谱新增失败"""

    def __init__(self, graph_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"知识图谱新增失败: {graph_name}" if graph_name else "知识图谱新增失败"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_CREATE_FAILED.value, message=message, graph_name=graph_name, **kwargs
        )


class KnowledgeGraphUpdateFailedException(KnowledgeGraphException):
    """知识图谱更新失败"""

    def __init__(self, graph_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"知识图谱更新失败: {graph_id}" if graph_id else "知识图谱更新失败"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_UPDATE_FAILED.value, message=message, graph_id=graph_id, **kwargs
        )


class KnowledgeGraphDeleteFailedException(KnowledgeGraphException):
    """知识图谱删除失败"""

    def __init__(self, graph_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"知识图谱删除失败: {graph_id}" if graph_id else "知识图谱删除失败"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_DELETE_FAILED.value, message=message, graph_id=graph_id, **kwargs
        )


class KnowledgeGraphChangeStatusFailedException(KnowledgeGraphException):
    """知识图谱状态修改失败"""

    def __init__(self, graph_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"知识图谱状态修改失败: {graph_id}" if graph_id else "知识图谱状态修改失败"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_CHANGE_STATUS_FAILED.value,
            message=message,
            graph_id=graph_id,
            **kwargs,
        )


class KnowledgeGraphCourseNotFoundException(KnowledgeGraphException):
    """关联的课程不存在"""

    def __init__(self, course_id: int = None, message: str = None, **kwargs):
        if course_id and message is None:
            message = f"关联的课程ID {course_id} 不存在"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_BOOK_NOT_FOUND.value, message=message, course_id=course_id, **kwargs
        )


class KnowledgeGraphNoPermissionException(KnowledgeGraphException):
    """无权访问该知识图谱数据"""

    def __init__(self, graph_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"无权访问知识图谱ID {graph_id} 的数据" if graph_id else "无权访问该知识图谱数据"

        super().__init__(
            error_code=ErrorCode.KNOWLEDGE_GRAPH_NO_PERMISSION.value, message=message, graph_id=graph_id, **kwargs
        )


# 导出所有异常类
__all__ = [
    "KnowledgeGraphAlreadyExistsException",
    "KnowledgeGraphChangeStatusFailedException",
    "KnowledgeGraphCourseNotFoundException",
    "KnowledgeGraphCreateFailedException",
    "KnowledgeGraphDeleteFailedException",
    "KnowledgeGraphException",
    "KnowledgeGraphIdListEmptyException",
    "KnowledgeGraphNameAlreadyExistsException",
    "KnowledgeGraphNoPermissionException",
    "KnowledgeGraphNotFoundException",
    "KnowledgeGraphUpdateFailedException",
]
