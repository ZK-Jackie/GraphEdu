"""定时任务模块

此模块包含所有可被定时任务调用的函数

使用方式：
1. Python 函数调用：在任务中指定调用目标为 'graphedu.jobs.sample_task.sample_task'
2. Webhook 调用：在任务中指定调用目标为 'graphedu.jobs.webhook_handler.webhook_entry'

模块导出：
- sample_task: 示例任务函数
- webhook_entry: Webhook 调用入口函数
"""

from .sample_task import sample_task
from .webhook_handler import webhook_entry

__all__ = ["sample_task", "webhook_entry"]
