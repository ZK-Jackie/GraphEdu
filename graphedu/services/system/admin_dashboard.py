"""Admin 仪表盘服务模块

提供管理员仪表盘的业务逻辑。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.vo.systemv2.admin_dashboard import AdminDashboardSummaryVO
from graphedu.mapper.system.admin_dashboard import AdminDashboardMapper


class AdminDashboardService:
    """管理员仪表盘服务类"""

    @staticmethod
    async def get_overview(query_db: AsyncSession) -> AdminDashboardSummaryVO:
        """获取管理员仪表盘总览统计

        :param query_db: 数据库会话
        :return: 管理员仪表盘总览 VO
        """
        total_users = await AdminDashboardMapper.get_total_users(query_db)
        total_students = await AdminDashboardMapper.get_total_students(query_db)
        total_teachers = await AdminDashboardMapper.get_total_teachers(query_db)
        total_courses = await AdminDashboardMapper.get_total_courses(query_db)
        total_knowledge_graphs = await AdminDashboardMapper.get_total_knowledge_graphs(query_db)
        today_login_users = await AdminDashboardMapper.get_today_login_users(query_db)

        return AdminDashboardSummaryVO(
            total_users=total_users,
            total_students=total_students,
            total_teachers=total_teachers,
            total_courses=total_courses,
            total_knowledge_graphs=total_knowledge_graphs,
            today_login_users=today_login_users,
        )
