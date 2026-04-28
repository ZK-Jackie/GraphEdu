"""GraphRAG 任务相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class GraphRAGTaskQueryDTO(PageQuery):
    """GraphRAG 任务查询 DTO"""

    course_id: int = Field(description="课程ID")
    task_id: int | None = Field(default=None, description="任务ID")
    task_status: Literal["pending", "processing", "success", "failed", "cancelled"] | None = Field(
        default=None, description="任务状态（pending待处理/processing处理中/success成功/failed失败/cancelled已取消）"
    )
    task_type: str | None = Field(default=None, description="任务类型（如：graphrag_build构建、graphrag_update更新等）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class GraphRAGTaskCreateDTO(DTO):
    """创建 GraphRAG 任务 DTO

    用于创建新的 GraphRAG 任务记录

    Attributes:
        course_id: 关联课程ID
        resource_ids: 处理的文档ID列表
        task_type: 任务类型（如：graphrag_build构建、graphrag_update更新等）
        entity_types: 涉及的实体类型列表（可选）
        prompt_template: 使用的提示词模板（可选）
        custom_prompt_template: 自定义提示词模板（可选）
    """

    course_id: int = Field(description="关联课程ID")
    resource_ids: list[int] = Field(min_length=1, description="处理的文档ID列表")
    task_type: str = Field(
        min_length=1, max_length=32, description="任务类型（如：graphrag_build构建、graphrag_update更新等）"
    )
    entity_types: list[str] | None = Field(default=None, description="涉及的实体类型列表（可选）")
    prompt_template: str | None = Field(default=None, max_length=255, description="使用的提示词模板（可选）")
    custom_prompt_template: dict | None = Field(default=None, description="自定义提示词模板（可选）")


class GraphRAGTaskUpdateDTO(DTO):
    """更新 GraphRAG 任务 DTO

    用于更新 GraphRAG 任务信息

    Attributes:
        task_id: 任务ID
        task_status: 任务状态（可选）
        task_message: 任务最后信息（可选）
        entity_types: 涉及的实体类型列表（可选）
        prompt_template: 使用的提示词模板（可选）
        custom_prompt_template: 自定义提示词模板（可选）
        stats: 任务统计信息（可选）
        start_time: 任务开始时间（可选）
        end_time: 任务结束时间（可选）
    """

    task_id: int = Field(description="任务ID")
    task_status: Literal["pending", "processing", "success", "failed", "cancelled"] | None = Field(
        default=None, description="任务状态（pending待处理/processing处理中/success成功/failed失败/cancelled已取消）"
    )
    task_message: str | None = Field(default=None, description="任务最后信息（如果任务失败，记录错误详情）")
    entity_types: list[str] | None = Field(default=None, description="涉及的实体类型列表（可选）")
    prompt_template: str | None = Field(default=None, max_length=255, description="使用的提示词模板（可选）")
    custom_prompt_template: dict | None = Field(default=None, description="自定义提示词模板（可选）")
    stats: dict | None = Field(default=None, description="任务统计信息（JSONB格式，可选）")
    start_time: datetime | None = Field(default=None, description="任务开始时间")
    end_time: datetime | None = Field(default=None, description="任务结束时间")


class GraphRAGBuildCreateDTO(DTO):
    """GraphRAG 索引构建请求 DTO

    用于教师为已文本化的教学资源构建 GraphRAG 知识图谱索引

    Attributes:
        course_id: 课程ID
        resource_ids: 资源ID列表
        entity_types: 实体类型列表（预设选项：概念、原理、方法、公式、例题、定义、定理等，支持自定义）
        prompt_template: 提示词模板（default/en、default/zh、edu/en、edu/zh）
    """

    course_id: int = Field(description="课程ID")
    resource_ids: list[int] = Field(min_length=1, description="资源ID列表")
    entity_types: list[str] = Field(min_length=1, description="实体类型列表")
    prompt_template: Literal["default/en", "default/zh", "edu/en", "edu/zh"] = Field(
        default="edu/zh", description="提示词模板"
    )


class GraphRAGResourceQueryDTO(PageQuery):
    """可构建 GraphRAG 的资源查询 DTO

    用于查询课程下可构建 GraphRAG 的资源

    Attributes:
        course_id: 课程ID
        parse_status: 文本化状态（固定为 '2'，用于文档类型资源）
        include_text_directly: 是否包含 text 类型直通资源（无需文本化）
        resource_name: 资源名称模糊搜索
    """

    course_id: int = Field(description="课程ID")
    parse_status: Literal["2"] = Field(default="2", description="文档类型仅查询已文本化资源")
    include_text_directly: bool = Field(default=True, description="是否包含 text 类型直通资源")
    resource_name: str | None = Field(default=None, description="资源名称模糊搜索")
