"""UUID 工具模块。

统一使用 UUIDv7（基于时间戳、单调递增、可排序）替代 UUIDv4。
所有业务场景均应通过本模块获取 UUID。
"""

from uuid import UUID

from uuid_utils import uuid7 as _uuid7


def uuid7() -> UUID:
    """生成 UUIDv7。

    UUIDv7 基于时间戳，具有以下优势：
    - 单调递增，天然有序，有利于数据库索引性能
    - 包含毫秒级时间戳，可用于排序
    - 全局唯一，无需中心化协调
    """
    return _uuid7()


def uuid7_str() -> str:
    """生成 UUIDv7 字符串。"""
    return str(_uuid7())
