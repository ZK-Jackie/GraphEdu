"""知识点依赖关系推断服务

通过 LLM 分析知识点列表，推断知识点之间的逻辑依赖关系。

支持的关系类型：
- PRIOR_TO: A 是 B 的前置知识（学 B 之前必须先学 A）
- RELATED_TO: A 与 B 相关（内容相关，但无严格前置依赖）
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)

_DEP_INFER_PROMPT = """\
你是一个专业的课程知识结构分析助手。请分析以下知识点列表，推断它们之间的逻辑依赖关系。

# 知识点列表
{points_text}

# 关系类型说明
- PRIOR_TO: 前置依赖（必须先掌握源知识点，才能学习目标知识点）
- RELATED_TO: 相关关系（两个知识点内容相关，但无强制前置要求）

# 推断要求
1. 只推断有意义的关系，不要强行关联所有知识点。
2. PRIOR_TO 关系的置信度（0-1）表示该依赖的确定程度。
3. RELATED_TO 关系表示知识点间的知识关联。
4. source 和 target 必须与上方列表中的标题完全一致。
5. 避免循环依赖（A→B→C→A）。
6. 总关系数不超过知识点数量的 2 倍。

# 输出格式（严格 JSON）
{{
  "relationships": [
    {{
      "source_title": "源知识点标题",
      "target_title": "目标知识点标题",
    "relation_type": "PRIOR_TO",
      "confidence": 0.9
    }}
  ]
}}
"""


@dataclass
class KnowledgeRelationshipBO:
    """知识点关系业务对象（临时，未持久化）"""

    source_title: str
    target_title: str
    relation_type: str  # "RELATED_TO" | "PRIOR_TO" | "SUBTOPIC_OF"
    confidence: float = 1.0
    description: str | None = None


@dataclass
class DependencyInferenceResult:
    """依赖关系推断结果"""

    relationships: list[KnowledgeRelationshipBO] = field(default_factory=list)


def _build_chat_llm():
    """根据项目配置构建 LangChain ChatOpenAI 实例。"""
    from langchain_openai import ChatOpenAI

    from graphedu.common.config.manager import get_config

    cfg = get_config()
    lc_attr = cfg.model.chat.get_lc_attr()
    return ChatOpenAI(**lc_attr)


def _parse_llm_json(raw: str) -> dict:
    """从 LLM 响应中提取 JSON，支持 Markdown 代码块包裹。"""
    content = raw.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        start = 1 if lines[0].startswith("```") else 0
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        content = "\n".join(lines[start:end]).strip()
    return json.loads(content)


class DependencyInferenceService:
    """知识点依赖关系推断服务"""

    @staticmethod
    async def infer_dependencies(
        point_titles: list[str],
    ) -> DependencyInferenceResult:
        """推断知识点之间的依赖关系。

        Args:
            point_titles: 知识点标题列表（与提取结果一致）。

        Returns:
            DependencyInferenceResult: 包含推断的关系列表（草稿，未持久化）。
        """
        if not point_titles:
            return DependencyInferenceResult()

        # 构建编号列表文本
        points_text = "\n".join(f"{i + 1}. {title}" for i, title in enumerate(point_titles))
        llm = _build_chat_llm()
        prompt = _DEP_INFER_PROMPT.format(points_text=points_text)

        try:
            response = await llm.ainvoke(prompt)
            parsed = _parse_llm_json(response.content)
            raw_rels = parsed.get("relationships", [])
        except Exception as e:
            logger.error(f"依赖关系推断 LLM 调用失败: {e}")
            return DependencyInferenceResult()

        # 合法标题集合（用于校验 LLM 输出）
        valid_titles = set(point_titles)
        relationships = []
        for item in raw_rels:
            src = item.get("source_title", "").strip()
            tgt = item.get("target_title", "").strip()
            rel = item.get("relation_type", "RELATED_TO").upper()
            conf = float(item.get("confidence", 1.0))

            # 只保留合法标题和关系类型
            if src not in valid_titles or tgt not in valid_titles:
                continue
            if rel == "PREREQUISITE":
                rel = "PRIOR_TO"
            if rel not in ("PRIOR_TO", "RELATED_TO", "SUBTOPIC_OF"):
                rel = "RELATED_TO"
            if src == tgt:
                continue

            relationships.append(
                KnowledgeRelationshipBO(
                    source_title=src,
                    target_title=tgt,
                    relation_type=rel,
                    confidence=max(0.0, min(1.0, conf)),
                )
            )

        logger.info(f"推断出 {len(relationships)} 条关系")
        return DependencyInferenceResult(relationships=relationships)
