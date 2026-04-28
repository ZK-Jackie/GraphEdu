"""课程练习相关 VO 模型。"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.shared import QuestionOptionContent
from graphedu.common.models.vo import VO


class CourseExerciseListVO(VO):
    """课程练习列表项 VO"""

    exercise_id: int = Field(description="练习ID")
    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID（可选）")
    exercise: QuestionOptionContent | list[QuestionOptionContent] | None = Field(
        default=None,
        description="练习内容，结构同 QuestionOptionContent，支持单题或题目列表",
    )
    source: str | None = Field(default=None, description="练习来源")
    status: str = Field(description="练习状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")


class CourseExerciseDetailVO(CourseExerciseListVO):
    """课程练习详细信息 VO"""

    create_by: int | None = Field(default=None, description="创建者")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")


class CourseExerciseGenerateTaskVO(VO):
    """AI 习题异步生成任务提交结果 VO"""

    task_id: str = Field(description="Celery 任务 ID")
    task_status: str = Field(description="任务状态")
    message: str | None = Field(default=None, description="提示信息")


class CourseExerciseGenerateProgressVO(VO):
    """AI 习题异步生成任务进度 VO"""

    task_id: str = Field(description="Celery 任务 ID")
    task_status: str = Field(description="任务状态 (pending/processing/success/failed)")
    progress_percent: int = Field(default=0, description="进度百分比 (0-100)")
    generated_count: int = Field(default=0, description="已生成题目数量（成功时有效）")
    message: str | None = Field(default=None, description="进度描述或错误信息")


class ExerciseAttemptVO(VO):
    """作答记录 VO"""

    attempt_id: int = Field(description="作答记录ID")
    exercise_id: int = Field(description="关联习题ID")
    student_id: int = Field(description="学生ID")
    student_answer: list[str] | str | None = Field(default=None, description="学生答案")
    is_correct: bool | None = Field(default=None, description="是否正确")
    time_spent: int | None = Field(default=None, description="用时（秒）")
    attempt_time: datetime | None = Field(default=None, description="作答时间")


class ExerciseAttemptStatisticsVO(VO):
    """作答统计 VO"""

    exercise_id: int = Field(description="习题ID")
    total_attempts: int = Field(description="总作答次数")
    correct_count: int = Field(description="正确次数")
    correct_rate: float = Field(description="正确率（0-100）")
    avg_time_spent: float | None = Field(default=None, description="平均用时（秒）")
