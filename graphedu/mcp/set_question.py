"""出题工具"""

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field

from graphedu.common import get_config
from graphedu.common.models.bo import ChatState
from graphedu.common.models.bo.agent import ChatContext
from graphedu.common.models.bo.exercise import (
    ExerciseGenerateRequest,
    ExerciseGenerateResponse,
    ExerciseWorkflowResponse,
)
from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum
from graphedu.common.models.shared import QuestionOptionContent
from graphedu.common.resource.deps import get_http_client
from graphedu.mcp.graphrag_query import logger
from graphedu.services.external.dify import DifyService

set_question_description = (
    "平台生成题目。工具会直接展出题目完整信息，除了答案和解析。\n"
    "何时使用:\n"
    "- 用户需要练习某个知识点，但没有特定题目要求时。\n"
    "- 用户对于某一知识点有疑问，且愿意通过做题学习知识点。\n"
    "- 用户要求做题。\n"
)
question_type_map = {
    "选择题": "single",
    "单选题": "single",
    "单项选择题": "single",
    "single": "single",
    "多选题": "multi",
    "多项选择题": "multi",
    "multi": "multi",
    "判断题": "judge",
    "judge": "judge",
    "简答题": "essay",
    "essay": "essay",
}


class SetQuestionArgsSchema(BaseModel):
    """设置问题工具的输入参数"""

    field: str = Field(description="知识点领域，例如：二叉树、动态规划")
    difficulty: str = Field(description="难度等级，例如：简单、中等、困难")
    question_type: str = Field(description="题目类型，例如：选择题、判断题、多选题")
    extra_info: str | None = Field(
        default=None, description="对需要出的题目的描述信息，描述越丰富细致，出的题目越符合预期"
    )


@tool("set_a_question", description=set_question_description, args_schema=SetQuestionArgsSchema)
async def set_question(
    field: str,
    difficulty: str,
    question_type: str,
    runtime: ToolRuntime[ChatContext, ChatState],
    extra_info: str | None = None,
) -> Command:
    """出题"""
    # 获取配置和 http_client
    config = get_config().dify
    http_client = await get_http_client()

    # 规范化题目类型
    normalized_question_type = question_type_map.get(question_type, "single")

    # 构建请求
    request = ExerciseGenerateRequest(
        field=field,
        difficulty=difficulty,
        question_type=normalized_question_type,
        extra_info=extra_info,
    )

    # 调用 Dify workflow
    try:
        workflow_response: ExerciseWorkflowResponse = await DifyService.invoke_workflow(
            inputs=request,
            user=str(runtime.context.user_id),
            api_key=config.workflows.exercise_generation.api_key,
            base_url=config.base_url,
            http_client=http_client,
            workflow_id=config.workflows.exercise_generation.id,
            return_model=ExerciseWorkflowResponse,
        )
    except Exception as e:
        logger.error(f"调用 Dify workflow 失败: {e}")
        return Command(
            update={
                "lc_messages": [ToolMessage(content=f"题目生成失败：{e}", tool_call_id=runtime.tool_call_id)],
            }
        )

    # 从 workflow 响应中提取题目
    exercise_response: ExerciseGenerateResponse = workflow_response.output

    # 构建答案列表
    if exercise_response.answer is None:
        answer_list: list[str] | None = None
    elif isinstance(exercise_response.answer, bool):
        answer_list = ["正确"] if exercise_response.answer else ["错误"]
    elif isinstance(exercise_response.answer, str):
        answer_list = [exercise_response.answer]
    else:
        answer_list = exercise_response.answer

    # 构建 QuestionOptionContent
    question_content = QuestionOptionContent(
        question_type=normalized_question_type,
        title=exercise_response.topic or f"{field} 练习",
        content=exercise_response.question,
        options=exercise_response.options
        or (
            ["A", "B", "C", "D"]
            if normalized_question_type not in ("judge", "essay")
            else ["正确", "错误"]
            if normalized_question_type == "judge"
            else []
        ),
        answer=answer_list,
        explanation=exercise_response.explanation,
    )

    # 构建 ChatMessage
    question_msg = ChatMessage.auto_new_message(
        role=RoleEnum.TOOL,
        content_type=ContentTypeEnum.QUESTION_OPTION,
        content=question_content,
        user_id=runtime.context.user_id,
        conv_id=runtime.context.conv_id,
    )

    return Command(
        update={
            "gm_messages": [question_msg],
            "lc_messages": [
                ToolMessage(
                    content=f"题目已经显示在屏幕上，用户当前可以看到题目。\n{exercise_response.model_dump()}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
