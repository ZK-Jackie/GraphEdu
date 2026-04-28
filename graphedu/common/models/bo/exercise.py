"""习题业务"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExerciseGenerateRequest(BaseModel):
    """习题生成请求"""

    field: str | None = Field(default=None, description="知识点领域")
    difficulty: str | None = Field(default=None, description="难度等级（例如：简单、中等、困难）")
    question_type: str | None = Field(default=None, description="题目类型（例如：选择题、判断题、多选题、简答题）")
    extra_info: str | None = Field(default=None, description="需要出的题目的更多信息，如更多对题目类型的描述等")


class ExerciseGenerateResponse(BaseModel):
    """习题生成响应"""

    topic: str = Field(description="知识点主题")
    question: str = Field(description="练习题的问题描述")
    answer: str | list[str] | bool = Field(
        description="练习题的答案，可以是字符串、字符串列表或布尔值，具体取决于题目类型"
    )
    explanation: str | None = Field(default=None, description="练习题的答案解析或解答步骤")
    options: list[str] | None = Field(default=None, description="练习题的选项列表，适用于选择题")


class ExerciseWorkflowResponse(BaseModel):
    """习题生成 Workflow 响应"""

    output: ExerciseGenerateResponse
    usage: dict
    reasoning_content: str
    structured_output: dict

    model_config = ConfigDict(extra="allow")

    @field_validator("output", mode="before")
    @classmethod
    def output_response_validator(cls, value: dict | ExerciseGenerateResponse | str):
        """输出序列化"""
        if isinstance(value, str):
            return ExerciseGenerateResponse.model_validate_json(value)
        return ExerciseGenerateResponse.model_validate(value)
