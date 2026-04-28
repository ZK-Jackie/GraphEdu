"""GraphRAG 任务相关异常。

包含 GraphRAG 任务管理相关的异常定义，包含基类 GraphRAGTaskException 及其子类。
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class GraphRAGTaskException(ServiceException):
    """GraphRAG 任务异常基类。"""

    def __init__(self, error_code: str = ErrorCode.GRAPHRAG_TASK_NOT_FOUND.value, message: str | None = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class GraphRAGTaskNotFoundException(GraphRAGTaskException):
    """GraphRAG 任务不存在。"""

    def __init__(self, task_id: int | None = None, message: str | None = None, **kwargs):
        if task_id and message is None:
            message = f"GraphRAG 任务ID {task_id} 不存在"

        super().__init__(error_code=ErrorCode.GRAPHRAG_TASK_NOT_FOUND.value, message=message, task_id=task_id, **kwargs)


class GraphRAGTaskIdListEmptyException(GraphRAGTaskException):
    """GraphRAG 任务ID列表为空。"""

    def __init__(self, message: str | None = None, **kwargs):
        if message is None:
            message = "GraphRAG 任务ID列表不能为空"

        super().__init__(error_code=ErrorCode.GRAPHRAG_TASK_ID_LIST_EMPTY.value, message=message, **kwargs)


class GraphRAGBuildResourceNotTextedException(GraphRAGTaskException):
    """资源尚未文本化。"""

    def __init__(
        self,
        resource_name: str | None = None,
        current_status: str | None = None,
        message: str | None = None,
        **kwargs,
    ):
        if resource_name and current_status and message is None:
            message = f"资源 [{resource_name}] 尚未完成文本化, 当前状态: {current_status}"
        elif message is None:
            message = "资源尚未完成文本化, 无法构建 GraphRAG 索引"

        super().__init__(
            error_code=ErrorCode.GRAPHRAG_ERROR.value,
            message=message,
            resource_name=resource_name,
            current_status=current_status,
            **kwargs,
        )


class GraphRAGBuildCourseNotFoundException(GraphRAGTaskException):
    """构建时课程不存在。"""

    def __init__(self, course_id: int | None = None, message: str | None = None, **kwargs):
        if course_id and message is None:
            message = f"课程 ID [{course_id}] 不存在"
        elif message is None:
            message = "课程不存在"

        super().__init__(error_code=ErrorCode.COURSE_NOT_FOUND.value, message=message, course_id=course_id, **kwargs)


class GraphRAGBuildTaskCannotCancelException(GraphRAGTaskException):
    """任务无法取消。"""

    def __init__(self, current_status: str | None = None, message: str | None = None, **kwargs):
        if current_status and message is None:
            message = f"任务当前状态为 [{current_status}], 无法取消"
        elif message is None:
            message = "任务当前状态不允许取消"

        super().__init__(
            error_code=ErrorCode.GRAPHRAG_ERROR.value,
            message=message,
            current_status=current_status,
            **kwargs,
        )


class GraphRAGTaskCannotEnableException(GraphRAGTaskException):
    """GraphRAG 任务无法启用（未构建成功）。"""

    def __init__(self, current_status: str | None = None, message: str | None = None, **kwargs):
        if current_status and message is None:
            message = f"任务当前状态为 [{current_status}], 只有构建成功的任务才能启用"
        elif message is None:
            message = "只有构建成功的任务才能启用"

        super().__init__(
            error_code=ErrorCode.GRAPHRAG_TASK_CANNOT_ENABLE.value,
            message=message,
            current_status=current_status,
            **kwargs,
        )


class GraphRAGBuildTaskCannotRetryException(GraphRAGTaskException):
    """GraphRAG 任务无法重试/重建（非失败/已取消/已成功状态）。"""

    def __init__(self, current_status: str | None = None, message: str | None = None, **kwargs):
        if current_status and message is None:
            message = f"任务当前状态为 [{current_status}], 只有失败、已取消或已成功的任务才能重试/重建"
        elif message is None:
            message = "只有失败、已取消或已成功的任务才能重试/重建"

        super().__init__(
            error_code=ErrorCode.GRAPHRAG_TASK_CANNOT_RETRY.value,
            message=message,
            current_status=current_status,
            **kwargs,
        )


class GraphRAGIndexNotBuiltException(GraphRAGTaskException):
    """课程尚未构建可用的 GraphRAG 语义索引。"""

    def __init__(self, course_id: int | None = None, message: str | None = None, **kwargs):
        if course_id and message is None:
            message = (
                f"课程 [{course_id}] 尚未构建可用的 GraphRAG 语义索引，"
                "请先完成基础资源的文本解析和「建立语义检索索引」操作"
            )
        elif message is None:
            message = (
                "尚未构建可用的 GraphRAG 语义索引，"
                "请先完成基础资源的文本解析和「建立语义检索索引」操作"
            )

        super().__init__(
            error_code=ErrorCode.GRAPHRAG_TASK_NOT_FOUND.value,
            message=message,
            course_id=course_id,
            **kwargs,
        )


__all__ = [
    "GraphRAGBuildCourseNotFoundException",
    "GraphRAGBuildResourceNotTextedException",
    "GraphRAGBuildTaskCannotCancelException",
    "GraphRAGBuildTaskCannotRetryException",
    "GraphRAGIndexNotBuiltException",
    "GraphRAGTaskCannotEnableException",
    "GraphRAGTaskException",
    "GraphRAGTaskIdListEmptyException",
    "GraphRAGTaskNotFoundException",
]
