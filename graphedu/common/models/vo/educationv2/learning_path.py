"""学习路径相关 VO 模型。"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.educationv2.knowledge_graph import NvlGraphDataVO


class LearningPlanListVO(VO):
    """学习路径列表项 VO。"""

    plan_id: str = Field(description="计划 UUID")
    course_id: int = Field(description="课程 ID")
    title: str = Field(description="计划标题")
    status: str = Field(description="状态：active/completed/archived")
    create_time: datetime | None = Field(default=None, description="创建时间")


class LearningPathProgressDetailVO(VO):
    """学习路径中单个知识点的进度详情 VO。"""

    node_uuid: str = Field(description="知识点 UUID")
    mastery_level: str = Field(description="掌握等级（unknown/low/medium/high）")
    mastery_score: float | None = Field(default=None, description="掌握度评分")
    mastered: bool = Field(description="是否已掌握")


class LearningPlanProgressVO(VO):
    """学习路径进度 VO。"""

    total: int = Field(description="知识点总数")
    mastered: int = Field(description="已掌握数量")
    progress_pct: int = Field(description="完成百分比（0-100）")
    details: list[LearningPathProgressDetailVO] = Field(description="每个知识点的进度详情")


class LearningPlanDetailVO(VO):
    """学习路径详情 VO（含子图 + 进度）。"""

    plan: LearningPlanListVO = Field(description="学习计划基本信息")
    graph: NvlGraphDataVO | None = Field(default=None, description="知识点子图数据")
    progress: LearningPlanProgressVO | None = Field(default=None, description="学习进度")
