"""教师根据文件生成习题业务"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from graphedu.common.models.bo.dify import DifyFile
from graphedu.common.utils import try_parse_json_object


class CourseExerciseGenerateRequest(BaseModel):
    """习题生成请求"""

    upload_files: list[DifyFile] | None = Field(default_factory=list, description="上传的文件")
    difficulty: str | None = Field(default=None, description="难度等级（例如：简单、中等、困难）")
    question_type: Literal["single", "judge", "multi"] | None = Field(default=None, description="题目类型")
    extra_info: str | None = Field(default=None, description="需要出的题目的更多信息，如更多对题目类型的描述等")
    number: int = Field(default=1, description="需要生成的习题数量")


class CourseExerciseGenerateResponse(BaseModel):
    """习题生成响应"""

    topic: str = Field(description="知识点主题")
    question: str = Field(description="练习题的问题描述")
    answer: str | list[str] | bool = Field(
        description="练习题的答案，可以是字符串、字符串列表或布尔值，具体取决于题目类型"
    )
    explanation: str | None = Field(default=None, description="练习题的答案解析或解答步骤")
    options: list[str] | None = Field(default=None, description="练习题的选项列表，适用于选择题")


class CourseExerciseWorkflowResponse(BaseModel):
    """习题生成 Workflow 响应"""

    output: list[CourseExerciseGenerateResponse]
    usage: dict | None
    reasoning_content: str | None
    structured_output: dict | None

    model_config = ConfigDict(extra="allow")

    @field_validator("output", mode="before")
    @classmethod
    def output_response_validator(cls, value: list | CourseExerciseGenerateResponse | str):
        """输出序列化"""
        if isinstance(value, str):
            _, value = try_parse_json_object(value, expect_type=list)
        if isinstance(value, list):
            return [
                CourseExerciseGenerateResponse.model_validate_strings(item)
                if isinstance(item, str)
                else CourseExerciseGenerateResponse.model_validate(item)
                for item in value
            ]
        if isinstance(value, CourseExerciseGenerateResponse):
            return value
        raise ValidationError("Invalid output format for CourseExerciseWorkflowResponse")
