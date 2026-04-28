"""错误消息管理

支持i18n的多语言错误消息
"""

from graphedu.common.exceptions.services.codes import ErrorCode


def get_message(error_code: ErrorCode, locale: str = "zh_CN", **kwargs) -> str:
    """获取错误消息

    Args:
        error_code: 错误码
        locale: 语言代码 (zh_CN, en_US等)
        **kwargs: 消息格式化参数

    Returns:
        格式化后的错误消息
    """
    # 导入对应语言的消息映射
    if locale == "zh_CN":
        from .zh_cn import MESSAGES_ZH_CN as messages  # noqa: N811
    elif locale == "en_US":
        from .en_us import MESSAGES_EN_US as messages  # noqa: N811
    else:
        from .zh_cn import MESSAGES_ZH_CN as messages  # noqa: N811

    # 获取消息模板
    msg_template = messages.get(error_code, "Unknown error")

    # 格式化消息
    if kwargs:
        try:
            return msg_template.format(**kwargs)
        except (KeyError, ValueError):
            return msg_template

    return msg_template


__all__ = ["get_message"]
