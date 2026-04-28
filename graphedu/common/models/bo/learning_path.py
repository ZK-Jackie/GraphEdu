"""学习路径业务对象。"""

from pydantic import BaseModel, Field


class LearningPathNodeProgressBO(BaseModel):
    """学习路径中单个知识点的进度详情。"""

    node_uuid: str = Field(description="知识点 UUID")
    mastery_level: str = Field(description="掌握等级（unknown/low/medium/high）")
    mastery_score: float | None = Field(default=None, description="掌握度评分")
    mastered: bool = Field(description="是否已掌握")


class LearningPathProgressBO(BaseModel):
    """学习路径进度业务对象。"""

    total: int = Field(description="知识点总数")
    mastered: int = Field(description="已掌握数量")
    progress_pct: int = Field(description="完成百分比（0-100）")
    details: list[LearningPathNodeProgressBO] = Field(description="每个知识点的进度详情")
