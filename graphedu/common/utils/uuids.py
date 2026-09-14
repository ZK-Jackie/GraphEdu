"""UUID 工具模块。

统一使用 UUIDv7（基于时间戳、单调递增、可排序）替代 UUIDv4。
所有业务场景均应通过本模块获取 UUID。
"""

from uuid import UUID, uuid5

from uuid_utils import uuid7 as _uuid7

# 知识点确定性 UUID 的固定 namespace（任意固定值，用于 uuid5 哈希）
_KNOWLEDGE_POINT_NAMESPACE = UUID("7f3a2e1b-4c5d-6a7b-8c9d-0e1f2a3b4c5d")


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


def knowledge_point_uuid(course_id: int, title: str) -> str:
    """基于 course_id + title 确定性生成知识点 UUID（UUIDv5）。

    相同 course_id + 相同 title 永远产生相同 UUID。用于知识点节点标识，使图谱
    重建时同一知识点获得相同 UUID，从而 edu_student_mastery /
    edu_student_learning_event 等历史关联不会因重建而悬空。

    注意：标识稳定性依赖 title 文本稳定——title 变化会被视为不同知识点。

    Args:
        course_id: 课程ID（隔离不同课程的同名知识点）。
        title: 知识点标题。

    Returns:
        str: 确定性 UUID 字符串。
    """
    return str(uuid5(_KNOWLEDGE_POINT_NAMESPACE, f"{course_id}:{title}"))
