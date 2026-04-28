"""Admin 仪表盘 VO 模型"""

from pydantic import Field

from graphedu.common.models.vo import VO


class AdminDashboardSummaryVO(VO):
    """管理员仪表盘总览统计"""

    total_users: int = Field(default=0, description="总用户数")
    total_students: int = Field(default=0, description="总学生数")
    total_teachers: int = Field(default=0, description="总教师数")
    total_courses: int = Field(default=0, description="总课程数")
    total_knowledge_graphs: int = Field(default=0, description="总知识图谱数")
    today_login_users: int = Field(default=0, description="今日登录用户数")
