"""教育统计分析 VO 模型"""

from datetime import date, datetime
from typing import Any

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.educationv2.chapter import ChapterCompletionItemVO, ChapterListVO
from graphedu.common.models.vo.educationv2.course import CourseStudentStatsVO
from graphedu.common.models.vo.educationv2.fragments import (
    CoverageFragment,
    InteractionFragment,
    MasteryDistributionFragment,
    MasteryFragment,
    StudyTimeFragment,
)

# ============================================================================
# 简单 VO（字段少，无需 Fragment）
# ============================================================================


class StudentRecordVO(VO):
    """学习记录 VO（合并原 DetailVO + ListVO）"""

    record_id: int = Field(description="记录ID")
    student_id: int = Field(description="学生ID")
    course_id: int | None = Field(default=None, description="课程ID")
    session_id: int | None = Field(default=None, description="会话ID")
    study_duration: int = Field(default=0, description="学习时长（分钟）")
    question_count: int = Field(default=0, description="提问数量")
    study_date: date = Field(description="学习日期")
    create_time: datetime = Field(description="创建时间")
    # ListVO 额外字段（可选）
    course_name: str | None = Field(default=None, description="课程名称")
    student_name: str | None = Field(default=None, description="学生姓名")


class DailyActiveItemVO(VO):
    """教师工作台：每日活跃度列表项 VO"""

    date: str = Field(description="日期（MM-DD 格式）")
    count: int = Field(default=0, description="当日活跃学生数")


class ProgressDistributionItemVO(VO):
    """教师工作台：进度分布列表项 VO"""

    range: str = Field(description="进度区间（如 0-20%）")
    count: int = Field(default=0, description="落在该区间的学生数")


class StudentDailyActiveItemVO(VO):
    """每日学习活跃度项 VO"""

    date: str = Field(description="日期（MM-DD 格式）")
    active_minutes: int = Field(default=0, description="活跃时长（分钟）")


class DashboardCalendarItemVO(VO):
    """日历热力图数据项"""

    date: str = Field(description="日期（YYYY-MM-DD）")
    minutes: int = Field(default=0, description="学习分钟数")


class DashboardCourseItemVO(VO):
    """仪表盘课程卡片项"""

    course_id: int = Field(description="课程ID")
    course_name: str = Field(description="课程名称")
    cover_url: str | None = Field(default=None, description="封面URL")
    progress: int = Field(default=0, description="学习进度（0-100）")
    last_study_time: datetime | None = Field(default=None, description="最后学习时间")


class StudentResourceProgressItemVO(VO):
    """学生资源阅读进度项 VO"""

    resource_id: int = Field(description="资料ID")
    resource_name: str = Field(description="资料名称")
    resource_type: str = Field(description="资料类型（video/document/text）")
    completion_rate: int = Field(default=0, description="完成度（0-100）")
    is_completed: str = Field(default="N", description="是否完成（Y/N）")
    view_count: int = Field(default=0, description="阅读次数")
    total_duration: int = Field(default=0, description="累计阅读时长（秒）")
    last_view_time: datetime | None = Field(default=None, description="最后阅读时间")


class StudentDashboardSummaryVO(VO):
    """学生仪表盘总览统计"""

    total_study_days: int = Field(default=0, description="累计学习天数")
    total_study_minutes: int = Field(default=0, description="总学习时长（分钟）")
    effective_study_minutes: int = Field(default=0, description="有效学习时长（分钟），排除空闲")
    review_study_minutes: int = Field(default=0, description="复习时长（分钟）")
    active_course_count: int = Field(default=0, description="在修课程数")
    consecutive_days: int = Field(default=0, description="连续学习天数")


class TeacherDashboardSummaryVO(VO):
    """教师仪表盘总览统计"""

    total_courses: int = Field(default=0, description="课程总数")
    total_students: int = Field(default=0, description="总学生数")
    today_active_students: int = Field(default=0, description="今日活跃学生数")
    avg_mastery_score: float | None = Field(default=None, description="平均掌握度评分")


class TeacherDashboardCourseVO(VO):
    """教师仪表盘课程概览项"""

    course_id: int = Field(description="课程ID")
    course_name: str = Field(default="", description="课程名称")
    student_count: int = Field(default=0, description="学生数")
    avg_mastery_score: float = Field(default=0, description="平均掌握度评分")
    quiz_correct_rate: float | None = Field(default=None, description="答题正确率（%）")


class TeacherDashboardRankingVO(VO):
    """教师仪表盘学生排名项"""

    student_id: int = Field(description="学生ID")
    student_name: str = Field(default="", description="学生姓名")
    course_name: str = Field(default="", description="所属课程")
    mastery_percentile: float = Field(description="掌握度百分位（0-1）")
    avg_mastery_score: float | None = Field(default=None, description="平均掌握度评分")


class StudentChapterResourceDetailVO(VO):
    """教师工作台：学生章节资料阅读明细"""

    progress_id: int = Field(description="进度记录ID")
    resource_id: int = Field(description="资料ID")
    resource_name: str | None = Field(default=None, description="资料名称")
    resource_type: str = Field(description="资料类型")
    completion_rate: int = Field(default=0, description="完成度（0-100）")
    is_completed: str = Field(default="N", description="是否完成（Y/N）")
    view_count: int = Field(default=0, description="阅读次数")
    total_duration: int = Field(default=0, description="累计阅读时长（秒）")
    last_view_time: datetime | None = Field(default=None, description="最后阅读时间")


class StudentChapterExerciseDetailVO(VO):
    """教师工作台：学生章节答题记录明细"""

    attempt_id: int = Field(description="作答记录ID")
    exercise_id: int = Field(description="习题ID")
    student_answer: Any | None = Field(default=None, description="学生答案")
    is_correct: bool | None = Field(default=None, description="是否正确")
    time_spent: int | None = Field(default=None, description="用时（秒）")
    attempt_time: datetime | None = Field(default=None, description="作答时间")


class StudentChapterMasteryDetailVO(VO):
    """教师工作台：学生章节知识点掌握明细"""

    mastery_id: int = Field(description="评估记录ID")
    node_uuid: str = Field(description="知识点UUID")
    node_title: str | None = Field(default=None, description="知识点标题")
    mastery_score: float | None = Field(default=None, description="掌握度评分（0-100）")
    mastery_level: str | None = Field(default=None, description="掌握等级")
    assessed_at: datetime | None = Field(default=None, description="评估时间")


class StudentChapterDetailResultVO(VO):
    """教师工作台：学生章节可展开详情结果"""

    detail_type: str = Field(description="详情类型（resources/exercises/mastery）")
    items: list[Any] = Field(default_factory=list, description="详情列表")
    total: int = Field(default=0, description="总数")


# ============================================================================
# Fragment 增强型 VO（通过继承消除字段重复）
# ============================================================================


class StudentKnowledgeProfileVO(InteractionFragment, MasteryFragment, VO):
    """学生知识点画像 VO"""

    node_uuid: str = Field(description="知识点UUID")
    node_name: str = Field(default="", description="知识点名称")
    first_interaction_at: datetime | None = Field(default=None, description="首次交互时间")
    last_interaction_at: datetime | None = Field(default=None, description="最后交互时间")
    total_study_seconds: int = Field(default=0, description="总学习时长（秒）")
    latest_assessment_reason: str | None = Field(default=None, description="最新AI评估理由")


class StudentWeakPointVO(MasteryFragment, VO):
    """学生薄弱知识点 VO"""

    node_uuid: str = Field(description="知识点UUID")
    node_name: str = Field(default="", description="知识点名称")
    total_interaction_count: int = Field(default=0, description="总交互次数")
    total_question_count: int = Field(default=0, description="总提问次数")
    total_study_seconds: int = Field(default=0, description="总学习时长（秒）")
    effort_ratio: float = Field(default=0, description="投入产出比")


class DashboardWeakPointVO(MasteryFragment, VO):
    """仪表盘薄弱知识点项（含课程名）"""

    node_uuid: str = Field(description="知识点UUID")
    node_name: str = Field(default="", description="知识点名称")
    course_name: str = Field(default="", description="所属课程名称")
    total_interaction_count: int = Field(default=0, description="总交互次数")
    total_question_count: int = Field(default=0, description="总提问次数")
    total_study_seconds: int = Field(default=0, description="总学习时长（秒）")


class StudentRankingItemVO(CoverageFragment, StudyTimeFragment, VO):
    """教师工作台：课程学生排名项 VO"""

    student_id: int = Field(description="学生ID")
    student_name: str = Field(default="", description="学生姓名")
    total_event_count: int = Field(default=0, description="总事件数")
    question_count: int = Field(default=0, description="提问次数")
    quiz_count: int = Field(default=0, description="答题次数")
    quiz_correct_rate: float | None = Field(default=None, description="答题正确率（%）")
    avg_mastery_score: float | None = Field(default=None, description="平均掌握度评分")
    study_days: int = Field(default=0, description="学习天数")
    mastery_percentile: float = Field(default=0, description="掌握度百分位（0-1）")
    # 覆盖 StudyTimeFragment 的可选类型为必填
    total_study_seconds: int = Field(default=0, description="总学习时长（秒）")


class CourseAnalyticsVO(MasteryDistributionFragment, VO):
    """教师工作台：课程数据分析 VO"""

    total_students: int = Field(default=0, description="总学生数")
    active_students: int = Field(default=0, description="时间范围内活跃学生数")
    average_progress: int = Field(default=0, description="平均学习进度（0-100）")
    total_study_time: int = Field(default=0, description="时间范围内总学习时长（分钟）")
    chapter_completion: list[ChapterCompletionItemVO] = Field(default_factory=list, description="章节完成率列表")
    daily_active: list[DailyActiveItemVO] = Field(default_factory=list, description="每日活跃度列表")
    progress_distribution: list[ProgressDistributionItemVO] = Field(default_factory=list, description="学习进度分布")
    total_event_count: int = Field(default=0, description="总事件数")
    total_question_count: int = Field(default=0, description="总提问次数")
    total_quiz_count: int = Field(default=0, description="总答题次数")
    quiz_correct_rate: float = Field(default=0, description="答题正确率（%）")
    avg_mastery_score: float | None = Field(default=None, description="平均掌握度评分")
    nodes_touched: int = Field(default=0, description="接触的知识点数")


class StudentChapterLearningItemVO(StudyTimeFragment, VO):
    """教师工作台：学生章节学习摘要项"""

    chapter_id: int = Field(description="章节ID")
    chapter_name: str = Field(description="章节名称")
    chapter_no: int = Field(default=0, description="章节序号")
    parent_id: int = Field(default=0, description="父章节ID")
    completion_rate: int = Field(default=0, description="章节完成度（0-100）")
    is_completed: str = Field(default="N", description="是否完成（Y/N）")
    quiz_total: int = Field(default=0, description="总答题次数")
    quiz_correct: int = Field(default=0, description="答对次数")
    quiz_correct_rate: float | None = Field(default=None, description="答题正确率（0-100）")
    avg_mastery_score: float | None = Field(default=None, description="平均知识点掌握评分（0-100）")
    last_study_time: datetime | None = Field(default=None, description="最后学习时间")
    # 覆盖 StudyTimeFragment 的可选类型为必填
    total_study_seconds: int = Field(default=0, description="学习时长（秒）")


# ============================================================================
# 复合 VO（结构复杂，保持独立）
# ============================================================================


class ChapterProgressDetailVO(VO):
    """章节进度详细信息 VO（来自物化视图）"""

    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    completion_rate: int = Field(default=0, description="章节完成度（0-100）")
    is_completed: str = Field(description="是否完成（Y/N）")
    first_visit_time: datetime | None = Field(default=None, description="首次访问时间")
    last_visit_time: datetime | None = Field(default=None, description="最后访问时间")
    complete_time: datetime | None = Field(default=None, description="完成时间")
    chapter: ChapterListVO | None = Field(default=None, description="关联章节信息")


class ChapterProgressListVO(VO):
    """章节进度列表项 VO（来自物化视图）"""

    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    completion_rate: int = Field(default=0, description="章节完成度（0-100）")
    is_completed: str = Field(description="是否完成（Y/N）")
    last_visit_time: datetime | None = Field(default=None, description="最后访问时间")
    chapter_name: str | None = Field(default=None, description="章节名称")


class StudentCourseOverviewVO(VO):
    """学生课程学习概览 VO"""

    course_id: int = Field(description="课程ID")
    student_id: int = Field(description="学生ID")
    progress: int = Field(default=0, description="学习进度（0-100）")
    completed_chapters: int = Field(default=0, description="已完成章节数")
    total_chapters: int = Field(default=0, description="总章节数")
    total_study_time: int = Field(default=0, description="累计学习时长（分钟）")
    last_study_time: datetime | None = Field(default=None, description="最后学习时间")
    consecutive_days: int = Field(default=0, description="连续学习天数")
    rank_percentile: str | None = Field(default=None, description="排名百分位（如 'Top 5%'）")
    course_stats: CourseStudentStatsVO = Field(description="课程整体统计")
    daily_active: list[StudentDailyActiveItemVO] = Field(default_factory=list, description="每日学习活跃度")


class StudentChapterProgressVO(VO):
    """学生章节学习进度 VO"""

    chapter_id: int = Field(description="章节ID")
    chapter_name: str = Field(description="章节名称")
    chapter_no: int = Field(default=0, description="章节序号")
    parent_id: int = Field(default=0, description="父章节ID")
    completion_rate: int = Field(default=0, description="完成度（0-100）")
    is_completed: str = Field(default="N", description="是否完成（Y/N）")
    resource_count: int = Field(default=0, description="总资料数")
    completed_resource_count: int = Field(default=0, description="已完成资料数")
    last_visit_time: datetime | None = Field(default=None, description="最后访问时间")
    resources: list[StudentResourceProgressItemVO] = Field(default_factory=list, description="资料阅读进度列表")


class StudentChapterLearningResultVO(VO):
    """教师工作台：学生章节学习汇总结果"""

    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    chapters: list[StudentChapterLearningItemVO] = Field(default_factory=list, description="章节学习列表")
    total_chapters: int = Field(default=0, description="总章节数")
    completed_chapters: int = Field(default=0, description="已完成章节数")
    total_study_seconds: int = Field(default=0, description="总学习时长（秒）")
