"""教育聊天 Agent 类"""

from collections.abc import AsyncGenerator
import logging
from typing import Self

from dependency_injector.wiring import Provide, inject
from langchain_core.messages import AIMessageChunk, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime

from graphedu.common.models.bo.agent import ChatContext, ChatState, InvokableConfig, InvokableValues
from graphedu.common.models.dto.educationv2.agent import ChatMessage, RoleEnum
from graphedu.common.utils.llm.messages import generate_msg_id
from graphedu.mcp.graphrag_query import graphrag_query
from graphedu.mcp.learning_path import generate_learning_path
from graphedu.mcp.query_exercise import query_exercise
from graphedu.mcp.set_question import set_question
from graphedu.mcp.visualize_graph_query import visualize_graph_query
from graphedu.services.agent.session import ChatSessionManager, RequestMetadata

logger = logging.getLogger(__name__)


class ChatAgent:
    """教育聊天 Agent 类

    提供：
    1. 自动工具调用
    2. 流式响应处理
    3. 会话历史管理
    """

    _agent: CompiledStateGraph | None = None
    _chat_llm: ChatOpenAI | None = None
    _thinking_llm: ChatOpenAI | None = None
    _checkpointer: AsyncPostgresSaver | None = None
    _initialized: bool = False

    def __init__(self):
        """初始化 ChatAgent 实例"""
        self._agent: CompiledStateGraph | None = None
        self._chat_llm: ChatOpenAI | None = None
        self._checkpointer = None
        self._initialized: bool = False

    def is_initialized(self) -> bool:
        """检查 Agent 是否已初始化"""
        return self._initialized

    @inject
    async def init(
        self,
        chat_llm: ChatOpenAI = Provide["chat_llm"],
        think_llm: ChatOpenAI = Provide["think_llm"],
        checkpointer: AsyncPostgresSaver = Provide["langgraph_checkpointer"],
    ) -> Self:
        """初始化 Agent

        Args:
            chat_llm: 对话型 LLM 实例（通过依赖注入）
            think_llm: 思考型 LLM 示例（通过依赖注入）
            checkpointer: LangGraph 检查点保存器（通过依赖注入）

        Returns:
            Self: 返回自身实例
        """
        self._chat_llm = chat_llm
        self._thinking_llm = think_llm
        self._checkpointer = checkpointer

        # 创建 StateGraph
        graph_builder = StateGraph(ChatState, context_schema=ChatContext)

        # 添加节点和边
        graph_builder.add_node("agent", self._agent_node)
        graph_builder.add_node("check_assessment", self._check_assessment_node)
        graph_builder.add_node(
            "tools",
            ToolNode(
                [visualize_graph_query, graphrag_query, query_exercise, set_question, generate_learning_path],
                messages_key="lc_messages",
            ),
        )
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges(
            "agent",
            lambda state: tools_condition(state, messages_key="lc_messages"),
            {
                "tools": "tools",
                "__end__": "check_assessment",
            },
        )
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("check_assessment", END)

        # 编译
        self._agent = graph_builder.compile(checkpointer=checkpointer)
        self._initialized = True

        logger.info("ChatAgent initialized successfully")
        return self

    async def async_stream(self, values: InvokableValues, config: InvokableConfig) -> AsyncGenerator[ChatMessage]:
        """流式 Agent 响应

        Args:
            values: 输入值
            config: 调用配置

        Yields:
            ChatMessage: 流式消息
        """
        if not self._initialized:
            raise RuntimeError("ChatAgent not initialized")
        if self._agent is None:
            raise RuntimeError("ChatAgent graph not initialized")

        # 1. 准备配置
        input_config = RunnableConfig(configurable=dict(config))
        req_data_key = f"{config['thread_id']}"
        req_data = RequestMetadata(req_data_key)

        # 2. 获取新消息并转换
        new_message: ChatMessage = values.get("new_message")
        lc_message = new_message.to_lc_message()
        input_values = ChatState(lc_messages=[lc_message], gm_messages=[new_message])

        # 3. 会话上下文
        with ChatSessionManager.session_context(req_data_key, req_data):
            try:
                # 4. 流式调用
                stream_iters = self._agent.astream(
                    input_values,
                    input_config,
                    stream_mode=["messages", "updates"],
                    context=ChatContext(
                        user_id=config["user_id"],
                        conv_id=config["conv_id"],
                        course_id=config.get("course_id"),
                        **new_message.feature.model_dump(),
                    ),
                )

                # 5. 处理流式输出
                async for stream_part in stream_iters:
                    # 检查是否被撤销
                    if await req_data.is_revoked():
                        break

                    # 兼容 v1/v2 流式输出
                    mode = None
                    payload = None
                    if isinstance(stream_part, dict) and "type" in stream_part and "data" in stream_part:
                        mode = stream_part["type"]
                        payload = stream_part["data"]
                    elif isinstance(stream_part, tuple) and len(stream_part) == 2 and isinstance(stream_part[0], str):
                        mode, payload = stream_part

                    if mode == "messages" and isinstance(payload, tuple) and len(payload) == 2:
                        token, _metadata = payload
                        if not isinstance(token, AIMessageChunk):
                            continue

                        # 处理 content_blocks
                        if hasattr(token, "content_blocks"):
                            for block in token.content_blocks:
                                if block["type"] == "reasoning":
                                    # 发送思考消息
                                    thinking_msg = ChatMessage.auto_new_message(
                                        role=RoleEnum.THINKING,
                                        content_type="text",
                                        content=block.get("reasoning", ""),
                                        user_id=config["user_id"],
                                        conv_id=config["conv_id"],
                                        message_id=token.id or generate_msg_id(),
                                    )
                                    yield thinking_msg

                                elif block["type"] == "text":
                                    # 发送文本消息
                                    text_msg = ChatMessage.auto_new_message(
                                        role=RoleEnum.AI,
                                        content_type="text",
                                        content=block.get("text", ""),
                                        user_id=config["user_id"],
                                        conv_id=config["conv_id"],
                                        message_id=token.id or generate_msg_id(),
                                    )
                                    yield text_msg

                    elif mode == "updates" and isinstance(payload, dict):
                        for node_name, node_update in payload.items():
                            # agent 节点的 gm_messages 已通过 messages token 流对外发送，
                            # 这里只透传 tools 节点状态更新，避免重复输出。
                            if node_name != "tools":
                                continue
                            if not isinstance(node_update, dict):
                                continue
                            gm_updates = node_update.get("gm_messages")
                            if isinstance(gm_updates, ChatMessage):
                                yield gm_updates
                            elif isinstance(gm_updates, list):
                                for item in gm_updates:
                                    if isinstance(item, ChatMessage):
                                        yield item

            except Exception as e:
                logger.error(f"Agent stream error: {e}")
                raise

    async def async_get_history(self, config: InvokableConfig) -> list[ChatMessage]:
        """获取会话历史消息

        Args:
            config: 调用配置

        Returns:
            list[ChatMessage]: 历史消息列表
        """
        if not self._initialized:
            raise RuntimeError("ChatAgent not initialized")
        if self._agent is None:
            raise RuntimeError("ChatAgent graph not initialized")

        from langgraph.types import StateSnapshot

        # 1. 准备配置
        user_config = RunnableConfig(configurable=dict(config))

        # 2. 获取状态快照
        snapshot: StateSnapshot = await self._agent.aget_state(user_config)

        # 3. 提取消息
        if not snapshot.values or "gm_messages" not in snapshot.values:
            return []

        return snapshot.values["gm_messages"]

    async def _agent_node(self, state: ChatState, runtime: Runtime[ChatContext]):
        """核心 Agent 节点

        处理用户消息，调用 LLM 并绑定工具，返回响应。

        Args:
            state: 当前对话状态
            config: 运行配置
            runtime: 运行时上下文信息

        Returns:
            更新的状态字典
        """
        # 获取最新的 LangChain 消息
        messages = state.lc_messages
        if self._chat_llm is None:
            raise RuntimeError("ChatAgent LLM not initialized")

        # 注入系统提示词（仅当消息列表中尚无 SystemMessage 时）
        system_prompt = self._build_system_prompt(runtime.context)
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt), *messages]

        # 根据 thinking_mode 选择 LLM
        if runtime.context.thinking_mode == "enable":
            llm = self._thinking_llm
        else:
            llm = self._chat_llm

        # 根据 feature 条件构建工具列表
        tools = [query_exercise, set_question, generate_learning_path]
        if runtime.context.graphrag:
            tools.extend([visualize_graph_query, graphrag_query])

        # 调用 LLM（绑定工具）
        llm_with_tools = llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke(messages)

        user_id = runtime.context.user_id
        conv_id = runtime.context.conv_id
        gm_messages: list[ChatMessage] = []

        thinking_text = response.additional_kwargs.get("reasoning_content") if response.additional_kwargs else None
        if thinking_text:
            # 思考消息：使用独立 ID，避免与 AI 回复 message_id 冲突导致去重丢失
            gm_messages.append(
                ChatMessage.auto_new_message(
                    role=RoleEnum.THINKING,
                    content_type="text",
                    content=thinking_text,
                    user_id=user_id,
                    conv_id=conv_id,
                    message_id=generate_msg_id(),
                )
            )

        # 有 tool_calls 时只走 lc_messages，但保留已有的思考消息
        if response.tool_calls:
            result = {"lc_messages": [response]}
            if gm_messages:
                result["gm_messages"] = gm_messages
            return result

        # 纯文本 AI 回复
        gm_messages.append(
            ChatMessage.from_lc_message(
                user_id=user_id,
                conv_id=conv_id,
                lc_message=response,
            )
        )

        # 返回更新
        return {"lc_messages": [response], "gm_messages": gm_messages}

    async def _check_assessment_node(self, state: ChatState, runtime: Runtime[ChatContext]):
        """检查是否需要触发知识点掌握度评估。

        当 lc_messages 中 HumanMessage 数量达到 10 的倍数时，提交 Celery 异步任务进行评估。
        异常不阻塞正常对话流。

        Args:
            state: 当前对话状态
            runtime: 运行时上下文信息

        Returns:
            空字典（不修改状态）
        """
        try:
            from langchain_core.messages import HumanMessage

            human_msgs = [m for m in state.lc_messages if isinstance(m, HumanMessage)]
            human_count = len(human_msgs)
            if human_count > 0 and human_count % 10 == 0:
                message_id = human_msgs[-1].id  # 最后一条 HumanMessage 的 ID
                from graphedu.workers.study_assessment_tasks import assess_session_task

                assess_session_task.delay(
                    runtime.context.conv_id,
                    runtime.context.user_id,
                    trigger_type="chat_round",
                    message_id=message_id,
                )
                logger.info(
                    "已提交掌握度评估任务: conv_id=%s, human_count=%d, message_id=%s",
                    runtime.context.conv_id,
                    human_count,
                    message_id,
                )
        except Exception as e:
            logger.exception("提交掌握度评估任务失败")
            logger.error("错误: %s", e)
        return {}

    @staticmethod
    def _build_system_prompt(context: ChatContext) -> str:
        """根据运行时上下文构建系统提示词

        Args:
            context: 当前会话上下文

        Returns:
            系统提示词文本
        """
        parts = [
            "你是一个智能教育助手，专注于帮助学生理解知识点、解答疑问、推荐学习路径和提供练习题。",
            "",
            "## 工具使用策略",
            "",
            "你可以使用以下工具来辅助学生：",
            "",
            "1. **knowledge_point_query**（知识图谱查询）：当学生询问某个知识点、概念或实体时调用。"
            "传入提炼的关键词，返回知识图谱可视化。",
            "2. **teaching_document_retrieval**（教学文档检索）：当需要深入解释知识点、提供课程资料支持时调用。"
            "优先用于回答课程相关的问题。",
            "3. **query_exercise**（题库查询）：当学生想要做题练习时优先调用此工具查询题库中是否已有相关题目。"
            "如果返回没有匹配题目，再使用 set_a_question 生成新题。",
            "4. **set_a_question**（生成题目）：当题库中没有合适的题目时调用，用于按知识点和难度生成新题目。",
            '5. **generate_learning_path**（学习路径推荐）：当学生表达学习目标（如"我想学XXX"、"帮我规划学习"）时调用，'
            "传入提炼的知识关键词列表。",
            "",
            "### 工具使用原则",
            "- 回答知识点问题时，优先使用 knowledge_point_query 或 teaching_document_retrieval 获取课程资料，"
            "避免凭通用知识回答。",
            "- 学生要求做题时，先 query_exercise 查题库，无题再用 set_a_question 生成。",
            "- 每次只调用最相关的 1-2 个工具，不要一次调用所有工具。",
            "- 回答时使用中文，保持简洁、友好。",
        ]

        # 动态上下文
        if context.chapter_id:
            parts.extend(["", "## 当前会话上下文", f"当前关联章节 ID: {context.chapter_id}"])
        if context.graphrag:
            parts.append("知识问答功能：已启用（可直接使用 teaching_document_retrieval 工具）")

        return "\n".join(parts)
