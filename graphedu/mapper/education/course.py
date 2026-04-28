"""课程管理 Mapper 层

负责课程数据的访问操作，包括课程信息的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.course import CourseQueryDTO
from graphedu.common.models.orm.education import EduCourse


class CourseMapper:
    """课程数据访问层

    提供课程信息的 CRUD 操作。
    """

    @staticmethod
    async def add_course(course_info: EduCourse, db_session: AsyncSession) -> EduCourse:
        """添加课程

        :param db_session: 数据库会话
        :param course_info: 课程信息
        :return: 课程对象
        """
        db_session.add(course_info)
        await db_session.flush()
        return course_info

    @staticmethod
    async def get_by_id(course_id: int, db_session: AsyncSession) -> EduCourse | None:
        """根据课程ID查询课程信息

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 课程对象
        """
        stmt = select(EduCourse).where(
            EduCourse.course_id == course_id, EduCourse.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_course_by_code_for_unique_check(course_code: str, db_session: AsyncSession) -> EduCourse | None:
        """根据课程代码查询课程（用于唯一性校验）

        :param db_session: 数据库会话
        :param course_code: 课程代码
        :return: 课程对象
        """
        stmt = select(EduCourse).where(
            EduCourse.status != SystemConstants.Status.DELETED, EduCourse.course_code == course_code
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_course_list(
        db: AsyncSession, query_object: CourseQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[tuple[EduCourse, int | None, str | None]], int]:
        """根据查询参数获取课程列表信息（包含主教师）

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows为 (课程, 教师ID, 教师姓名) 元组列表，total为总数
        """
        from graphedu.common.models.orm.education import EduCourseTeacher, EduTeacher

        # 构建基础查询条件
        base_conditions = [EduCourse.status != SystemConstants.Status.DELETED]

        if query_object.course_id is not None:
            base_conditions.append(EduCourse.course_id == query_object.course_id)
        if query_object.course_code:
            base_conditions.append(EduCourse.course_code.like(f"%{query_object.course_code}%"))
        if query_object.course_name:
            base_conditions.append(EduCourse.course_name.like(f"%{query_object.course_name}%"))
        if query_object.faculty:
            base_conditions.append(EduCourse.faculty.like(f"%{query_object.faculty}%"))
        if query_object.status:
            base_conditions.append(EduCourse.status == query_object.status)
        if query_object.is_public:
            base_conditions.append(EduCourse.is_public == query_object.is_public)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduCourse.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 使用子查询获取每个课程的主教师（第一个绑定的教师）
        teacher_subquery = (
            select(EduCourseTeacher.course_id, EduCourseTeacher.teacher_id, EduTeacher.real_name)
            .join(EduTeacher, EduCourseTeacher.teacher_id == EduTeacher.teacher_id)
            .where(EduTeacher.status != SystemConstants.Status.DELETED)
            .distinct()
            .order_by(EduCourseTeacher.course_id, EduCourseTeacher.teacher_id)
        ).alias("teacher_cte")

        # 使用 DISTINCT ON 获取每个课程的第一个教师
        teacher_first = (
            select(
                func.row_number()
                .over(partition_by=teacher_subquery.c.course_id, order_by=teacher_subquery.c.teacher_id)
                .label("rn"),
                teacher_subquery.c.course_id.label("t_course_id"),
                teacher_subquery.c.teacher_id,
                teacher_subquery.c.real_name,
            ).select_from(teacher_subquery)
        ).alias("teacher_first")

        # 构建 LEFT JOIN 查询
        query = (
            select(EduCourse, teacher_first.c.teacher_id, teacher_first.c.real_name)
            .outerjoin(
                teacher_first,
                and_(
                    EduCourse.course_id == teacher_first.c.t_course_id,
                    teacher_first.c.rn == 1,
                ),
            )
            .where(and_(*base_conditions))
            .order_by(EduCourse.course_id.desc())
        )

        # 获取总数
        count_query = select(func.count()).select_from(EduCourse).where(and_(*base_conditions))
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
    async def update(course_info: EduCourse, query_db: AsyncSession) -> None:
        """更新课程信息

        :param query_db: 数据库会话
        :param course_info: 课程信息
        :return: None
        """
        await query_db.merge(course_info)
        await query_db.flush()

    @staticmethod
    async def delete_course(course_id: int, query_db: AsyncSession) -> None:
        """根据课程ID软删除课程

        :param query_db: 数据库会话
        :param course_id: 课程ID
        :return: None
        """
        course = await CourseMapper.get_by_id(course_id, query_db)
        if course:
            course.status = SystemConstants.Status.DELETED
            await CourseMapper.update(course, query_db)

    @staticmethod
    async def get_course_detail_with_relations(
        course_id: int, db_session: AsyncSession
    ) -> tuple[EduCourse | None, list]:
        """获取课程详情及其关联的教师（使用 JOIN 优化）

        参考: graphedu/mapper/course_teacher.py 的 get_course_teacher_list() 方法

        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: (课程对象, 教师列表) 元组
        """
        from graphedu.common.models.orm.education import EduCourseTeacher, EduTeacher

        # 1. 查询课程基本信息
        course = await CourseMapper.get_by_id(course_id, db_session)
        if not course:
            return None, []

        # 2. 使用 JOIN 查询教师（参考 CourseTeacherMapper.get_course_teacher_list）
        teacher_query = (
            select(EduTeacher)
            .join(
                EduCourseTeacher,
                and_(
                    EduCourseTeacher.teacher_id == EduTeacher.teacher_id,
                    EduTeacher.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(EduCourseTeacher.course_id == course_id)
            .order_by(EduTeacher.teacher_id)
            .distinct()
        )
        teacher_result = await db_session.execute(teacher_query)
        teachers = list(teacher_result.scalars().all())

        return course, teachers

    @staticmethod
    async def get_teacher_course_list(
        db: AsyncSession,
        teacher_id: int,
        query_object: "CourseQueryDTO",
        is_page: bool = False,
    ) -> tuple[Sequence[tuple[EduCourse, int | None, str | None]], int]:
        """获取指定教师任教的课程列表（仅含该教师课程，附带主教师信息）

        :param db: 数据库会话
        :param teacher_id: 教师ID（只返回该教师的课程）
        :param query_object: 查询参数对象（支持 course_name/course_code/status）
        :param is_page: 是否开启分页
        :return: (rows, total) 元组，rows 为 (课程, 教师ID, 教师姓名) 元组列表
        """
        from graphedu.common.models.orm.education import EduCourseTeacher, EduTeacher

        # 构建过滤条件
        base_conditions = [EduCourse.status != SystemConstants.Status.DELETED]
        if hasattr(query_object, "course_name") and query_object.course_name:
            base_conditions.append(EduCourse.course_name.like(f"%{query_object.course_name}%"))
        if hasattr(query_object, "course_code") and query_object.course_code:
            base_conditions.append(EduCourse.course_code.like(f"%{query_object.course_code}%"))
        if hasattr(query_object, "status") and query_object.status:
            base_conditions.append(EduCourse.status == query_object.status)

        # 子查询：取每个课程的第一个教师
        teacher_subquery = (
            select(EduCourseTeacher.course_id, EduCourseTeacher.teacher_id, EduTeacher.real_name)
            .join(EduTeacher, EduCourseTeacher.teacher_id == EduTeacher.teacher_id)
            .where(EduTeacher.status != SystemConstants.Status.DELETED)
            .distinct()
            .order_by(EduCourseTeacher.course_id, EduCourseTeacher.teacher_id)
        ).alias("teacher_cte")

        teacher_first = (
            select(
                func.row_number()
                .over(
                    partition_by=teacher_subquery.c.course_id,
                    order_by=teacher_subquery.c.teacher_id,
                )
                .label("rn"),
                teacher_subquery.c.course_id.label("t_course_id"),
                teacher_subquery.c.teacher_id,
                teacher_subquery.c.real_name,
            ).select_from(teacher_subquery)
        ).alias("teacher_first")

        # INNER JOIN edu_course_teacher 限定当前教师的课程
        query = (
            select(EduCourse, teacher_first.c.teacher_id, teacher_first.c.real_name)
            .join(
                EduCourseTeacher,
                and_(
                    EduCourse.course_id == EduCourseTeacher.course_id,
                    EduCourseTeacher.teacher_id == teacher_id,
                ),
            )
            .outerjoin(
                teacher_first,
                and_(
                    EduCourse.course_id == teacher_first.c.t_course_id,
                    teacher_first.c.rn == 1,
                ),
            )
            .where(and_(*base_conditions))
            .order_by(EduCourse.course_id.desc())
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count(func.distinct(EduCourse.course_id)))
            .select_from(EduCourse)
            .join(
                EduCourseTeacher,
                and_(
                    EduCourse.course_id == EduCourseTeacher.course_id,
                    EduCourseTeacher.teacher_id == teacher_id,
                ),
            )
            .where(and_(*base_conditions))
        )
        total = (await db.execute(count_query)).scalar() or 0

        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        rows = (await db.execute(query)).all()
        return rows, total
