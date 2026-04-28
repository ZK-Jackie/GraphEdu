"""课程练习相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery
from graphedu.common.models.shared import QuestionOptionContent


class CourseExerciseQueryDTO(PageQuery):
    """课程练习查询 DTO"""

    exercise_id: int | None = Field(default=None, description="练习ID")
    course_id: int | None = Field(default=None, description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    source: str | None = Field(default=None, description="练习来源")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="练习状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class CourseExerciseCreateDTO(DTO):
    """创建课程练习 DTO"""

    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID（可选）")
    exercise: QuestionOptionContent | list[QuestionOptionContent] | None = Field(
        default=None,
        description="练习内容，结构同 QuestionOptionContent，支持单题或题目列表",
    )
    source: str | None = Field(default=None, max_length=255, description="练习来源（如：教师上传、系统生成等）")


class CourseExerciseUpdateDTO(DTO):
    """更新课程练习 DTO"""

    exercise_id: int = Field(description="练习ID")
    chapter_id: int | None = Field(default=None, description="章节ID（可选）")
    exercise: QuestionOptionContent | list[QuestionOptionContent] | None = Field(
        default=None,
        description="练习内容，结构同 QuestionOptionContent，支持单题或题目列表",
    )
    source: str | None = Field(default=None, max_length=255, description="练习来源（如：教师上传、系统生成等）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="练习状态（0正常 1停用 2已删除）")


class CourseExerciseBatchGenerateDTO(DTO):
    """教师端批量生成课程练习 DTO"""

    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID（可选）")
    resource_ids: list[int] = Field(description="章节资料ID列表（edu_resource.resource_id）")
    difficulty: str | None = Field(default=None, description="难度等级（例如：简单、中等、困难）")
    question_type: Literal["single", "judge", "multi"] | None = Field(default=None, description="题目类型")
    extra_info: str | None = Field(default=None, description="需要出的题目的更多信息")
    number: int = Field(default=1, description="需要生成的习题数量")


class ExerciseAttemptSubmitDTO(DTO):
    """学生提交作答 DTO"""

    exercise_id: int = Field(description="关联习题ID")
    student_answer: list[str] | str = Field(description="学生答案（单选/判断为单个字符串，多选为列表）")
    time_spent: int | None = Field(default=None, ge=0, description="用时（秒）")


class ExerciseAttemptQueryDTO(PageQuery):
    """作答记录查询 DTO"""

    exercise_id: int | None = Field(default=None, description="习题ID")
    student_id: int | None = Field(default=None, description="学生ID")
    course_id: int | None = Field(default=None, description="课程ID（通过习题间接关联）")
    is_correct: bool | None = Field(default=None, description="是否正确")
