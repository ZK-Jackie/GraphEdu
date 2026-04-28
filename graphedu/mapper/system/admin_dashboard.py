"""Admin 仪表盘 Mapper 层

提供管理员仪表盘所需的聚合统计查询。
"""

from datetime import date

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduCourse, EduKnowledgeGraph, EduStudent, EduTeacher
from graphedu.common.models.orm.system import SysLogininfor, SysUser


class AdminDashboardMapper:
    """管理员仪表盘数据访问层"""

    @staticmethod
    async def get_total_users(db: AsyncSession) -> int:
        """获取总用户数（排除已删除）"""
        stmt = select(func.count()).select_from(SysUser).where(SysUser.status != "2")
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_total_students(db: AsyncSession) -> int:
        """获取总学生数（排除已删除）"""
        stmt = select(func.count()).select_from(EduStudent).where(EduStudent.status != "2")
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_total_teachers(db: AsyncSession) -> int:
        """获取总教师数（排除已删除）"""
        stmt = select(func.count()).select_from(EduTeacher).where(EduTeacher.status != "2")
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_total_courses(db: AsyncSession) -> int:
        """获取总课程数（排除已删除）"""
        stmt = select(func.count()).select_from(EduCourse).where(EduCourse.status != "2")
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_total_knowledge_graphs(db: AsyncSession) -> int:
        """获取总知识图谱数（排除已删除）"""
        stmt = select(func.count()).select_from(EduKnowledgeGraph).where(EduKnowledgeGraph.status != "2")
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_today_login_users(db: AsyncSession) -> int:
        """获取今日登录用户数（按用户名去重）"""
        today = date.today()
        stmt = (
            select(func.count(func.distinct(SysLogininfor.user_name)))
            .where(cast(SysLogininfor.login_time, Date) == today)
            .where(SysLogininfor.status == "0")
        )
        return (await db.execute(stmt)).scalar() or 0
