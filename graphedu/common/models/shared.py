"""跨层共享的内容模型。

此处放置被 DTO、VO、Service 等多层同时使用的纯数据结构。
这些模型不属于任何特定分层（非 DTO/VO/BO），仅供复用。
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class QuestionOptionContent(BaseModel):
    """题目类型消息"""

    question_type: str
    """题目类型，例如：选择题、判断题、多选题、简答题等"""

    title: str
    """消息卡片标题"""

    content: str
    """消息问题或正文"""

    options: list[str]
    """选项列表"""

    answer: list[str] | None = Field(default=None)
    """题目答案"""

    explanation: str | None = Field(default=None)
    """题目解析"""

    exercise_id: int | None = Field(default=None)
    """关联习题ID（来自题库时非空，用于前端提交作答记录）"""

    model_config = ConfigDict(alias_generator=to_camel, validate_by_alias=True, validate_by_name=True)
