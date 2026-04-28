"""课程 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.educationv2.teacher import TeacherListVO


class CourseDetailVO(VO):
    """课程详细信息 VO"""

    course_id: int = Field(description="课程ID")
    course_code: str = Field(description="课程代码")
    course_name: str = Field(description="课程名称")
    faculty: str | None = Field(default=None, description="所属学院")
    description: str | None = Field(default=None, description="课程描述")
    cover_file_id: int | None = Field(default=None, description="课程封面文件ID")
    cover_url: str | None = Field(default=None, description="课程封面URL")
    # 课程扩展信息
    category: str | None = Field(default=None, description="课程分类")
    difficulty_level: str = Field(default="1", description="难度级别（1初级 2中级 3高级）")
    total_hours: int = Field(default=0, description="总学时（小时）")
    course_outline: str | None = Field(default=None, description="课程大纲（富文本）")
    target_audience: str | None = Field(default=None, description="适用人群（富文本）")
    learning_goals: str | None = Field(default=None, description="学习目标（富文本）")
    tags: list[str] | None = Field(default=None, description="课程标签列表")
    # 课程状态
    status: str = Field(description="课程状态，对照 sys_data_status（0正常 1停用 2已删除）")
    is_public: str = Field(description="是否公开，对照 sys_data_option（Y是 N否）")
    student_count: int = Field(default=0, description="学生人数")
    view_count: int = Field(default=0, description="浏览次数")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")

    # 关联信息
    teacher_ids: list[int] | None = Field(default=None, description="授课教师ID列表")
    teachers: list[TeacherListVO] | None = Field(default=None, description="授课教师列表")


class CourseListVO(VO):
    """课程列表项 VO"""

    course_id: int = Field(description="课程ID")
    course_code: str = Field(description="课程代码")
    course_name: str = Field(description="课程名称")
    faculty: str | None = Field(default=None, description="所属学院")
    cover_file_id: int | None = Field(default=None, description="课程封面文件ID")
    cover_url: str | None = Field(default=None, description="课程封面URL")
    # 课程扩展信息
    category: str | None = Field(default=None, description="课程分类")
    difficulty_level: str = Field(default="1", description="难度级别（1初级 2中级 3高级）")
    total_hours: int = Field(default=0, description="总学时（小时）")
    tags: list[str] | None = Field(default=None, description="课程标签列表")
    # 课程状态
    status: str = Field(description="课程状态，对照 sys_data_status（0正常 1停用 2已删除）")
    is_public: str = Field(description="是否公开，对照 sys_data_option（Y是 N否）")
    student_count: int = Field(default=0, description="学生人数")
    view_count: int = Field(default=0, description="浏览次数")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联的教师信息（主教师）
    teacher_id: int | None = Field(default=None, description="主教师ID")
    teacher_name: str | None = Field(default=None, description="主教师姓名")


class CourseStudentVO(VO):
    """教师工作台：课程学生列表项 VO"""

    enrollment_id: int = Field(description="选课记录ID")
    student_id: int = Field(description="学生ID")
    real_name: str = Field(description="真实姓名")
    student_no: str | None = Field(default=None, description="学号")
    class_name: str | None = Field(default=None, description="班级")
    faculty: str | None = Field(default=None, description="学院")
    gender: int | None = Field(default=None, description="性别（1男 2女 0未知）")
    avatar_url: str | None = Field(default=None, description="头像URL")
    enroll_time: datetime = Field(description="选课时间")
    progress: int = Field(default=0, description="学习进度（0-100）")
    last_study_time: datetime | None = Field(default=None, description="最后学习时间")
    status: str = Field(description="学生状态（0正常 1停用 2已删除）")


class CourseStudentStatsVO(VO):
    """教师工作台：课程学生统计汇总 VO"""

    total_students: int = Field(default=0, description="总学生数")
    average_progress: int = Field(default=0, description="平均学习进度（0-100）")
    completed_students: int = Field(default=0, description="已完成学生数（progress=100）")
    today_active: int = Field(default=0, description="今日活跃学生数")


class CourseStudentsResultVO(VO):
    """教师工作台：课程学生列表+统计 VO"""

    students: list[CourseStudentVO] = Field(default_factory=list, description="学生列表")
    stats: CourseStudentStatsVO = Field(description="统计汇总")
    total: int = Field(default=0, description="总记录数")


class StudentCourseDetailVO(VO):
    """学生选课详细信息 VO"""

    id: int = Field(description="记录ID")
    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    enroll_time: datetime = Field(description="选课时间")
    progress: int = Field(default=0, description="学习进度（0-100）")
    last_study_time: datetime | None = Field(default=None, description="最后学习时间")

    # 关联的课程信息
    course: CourseListVO | None = Field(default=None, description="课程信息")


class StudentCourseListVO(VO):
    """学生选课列表项 VO"""

    id: int = Field(description="记录ID")
    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    enroll_time: datetime = Field(description="选课时间")
    progress: int = Field(default=0, description="学习进度（0-100）")
    last_study_time: datetime | None = Field(default=None, description="最后学习时间")

    # 关联的课程信息
    course_name: str | None = Field(default=None, description="课程名称")
    course_code: str | None = Field(default=None, description="课程代码")
    cover_file_id: int | None = Field(default=None, description="课程封面文件ID")
    cover_url: str | None = Field(default=None, description="课程封面URL")


class StudentCourseProgressVO(VO):
    """学生课程学习进度视图 VO（教师端，从事件表聚合计算）"""

    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    course_name: str = Field(description="课程名称")
    total_event_count: int = Field(description="总事件数")
    question_count: int = Field(description="提问次数")
    interest_count: int = Field(description="标记兴趣次数")
    explain_request_count: int = Field(description="请求解释次数")
    quiz_count: int = Field(description="答题次数")
    quiz_correct_count: int = Field(description="答对次数")
    quiz_correct_rate: float | None = Field(default=None, description="答题正确率（%）")
    avg_mastery_score: float | None = Field(default=None, description="平均掌握度评分")
    max_mastery_score: float | None = Field(default=None, description="最高掌握度评分")
    chapters_touched: int = Field(description="接触的章节数")
    total_chapters: int = Field(description="课程总章节数")
    chapter_coverage_rate: float = Field(description="章节覆盖率（%）")
    nodes_touched: int = Field(description="接触的知识点数")
    total_nodes: int = Field(description="课程总知识点数")
    node_coverage_rate: float = Field(description="知识点覆盖率（%）")
    total_study_seconds: int | None = Field(default=None, description="总学习时长（秒）")
    study_days: int = Field(description="学习天数")
    first_event_time: datetime | None = Field(default=None, description="首次事件时间")
    last_event_time: datetime | None = Field(default=None, description="最后事件时间")


class CourseStudentRankingVO(VO):
    """课程学生排名视图 VO（含掌握度、覆盖率、学习时长百分位）"""

    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    course_name: str = Field(description="课程名称")
    total_event_count: int = Field(description="总事件数")
    question_count: int = Field(description="提问次数")
    quiz_count: int = Field(description="答题次数")
    quiz_correct_rate: float | None = Field(default=None, description="答题正确率（%）")
    avg_mastery_score: float | None = Field(default=None, description="平均掌握度评分")
    chapters_touched: int = Field(description="接触的章节数")
    chapter_coverage_rate: float = Field(description="章节覆盖率（%）")
    nodes_touched: int = Field(description="接触的知识点数")
    node_coverage_rate: float = Field(description="知识点覆盖率（%）")
    total_study_seconds: int | None = Field(default=None, description="总学习时长（秒）")
    study_days: int = Field(description="学习天数")
    mastery_percentile: float = Field(description="掌握度百分位（0-1）")
    coverage_percentile: float = Field(description="覆盖率百分位（0-1）")
    study_time_percentile: float = Field(description="学习时长百分位（0-1）")
