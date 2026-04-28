"""知识图谱专属 VO 模型。"""

from datetime import datetime

from pydantic import ConfigDict, Field

from graphedu.common.models.vo.base import VO


class KnowledgeGraphDetailVO(VO):
    """知识图谱详细信息 VO。"""

    graph_id: int = Field(description="图谱ID")
    course_id: int = Field(description="课程ID")
    graph_name: str = Field(description="图谱名称")
    graph_database: str = Field(description="AGE 图名称")
    version: str = Field(default="1.0.0", description="图谱版本号")
    description: str | None = Field(default=None, description="图谱描述")
    total_nodes: int | None = Field(default=None, description="总节点数")
    total_relationships: int | None = Field(default=None, description="总关系数")
    node_type_stats: dict | None = Field(default=None, description="节点类型统计（JSONB格式）")
    relationship_type_stats: dict | None = Field(default=None, description="关系类型统计（JSONB格式）")
    average_degree: float | None = Field(default=None, description="平均度数")
    connectivity_score: float | None = Field(default=None, description="连通性评分")
    build_method: str | None = Field(default=None, description="构建方法，对照 kg_build_method")
    build_info: dict | None = Field(default=None, description="构建信息（JSONB格式，包含构建参数、模型信息等）")
    last_extended: datetime | None = Field(default=None, description="最后扩展时间")
    status: str = Field(description="知识图谱状态，对照 sys_data_status（0正常 1停用 2已删除）")
    is_draft: str = Field(description="是否草稿（Y待审核/N已确认）")
    task_status: str | None = Field(default=None, description="异步生成任务状态（pending/processing/success/failed）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    course_name: str | None = Field(default=None, description="课程名称")


class KnowledgeGraphListVO(VO):
    """知识图谱列表项 VO。"""

    graph_id: int = Field(description="图谱ID")
    course_id: int = Field(description="课程ID")
    graph_name: str = Field(description="图谱名称")
    graph_database: str = Field(description="AGE 图名称")
    version: str = Field(default="1.0.0", description="图谱版本号")
    total_nodes: int | None = Field(default=None, description="总节点数")
    total_relationships: int | None = Field(default=None, description="总关系数")
    build_method: str | None = Field(default=None, description="构建方法，对照 kg_build_method")
    status: str = Field(description="知识图谱状态，对照 sys_data_status")
    is_draft: str = Field(description="是否草稿（Y待审核/N已确认）")
    task_status: str | None = Field(default=None, description="异步生成任务状态（pending/processing/success/failed）")
    create_time: datetime | None = Field(default=None, description="创建时间")
    last_extended: datetime | None = Field(default=None, description="最后扩展时间")
    course_name: str | None = Field(default=None, description="课程名称")
    course_cover: str | None = Field(default=None, description="课程封面文件ID")


class GraphRelationshipCreatedVO(VO):
    """创建知识图谱关系成功响应 VO。"""

    rel_id: str = Field(description="新建关系的 ID")


class GraphRelationshipDetailVO(VO):
    """查询知识图谱关系详情响应 VO。"""

    rel_id: str = Field(description="关系 ID")
    rel_type: str = Field(description="关系类型（RELATED_TO / PRIOR_TO / SUBTOPIC_OF）")
    from_node_id: str = Field(description="源节点 ID")
    to_node_id: str = Field(description="目标节点 ID")
    confidence: float | None = Field(default=None, description="置信度（0-1）")
    description: str | None = Field(default=None, description="关系描述")


class KnowledgePointDraftVO(VO):
    """AI 提取的知识点草稿 VO（未持久化）。"""

    title: str = Field(description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int = Field(default=3, ge=1, le=5, description="重要程度（1-5）")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度（0-1）")
    source: str = Field(default="ai", description="来源（ai/manual）")


class KnowledgeRelationshipDraftVO(VO):
    """AI 推断的知识点关系草稿 VO（未持久化）。"""

    source_title: str = Field(description="源知识点标题")
    target_title: str = Field(description="目标知识点标题")
    relation_type: str = Field(description="关系类型（RELATED_TO/PRIOR_TO/SUBTOPIC_OF）")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度（0-1）")
    description: str | None = Field(default=None, description="关系描述")


class KnowledgeExtractionResultVO(VO):
    """知识点提取结果 VO（包含草稿知识点和推断关系）。"""

    points: list[KnowledgePointDraftVO] = Field(description="提取的知识点列表")
    relationships: list[KnowledgeRelationshipDraftVO] = Field(description="推断的关系列表")
    mode: str = Field(description="提取模式")
    total_points: int = Field(description="知识点总数")
    total_relationships: int = Field(description="关系总数")


class NvlNodePropertiesVO(VO):
    """NVL 节点属性 VO。"""

    title: str = Field(description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int = Field(default=3, description="重要程度（1-5）")
    source: str = Field(default="ai", description="来源")
    uuid: str | None = Field(default=None, description="知识点 UUID")


class NvlRelationshipPropertiesVO(VO):
    """NVL 关系属性 VO。"""

    confidence: float | None = Field(default=None, description="置信度（0-1）")
    description: str | None = Field(default=None, description="关系描述")


class NvlNodeVO(VO):
    """NVL 图节点 VO。"""

    id: str = Field(description="节点唯一ID（AGE 图节点ID）")
    labels: list[str] = Field(description="节点标签列表")
    properties: NvlNodePropertiesVO = Field(description="节点属性")


class NvlRelationshipVO(VO):
    """NVL 图关系 VO。"""

    id: str = Field(description="关系唯一ID")
    type: str = Field(description="关系类型（RELATED_TO/PRIOR_TO/SUBTOPIC_OF）")
    from_: str = Field(alias="from", description="源节点ID")
    to: str = Field(description="目标节点ID")
    properties: NvlRelationshipPropertiesVO = Field(default_factory=NvlRelationshipPropertiesVO, description="关系属性")

    model_config = ConfigDict(populate_by_name=True)


class NvlGraphDataVO(VO):
    """完整图谱可视化数据 VO（NVL 格式）。"""

    nodes: list[NvlNodeVO] = Field(description="节点列表")
    relationships: list[NvlRelationshipVO] = Field(description="关系列表")
    total_nodes: int = Field(description="节点总数")
    total_relationships: int = Field(description="关系总数")


class KnowledgePointVO(VO):
    """知识点节点 VO（已持久化在 AGE 图中）。"""

    id: str = Field(description="AGE 节点ID")
    course_id: int = Field(description="课程ID")
    title: str = Field(description="知识点标题")
    description: str | None = Field(default=None, description="知识点描述")
    importance: int = Field(default=3, description="重要程度（1-5）")
    source: str = Field(default="ai", description="来源（ai/manual）")


class TopNodesVO(VO):
    """图谱顶层节点 VO。"""

    nodes: list[NvlNodeVO] = Field(description="顶层节点列表（入度为0的节点）")
    relationships: list[NvlRelationshipVO] = Field(default_factory=list, description="顶层节点之间的关系列表")
    total: int = Field(description="顶层节点总数")


class NodeNeighborsVO(VO):
    """节点邻居查询结果 VO。"""

    center_node_id: str = Field(description="中心节点ID")
    nodes: list[NvlNodeVO] = Field(description="邻居节点列表")
    relationships: list[NvlRelationshipVO] = Field(description="关系列表")
    depth: int = Field(description="查询深度")
    total_nodes: int = Field(description="返回的节点总数")
    total_relationships: int = Field(description="返回的关系总数")


class AutoGenerateSubmitVO(VO):
    """提交异步自动生成知识图谱任务的响应。"""

    graph_id: int = Field(description="知识图谱ID")
    task_status: str = Field(description="任务状态，固定为 pending")


class ChapterKnowledgePointLinkResultVO(VO):
    """章节知识点关联结果 VO"""

    added: int = Field(description="成功关联数量")
    skipped: int = Field(description="跳过数量（已存在）")


class KnowledgeNodeChapterDetailVO(VO):
    """知识点-章节关联详细信息 VO"""

    node_chapter_id: int = Field(description="关系ID")
    chapter_id: int = Field(description="章节ID")
    node_uuid: str = Field(description="知识点业务UUID")
    relevance_score: float = Field(description="知识点与章节的相关性评分（0-1）")
    description: str | None = Field(default=None, description="关系描述")
    is_primary: str = Field(description="是否主要关联（Y是 N否）")
    status: str = Field(description="关系状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    # 冗余知识点详情（从知识图谱查询补充）
    node_title: str | None = Field(default=None, description="知识点标题")
    node_description: str | None = Field(default=None, description="知识点描述")
    node_importance: int | None = Field(default=None, description="重要程度（1-5）")


class KnowledgeNodeChapterListVO(VO):
    """知识点-章节关联列表项 VO"""

    node_chapter_id: int = Field(description="关系ID")
    chapter_id: int = Field(description="章节ID")
    node_uuid: str = Field(description="知识点业务UUID")
    relevance_score: float = Field(description="知识点与章节的相关性评分（0-1）")
    is_primary: str = Field(description="是否主要关联（Y是 N否）")
    status: str = Field(description="关系状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")
    # 冗余知识点详情
    node_title: str | None = Field(default=None, description="知识点标题")


class KnowledgeNodeChapterLinkResultVO(VO):
    """知识点-章节批量关联结果 VO"""

    added: int = Field(description="成功关联数量")
    skipped: int = Field(description="跳过数量（已存在）")
