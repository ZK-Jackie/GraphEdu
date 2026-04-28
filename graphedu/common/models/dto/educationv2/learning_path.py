"""学习路径 DTO 模型。"""
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO


class LearningPathStatusUpdateDTO(DTO):
    """更新学习路径状态 DTO。"""

    status: Literal["active", "completed", "archived"] = Field(description="目标状态：active/completed/archived")
