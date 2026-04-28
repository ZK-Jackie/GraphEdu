"""学习评估 Celery 任务

包含会话知识点掌握度评估任务（assess_session_task）。
由 chat_agent 的 _check_assessment_node 每满 10 条 HumanMessage 时触发。
"""

import asyncio
import logging
import sys
from uuid import UUID

from celery import Task
from sqlalchemy import select

from graphedu.common.models.orm.education import EduExerciseAttempt, EduExerciseKnowledgePoint
from graphedu.common.resource import ContainerMode, try_get_container
from graphedu.common.resource.container import WorkerContainer
from graphedu.common.utils import try_parse_json_object
from graphedu.mapper.education.chat_session import ChatSessionMapper
from graphedu.mapper.education.knowledge_point_embedding import KnowledgePointEmbeddingMapper
from graphedu.mapper.education.learning_event import LearningEventMapper
from graphedu.mapper.education.mastery import MasteryMapper
from graphedu.workers.celery import celery_app

logger = logging.getLogger(__name__)


# ============================================================================
# Celery 任务入口
# ============================================================================


@celery_app.task(bind=True, name="graphedu.workers.assess_session_task", max_retries=1)
def assess_session_task(
    self: Task,
    conv_id: int,
    user_id: int,
    *,
    trigger_type: str = "chat_round",
    message_id: str | None = None,
):
    """异步评估会话中学生对各知识点的掌握程度。

    Args:
        self: Celery 任务实例
        conv_id: 会话 ID
        user_id: 用户 ID
        trigger_type: 触发类型（chat_round / quiz_complete / manual 等）
        message_id: 触发评估的消息 ID（可选），用于精确截取对话范围
    """

    async def _process():
        container: WorkerContainer = await try_get_container(ContainerMode.WORKER)
        count = await assess_session(
            container,
            conv_id,
            user_id,
            trigger_type=trigger_type,
            message_id=message_id,
        )
        logger.info(
            "Celery 评估任务完成: conv_id=%s, user_id=%s, trigger=%s, count=%d",
            conv_id,
            user_id,
            trigger_type,
            count,
        )
        return count

    asyncio_run_kwargs = {}
    if sys.platform == "win32":
        asyncio_run_kwargs = {"loop_factory": asyncio.SelectorEventLoop}
    return asyncio.run(_process(), **asyncio_run_kwargs)


# ============================================================================
# Prompt 模板
# ============================================================================

_KEYWORD_EXTRACTION_PROMPT = """你是一位教育内容分析专家。
请从以下学生与 AI 的对话历史中，提取学生讨论或询问的知识概念/关键词。

## 对话历史
{conversation}

## 输出格式
请严格输出 JSON 数组，不要包含其他内容：
```json
["关键词1", "关键词2", ...]
```"""

_ASSESSMENT_PROMPT = """你是一位教育评估专家。请根据学生与 AI 的对话历史和学习行为数据，
对学生涉及的知识点掌握度进行 CRUD 评估操作。

## 候选知识点（从对话和学习行为中提取）
{candidate_knowledge_points}

## 当前已有的评估记录（学生在此会话中的知识点掌握度）
{existing_mastery_records}

## 对话历史
{conversation}

## 评估要求
1. 根据对话交互质量、做题情况等，对已有评估记录进行修订或确认
2. 对新发现的知识点添加评估记录
3. 若已有记录中的知识点在当前对话中完全未被涉及且无学习行为支撑，不予理会
4. mastery_level 取值：unknown（无法判断）、low（初步了解）、medium（基本理解）、high（深入掌握）

## 输出格式
请严格输出 JSON 数组：
```json
[
  {{
    "action": "add",
    "node_uuid": "知识点的UUID",
    "mastery_score": 0-100,
    "mastery_level": "unknown/low/medium/high",
    "reason": "简短评估理由"
  }},
  {{
    "action": "update",
    "node_uuid": "知识点的UUID",
    "mastery_score": 0-100,
    "mastery_level": "unknown/low/medium/high",
    "reason": "简短评估理由"
  }},
  {{
    "action": "delete",
    "node_uuid": "知识点的UUID",
    "reason": "简短删除理由"
  }}
]
```
- action=add: 添加新评估记录（node_uuid 不在已有记录中）
- action=update: 修订已有记录（需与已有记录的 node_uuid 匹配）
- action=delete: 删除已有记录（需与已有记录的 node_uuid 匹配）"""


# ============================================================================
# 核心评估流程
# ============================================================================


async def assess_session(
    container: WorkerContainer,
    conv_id: int,
    user_id: int,
    *,
    trigger_type: str = "chat_round",
    message_id: str | None = None,
) -> int:
    """评估指定会话中学生对各知识点的掌握程度。

    流程：
    1. 从 checkpointer 获取对话历史，按 message_id 截取
    2. 收集候选知识点（学习事件 + LLM 关键词提取 + 混合检索）
    3. 补充做题数据
    4. 查询已有评估记录
    5. LLM 综合评估，输出 CRUD 操作
    6. 执行操作

    Args:
        container: Worker 容器实例，提供所有资源
        conv_id: 会话 ID
        user_id: 用户 ID
        trigger_type: 触发类型
        message_id: 触发消息 ID（可选）

    Returns:
        int: 操作的掌握度评估记录数量
    """
    db_client = await container.postgresql_client()
    chat_llm = await container.chat_llm()
    checkpointer = await container.langgraph_checkpointer()

    async with db_client.session_context() as db_session:
        # 1. 获取会话信息
        session = await ChatSessionMapper.get_by_conv_id_and_user(
            conv_id=conv_id,
            user_id=user_id,
            db_session=db_session,
        )
        if not session:
            logger.warning("评估跳过：会话不存在 conv_id=%s", conv_id)
            return 0

        course_id = session.course_id
        if not course_id:
            logger.warning("评估跳过：会话未关联课程 conv_id=%s", conv_id)
            return 0

        # 2. 从 checkpointer 获取对话历史
        gm_messages = await _get_gm_messages(checkpointer, conv_id, user_id)
        if not gm_messages:
            logger.info("评估跳过：无对话历史 conv_id=%s", conv_id)
            return 0

        # 3. 按 message_id 截取对话（回溯 10 条 HumanMessage）
        conversation_text = _slice_conversation_text(gm_messages, message_id=message_id)
        if not conversation_text or conversation_text.startswith("（"):
            logger.info("评估跳过：无有效对话内容 conv_id=%s", conv_id)
            return 0

        # 4. 收集候选知识点
        candidate_map: dict[str, dict] = {}
        await _collect_candidates_from_events(candidate_map, conv_id, db_session)

        # 5. LLM 提取关键词 → 混合检索
        keywords = await _extract_keywords(chat_llm, conversation_text)
        if keywords:
            search_results = await _hybrid_search_knowledge_points(
                course_id=course_id,
                keywords=keywords,
                container=container,
                db_session=db_session,
            )
            for uuid_str, info in search_results.items():
                if uuid_str not in candidate_map:
                    candidate_map[uuid_str] = info
                elif not candidate_map[uuid_str]["title"]:
                    candidate_map[uuid_str]["title"] = info["title"]
                    candidate_map[uuid_str]["description"] = info.get("description")

        if not candidate_map:
            logger.info("评估跳过：无匹配知识点 conv_id=%s", conv_id)
            return 0

        # 6. 补充做题数据
        await _supplement_exercise_data(candidate_map, user_id, session.create_time, db_session)

        # 7. 查询已有评估记录
        existing_records = await MasteryMapper.get_by_student_session(
            student_id=user_id,
            course_id=course_id,
            session_id=conv_id,
            db_session=db_session,
        )

        # 8. LLM 评估
        candidate_text = _build_candidate_text(candidate_map)
        existing_text = _build_existing_records_text(existing_records)

        prompt = _ASSESSMENT_PROMPT.format(
            candidate_knowledge_points=candidate_text,
            existing_mastery_records=existing_text,
            conversation=conversation_text,
        )

        try:
            response = await chat_llm.ainvoke(prompt)
            assessments = _parse_assessment_response(response.content)
        except Exception:
            logger.exception("LLM 评估失败 conv_id=%s", conv_id)
            return 0

        if not assessments:
            logger.warning("评估结果为空 conv_id=%s", conv_id)
            return 0

        # 9. 执行 CRUD 操作
        count = await _execute_assessment_actions(
            assessments=assessments,
            candidate_map=candidate_map,
            existing_records=existing_records,
            user_id=user_id,
            course_id=course_id,
            session_id=conv_id,
            trigger_type=trigger_type,
            db_session=db_session,
        )

        logger.info("评估完成：conv_id=%s, 执行 %d 条操作", conv_id, count)
        return count


# ============================================================================
# 对话历史获取与截取
# ============================================================================


async def _get_gm_messages(checkpointer, conv_id: int, user_id: int):
    """通过 checkpointer 直接获取对话的 gm_messages。

    Args:
        checkpointer: AsyncPostgresSaver 实例
        conv_id: 会话 ID
        user_id: 用户 ID

    Returns:
        list[ChatMessage] | None: 消息列表
    """
    try:
        from graphedu.common.models.dto.educationv2.agent import ChatMessage as AgentChatMessage

        thread_id = AgentChatMessage.build_chat_uid(user_id, conv_id)
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = await checkpointer.aget_tuple(config)
        if not checkpoint_tuple or not checkpoint_tuple.checkpoint:
            return None
        channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
        return channel_values.get("gm_messages") or []
    except Exception:
        logger.exception("获取对话历史失败 conv_id=%s", conv_id)
        return None


def _slice_conversation_text(messages, *, message_id: str | None = None, human_count: int = 10) -> str:
    """根据 message_id 向前回溯指定数量的 HumanMessage，生成对话文本。

    Args:
        messages: gm_messages 列表（ChatMessage 对象）
        message_id: 触发消息 ID（可选）
        human_count: 回溯的 HumanMessage 数量

    Returns:
        str: 格式化的对话文本
    """
    if not messages:
        return "（无对话历史）"

    # 1. 找到目标消息位置
    target_idx = len(messages) - 1
    if message_id:
        for i, msg in enumerate(messages):
            if getattr(msg, "message_id", None) == message_id:
                target_idx = i
                break

    # 2. 从目标位置向前回溯，数 human_count 条 HUMAN 消息
    human_found = 0
    start_idx = 0
    for i in range(target_idx, -1, -1):
        if getattr(messages[i], "role", -1) == 0:  # HUMAN
            human_found += 1
            if human_found >= human_count:
                start_idx = i
                break

    # 3. 截取范围内的 HUMAN + AI 消息
    lines = []
    for msg in messages[start_idx : target_idx + 1]:
        role = getattr(msg, "role", -1)
        if role == 0:  # HUMAN
            label = "学生"
        elif role == 1:  # AI
            label = "AI"
        else:
            continue
        text = ""
        contents = getattr(msg, "contents", None)
        if contents:
            for content in contents:
                content_text = getattr(content, "text", None)
                if content_text:
                    text += content_text
        if text:
            lines.append(f"{label}: {text}")

    return "\n".join(lines) if lines else "（对话历史为空）"


# ============================================================================
# 候选知识点收集
# ============================================================================


async def _collect_candidates_from_events(
    candidate_map: dict[str, dict],
    conv_id: int,
    db_session,
) -> None:
    """从学习事件中收集候选知识点，就地更新 candidate_map。"""
    events = await LearningEventMapper.get_session_events(
        session_id=conv_id,
        event_type=None,
        db_session=db_session,
    )
    for event in events:
        if not event.node_uuid:
            continue
        uuid_str = str(event.node_uuid)
        if uuid_str not in candidate_map:
            candidate_map[uuid_str] = {
                "title": "",
                "description": None,
                "questions": [],
                "other_events": [],
                "exercises": [],
            }
        if event.event_type == "question" and event.event_content:
            candidate_map[uuid_str]["questions"].append(event.event_content)
        elif event.event_type not in ("question", "quiz_answer", "resource_complete", "resource_progress"):
            candidate_map[uuid_str]["other_events"].append(
                f"内容: {event.event_content}" if event.event_content else event.event_type
            )


async def _extract_keywords(llm, conversation_text: str) -> list[str]:
    """从对话历史中提取知识概念关键词。"""
    prompt = _KEYWORD_EXTRACTION_PROMPT.format(conversation=conversation_text)
    try:
        response = await llm.ainvoke(prompt)
        _, result = try_parse_json_object(response.content, expect_type=list)
        if isinstance(result, list):
            return [str(kw).strip() for kw in result if kw]
        return []
    except Exception:
        logger.exception("关键词提取失败")
        return []


async def _hybrid_search_knowledge_points(
    course_id: int,
    keywords: list[str],
    container: WorkerContainer,
    db_session,
) -> dict[str, dict]:
    """混合检索知识点：关键词检索（AGE）+ 向量检索（pgvector）。"""
    from graphedu.mapper.education.syllabus_graph import SyllabusGraphMapper
    from graphedu.services.education.syllabus_graph import SyllabusGraphService

    result_map: dict[str, dict] = {}
    pg_client = await container.postgresql_client()

    # 关键词检索（AGE）— 并行执行
    keyword_tasks = [SyllabusGraphMapper.search_nodes(pg_client, course_id, keyword, limit=10) for keyword in keywords]

    try:
        keyword_results = await asyncio.gather(*keyword_tasks, return_exceptions=True)
        for idx, nodes in enumerate(keyword_results):
            if isinstance(nodes, Exception):
                logger.warning("关键词检索失败: %s, 错误: %s", keywords[idx], nodes)
                continue
            for node in nodes:
                if node.uuid:
                    result_map.setdefault(
                        node.uuid,
                        {
                            "title": node.title,
                            "description": node.description,
                            "questions": [],
                            "other_events": [],
                            "exercises": [],
                        },
                    )
    except Exception:
        logger.exception("关键词检索异常")

    # 向量检索（pgvector）
    try:
        embedding_llm = SyllabusGraphService._get_embedding_llm()
        embeddings = await embedding_llm.aembed_documents(keywords)

        for embedding in embeddings:
            matches = await KnowledgePointEmbeddingMapper.search_by_embedding(
                course_id=course_id,
                query_embedding=embedding,
                top_k=10,
                distance_threshold=0.5,
                db_session=db_session,
            )
            for match in matches:
                uuid_str = str(match.node_uuid)
                result_map.setdefault(
                    uuid_str,
                    {"title": match.title, "description": None, "questions": [], "other_events": [], "exercises": []},
                )
    except Exception:
        logger.exception("向量检索异常")

    return result_map


async def _supplement_exercise_data(
    candidate_map: dict[str, dict],
    user_id: int,
    session_create_time,
    db_session,
) -> None:
    """补充做题数据到 candidate_map。"""
    uuids = [UUID(u) for u in candidate_map]
    if not uuids:
        return

    try:
        stmt = (
            select(
                EduExerciseAttempt.is_correct,
                EduExerciseAttempt.time_spent,
                EduExerciseKnowledgePoint.node_uuid,
            )
            .join(
                EduExerciseKnowledgePoint,
                EduExerciseAttempt.exercise_id == EduExerciseKnowledgePoint.exercise_id,
            )
            .where(
                EduExerciseAttempt.student_id == user_id,
                EduExerciseAttempt.attempt_time >= session_create_time,
                EduExerciseKnowledgePoint.node_uuid.in_(uuids),
            )
            .order_by(EduExerciseAttempt.attempt_time.asc())
        )
        result = await db_session.execute(stmt)
        for is_correct, time_spent, node_uuid in result.all():
            uuid_str = str(node_uuid)
            if uuid_str in candidate_map:
                status = "正确" if is_correct else ("错误" if is_correct is False else "待批改")
                candidate_map[uuid_str].setdefault("exercises", []).append(
                    f"结果: {status}, 用时: {time_spent or 0}秒"
                )
    except Exception:
        logger.exception("补充做题数据失败")


# ============================================================================
# 文本构建
# ============================================================================


def _build_candidate_text(candidate_map: dict[str, dict]) -> str:
    """构建候选知识点文本，供 LLM 评估。"""
    lines = []
    for node_uuid, info in candidate_map.items():
        lines.append(f"- UUID: {node_uuid}")
        lines.append(f"  标题: {info['title']}")
        if info.get("description"):
            lines.append(f"  描述: {info['description'][:200]}")
        if info.get("questions"):
            lines.append(f"  相关提问: {'; '.join(info['questions'][:3])}")
        if info.get("other_events"):
            lines.append(f"  其他学习行为: {'; '.join(info['other_events'][:5])}")
        if info.get("exercises"):
            lines.append(f"  做题情况: {'; '.join(info['exercises'])}")
    return "\n".join(lines)


def _build_existing_records_text(records) -> str:
    """构建已有评估记录文本。"""
    if not records:
        return "（无已有评估记录）"
    lines = []
    for r in records:
        lines.append(f"- mastery_id: {r.mastery_id}")
        lines.append(f"  node_uuid: {r.node_uuid}")
        lines.append(f"  mastery_score: {r.mastery_score}")
        lines.append(f"  mastery_level: {r.mastery_level}")
        lines.append(f"  trigger_type: {r.trigger_type}")
        lines.append(f"  assessed_at: {r.assessed_at}")
    return "\n".join(lines)


# ============================================================================
# CRUD 操作执行
# ============================================================================


async def _execute_assessment_actions(
    assessments: list[dict],
    candidate_map: dict[str, dict],
    existing_records: list,
    user_id: int,
    course_id: int,
    session_id: int,
    trigger_type: str,
    db_session,
) -> int:
    """执行 LLM 返回的 CRUD 操作。

    Args:
        assessments: LLM 返回的评估操作列表
        candidate_map: 候选知识点映射
        existing_records: 已有评估记录
        user_id: 学生 ID
        course_id: 课程 ID
        session_id: 会话 ID
        trigger_type: 触发类型
        db_session: 数据库会话

    Returns:
        int: 操作的记录数量
    """
    from datetime import datetime

    existing_map = {str(r.node_uuid): r for r in existing_records}
    count = 0

    for item in assessments:
        action = item.get("action", "add")
        node_uuid_str = item.get("node_uuid")
        if not node_uuid_str:
            continue

        reason = item.get("reason")

        if action == "add":
            if node_uuid_str in candidate_map and node_uuid_str not in existing_map:
                await MasteryMapper.create_mastery(
                    student_id=user_id,
                    course_id=course_id,
                    node_uuid=UUID(node_uuid_str),
                    mastery_score=item.get("mastery_score", 0),
                    mastery_level=item.get("mastery_level", "unknown"),
                    trigger_type=trigger_type,
                    session_id=session_id,
                    reason=reason,
                    db_session=db_session,
                )
                count += 1

        elif action == "update":
            existing = existing_map.get(node_uuid_str)
            if existing:
                existing.mastery_score = item.get("mastery_score", existing.mastery_score)
                existing.mastery_level = item.get("mastery_level", existing.mastery_level)
                existing.trigger_type = trigger_type
                existing.reason = reason or existing.reason
                existing.assessed_at = datetime.now()
                await db_session.flush()
                count += 1

        elif action == "delete":
            existing = existing_map.get(node_uuid_str)
            if existing:
                await MasteryMapper.delete_mastery(existing.mastery_id, db_session)
                count += 1

    return count


# ============================================================================
# 解析工具
# ============================================================================


def _parse_assessment_response(content: str) -> list[dict]:
    """解析 LLM 返回的评估结果 JSON。"""
    _, result = try_parse_json_object(content, expect_type=list)
    if isinstance(result, list):
        return result
    return []
