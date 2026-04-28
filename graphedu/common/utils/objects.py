"""Object utility functions.

This module provides utilities for object manipulation, type checking,
and dynamic module/class imports.
"""

from datetime import date, datetime
from decimal import Decimal
import importlib
from types import NoneType, UnionType
from typing import Any, Literal, TypedDict, TypeVar, Union, get_origin

_T = TypeVar("_T")
_primitive_types = {str, int, float, bool, datetime, date, Decimal, bytes, NoneType}
_container_types = [list, dict, set, TypedDict]


def cp_dict_attr[T](d: dict, o: T) -> T:
    """Copy dictionary attributes to an object.

    Args:
        d: Dictionary containing attributes to copy.
        o: Object to copy attributes to.

    Returns:
        The modified object with copied attributes.
    """
    for k, v in d.items():
        setattr(o, k, v)
    return o


def is_primitive_object(obj: object) -> bool:
    """Check if an object is of a primitive type.

    Args:
        obj: Object to check.

    Returns:
        True if the object is a primitive type, False otherwise.
    """
    return type(obj) in _primitive_types


def is_primitive_type(tp: type | UnionType) -> bool:
    """Check if a type is a primitive type (excluding classes).

    Args:
        tp: Type to check.

    Returns:
        True if the type is a primitive type, False otherwise.
    """
    from typing import get_args, get_origin

    # 检查是否是原始类型
    if tp in _primitive_types:
        return True

    # 获取原始类型（对于泛型）
    origin = get_origin(tp)

    # 处理 Literal 类型（如 Literal["dev", "prod"]）
    if origin is Literal:
        # Literal 类型：检查所有参数是否都是原始类型
        args = get_args(tp)
        if args:
            return all(isinstance(arg, (str, int, float, bool)) for arg in args)
        return False

    # 处理 Union 和 Optional 类型（包括 X | None 语法）
    if origin is Union or origin is UnionType:
        # Union 类型：所有参数都是原始类型才返回 True
        if hasattr(tp, "__args__"):
            return all(is_primitive_type(t) for t in tp.__args__)
        return False

    # 处理容器类型（如 list[str], dict[str, int]）
    if origin in _container_types:
        # 容器类型本身是基础类型，但需要检查其泛型参数
        args = get_args(tp)
        if args:
            # 如果有类型参数，检查所有参数是否都是原始类型
            return all(is_primitive_type(arg) for arg in args)
        # 没有类型参数的容器（如裸 list, dict）也被认为是基础类型
        return True

    # 检查是否是裸容器类型（无泛型参数）
    if tp in _container_types:
        return True

    # 处理其他泛型类型
    if tp is not None:
        # 检查原始类型是否是原始类型
        return tp in _primitive_types

    return False


def is_container_of_baseconfig(tp: type | UnionType) -> bool:
    """Check if a type is a container (list/dict) containing BaseConfig.

    Args:
        tp: Type to check.

    Returns:
        True if the type is list[BaseConfig] or dict[X, BaseConfig], False otherwise.
    """
    from typing import get_args

    origin = get_origin(tp)

    # 检查是否是 list 或 dict
    if origin not in (list, dict):
        return False

    # 导入 BaseConfig（延迟导入避免循环依赖）
    try:
        from ..config.core.base import BaseConfig
    except ImportError:
        return False

    args = get_args(tp)
    if not args:
        return False

    # 对于 list[T]，检查 T 是否是 BaseConfig
    if origin is list:
        return len(args) == 1 and isinstance(args[0], type) and issubclass(args[0], BaseConfig)

    # 对于 dict[K, V]，检查 V 是否是 BaseConfig
    if origin is dict:
        return len(args) == 2 and isinstance(args[1], type) and issubclass(args[1], BaseConfig)

    return False


def get_baseconfig_from_container(tp: type | UnionType) -> type | None:
    """Extract BaseConfig class from a container type.

    Args:
        tp: Container type like list[BaseConfig] or dict[str, BaseConfig].

    Returns:
        The BaseConfig class, or None if not found.
    """
    from typing import get_args

    origin = get_origin(tp)
    args = get_args(tp)

    if not args:
        return None

    # 对于 list[T]，返回 T
    if origin is list and len(args) == 1:
        return args[0]

    # 对于 dict[K, V]，返回 V
    if origin is dict and len(args) == 2:
        return args[1]

    return None


def get_class(tp: type | UnionType) -> type:
    """Get the class from a type.

    Args:
        tp: Type to extract class from.

    Returns:
        The class of the type.
    """
    if hasattr(tp, "__origin__"):
        return tp.__origin__
    return tp


def get_specific_class_from_union(tp: Any, subclass_of: type = object) -> type | None:
    """Get a specific class from a Union type.

    Args:
        tp: Type to extract class from (should be a Union type).
        subclass_of: Filter for subclasses of this type.

    Returns:
        The matching class, or None if not found or type is not a Union.
    """
    import warnings

    origin = get_origin(tp)
    # Handle Union types and | syntax
    if origin is Union or origin is UnionType:
        for arg in tp.__args__:
            if issubclass(get_class(arg), subclass_of):
                return get_class(arg)
        # Union 类型但没有找到匹配的类型，返回 None（不警告）
        return None

    # 非 Union 类型时发出警告
    warnings.warn(
        f"传入的类型 {tp} 不是 Union 类型，get_specific_class_from_union 仅支持 Union 类型", UserWarning, stacklevel=2
    )
    return None


def import_from_string(dot_path: str):
    """Dynamically import a module or class from a string path.

    Example:
        "uvloop.EventLoopPolicy" → Returns the EventLoopPolicy class reference

    Args:
        dot_path: Module or class path in dot notation.

    Returns:
        The imported module or class reference.

    Raises:
        ImportError: If the import fails.
    """
    try:
        # 分割模块路径和类名
        module_path, class_name = dot_path.rsplit(".", 1)
    except ValueError:
        raise ImportError(f"路径格式错误，必须包含至少一个点（.）：{dot_path}") from None

    # 动态导入模块
    module = importlib.import_module(module_path)

    # 从模块中获取类
    return getattr(module, class_name)
