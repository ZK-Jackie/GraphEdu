"""教师管理 Mapper 层

负责教师数据的访问操作，包括教师信息的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.teacher import TeacherQueryDTO
from graphedu.common.models.orm.education import EduTeacher
from graphedu.common.models.orm.system import SysUser


class TeacherMapper:
    """教师数据访问层

    提供教师信息的 CRUD 操作。
    """

    @staticmethod
    async def add_teacher(teacher_info: EduTeacher, db_session: AsyncSession) -> EduTeacher:
        """添加教师

        :param db_session: 数据库会话
        :param teacher_info: 教师信息
        :return: 教师对象
        """
        db_session.add(teacher_info)
        await db_session.flush()
        return teacher_info

    @staticmethod
    async def get_by_id(teacher_id: int, db_session: AsyncSession) -> EduTeacher | None:
        """根据教师ID查询教师信息

        :param db_session: 数据库会话
        :param teacher_id: 教师ID
        :return: 教师对象
        """
        stmt = select(EduTeacher).where(
            EduTeacher.teacher_id == teacher_id, EduTeacher.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_user_id(user_id: int, db_session: AsyncSession) -> EduTeacher | None:
        """根据用户ID查询教师信息

        :param db_session: 数据库会话
        :param user_id: 用户ID
        :return: 教师对象
        """
        stmt = select(EduTeacher).where(
            EduTeacher.teacher_id == user_id, EduTeacher.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def is_teacher_no_exists(teacher_no: str, db_session: AsyncSession) -> bool:
        """校验工号是否存在

        :param db_session: 数据库会话
        :param teacher_no: 工号
        :return: 是否存在
        """
        stmt = select(EduTeacher).where(
            EduTeacher.status != SystemConstants.Status.DELETED, EduTeacher.teacher_no == teacher_no
        )
        teacher = (await db_session.execute(stmt)).scalars().first()
        return teacher is not None

    @staticmethod
    async def get_teacher_by_no_for_unique_check(teacher_no: str, db_session: AsyncSession) -> EduTeacher | None:
        """根据工号查询教师（用于唯一性校验，查询所有未删除的教师）

        :param db_session: 数据库会话
        :param teacher_no: 工号
        :return: 教师对象
        """
        stmt = select(EduTeacher).where(
            EduTeacher.status != SystemConstants.Status.DELETED, EduTeacher.teacher_no == teacher_no
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_teacher_by_no_for_binding(teacher_no: str, db_session: AsyncSession) -> EduTeacher | None:
        """根据工号查询教师（用于身份绑定）

        :param db_session: 数据库会话
        :param teacher_no: 工号
        :return: 教师对象
        """
        stmt = select(EduTeacher).where(
            EduTeacher.teacher_no == teacher_no, EduTeacher.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_teacher_list(
        db: AsyncSession, query_object: TeacherQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[tuple[EduTeacher, SysUser | None]], int]:
        """根据查询参数获取教师列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为教师列表，total为总数
        """
        # 构建基础查询条件
        base_conditions = [EduTeacher.status != SystemConstants.Status.DELETED]

        if query_object.teacher_id is not None:
            base_conditions.append(EduTeacher.teacher_id == query_object.teacher_id)
        if query_object.real_name:
            base_conditions.append(EduTeacher.real_name.like(f"%{query_object.real_name}%"))
        if query_object.teacher_no:
            base_conditions.append(EduTeacher.teacher_no.like(f"%{query_object.teacher_no}%"))
        if query_object.faculty:
            base_conditions.append(EduTeacher.faculty.like(f"%{query_object.faculty}%"))
        if query_object.title:
            base_conditions.append(EduTeacher.title.like(f"%{query_object.title}%"))
        if query_object.status:
            base_conditions.append(EduTeacher.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduTeacher.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建主查询（关联 sys_user 表获取用户账号等信息）
        query = (
            select(EduTeacher, SysUser)
            .join(
                SysUser,
                and_(EduTeacher.teacher_id == SysUser.user_id, SysUser.status != SystemConstants.Status.DELETED),
                isouter=True,
            )
            .where(and_(*base_conditions))
            .order_by(EduTeacher.teacher_id)
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count(func.distinct(EduTeacher.teacher_id)))
            .select_from(EduTeacher)
            .join(
                SysUser,
                and_(EduTeacher.teacher_id == SysUser.user_id, SysUser.status != SystemConstants.Status.DELETED),
                isouter=True,
            )
            .where(and_(*base_conditions))
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.all()

        return rows, total

    @staticmethod
    async def update(teacher_info: EduTeacher, query_db: AsyncSession) -> None:
        """更新教师信息

        :param query_db: 数据库会话
        :param teacher_info: 教师信息
        :return: None
        """
        await query_db.merge(teacher_info)
        await query_db.flush()

    @staticmethod
    async def delete_teacher(teacher_id: int, query_db: AsyncSession) -> None:
        """根据教师ID软删除教师

        :param query_db: 数据库会话
        :param teacher_id: 教师ID
        :return: None
        """
        teacher = await TeacherMapper.get_by_id(teacher_id, query_db)
        if teacher:
            teacher.status = SystemConstants.Status.DELETED
            await TeacherMapper.update(teacher, query_db)

    @staticmethod
    async def get_unbound_teachers(
        db: AsyncSession, query_object: TeacherQueryDTO, is_page: bool = True
    ) -> tuple[Sequence[SysUser], int]:
        """查询未关联教师记录的 sys_user 列表

        返回 sys_user 中不存在对应 edu_teacher 记录的正常状态用户，
        可用于"创建教师时选择要关联的用户"等场景。

        :param db: 数据库会话
        :param query_object: 查询参数对象（仅使用 real_name / teacher_no 做模糊过滤）
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为用户列表，total为总数
        """
        # 基础条件：sys_user 正常状态，且在 edu_teacher 中没有对应记录
        base_conditions = [
            SysUser.status == SystemConstants.Status.NORMAL,
            ~SysUser.user_id.in_(
                select(EduTeacher.teacher_id).where(EduTeacher.status != SystemConstants.Status.DELETED)
            ),
        ]

        # 可选过滤条件（使用 real_name 匹配用户昵称，teacher_no 匹配用户账号）
        if query_object.real_name:
            base_conditions.append(SysUser.nick_name.like(f"%{query_object.real_name}%"))
        if query_object.teacher_no:
            base_conditions.append(SysUser.user_name.like(f"%{query_object.teacher_no}%"))

        # 构建主查询
        query = select(SysUser).where(and_(*base_conditions)).order_by(SysUser.user_id).distinct()

        # 获取总数
        count_query = (
            select(func.count(func.distinct(SysUser.user_id)))
            .select_from(SysUser)
            .where(and_(*base_conditions))
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.scalars().all()

        return rows, total
