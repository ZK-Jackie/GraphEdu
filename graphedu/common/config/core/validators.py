"""通用验证器。"""

import warnings


def validate_header_lowercase(value: str) -> str:
    """验证并转换 header 为小写。

    Args:
        value: 原始 header 值

    Returns:
        转换为小写后的 header 值
    """
    if value and any(c.isupper() for c in value):
        warnings.warn(
            f"Token header must be lowercase, converting '{value}' to lowercase",
            stacklevel=2,
        )
        return value.lower()
    return value
