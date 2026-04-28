"""GraphRAG 服务层

封装 Microsoft GraphRAG 的索引构建与查询能力。

提供以下功能：
- global_search：基于全局社区摘要的检索（适用于跨章节综合问答）
- local_search：基于局部实体的检索（适用于精确知识点查询）
- drift_search：结合全局与局部的混合检索（适用于复杂综合问题）
- basic_search：基于文本块向量检索的简易模式（适用于简单文档片段召回）
- generate_chapter_description：调用 local_search 自动生成章节描述
"""

import asyncio
from dataclasses import dataclass, field
import io
import logging
from pathlib import Path

import anyio
from graphrag.config.defaults import DEFAULT_COMPLETION_MODEL_ID, DEFAULT_EMBEDDING_MODEL_ID
from graphrag.config.enums import AsyncType, ReportingType
from graphrag.config.models.basic_search_config import BasicSearchConfig
from graphrag.config.models.community_reports_config import CommunityReportsConfig
from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.config.models.embed_text_config import EmbedTextConfig
from graphrag.config.models.extract_claims_config import ExtractClaimsConfig
from graphrag.config.models.extract_graph_config import ExtractGraphConfig
from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.config.models.global_search_config import GlobalSearchConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.local_search_config import LocalSearchConfig
from graphrag.config.models.reporting_config import ReportingConfig
from graphrag.config.models.summarize_descriptions_config import SummarizeDescriptionsConfig
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.factory import (
    get_basic_search_engine,
    get_drift_search_engine,
    get_global_search_engine,
    get_local_search_engine,
)
from graphrag.query.indexer_adapters import (
    read_indexer_communities,
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_report_embeddings,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.structured_search.basic_search.search import BasicSearch
from graphrag.query.structured_search.global_search.search import GlobalSearch, GlobalSearchResult
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag_cache import CacheConfig, CacheType
from graphrag_chunking.chunk_strategy_type import ChunkerType
from graphrag_chunking.chunking_config import ChunkingConfig
from graphrag_input import InputConfig, InputType
from graphrag_llm.config import ModelConfig, RateLimitConfig, RetryConfig, RetryType
from graphrag_pgvector import (
    PgVectorStoreConfig,
    PostgresStorage,
    PostgresVectorStore,
    register_graphrag_pgvector,
    register_graphrag_pgvector_storage,
)
from graphrag_pgvector.config import PgStorageConfig
from graphrag_storage import StorageConfig, StorageType
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import pandas as pd
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from graphedu.common import get_config
from graphedu.common.exceptions.services.education import GraphRAGException
from graphedu.common.models.bo.graphrag import GraphEdgeBO, GraphNodeBO, VisualGraphBO
from graphedu.common.utils import try_parse_json_object

register_graphrag_pgvector_storage()
register_graphrag_pgvector()

logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================


@dataclass
class GraphRAGSearchResult:
    """GraphRAG 检索结果"""

    answer: str
    """生成的回答文本"""

    sources: list[dict] = field(default_factory=list)
    """引用来源列表"""

    context_data: dict = field(default_factory=dict)
    """上下文数据（调试用）"""

    search_type: str = "local"
    """检索类型：'local' | 'global' | 'drift' | 'basic'"""


@dataclass
class GraphRAGBuildResult:
    """GraphRAG 索引构建结果"""

    entity_count: int = 0
    relation_count: int = 0
    community_count: int = 0
    chunk_count: int = 0
    output_dir: str = ""


# ============================================================================
# 内部工具：从 PostgresStorage 读取 GraphRAG artifact
# ============================================================================

# graphrag pipeline 写入 output_storage 时使用的 artifact 键名，
# 与 graphrag 默认输出文件名保持一致
_ARTIFACT_KEYS: tuple[str, ...] = (
    "entities.parquet",
    "communities.parquet",
    "community_reports.parquet",
    "relationships.parquet",
    "text_units.parquet",
    "covariates.parquet",
)


async def _load_all_dataframes_from_storage(namespace: str) -> dict:
    """从 PostgresStorage 读取所有 GraphRAG artifact，返回名称 → DataFrame 字典。

    每个 artifact 将存储在 ``graphrag_storage`` 表中，
    namespace = str(graphrag_task_id)，key = '<artifact>.parquet'。
    若对应 key 不存在，则对应 DataFrame 为空。
    """
    cfg = get_config()
    storage = PostgresStorage(
        connection_string=str(cfg.datasource.postgresql.dsn),
        table_name="public.graphrag_storage",
        namespace=namespace,
    )

    result: dict = {}
    for key in _ARTIFACT_KEYS:
        name = key.replace(".parquet", "")  # e.g. "entities"
        raw: bytes | None = await storage.get(key, as_bytes=True)
        if raw:
            try:
                result[name] = pd.read_parquet(io.BytesIO(raw))
                logger.debug("[GraphRAG] 已加载 %s（%d 行）", key, len(result[name]))
            except Exception as exc:
                logger.warning("[GraphRAG] 解析 %s 失败，使用空 DataFrame: %s", key, exc)
                result[name] = pd.DataFrame()
        else:
            logger.debug("[GraphRAG] artifact 不存在，跳过: namespace=%s key=%s", namespace, key)
            result[name] = pd.DataFrame()
    return result


def _extract_sources(context_data) -> list[dict]:
    """从 GraphRAG SearchResult.context_data 提取引用来源列表。

    context_data 通常是 dict[str, DataFrame]，从中提取实体或社区报告作为来源。
    """
    if not isinstance(context_data, dict):
        return []
    sources: list[dict] = []
    # 从 entities DataFrame 提取（Local Search）
    entities_df = context_data.get("entities")
    if entities_df is not None and not entities_df.empty:
        for _, row in entities_df.head(5).iterrows():
            sources.append(
                {
                    "id": str(row.get("id", "")),
                    "title": str(row.get("entity", "")),
                    "description": str(row.get("description", "")),
                }
            )
    # 从 community reports DataFrame 提取（Global Search / Local Search community context）
    reports_df = context_data.get("reports")
    if reports_df is not None and not reports_df.empty:
        for _, row in reports_df.head(5).iterrows():
            sources.append(
                {
                    "id": str(row.get("id", "")),
                    "title": str(row.get("title", "")),
                    "description": str(row.get("summary", row.get("content", ""))),
                }
            )
    return sources


def _build_vector_store(namespace: str, index_name: str):
    """构建 PgVector 向量存储实例。

    Args:
        namespace: 向量存储的命名空间（通常为 graphrag_task_id）。
        index_name: 向量索引名称，对应 GraphRAG 内部的嵌入集合名称。
    """
    cfg = get_config()
    store = PostgresVectorStore(
        connection_string=str(cfg.datasource.postgresql.dsn),
        table_name="public.graphrag_vectors",
        namespace=namespace,
        index_name=index_name,
        vector_size=cfg.graphrag.embeddings.dimensions,
    )
    store.connect()
    logger.debug(
        "[GraphRAG] 使用 PgVector 向量存储: namespace=%s, index=%s, vector_size=%d",
        namespace,
        index_name,
        store.vector_size,
    )
    return store


def _build_description_embedding_store(namespace: str):
    """构建用于 Local / DRIFT Search 的 description_embedding_store。"""
    return _build_vector_store(namespace, "entity_description")


def _build_text_unit_embedding_store(namespace: str):
    """构建用于 Basic Search 的 text_unit_text embedding store。"""
    return _build_vector_store(namespace, "text_unit_text")


def _build_full_content_embedding_store(namespace: str):
    """构建用于 DRIFT Search 的 community_full_content embedding store。"""
    return _build_vector_store(namespace, "community_full_content")


# ============================================================================
# Prompt 文件解析
# ============================================================================

# 需要从 prompt 模板目录中查找的 prompt 文件名列表
_PROMPT_FILENAMES: tuple[str, ...] = (
    # 索引阶段
    "extract_graph.txt",
    "community_report_graph.txt",
    "community_report_text.txt",
    "summarize_descriptions.txt",
    "extract_claims.txt",
    # 搜索阶段
    "local_search_system_prompt.txt",
    "global_search_map_system_prompt.txt",
    "global_search_reduce_system_prompt.txt",
    "global_search_knowledge_system_prompt.txt",
    "drift_search_system_prompt.txt",
    "drift_search_reduce_prompt.txt",
    "basic_search_system_prompt.txt",
)


def _resolve_prompt_files(
    prompt_repo_dir: str,
    prompt_template: str | None,
) -> dict[str, str]:
    """根据 prompt_template 子目录解析所有可用的 prompt 文件。

    Args:
        prompt_repo_dir: prompt 模板根目录（如 ``data/prompts``）。
        prompt_template: 用户选择的模板子目录（如 ``edu/zh``），
                         为 ``None`` 时返回空字典，使用 GraphRAG 内置默认值。

    Returns:
        dict[str, str]: 文件名 → 绝对路径 的映射，仅包含实际存在的文件。
    """
    prompt_template = "edu/zh" if prompt_template is None else prompt_template
    prompt_dir = Path(prompt_repo_dir).resolve() / prompt_template
    if not prompt_dir.is_dir():
        logger.warning("[GraphRAG] prompt 模板目录不存在: %s", prompt_dir)
        return {}

    result: dict[str, str] = {}
    for filename in _PROMPT_FILENAMES:
        prompt_file = prompt_dir / filename
        if prompt_file.is_file():
            result[filename] = str(prompt_file)
        else:
            logger.debug("[GraphRAG] prompt 文件不存在，使用默认: %s", prompt_file)
    return result


# ============================================================================
# GraphRAGService
# ============================================================================


class GraphRAGService:
    """Microsoft GraphRAG 搜索服务封装。

    所有方法均为 async staticmethod，可直接 await 调用：

        result = await GraphRAGService.global_search("深度学习与机器学习的关系", task_id=1)
        result = await GraphRAGService.local_search("卷积神经网络", task_id=1)
        result = await GraphRAGService.drift_search("深度学习在NLP中的应用", task_id=1)
        result = await GraphRAGService.basic_search("什么是反向传播", task_id=1)
        desc   = await GraphRAGService.generate_chapter_description("卷积神经网络", task_id=1)
    """

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(result: GlobalSearchResult , search_type: str) -> "GraphRAGSearchResult":
        """将 GraphRAG SearchResult 转换为 GraphRAGSearchResult。"""
        return GraphRAGSearchResult(
            answer=result.response if isinstance(result.response, str) else str(result.response),
            sources=_extract_sources(result.context_data),
            context_data=getattr(result, "context_data", {}),
            search_type=search_type,
        )

    @staticmethod
    async def _search_with_retry(
        engine: GlobalSearch | LocalSearch | BasicSearch,
        query: str,
        search_type: str,
        history: ConversationHistory,
    ) -> "GraphRAGSearchResult | None":
        """对单个 query 执行搜索，使用 tenacity AsyncRetrying 处理瞬态故障。

        仅对 (TimeoutError, ConnectionError, OSError) 做指数退避重试（最多 3 次），
        其余异常直接捕获并返回 None。

        Args:
            engine: 已初始化的 GraphRAG SearchEngine 实例。
            query: 查询文本。
            search_type: 搜索类型标识。
            history: 对话历史。

        Returns:
            成功时返回 GraphRAGSearchResult，失败时返回 None。
        """
        result: GraphRAGSearchResult | None = None
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=2, min=2, max=30),
                retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
                before_sleep=lambda _: logger.debug(
                    "[GraphRAG] 搜索重试: type=%s, query='%s'", search_type, query
                ),
            ):
                with attempt:
                    raw = await engine.search(query=query, conversation_history=history)
                if not attempt.retry_state.outcome.failed:
                    result = GraphRAGService._build_result(raw, search_type=search_type)
                    attempt.retry_state.set_result(result)
        except Exception:
            logger.exception("[GraphRAG] 搜索最终失败: type=%s, query='%s'", search_type, query)
            return None
        return result

    @staticmethod
    async def _batch_search(
        engine,
        queries: list[str],
        search_type: str,
        conversation_history: list[dict] | None = None,
    ) -> list["GraphRAGSearchResult | None"]:
        """用已构建好的引擎对多个 query 并发搜索。

        内部为每个 query 调用 _search_with_retry，通过 asyncio.gather 并发执行。
        返回与 queries 等长的列表，单条失败时对应位置为 None。
        """
        history = ConversationHistory.from_list(conversation_history or [])
        return list(
            await asyncio.gather(
                *[GraphRAGService._search_with_retry(engine, q, search_type, history) for q in queries]
            )
        )

    # ------------------------------------------------------------------
    # Global Search
    # ------------------------------------------------------------------

    @staticmethod
    async def _build_global_search_engine(
        graphrag_task_id: int,
        prompt_template: str = "edu/zh",
    ):
        """构建 Global Search 引擎实例（供 global_search / global_search_batch 共用）。"""
        cfg = get_config()
        gr_cfg = cfg.graphrag
        namespace = str(graphrag_task_id)
        dfs = await _load_all_dataframes_from_storage(namespace)

        communities_ = read_indexer_communities(dfs["communities"], dfs["community_reports"])
        reports = read_indexer_reports(
            dfs["community_reports"],
            dfs["communities"],
            community_level=gr_cfg.community_level,
            dynamic_community_selection=False,
        )
        entities_ = read_indexer_entities(dfs["entities"], dfs["communities"], community_level=gr_cfg.community_level)

        graphrag_config = build_graphrag_config(namespace=namespace, entity_types=None, prompt_template=prompt_template)
        return get_global_search_engine(
            graphrag_config,
            reports=reports,
            entities=entities_,
            communities=communities_,
            response_type=gr_cfg.response_type,
            dynamic_community_selection=False,
            map_system_prompt=await anyio.Path(graphrag_config.global_search.map_prompt).read_text(encoding="utf-8")
            if graphrag_config.global_search.map_prompt
            else None,
            reduce_system_prompt=await anyio.Path(graphrag_config.global_search.reduce_prompt).read_text(
                encoding="utf-8"
            )
            if graphrag_config.global_search.reduce_prompt
            else None,
            general_knowledge_inclusion_prompt=await anyio.Path(
                graphrag_config.global_search.knowledge_prompt
            ).read_text(encoding="utf-8")
            if graphrag_config.global_search.knowledge_prompt
            else None,
        )

    @staticmethod
    async def global_search(
        query: str,
        graphrag_task_id: int,
        conversation_history: list[dict] | None = None,
        prompt_template: str = "edu/zh",
    ) -> GraphRAGSearchResult | None:
        """Global Search：基于全局社区摘要的检索（单条）。"""
        logger.info("[GraphRAG] Global Search: query='%s', task_id=%d", query, graphrag_task_id)
        engine = await GraphRAGService._build_global_search_engine(graphrag_task_id, prompt_template)
        history = ConversationHistory.from_list(conversation_history or [])
        return await GraphRAGService._search_with_retry(engine, query, "global", history)

    @staticmethod
    async def global_search_batch(
        queries: list[str],
        graphrag_task_id: int,
        conversation_history: list[dict] | None = None,
        prompt_template: str = "edu/zh",
    ) -> list[GraphRAGSearchResult | None]:
        """批量 Global Search：构建一次引擎，对多个 query 并发检索。"""
        logger.info("[GraphRAG] Global Search Batch: %d queries, task_id=%d", len(queries), graphrag_task_id)
        engine = await GraphRAGService._build_global_search_engine(graphrag_task_id, prompt_template)
        return await GraphRAGService._batch_search(engine, queries, "global", conversation_history)

    # ------------------------------------------------------------------
    # Local Search
    # ------------------------------------------------------------------

    @staticmethod
    async def _build_local_search_engine(
        graphrag_task_id: int,
        prompt_template: str = "edu/zh",
    ):
        """构建 Local Search 引擎实例（供 local_search / local_search_batch 共用）。"""
        cfg = get_config()
        gr_cfg = cfg.graphrag
        namespace = str(graphrag_task_id)
        dfs = await _load_all_dataframes_from_storage(namespace)

        entities_ = read_indexer_entities(dfs["entities"], dfs["communities"], community_level=gr_cfg.community_level)
        reports = read_indexer_reports(
            dfs["community_reports"],
            dfs["communities"],
            community_level=gr_cfg.community_level,
        )
        relationships_ = read_indexer_relationships(dfs["relationships"])
        text_units_ = read_indexer_text_units(dfs["text_units"])
        covariates_: dict = {"claims": []}
        if not dfs["covariates"].empty:
            covariates_ = {"claims": read_indexer_covariates(dfs["covariates"])}

        graphrag_config = build_graphrag_config(namespace=namespace, entity_types=None, prompt_template=prompt_template)
        description_embedding_store = _build_description_embedding_store(namespace)

        return get_local_search_engine(
            graphrag_config,
            reports=reports,
            text_units=text_units_,
            entities=entities_,
            relationships=relationships_,
            covariates=covariates_,
            response_type=gr_cfg.response_type,
            description_embedding_store=description_embedding_store,
        )

    @staticmethod
    async def local_search(
        query: str,
        graphrag_task_id: int,
        conversation_history: list[dict] | None = None,
        prompt_template: str = "edu/zh",
    ) -> GraphRAGSearchResult | None:
        """Local Search：基于社区内局部实体的检索（单条）。"""
        logger.info("[GraphRAG] Local Search: query='%s', task_id=%d", query, graphrag_task_id)
        engine = await GraphRAGService._build_local_search_engine(graphrag_task_id, prompt_template)
        history = ConversationHistory.from_list(conversation_history or [])
        return await GraphRAGService._search_with_retry(engine, query, "local", history)

    @staticmethod
    async def local_search_batch(
        queries: list[str],
        graphrag_task_id: int,
        conversation_history: list[dict] | None = None,
        prompt_template: str = "edu/zh",
    ) -> list[GraphRAGSearchResult | None]:
        """批量 Local Search：构建一次引擎，对多个 query 并发检索。"""
        logger.info("[GraphRAG] Local Search Batch: %d queries, task_id=%d", len(queries), graphrag_task_id)
        engine = await GraphRAGService._build_local_search_engine(graphrag_task_id, prompt_template)
        return await GraphRAGService._batch_search(engine, queries, "local", conversation_history)

    # ------------------------------------------------------------------
    # DRIFT Search
    # ------------------------------------------------------------------

    @staticmethod
    async def drift_search(
        query: str,
        graphrag_task_id: int,
        conversation_history: list[dict] | None = None,
        prompt_template: str = "edu/zh",
    ) -> GraphRAGSearchResult | None:
        """DRIFT Search：结合全局与局部检索的混合模式。

        通过社区报告嵌入和实体嵌入进行多轮检索，兼顾全局视野和局部精度，
        适用于需要综合多个知识点的复杂问题。
        """
        cfg = get_config()
        gr_cfg = cfg.graphrag
        namespace = str(graphrag_task_id)
        dfs = await _load_all_dataframes_from_storage(namespace)

        logger.info("[GraphRAG] DRIFT Search: query='%s', task_id=%d", query, graphrag_task_id)

        entities_ = read_indexer_entities(dfs["entities"], dfs["communities"], community_level=gr_cfg.community_level)
        reports = read_indexer_reports(
            dfs["community_reports"],
            dfs["communities"],
            community_level=gr_cfg.community_level,
        )

        full_content_embedding_store = _build_full_content_embedding_store(namespace)
        read_indexer_report_embeddings(reports, full_content_embedding_store)

        description_embedding_store = _build_description_embedding_store(namespace)
        graphrag_config = build_graphrag_config(namespace=namespace, entity_types=None, prompt_template=prompt_template)

        engine = get_drift_search_engine(
            graphrag_config,
            reports=reports,
            text_units=read_indexer_text_units(dfs["text_units"]),
            entities=entities_,
            relationships=read_indexer_relationships(dfs["relationships"]),
            description_embedding_store=description_embedding_store,
            response_type=gr_cfg.response_type,
        )

        history = ConversationHistory.from_list(conversation_history or [])
        return await GraphRAGService._search_with_retry(engine, query, "drift", history)

    # ------------------------------------------------------------------
    # Basic Search
    # ------------------------------------------------------------------

    @staticmethod
    async def basic_search(
        query: str,
        graphrag_task_id: int,
        conversation_history: list[dict] | None = None,
        prompt_template: str = "edu/zh",
    ) -> GraphRAGSearchResult | None:
        """Basic Search：基于文本块向量检索的简易模式。

        直接对 text_unit 进行向量相似度检索，不涉及知识图谱结构，
        适用于简单的文档片段召回场景。
        """
        cfg = get_config()
        gr_cfg = cfg.graphrag
        namespace = str(graphrag_task_id)
        dfs = await _load_all_dataframes_from_storage(namespace)

        logger.info("[GraphRAG] Basic Search: query='%s', task_id=%d", query, graphrag_task_id)

        text_units_ = read_indexer_text_units(dfs["text_units"])
        text_unit_embedding_store = _build_text_unit_embedding_store(namespace)
        graphrag_config = build_graphrag_config(namespace=namespace, entity_types=None, prompt_template=prompt_template)

        engine = get_basic_search_engine(
            text_units=text_units_,
            text_unit_embeddings=text_unit_embedding_store,
            config=graphrag_config,
            response_type=gr_cfg.response_type,
        )

        history = ConversationHistory.from_list(conversation_history or [])
        return await GraphRAGService._search_with_retry(engine, query, "basic", history)

    # ------------------------------------------------------------------
    # 章节描述生成
    # ------------------------------------------------------------------

    @staticmethod
    async def generate_chapter_description(
        chapter_name: str,
        graphrag_task_id: int,
        prompt_template: str = "edu/zh",
    ) -> str:
        """利用 GraphRAG Local Search 自动生成章节描述。

        以章节名称为查询，通过 Local Search 检索相关知识点，
        返回 LLM 生成的简洁章节描述。

        Args:
            chapter_name: 章节名称（作为检索查询词）。
            graphrag_task_id: EduGraphRAGTask 主键 ID，定位该章节对应的 PG 存储数据。
            prompt_template: Prompt 模板子目录（相对于 prompt_repo_dir），默认 ``"edu/zh"``。

        Returns:
            str: 生成的章节描述文本；检索失败时返回空字符串。
        """
        query = f"请简要介绍《{chapter_name}》的主要内容，用于学习平台的章节描述，100 到 200 字。"
        logger.info(
            "[GraphRAG] 生成章节描述: chapter_name='%s', task_id=%d",
            chapter_name,
            graphrag_task_id,
        )
        result = await GraphRAGService.local_search(
            query, graphrag_task_id=graphrag_task_id, prompt_template=prompt_template
        )
        if not result.answer:
            logger.warning("[GraphRAG] 章节描述生成失败（local_search 无结果）: '%s'", chapter_name)
        return result.answer

    # ------------------------------------------------------------------
    # 教学知识图谱生成（分阶段流水线）
    # ------------------------------------------------------------------

    @staticmethod
    async def generate_visual_graph(
        graphrag_task_id: int,
        chapter_names: list[str],
        *,
        batch_size: int = 15,
    ) -> "VisualGraphBO":
        """利用 GraphRAG 分阶段自动生成教学图谱节点与连边。

        每个阶段只构建一次搜索引擎、只加载一次 storage，所有 query 并发执行。
        """
        if not chapter_names:
            raise GraphRAGException(message="章节列表为空，无法生成知识图谱")

        # ── Phase 1: 章节级概念提取（一次 batch global search）──────────────
        logger.info(
            "[GraphRAG] 教学图谱生成 Phase 1: task_id=%d, %d 个章节",
            graphrag_task_id,
            len(chapter_names),
        )

        phase1_queries = [
            f"《{name}》章节中涉及的核心教学概念、算法或理论等关键实体有哪些？请逐一列举。" for name in chapter_names
        ]
        phase1_search_results = await GraphRAGService.global_search_batch(
            queries=phase1_queries,
            graphrag_task_id=graphrag_task_id,
        )

        # 并发 LLM 提取概念（含描述）
        async def _extract_concepts(search_result):
            if search_result is None:
                return []
            response_text = search_result.answer or ""
            if not response_text:
                return []
            prompt = (
                "你是一个文本分析助手。以下是一段关于教学章节内容的描述，"
                "请从中提取所有核心教学概念、算法或理论，"
                "以 JSON 数组格式输出，每项包含 name（名称）和 description（一句话简介）两个字段。\n\n"
                '示例：[{"name": "递归", "description": "函数调用自身的编程技术"}]\n'
                "只输出 JSON 数组，不要输出其他内容。\n\n"
                f"文本内容：\n{response_text}"
            )
            _, parsed = await GraphRAGService._llm_structured_extract(prompt, expect_type=list)
            if not isinstance(parsed, list):
                return []
            results = []
            for item in parsed:
                if isinstance(item, dict) and item.get("name"):
                    results.append({
                        "name": str(item["name"]).strip(),
                        "description": str(item.get("description", "")).strip(),
                    })
                elif isinstance(item, str) and item.strip():
                    results.append({"name": item.strip(), "description": ""})
            return results

        chapter_results = await asyncio.gather(
            *[_extract_concepts(sr) for sr in phase1_search_results],
            return_exceptions=True,
        )

        # 汇总：构建 concept_name → {description, chapter_indices} 映射
        concept_map: dict[str, dict] = {}  # name → {"description": str, "chapter_indices": set[int]}
        for idx, result in enumerate(chapter_results):
            if isinstance(result, Exception):
                logger.warning("[GraphRAG] 章节 '%s' 概念提取失败（跳过）: %s", chapter_names[idx], result)
                continue
            for item in result:
                name = item["name"]
                if not name:
                    continue
                if name not in concept_map:
                    concept_map[name] = {"description": item["description"], "chapter_indices": {idx}}
                else:
                    concept_map[name]["chapter_indices"].add(idx)
                    # 保留最长的描述
                    if len(item["description"]) > len(concept_map[name]["description"]):
                        concept_map[name]["description"] = item["description"]

        # 去重（忽略大小写合并）
        concept_map = GraphRAGService._deduplicate_concepts(concept_map)

        if not concept_map:
            raise GraphRAGException(message="未能从任何章节中提取到教学概念，请检查课程资源内容")

        logger.info("[GraphRAG] Phase 1 完成: %d 个去重概念", len(concept_map))
        concept_names_ordered = list(concept_map.keys())
        concept_to_id: dict[str, int] = {name: idx + 1 for idx, name in enumerate(concept_names_ordered)}

        # ── Phase 2: 分批关系推断（一次 batch global search）────────────────
        concept_names = list(concept_to_id.keys())
        batches = [concept_names[i : i + batch_size] for i in range(0, len(concept_names), batch_size)]

        logger.info("[GraphRAG] Phase 2: %d 个概念, %d 批", len(concept_names), len(batches))

        phase2_queries = [
            f"在教学概念【{'、'.join(batch)}】中，"
            "哪些概念之间存在先修关系（学习B之前必须先掌握A）"
            "或包含关系（A是B的子主题或组成部分）？请具体说明。"
            for batch in batches
        ]
        phase2_search_results = await GraphRAGService.global_search_batch(
            queries=phase2_queries,
            graphrag_task_id=graphrag_task_id,
        )

        # 并发 LLM 提取关系（含描述）
        async def _extract_edges(search_result):
            if search_result is None:
                return []
            response_text = search_result.answer or ""
            if not response_text:
                return []
            prompt = (
                "你是一个文本分析助手。以下是一段关于教学概念间关系的描述。"
                "请从中提取所有存在关系的概念对，以 JSON 数组格式输出。每项包含四个字段：\n"
                "- source: 源概念名称（字符串）\n"
                "- target: 目标概念名称（字符串）\n"
                "- type: 关系类型，只能是 PRIOR_TO（先修关系）或 SUBTOPIC_OF（包含关系）\n"
                "- description: 一句话描述该关系的具体含义\n\n"
                '示例：[{"source": "递归", "target": "排序算法", '
                '"type": "PRIOR_TO", "description": "理解递归是学习排序算法的前提"}]\n'
                "如果没有发现任何关系，输出空数组 []。只输出 JSON 数组，不要输出其他内容。\n\n"
                f"文本内容：\n{response_text}"
            )
            _, parsed = await GraphRAGService._llm_structured_extract(prompt, expect_type=list)
            if not isinstance(parsed, list):
                return []
            return [item for item in parsed if isinstance(item, dict) and "source" in item and "target" in item]

        batch_results = await asyncio.gather(
            *[_extract_edges(sr) for sr in phase2_search_results],
            return_exceptions=True,
        )

        all_edges_raw: list[dict] = []
        for idx, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.warning("[GraphRAG] 关系推断第 %d/%d 批失败: %s", idx + 1, len(batches), result)
                continue
            all_edges_raw.extend(result)

        logger.info("[GraphRAG] Phase 2 完成: %d 条关系", len(all_edges_raw))

        # ── 组装结果 ─────────────────────────────────────────────────────
        nodes = [
            GraphNodeBO(
                id=cid,
                label=name,
                description=concept_map[name].get("description") or None,
                chapter_indices=sorted(concept_map[name].get("chapter_indices", set())),
            )
            for name, cid in concept_to_id.items()
        ]
        edges = GraphRAGService._resolve_edges(all_edges_raw, concept_to_id)
        return VisualGraphBO(nodes=nodes, edges=edges)

    # ── LLM 结构化提取 ─────────────────────────────────────────────────────

    @staticmethod
    async def _llm_structured_extract(
        prompt: str,
        expect_type: type[dict | list] = list,
    ) -> tuple[str, dict | list | None]:
        """调用 LLM 对文本做结构化提取，返回 (raw_text, parsed_object)。

        使用 graphrag.llm 配置实例化 ChatOpenAI，让 LLM 输出 JSON，
        再通过 try_parse_json_object 解析。
        使用 tenacity AsyncRetrying 做指数退避重试（最多 3 次）。
        """
        cfg = get_config()
        lc_kwargs = cfg.graphrag.llm.get_lc_attr()
        llm = ChatOpenAI(**lc_kwargs)

        result: tuple[str, dict | list | None] | None = None
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=2, min=2, max=30),
            retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
            before_sleep=lambda _: logger.debug("[GraphRAG] LLM 结构化提取重试中..."),
        ):
            with attempt:
                response = await llm.ainvoke([HumanMessage(content=prompt)])
                raw = response.content if isinstance(response.content, str) else str(response.content)
            if not attempt.retry_state.outcome.failed:
                result = try_parse_json_object(raw, expect_type=expect_type)
                attempt.retry_state.set_result(result)
        return result  # type: ignore[return-value]

    @staticmethod
    def _deduplicate_concepts(concept_map: dict[str, dict]) -> dict[str, dict]:
        """对概念映射去重（忽略大小写），合并章节来源，保留最长描述。

        Args:
            concept_map: {name: {"description": str, "chapter_indices": set[int]}}

        Returns:
            去重后的 concept_map（key 为规范化后的名称）。
        """
        seen: dict[str, dict] = {}  # normalized_key → concept data
        for name, data in concept_map.items():
            normalized = name.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key not in seen:
                seen[key] = {
                    "description": data.get("description", ""),
                    "chapter_indices": set(data.get("chapter_indices", set())),
                    "original_name": normalized,
                }
            else:
                # 合并章节来源
                seen[key]["chapter_indices"].update(data.get("chapter_indices", set()))
                # 保留最长的描述
                if len(data.get("description", "")) > len(seen[key]["description"]):
                    seen[key]["description"] = data["description"]
        # 用原始名称作为 key 返回
        return {
            v["original_name"]: {
                "description": v["description"],
                "chapter_indices": v["chapter_indices"],
            }
            for v in seen.values()
        }

    @staticmethod
    def _resolve_edges(
        raw_edges: list[dict],
        concept_to_id: dict[str, int],
    ) -> "list[GraphEdgeBO]":
        """将解析出的关系列表转换为 GraphEdgeBO，过滤无效引用。"""
        resolved: list[GraphEdgeBO] = []
        seen_edges: set[tuple[int, int, str]] = set()  # 去重

        for edge in raw_edges:
            source_name = str(edge.get("source", "")).strip()
            target_name = str(edge.get("target", "")).strip()
            edge_type = str(edge.get("type", "")).strip()

            # 模糊匹配：忽略大小写
            source_id = concept_to_id.get(source_name) or concept_to_id.get(source_name.lower())
            target_id = concept_to_id.get(target_name) or concept_to_id.get(target_name.lower())

            if source_id is None or target_id is None:
                logger.debug(
                    "[GraphRAG] 跳过无效边（未匹配到概念）: %s → %s",
                    source_name,
                    target_name,
                )
                continue

            # 标准化关系类型
            if "PREREQUISITE" in edge_type.upper() or "PRIOR" in edge_type.upper():
                edge_type = "PRIOR_TO"
            elif "PART" in edge_type.upper() or "SUBTOPIC" in edge_type.upper() or "CONTAINS" in edge_type.upper():
                edge_type = "SUBTOPIC_OF"
            else:
                edge_type = "RELATED_TO"

            # 去重
            edge_key = (source_id, target_id, edge_type)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            resolved.append(
                GraphEdgeBO(
                    source=source_id,
                    target=target_id,
                    type=edge_type,
                    description=edge.get("description"),
                )
            )

        return resolved


INVOKE_MODEL_ID = "invoke_llm"
STREAM_MODEL_ID = "stream_llm"


def build_graphrag_config(
    namespace: str,
    entity_types: list[str] | None,
    prompt_template: str | None = None,
) -> GraphRagConfig:
    """根据项目配置生成一个 GraphRagConfig 实例。

    Args:
        namespace: Storage / VectorStore 的行级命名空间，使用 EduGraphRAGTask.task_id
                   字符串（即 Celery 自定义 task_id），确保跨重试时所有存储数据幂等。
                   input 临时文件、PG KV 存储、PG 向量存储均以此为命名空间。
        entity_types: 用户指定的实体类型列表（如 ['概念', '原理', '方法']），
                      传递给 GraphRAG 的实体抽取配置。
        prompt_template: 用户选择的提示词模板路径（如 'edu/zh'、'default/en'），
                         基于 prompt_repo_dir 解析为具体 prompt 文件路径。

    Returns:
        GraphRagConfig: 完整的 GraphRAG 运行时配置对象。
    """
    service_config = get_config()
    llm_config = service_config.graphrag.llm
    embedding_config = service_config.graphrag.embeddings
    gr_project_config = service_config.graphrag

    # input 临时文件按 namespace（graphrag_task_id）隔离，output 全部写入 PG 数据库
    working_dir = Path(gr_project_config.working_dir).resolve()
    input_dir = working_dir / namespace / "input"
    cache_dir = working_dir / namespace / "cache"
    report_dir = working_dir / namespace / "logs"
    working_dir.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    logger.debug(
        "[GraphRAG] 构建 GraphRagConfig: working_dir=%s, llm=%s, embedding=%s, entity_types=%s, prompt=%s",
        working_dir,
        llm_config.name,
        embedding_config.name,
        entity_types,
        prompt_template,
    )

    # ── 解析 prompt 文件 ────────────────────────────────────────────────────
    prompt_files = _resolve_prompt_files(gr_project_config.prompt_repo_dir, prompt_template)

    # ── completion model ──────────────────────────────────────────────────
    completion_model_cfg = ModelConfig(
        model_provider="openai",
        model=llm_config.name,
        api_key=llm_config.api_key,
        api_base=llm_config.api_base,
        # call_args={
        #     "temperature": llm_config.temperature,
        #     "max_tokens": llm_config.max_tokens,
        #     "top_p": llm_config.top_p,
        #     # "response_format": {"type": "json_object"},
        # },
        retry=RetryConfig(type=RetryType.ExponentialBackoff, max_retries=3, base_delay=5, max_delay=10),
        rate_limit=RateLimitConfig(requests_per_period=int(llm_config.concur_limit)),
    )
    invoke_model_cfg = ModelConfig(
        model_provider="zai",
        model=llm_config.name,
        api_key=llm_config.api_key,
        api_base=llm_config.api_base,
        # call_args={
        #     "temperature": llm_config.temperature,
        #     "max_tokens": llm_config.max_tokens,
        #     "top_p": llm_config.top_p,
        # },
        retry=RetryConfig(type=RetryType.ExponentialBackoff, max_retries=3, base_delay=5, max_delay=10),
        rate_limit=RateLimitConfig(requests_per_period=int(llm_config.concur_limit)),
    )

    # ── embedding model ───────────────────────────────────────────────────
    embedding_model_cfg = ModelConfig(
        # https://github.com/BerriAI/litellm/pull/12637
        model_provider="hosted_vllm",
        model=embedding_config.name,
        api_key=embedding_config.api_key,
        api_base=embedding_config.api_base,
        # embedding 只能保持默认为 1024 维
        call_args={"dimensions": embedding_config.dimensions, "encoding_format": "float"},
        retry=RetryConfig(type=RetryType.ExponentialBackoff, max_retries=3, base_delay=5, max_delay=10),
        rate_limit=RateLimitConfig(requests_per_period=int(embedding_config.concur_limit)),
    )
    embed_text_cfg = EmbedTextConfig(
        embedding_model_id=DEFAULT_EMBEDDING_MODEL_ID,
        batch_size=embedding_config.batch_size,
        batch_max_tokens=embedding_config.batch_max_tokens,
    )

    # ── 并发请求总数 ─────────────────────────────────────────────────────
    concurrent_requests = int(embedding_config.concur_limit) + int(llm_config.concur_limit)

    # ── 存储配置 ──────────────────────────────────────────────────────────
    # input 仍写本地临时文件；output / update_output 全部进 PostgreSQL
    pg_dsn = str(service_config.datasource.postgresql.dsn)
    input_cfg = InputConfig(type=InputType.Text, encoding="utf-8", file_pattern=r".*\.(txt|md)$")
    input_storage_cfg = StorageConfig(base_dir=str(input_dir), type=StorageType.File)
    output_storage_cfg = PgStorageConfig(
        type="pgvector",
        connection_string=pg_dsn,
        namespace=namespace,
        table_name="public.graphrag_storage",
    )
    update_output_storage_cfg = PgStorageConfig(
        type="pgvector",
        connection_string=pg_dsn,
        namespace=f"{namespace}/updates",
        table_name="public.graphrag_storage",
    )
    cache_cfg = CacheConfig(type=CacheType.Json, storage=StorageConfig(type=StorageType.File, base_dir=str(cache_dir)))
    report_cfg = ReportingConfig(base_dir=str(report_dir), type=ReportingType.file)
    # ── Chunk 配置 ──────────────────────────────────────────────────────────
    chunking_cfg = ChunkingConfig(
        type=ChunkerType.Sentence,
        encoding_model=gr_project_config.chunking_encoding_model,
    )

    # ── 向量存储配置（pgvector）────────────────────────────────────────────
    # namespace 使用 EduGraphRAGTask.task_id 字符串，确保重试幂等（upsert 覆盖）。
    # table_name 固定为单张共享表，GraphRAG 内部各集合（entities/relationships/…）
    # 通过 _index_key = "{namespace}__{collection}" 区分行级命名空间。
    vector_store_cfg = PgVectorStoreConfig(
        type="pgvector",
        connection_string=pg_dsn,
        vector_size=embedding_config.dimensions,
        table_name="public.graphrag_vectors",
        namespace=namespace,
    )

    # ── 索引阶段子配置 ──────────────────────────────────────────────────────
    extract_graph_cfg = ExtractGraphConfig(
        completion_model_id=DEFAULT_COMPLETION_MODEL_ID,
        entity_types=entity_types or [],
        prompt=prompt_files.get("extract_graph.txt"),
    )
    summarize_descriptions_cfg = SummarizeDescriptionsConfig(
        completion_model_id=DEFAULT_COMPLETION_MODEL_ID,
        prompt=prompt_files.get("summarize_descriptions.txt"),
    )
    extract_graph_nlp_cfg = ExtractGraphNLPConfig()
    extract_claims_cfg = ExtractClaimsConfig(
        enabled=True,
        completion_model_id=DEFAULT_COMPLETION_MODEL_ID,
        prompt=prompt_files.get("extract_claims.txt"),
    )
    community_reports_cfg = CommunityReportsConfig(
        completion_model_id=DEFAULT_COMPLETION_MODEL_ID,
        graph_prompt=prompt_files.get("community_report_graph.txt"),
        text_prompt=prompt_files.get("community_report_text.txt"),
    )

    # ── 搜索阶段子配置 ──────────────────────────────────────────────────────
    local_search_cfg = LocalSearchConfig(
        completion_model_id=INVOKE_MODEL_ID,
        prompt=prompt_files.get("local_search_system_prompt.txt"),
    )
    global_search_cfg = GlobalSearchConfig(
        completion_model_id=INVOKE_MODEL_ID,
        map_prompt=prompt_files.get("global_search_map_system_prompt.txt"),
        reduce_prompt=prompt_files.get("global_search_reduce_system_prompt.txt"),
        knowledge_prompt=prompt_files.get("global_search_knowledge_system_prompt.txt"),
    )
    drift_search_cfg = DRIFTSearchConfig(
        completion_model_id=INVOKE_MODEL_ID,
        prompt=prompt_files.get("drift_search_system_prompt.txt"),
        reduce_prompt=prompt_files.get("drift_search_reduce_prompt.txt"),
    )
    basic_search_cfg = BasicSearchConfig(
        completion_model_id=INVOKE_MODEL_ID,
        prompt=prompt_files.get("basic_search_system_prompt.txt"),
    )

    # ── 组装最终配置 ──────────────────────────────────────────────────────
    return GraphRagConfig(
        # 模型
        completion_models={DEFAULT_COMPLETION_MODEL_ID: completion_model_cfg, INVOKE_MODEL_ID: invoke_model_cfg},
        embedding_models={DEFAULT_EMBEDDING_MODEL_ID: embedding_model_cfg},
        concurrent_requests=max(1, concurrent_requests),
        # 运行模式
        async_mode=AsyncType.AsyncIO,
        # 输入
        input=input_cfg,
        input_storage=input_storage_cfg,
        # 存储
        output_storage=output_storage_cfg,
        update_output_storage=update_output_storage_cfg,
        vector_store=vector_store_cfg,
        cache=cache_cfg,
        reporting=report_cfg,
        # 索引 pipeline 子配置
        chunking=chunking_cfg,
        embed_text=embed_text_cfg,
        extract_graph=extract_graph_cfg,
        summarize_descriptions=summarize_descriptions_cfg,
        extract_graph_nlp=extract_graph_nlp_cfg,
        extract_claims=extract_claims_cfg,
        community_reports=community_reports_cfg,
        # 搜索
        local_search=local_search_cfg,
        global_search=global_search_cfg,
        drift_search=drift_search_cfg,
        basic_search=basic_search_cfg,
    )
