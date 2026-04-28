"""知识点提取 LLM 服务

支持三种模式从课程内容中提取知识点：
1. markdown - 从已解析的 Markdown 文档中提取
2. skeleton - 从教师手动输入的大纲文本中提取
3. combined - 结合两种来源进行提取

此服务返回草稿形式的知识点列表，不直接写入图数据库。
教师审核后通过 SyllabusGraphService 正式保存。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.resource import AioS3Client

logger = logging.getLogger(__name__)

_KP_EXTRACT_PROMPT = """\
你是一个专业的课程知识结构分析助手。请从以下课程内容中提取独立的知识点。

# 提取要求
1. 每个知识点应是一个独立的、可学习的概念或技能单元。
2. 知识点标题应简洁明确（5-20字）。
3. 知识点描述应说明该知识点的核心内容（30-100字）。
4. 重要程度（1-5）：1=补充了解，3=一般掌握，5=必须掌握。
5. 去除重复知识点，合并相似概念。
6. 最多提取 30 个知识点，专注于核心概念。

# 课程内容
{content}

# 输出格式（严格 JSON）
{{
  "knowledge_points": [
    {{
      "title": "知识点标题",
      "description": "知识点描述",
      "importance": 3,
      "confidence": 0.9
    }}
  ]
}}
"""

_KP_COMBINED_PROMPT = """\
你是一个专业的课程知识结构分析助手。请综合以下两个来源提取独立的知识点。

# 来源1：教师大纲（权重更高，优先保留大纲中的知识点）
{skeleton}

# 来源2：课程文档（补充细节知识点）
{markdown}

# 提取要求
1. 优先保留大纲中的知识点，文档作为补充。
2. 每个知识点应是独立可学习的概念或技能单元。
3. 知识点标题应简洁（5-20字），描述清晰（30-100字）。
4. 重要程度（1-5）：1=补充了解，3=一般掌握，5=必须掌握。
5. 合并重复和相似概念，最多提取 40 个知识点。

# 输出格式（严格 JSON）
{{
  "knowledge_points": [
    {{
      "title": "知识点标题",
      "description": "知识点描述",
      "importance": 3,
      "confidence": 0.9
    }}
  ]
}}
"""


@dataclass
class KnowledgePointBO:
    """知识点业务对象（临时，未持久化）"""

    title: str
    description: str | None = None
    importance: int = 3
    confidence: float = 1.0
    source: str = "ai"


@dataclass
class KnowledgeExtractionResult:
    """知识点提取结果"""

    points: list[KnowledgePointBO] = field(default_factory=list)
    mode: str = "markdown"


def _build_chat_llm():
    """根据项目配置构建 LangChain ChatOpenAI 实例。"""
    from langchain_openai import ChatOpenAI

    from graphedu.common.config.manager import get_config

    cfg = get_config()
    lc_attr = cfg.model.chat.get_lc_attr()
    return ChatOpenAI(**lc_attr)


def _parse_llm_json(raw: str) -> dict:
    """从 LLM 响应中提取并解析 JSON。支持 Markdown 代码块包裹的情况。"""
    content = raw.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        # 移除首尾代码块标记
        start = 1 if lines[0].startswith("```") else 0
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        content = "\n".join(lines[start:end]).strip()
    return json.loads(content)


class KnowledgeExtractionService:
    """知识点提取服务

    提供从不同来源提取知识点的功能。
    提取结果为草稿，需经教师审核后才写入图数据库。
    """

    @staticmethod
    async def extract_from_markdown(
        resource_id: int,
        db: AsyncSession,
        s3_client,
    ) -> KnowledgeExtractionResult:
        """从已解析的 Markdown 文档中提取知识点。

        Args:
            resource_id: 章节 资料ID。
            db: 数据库会话（用于查询文档内容）。
            s3_client: S3 客户端（用于下载 Markdown 内容）。

        Returns:
            KnowledgeExtractionResult: 包含提取的知识点草稿列表。
        """
        from graphedu.mapper.education.chapter_resource import ChapterResourceMapper

        resource = await ChapterResourceMapper.get_by_id(resource_id, db)
        if not resource:
            logger.warning(f"资源 {resource_id} 不存在，跳过提取")
            return KnowledgeExtractionResult(points=[], mode="markdown")

        # 从 resource_data 获取 markdown_s3_key
        resource_data = resource.resource_data or {}
        markdown_s3_key = resource_data.get("markdown_s3_key")
        if not markdown_s3_key:
            logger.warning(f"资源 {resource_id} 尚未解析，无 Markdown 内容")
            return KnowledgeExtractionResult(points=[], mode="markdown")

        # 从 S3 下载内容
        bytesio = await s3_client.download_to_bytesio(markdown_s3_key)
        content = bytesio.read().decode("utf-8")

        # Markdown 内容过长时截断（LLM token 限制）
        content = content[:12000] if len(content) > 12000 else content
        return await KnowledgeExtractionService._extract_from_text(content, mode="markdown")

    @staticmethod
    async def extract_from_skeleton(
        skeleton_text: str,
    ) -> KnowledgeExtractionResult:
        """从教师手动输入的大纲文本中提取知识点。

        Args:
            skeleton_text: 大纲文本（章节标题、要点等自由格式文本）。

        Returns:
            KnowledgeExtractionResult: 包含提取的知识点草稿列表。
        """
        return await KnowledgeExtractionService._extract_from_text(skeleton_text, mode="skeleton")

    @staticmethod
    async def extract_combined(
        resource_id: int | None,
        skeleton_text: str,
        db: AsyncSession,
        s3_client: AioS3Client,
    ) -> KnowledgeExtractionResult:
        """结合 Markdown 文档与大纲文本提取知识点。

        Args:
            resource_id: 章节 资料ID（可为 None，此时退化为纯大纲模式）。
            skeleton_text: 大纲文本。
            db: 数据库会话。
            s3_client: S3 客户端（用于下载 Markdown 内容）。

        Returns:
            KnowledgeExtractionResult: 包含提取的知识点草稿列表。
        """
        from graphedu.mapper.education.chapter_resource import ChapterResourceMapper

        markdown_content = ""
        if resource_id:
            resource = await ChapterResourceMapper.get_by_id(resource_id, db)
            if resource:
                resource_data = resource.resource_data or {}
                markdown_s3_key = resource_data.get("markdown_s3_key")
                if markdown_s3_key:
                    bytesio = await s3_client.download_to_bytesio(markdown_s3_key)
                    full_content = bytesio.read().decode("utf-8")
                    markdown_content = full_content[:8000]

        if not markdown_content:
            # 退化为纯大纲模式
            return await KnowledgeExtractionService.extract_from_skeleton(skeleton_text)

        return await KnowledgeExtractionService._extract_combined_internal(skeleton_text, markdown_content)

    @staticmethod
    async def _extract_from_text(content: str, mode: str) -> KnowledgeExtractionResult:
        """通用文本提取实现。"""
        llm = _build_chat_llm()
        prompt = _KP_EXTRACT_PROMPT.format(content=content)
        try:
            response = await llm.ainvoke(prompt)
            parsed = _parse_llm_json(response.content)
            raw_points = parsed.get("knowledge_points", [])
        except Exception as e:
            logger.error(f"知识点提取 LLM 调用失败: {e}")
            return KnowledgeExtractionResult(points=[], mode=mode)

        points = [
            KnowledgePointBO(
                title=item.get("title", ""),
                description=item.get("description"),
                importance=max(1, min(5, int(item.get("importance", 3)))),
                confidence=float(item.get("confidence", 1.0)),
                source="ai",
            )
            for item in raw_points
            if item.get("title")
        ]
        logger.info(f"[{mode}] 提取知识点 {len(points)} 个")
        return KnowledgeExtractionResult(points=points, mode=mode)

    @staticmethod
    async def _extract_combined_internal(skeleton: str, markdown: str) -> KnowledgeExtractionResult:
        """结合大纲和文档的双来源提取。"""
        llm = _build_chat_llm()
        prompt = _KP_COMBINED_PROMPT.format(skeleton=skeleton, markdown=markdown)
        try:
            response = await llm.ainvoke(prompt)
            parsed = _parse_llm_json(response.content)
            raw_points = parsed.get("knowledge_points", [])
        except Exception as e:
            logger.error(f"组合知识点提取 LLM 调用失败: {e}")
            return KnowledgeExtractionResult(points=[], mode="combined")

        points = [
            KnowledgePointBO(
                title=item.get("title", ""),
                description=item.get("description"),
                importance=max(1, min(5, int(item.get("importance", 3)))),
                confidence=float(item.get("confidence", 1.0)),
                source="ai",
            )
            for item in raw_points
            if item.get("title")
        ]
        logger.info(f"[combined] 提取知识点 {len(points)} 个")
        return KnowledgeExtractionResult(points=points, mode="combined")
