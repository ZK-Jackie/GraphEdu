"""数据字典相关异常

包含字典类型、字典数据管理相关的异常定义，包含基类 DictException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class DictException(ServiceException):
    """字典异常基类"""

    def __init__(self, error_code: str = ErrorCode.DICT_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


# ============================================================================
# 字典类型相关异常
# ============================================================================


class DictTypeNotFoundException(DictException):
    """字典类型不存在"""

    def __init__(self, dict_type: str = None, dict_id: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_TYPE_NOT_FOUND.value,
            message=message,
            dict_type=dict_type,
            dict_id=dict_id,
            **kwargs,
        )


class DictTypeAlreadyExistsException(DictException):
    """字典类型已存在"""

    def __init__(self, dict_type: str = None, dict_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_TYPE_ALREADY_EXISTS.value,
            message=message,
            dict_type=dict_type,
            dict_name=dict_name,
            **kwargs,
        )


class DictTypeHasDataException(DictException):
    """字典类型已分配字典数据，不能删除"""

    def __init__(self, dict_name: str = None, dict_type: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_TYPE_HAS_DATA.value,
            message=message,
            dict_name=dict_name,
            dict_type=dict_type,
            **kwargs,
        )


class DictTypeIdListEmptyException(DictException):
    """字典类型ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DICT_TYPE_ID_LIST_EMPTY.value, message=message, **kwargs)


class DictTypeCreateFailedException(DictException):
    """字典类型创建失败"""

    def __init__(self, dict_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_TYPE_CREATE_FAILED.value, message=message, dict_name=dict_name, **kwargs
        )


class DictTypeUpdateFailedException(DictException):
    """字典类型更新失败"""

    def __init__(self, dict_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DICT_TYPE_UPDATE_FAILED.value, message=message, dict_id=dict_id, **kwargs)


class DictTypeDeleteFailedException(DictException):
    """字典类型删除失败"""

    def __init__(self, dict_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DICT_TYPE_DELETE_FAILED.value, message=message, dict_id=dict_id, **kwargs)


# ============================================================================
# 字典数据相关异常
# ============================================================================


class DictDataNotFoundException(DictException):
    """字典数据不存在"""

    def __init__(self, dict_code: int = None, dict_value: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_NOT_FOUND.value,
            message=message,
            dict_code=dict_code,
            dict_value=dict_value,
            **kwargs,
        )


class DictDataAlreadyExistsException(DictException):
    """字典数据已存在"""

    def __init__(
        self, dict_type: str = None, dict_value: str = None, dict_label: str = None, message: str = None, **kwargs
    ):
        super().__init__(
            error_code=ErrorCode.DICT_ALREADY_EXISTS.value,
            message=message,
            dict_type=dict_type,
            dict_value=dict_value,
            dict_label=dict_label,
            **kwargs,
        )


class DictDataIdListEmptyException(DictException):
    """字典数据ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DICT_DATA_ID_LIST_EMPTY.value, message=message, **kwargs)


class DictDataCreateFailedException(DictException):
    """字典数据创建失败"""

    def __init__(self, dict_label: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_DATA_CREATE_FAILED.value, message=message, dict_label=dict_label, **kwargs
        )


class DictDataUpdateFailedException(DictException):
    """字典数据更新失败"""

    def __init__(self, dict_code: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_DATA_UPDATE_FAILED.value, message=message, dict_code=dict_code, **kwargs
        )


class DictDataDeleteFailedException(DictException):
    """字典数据删除失败"""

    def __init__(self, dict_code: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DICT_DATA_DELETE_FAILED.value, message=message, dict_code=dict_code, **kwargs
        )


# 导出所有异常类
__all__ = [
    "DictDataAlreadyExistsException",
    "DictDataCreateFailedException",
    "DictDataDeleteFailedException",
    "DictDataIdListEmptyException",
    "DictDataNotFoundException",
    "DictDataUpdateFailedException",
    "DictException",
    "DictTypeAlreadyExistsException",
    "DictTypeCreateFailedException",
    "DictTypeDeleteFailedException",
    "DictTypeHasDataException",
    "DictTypeIdListEmptyException",
    "DictTypeNotFoundException",
    "DictTypeUpdateFailedException",
]
