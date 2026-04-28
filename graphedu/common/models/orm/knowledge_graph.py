"""知识图谱实体"""

from datetime import UTC, datetime
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from graphedu.common.utils.uuids import uuid7

KnowledgeRelationshipName = Literal["RELATED_TO", "PRIOR_TO", "SUBTOPIC_OF"]

VALID_RELATIONSHIP_NAMES = frozenset({"RELATED_TO", "PRIOR_TO", "SUBTOPIC_OF"})
RELATIONSHIP_NAME_ALIASES = {
    "PREREQUISITE": "PRIOR_TO",
    "CONTAINS": "SUBTOPIC_OF",
}


def normalize_relationship_name(name: str | None) -> str:
    """将输入关系类型标准化为知识图谱规范名称。"""
    normalized = (name or RelatedTO.model_fields["name"].default).upper()
    normalized = RELATIONSHIP_NAME_ALIASES.get(normalized, normalized)
    if normalized not in VALID_RELATIONSHIP_NAMES:
        return RelatedTO.model_fields["name"].default
    return normalized


class Node(BaseModel):
    """知识图谱 = 节点 - 基类"""

    node_id: uuid.UUID = Field(default_factory=uuid7, description="节点ID")

    model_config = ConfigDict(extra="allow")


class Relationship(BaseModel):
    """知识图谱 - 节点关系 - 基类"""

    name: str = "RELATED_TO"
    start_id: uuid.UUID = Field(description="起始节点ID")
    end_id: uuid.UUID = Field(description="终点节点ID")

    model_config = ConfigDict(extra="allow")

    def is_bidirectional(self) -> bool:
        """是否是双向关系"""
        return False


class KnowledgePointMutation(BaseModel):
    """知识点更新实体。"""

    title: str | None = Field(default=None, description="节点名称")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int | None = Field(default=None, ge=1, le=5, description="重要程度（1-5）")
    update_time: datetime = Field(default_factory=lambda: datetime.now(UTC), description="更新时间")
    update_by: int | None = Field(default=None, description="更新者ID")


class KnowledgePointRecord(BaseModel):
    """知识点读模型。"""

    id: str = Field(description="AGE 节点ID")
    uuid: str | None = Field(default=None, description="业务 UUID")
    course_id: int = Field(description="课程ID")
    graph_id: int | None = Field(default=None, description="知识图谱ID")
    title: str = Field(description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int = Field(default=3, ge=1, le=5, description="重要程度（1-5）")
    source: str = Field(default="ai", description="来源")
    create_time: datetime | None = Field(default=None, description="创建时间")
    create_by: int | None = Field(default=None, description="创建者ID")
    update_time: datetime | None = Field(default=None, description="更新时间")
    update_by: int | None = Field(default=None, description="更新者ID")

    @field_validator("create_time", "update_time", "uuid", "title", "description", "source", mode="before")
    @classmethod
    def _strip_quoted_datetime(cls, v: datetime | str | None) -> datetime | str | None:
        """AGE Cypher RETURN 可能给字符串属性包裹多层引号，循环剥离直到无引号。"""
        if isinstance(v, str):
            while v.startswith('"') and v.endswith('"') and len(v) > 1:
                v = v[1:-1]
        return v


class KnowledgeRelationshipPayload(BaseModel):
    """知识点关系写模型。"""

    from_node_id: str = Field(description="源节点ID")
    to_node_id: str = Field(description="目标节点ID")
    type: KnowledgeRelationshipName = Field(default="RELATED_TO", description="关系类型")
    confidence: float | None = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    description: str | None = Field(default=None, description="关系描述")
    graph_id: int | None = Field(default=None, description="知识图谱ID")


class KnowledgeRelationshipRecord(BaseModel):
    """知识点关系读模型。"""

    id: str = Field(description="AGE 关系ID")
    type: KnowledgeRelationshipName = Field(default="RELATED_TO", description="关系类型")
    from_node_id: str = Field(description="源节点ID")
    to_node_id: str = Field(description="目标节点ID")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="置信度")
    description: str | None = Field(default=None, description="关系描述")


class KnowledgePoint(Node):
    """知识图谱 - 知识节点"""

    node_id: uuid.UUID = Field(default_factory=uuid7, description="知识图谱节点ID")
    course_id: int = Field(description="知识点关联的课程ID")
    graph_id: int | None = Field(default=None, description="所属知识图谱ID")
    title: str = Field(description="节点名称，必填")
    source: str = Field(description="创建源")
    importance: int | None = Field(default=None, ge=1, le=5, description="重要程度（1-5）")
    description: str | None = Field(default=None, description="知识点描述，markdown 格式")
    create_time: datetime = Field(default_factory=lambda: datetime.now(UTC), description="创建时间")
    create_by: int | None = Field(default=None, description="创建者ID")
    update_time: datetime = Field(default_factory=lambda: datetime.now(UTC), description="更新时间")
    update_by: int | None = Field(default=None, description="更新者ID")


class RelatedTO(Relationship):
    """知识图谱 - 关联关系"""

    name: str = "RELATED_TO"
    confidence: float = Field(description="知识点间的关联置信度")
    description: str | None = Field(default=None, description="关系描述，markdown 格式")

    def is_bidirectional(self) -> bool:
        """是否是双向关系"""
        return True


class PriorTo(Relationship):
    """知识图谱 - 先修关系"""

    name: str = "PRIOR_TO"
    description: str | None = Field(default=None, description="关系描述，markdown 格式")


class SubTopicOf(Relationship):
    """知识图谱 - 包含关系"""

    name: str = "SUBTOPIC_OF"
    description: str | None = Field(default=None, description="关系描述，markdown 格式")


# ============================================================================
# 学习路径相关 AGE 图节点与关系
# ============================================================================


class LearningPlan(Node):
    """学习路径 - 计划节点（存储在 AGE 图中）"""

    node_id: uuid.UUID = Field(default_factory=uuid7, description="计划节点 ID（同时作为 plan_id）")
    student_id: int = Field(description="学生 ID")
    course_id: int = Field(description="课程 ID")
    title: str = Field(description="计划标题")
    status: str = Field(default="active", description="状态：active/completed/archived")
    session_id: int | None = Field(default=None, description="创建该计划的聊天会话 ID")
    create_time: datetime = Field(default_factory=lambda: datetime.now(UTC), description="创建时间")


class PlanStep(Relationship):
    """学习路径 - 计划步骤关系（KnowledgePoint → KnowledgePoint）"""

    name: str = "PLAN_STEP"
    plan_id: uuid.UUID = Field(description="关联的学习计划 ID")
    step_order: int = Field(description="在计划中的顺序")


class LearningPlanRecord(BaseModel):
    """学习路径计划读模型。"""

    id: str = Field(description="AGE 节点 ID")
    plan_id: str = Field(description="计划 UUID")
    student_id: int = Field(description="学生 ID")
    course_id: int = Field(description="课程 ID")
    title: str = Field(description="计划标题")
    status: str = Field(default="active", description="状态")
    session_id: int | None = Field(default=None, description="创建该计划的聊天会话 ID")
    create_time: datetime | None = Field(default=None, description="创建时间")
