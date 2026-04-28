"""知识图谱相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery

KnowledgeGraphRelationType = Literal[
    "RELATED_TO",
    "PRIOR_TO",
    "SUBTOPIC_OF",
]


class KnowledgeGraphQueryDTO(PageQuery):
    """知识图谱查询 DTO"""

    graph_id: int | None = Field(default=None, description="图谱ID")
    course_id: int | None = Field(default=None, description="课程ID")
    graph_name: str | None = Field(default=None, description="图谱名称")
    graph_database: str | None = Field(default=None, description="AGE 图名称")
    build_method: str | None = Field(default=None, description="构建方法（nlp, llm, llm_assisted等）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="知识图谱状态（0正常 1停用 2已删除）")
    is_draft: str | None = Field(default=None, description="草稿状态筛选（Y/N/null全部）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class KnowledgeGraphCreateDTO(DTO):
    """创建知识图谱 DTO"""

    course_id: int = Field(description="课程ID")
    graph_name: str = Field(description="图谱名称")
    graph_database: str = Field(default="edu_knowledge_graph", description="AGE 图名称")
    description: str | None = Field(default=None, description="图谱描述")
    build_method: str | None = Field(default=None, description="构建方法（nlp, llm, llm_assisted等）")
    is_draft: str | None = Field(default=None, description="是否草稿（Y待审核/N已确认）")


class KnowledgeGraphUpdateDTO(DTO):
    """更新知识图谱 DTO"""

    graph_id: int = Field(description="图谱ID")
    course_id: int | None = Field(default=None, description="课程ID")
    graph_name: str | None = Field(default=None, description="图谱名称")
    graph_database: str | None = Field(default=None, description="AGE 图名称")
    version: str | None = Field(default=None, description="图谱版本号")
    description: str | None = Field(default=None, description="图谱描述")
    build_method: str | None = Field(default=None, description="构建方法（nlp, llm, llm_assisted等）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="知识图谱状态（0正常 1停用 2已删除）")


class KnowledgeExtractionRequestDTO(DTO):
    """知识点提取请求 DTO。"""

    mode: Literal["markdown", "skeleton", "combined"] = Field(
        default="markdown",
        description="提取模式（markdown/skeleton/combined）",
    )
    document_id: int | None = Field(
        default=None,
        description="资源文档ID（mode 为 markdown 或 combined 时必填）",
    )
    skeleton_text: str | None = Field(
        default=None,
        description="教师手动输入的大纲文本（mode 为 skeleton 或 combined 时必填）",
    )


class KnowledgePointSaveDTO(DTO):
    """单个知识点保存 DTO。"""

    title: str = Field(description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int = Field(default=3, ge=1, le=5, description="重要程度（1-5）")


class KnowledgeRelationshipSaveDTO(DTO):
    """知识点关系保存 DTO。"""

    source_title: str = Field(description="源知识点标题")
    target_title: str = Field(description="目标知识点标题")
    relation_type: KnowledgeGraphRelationType = Field(description="关系类型")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度（0-1）")
    description: str | None = Field(default=None, description="关系描述")


class SaveExtractionRequestDTO(DTO):
    """确认保存提取结果到 AGE 图谱的请求 DTO。"""

    points: list[KnowledgePointSaveDTO] = Field(description="知识点列表")
    relationships: list[KnowledgeRelationshipSaveDTO] = Field(default_factory=list, description="关系列表")


class KnowledgePointCreateDTO(DTO):
    """手动创建单个知识点 DTO。"""

    title: str = Field(description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int = Field(default=3, ge=1, le=5, description="重要程度（1-5）")
    source: str = Field(default="manual", description="来源（manual/ai）")


class KnowledgePointUpdateDTO(DTO):
    """更新知识点 DTO。"""

    title: str | None = Field(default=None, description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int | None = Field(default=None, ge=1, le=5, description="重要程度（1-5）")


class KnowledgeRelationshipCreateDTO(DTO):
    """创建知识点关系 DTO。"""

    source_id: str = Field(description="源知识点节点ID")
    target_id: str = Field(description="目标知识点节点ID")
    relation_type: KnowledgeGraphRelationType = Field(description="关系类型")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度（0-1）")
    description: str | None = Field(default=None, description="关系描述")


class KnowledgeRelationshipUpdateDTO(DTO):
    """更新知识点关系 DTO。

    仅允许更新关系属性，不允许变更源节点和目标节点。
    """

    relation_type: KnowledgeGraphRelationType | None = Field(default=None, description="关系类型")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="置信度（0-1）")
    description: str | None = Field(default=None, description="关系描述")


class NodeNeighborsQueryDTO(DTO):
    """查询节点邻居 DTO。"""

    depth: int = Field(default=1, ge=1, le=3, description="查询深度（1=直接邻居，2=两跳邻居，3=三跳邻居）")
    limit: int = Field(default=20, ge=1, le=100, description="每层返回的节点数量限制")
    direction: Literal["in", "out", "both"] = Field(default="both", description="关系方向（in/out/both）")


class AutoGenerateRequestDTO(DTO):
    """基于课程总体 GraphRAG 索引自动生成可视化图谱请求"""
    course_id: int = Field(description="课程ID")
    graph_name: str | None = Field(default=None, max_length=128, description="知识图谱名称（不提供则自动生成）")
