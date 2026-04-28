"""学生管理 Mapper 层

负责学生数据的访问操作，包括学生信息的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.student import StudentQueryDTO
from graphedu.common.models.orm.education import EduStudent
from graphedu.common.models.orm.system import SysUser


class StudentMapper:
    """学生数据访问层

    提供学生信息的 CRUD 操作。
    """

    @staticmethod
    async def add_student(student_info: EduStudent, db_session: AsyncSession) -> EduStudent:
        """添加学生

        :param db_session: 数据库会话
        :param student_info: 学生信息
        :return: 学生对象
        """
        db_session.add(student_info)
        await db_session.flush()
        return student_info

    @staticmethod
    async def get_by_id(student_id: int, db_session: AsyncSession) -> EduStudent | None:
        """根据学生ID查询学生信息

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :return: 学生对象
        """
        stmt = select(EduStudent).where(
            EduStudent.student_id == student_id, EduStudent.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_user_id(user_id: int, db_session: AsyncSession) -> EduStudent | None:
        """根据用户ID查询学生信息

        :param db_session: 数据库会话
        :param user_id: 用户ID
        :return: 学生对象
        """
        stmt = select(EduStudent).where(
            EduStudent.student_id == user_id, EduStudent.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def is_student_no_exists(student_no: str, db_session: AsyncSession) -> bool:
        """校验学号是否存在

        :param db_session: 数据库会话
        :param student_no: 学号
        :return: 是否存在
        """
        stmt = select(EduStudent).where(
            EduStudent.status != SystemConstants.Status.DELETED, EduStudent.student_no == student_no
        )
        student = (await db_session.execute(stmt)).scalars().first()
        return student is not None

    @staticmethod
    async def get_student_by_no_for_unique_check(student_no: str, db_session: AsyncSession) -> EduStudent | None:
        """根据学号查询学生（用于唯一性校验，查询所有未删除的学生）

        :param db_session: 数据库会话
        :param student_no: 学号
        :return: 学生对象
        """
        stmt = select(EduStudent).where(
            EduStudent.status != SystemConstants.Status.DELETED, EduStudent.student_no == student_no
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_student_by_no_for_binding(student_no: str, db_session: AsyncSession) -> EduStudent | None:
        """根据学号查询学生（用于身份绑定）

        :param db_session: 数据库会话
        :param student_no: 学号
        :return: 学生对象
        """
        stmt = select(EduStudent).where(
            EduStudent.student_no == student_no, EduStudent.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_student_list(
        db: AsyncSession, query_object: StudentQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[tuple[EduStudent, SysUser | None]], int]:
        """根据查询参数获取学生列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为学生列表，total为总数
        """
        # 构建基础查询条件
        base_conditions = [EduStudent.status != SystemConstants.Status.DELETED]

        if query_object.student_id is not None:
            base_conditions.append(EduStudent.student_id == query_object.student_id)
        if query_object.real_name:
            base_conditions.append(EduStudent.real_name.like(f"%{query_object.real_name}%"))
        if query_object.student_no:
            base_conditions.append(EduStudent.student_no.like(f"%{query_object.student_no}%"))
        if query_object.faculty:
            base_conditions.append(EduStudent.faculty.like(f"%{query_object.faculty}%"))
        if query_object.major:
            base_conditions.append(EduStudent.major.like(f"%{query_object.major}%"))
        if query_object.grade:
            base_conditions.append(EduStudent.grade.like(f"%{query_object.grade}%"))
        if query_object.class_name:
            base_conditions.append(EduStudent.class_name.like(f"%{query_object.class_name}%"))
        if query_object.gender:
            base_conditions.append(EduStudent.gender == int(query_object.gender))
        if query_object.status:
            base_conditions.append(EduStudent.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduStudent.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建主查询（关联 sys_user 表获取用户账号等信息）
        query = (
            select(EduStudent, SysUser)
            .join(
                SysUser,
                and_(EduStudent.student_id == SysUser.user_id, SysUser.status != SystemConstants.Status.DELETED),
                isouter=True,
            )
            .where(and_(*base_conditions))
            .order_by(EduStudent.student_id)
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count(func.distinct(EduStudent.student_id)))
            .select_from(EduStudent)
            .join(
                SysUser,
                and_(EduStudent.student_id == SysUser.user_id, SysUser.status != SystemConstants.Status.DELETED),
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
    async def update(student_info: EduStudent, query_db: AsyncSession) -> None:
        """更新学生信息

        :param query_db: 数据库会话
        :param student_info: 学生信息
        :return: None
        """
        await query_db.merge(student_info)
        await query_db.flush()

    @staticmethod
    async def delete_student(student_id: int, query_db: AsyncSession) -> None:
        """根据学生ID软删除学生

        :param query_db: 数据库会话
        :param student_id: 学生ID
        :return: None
        """
        student = await StudentMapper.get_by_id(student_id, query_db)
        if student:
            student.status = SystemConstants.Status.DELETED
            await StudentMapper.update(student, query_db)

    @staticmethod
    async def get_unbound_students(
        db: AsyncSession, query_object: StudentQueryDTO, is_page: bool = True
    ) -> tuple[Sequence[SysUser], int]:
        """查询未关联学生记录的 sys_user 列表

        返回 sys_user 中不存在对应 edu_student 记录的正常状态用户，
        可用于"创建学生时选择要关联的用户"等场景。

        :param db: 数据库会话
        :param query_object: 查询参数对象（仅使用 real_name / student_no 做模糊过滤）
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为用户列表，total为总数
        """
        # 基础条件：sys_user 正常状态，且在 edu_student 中没有对应记录
        base_conditions = [
            SysUser.status == SystemConstants.Status.NORMAL,
            ~SysUser.user_id.in_(
                select(EduStudent.student_id).where(EduStudent.status != SystemConstants.Status.DELETED)
            ),
        ]

        # 可选过滤条件（使用 real_name 匹配用户昵称，student_no 匹配用户账号）
        if query_object.real_name:
            base_conditions.append(SysUser.nick_name.like(f"%{query_object.real_name}%"))
        if query_object.student_no:
            base_conditions.append(SysUser.user_name.like(f"%{query_object.student_no}%"))

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
