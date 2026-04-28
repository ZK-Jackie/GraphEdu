"""GraphRAG 图谱生成业务模型"""

from pydantic import BaseModel, Field


class GraphNodeBO(BaseModel):
    """GraphRAG 生成的图谱节点"""

    id: str | int = Field(description="节点标识")
    label: str = Field(description="概念名称")
    description: str | None = Field(default=None, description="节点描述")
    chapter_indices: list[int] = Field(
        default_factory=list, description="来源章节索引列表（对应输入 chapter_names 的下标）"
    )


class GraphEdgeBO(BaseModel):
    """GraphRAG 生成的图谱连边"""

    source: str | int = Field(description="源节点 ID")
    target: str | int = Field(description="目标节点 ID")
    type: str = Field(description="关系类型（IS_PREREQUISITE_OF / IS_PART_OF）")
    description: str | None = Field(default=None, description="关系描述")


class VisualGraphBO(BaseModel):
    """GraphRAG 生成的可视化图谱完整数据"""

    nodes: list[GraphNodeBO] = Field(default_factory=list, description="节点列表")
    edges: list[GraphEdgeBO] = Field(default_factory=list, description="连边列表")
