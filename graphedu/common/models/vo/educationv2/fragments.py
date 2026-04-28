"""统计模块 Fragment 基类

提取高频字段组为独立 Fragment，具体 VO 通过多重继承组合。
Pydantic 多重继承保持 JSON 扁平序列化，前端无需改动。
"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO


class MasteryFragment(VO):
    """掌握度片段（8 个 VO 共用）"""

    latest_mastery_level: str = Field(default="", description="最新掌握等级")
    latest_mastery_score: float | None = Field(default=None, description="最新掌握度评分")
    latest_assessed_at: datetime | None = Field(default=None, description="最新评估时间")


class InteractionFragment(VO):
    """交互计数片段"""

    total_interaction_count: int = Field(default=0, description="总交互次数")
    total_question_count: int = Field(default=0, description="总提问次数")
    total_interest_count: int = Field(default=0, description="总标记兴趣次数")
    total_explain_request_count: int = Field(default=0, description="总请求解释次数")


class QuizFragment(VO):
    """答题统计片段（7 个 VO 共用）"""

    quiz_count: int = Field(default=0, description="答题次数")
    quiz_correct_count: int = Field(default=0, description="答对次数")
    quiz_correct_rate: float | None = Field(default=None, description="答题正确率（%）")


class CoverageFragment(VO):
    """覆盖率片段（4 个 VO 共用）"""

    chapters_touched: int = Field(default=0, description="接触的章节数")
    chapter_coverage_rate: float = Field(default=0, description="章节覆盖率（%）")
    nodes_touched: int = Field(default=0, description="接触的知识点数")
    node_coverage_rate: float = Field(default=0, description="知识点覆盖率（%）")


class MasteryDistributionFragment(VO):
    """掌握度分布片段"""

    high_mastery_count: int = Field(default=0, description="高掌握度人数")
    medium_mastery_count: int = Field(default=0, description="中掌握度人数")
    low_mastery_count: int = Field(default=0, description="低掌握度人数")


class StudyTimeFragment(VO):
    """学习时长片段（12 个 VO 共用）"""

    total_study_seconds: int | None = Field(default=None, description="总学习时长（秒）")
