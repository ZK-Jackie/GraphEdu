"""示例定时任务

用于测试定时任务功能
"""

import logging

logger = logging.getLogger(__name__)


async def sample_task(*args, **kwargs):
    """示例任务函数

    这是一个示例任务，用于测试定时任务功能是否正常工作。

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        dict: 执行结果
    """
    logger.info(f"执行示例任务: args={args}, kwargs={kwargs}")

    # 这里可以添加实际的任务逻辑
    result = {
        "status": "success",
        "message": "任务执行成功",
        "args": args,
        "kwargs": kwargs,
    }

    logger.info(f"示例任务执行完成: {result}")
    return result
