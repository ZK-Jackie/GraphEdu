"""学生管理服务模块

该模块提供学生信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.student import (
    StudentAlreadyExistsException,
    StudentIdListEmptyException,
    StudentNoAlreadyExistsException,
    StudentNotFoundException,
)
from graphedu.common.exceptions.services.system.user import UserIdNotFoundException
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.student import StudentCreateDTO, StudentQueryDTO, StudentUpdateDTO
from graphedu.common.models.orm.education import EduStudent
from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem, PageResponse
from graphedu.common.models.vo.educationv2.student import StudentDetailVO, StudentListVO
from graphedu.mapper.education.student import StudentMapper
from graphedu.mapper.education.study_analytics import StudyAnalyticsMapper
from graphedu.mapper.system.user import UserMapper

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_student_orm_to_list_vo(student_orm: EduStudent, user_name: str | None = None) -> StudentListVO:
    """将学生 ORM 对象转换为 StudentListVO。

    Args:
        student_orm: 学生 ORM 对象。
        user_name: 用户账号（可选）。

    Returns:
        StudentListVO: 学生列表项 VO。
    """
    return StudentListVO(
        student_id=student_orm.student_id,
        real_name=student_orm.real_name,
        student_no=student_orm.student_no,
        faculty=student_orm.faculty,
        major=student_orm.major,
        grade=student_orm.grade,
        class_name=student_orm.class_name,
        gender=student_orm.gender,
        status=student_orm.status,
        create_time=student_orm.create_time,
        user_id=student_orm.student_id,
        user_name=user_name,
        avatar_file_id=None,  # 如果需要头像信息，需要额外查询
    )


def _convert_student_orm_to_detail_vo(
    student_orm: EduStudent,
    user_name: str | None = None,
    *,
    total_study_time: int | None = None,
    course_count: int | None = None,
) -> StudentDetailVO:
    """将学生 ORM 对象转换为 StudentDetailVO。

    Args:
        student_orm: 学生 ORM 对象。
        user_name: 用户账号（可选）。
        total_study_time: 从 LearningEvent 实时聚合的学习时长（分钟）。
        course_count: 从 LearningEvent 实时聚合的课程数。

    Returns:
        StudentDetailVO: 学生详细信息 VO。
    """
    return StudentDetailVO(
        student_id=student_orm.student_id,
        real_name=student_orm.real_name,
        student_no=student_orm.student_no,
        faculty=student_orm.faculty,
        major=student_orm.major,
        grade=student_orm.grade,
        class_name=student_orm.class_name,
        gender=student_orm.gender,
        age=student_orm.age,
        study_style=student_orm.study_style,
        study_habit=student_orm.study_habit,
        continue_day=student_orm.continue_day,
        vip_level=student_orm.vip_level,
        vip_expire_time=student_orm.vip_expire_time,
        total_study_time=total_study_time,
        course_count=course_count,
        description=student_orm.description,
        status=student_orm.status,
        create_by=student_orm.create_by,
        create_time=student_orm.create_time,
        update_by=student_orm.update_by,
        update_time=student_orm.update_time,
        user_id=student_orm.student_id,
        user_name=user_name,
        avatar_file_id=None,  # 如果需要头像信息，需要额外查询
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_student_no_exists(student_no: str, query_db: AsyncSession) -> bool:
    """校验学号是否存在。

    Args:
        student_no: 学号。
        query_db: 数据库会话。

    Returns:
        bool: 学号是否存在。
    """
    return await StudentMapper.is_student_no_exists(student_no, query_db)


async def _check_student_no_unique_for_update(student_id: int, student_no: str, query_db: AsyncSession) -> bool:
    """校验学号是否唯一（编辑时用）。

    Args:
        student_id: 学生 ID。
        student_no: 学号。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在其他学生使用该学号）。
    """
    if not student_no:
        return False
    existing_student = await StudentMapper.get_student_by_no_for_unique_check(student_no, query_db)
    return existing_student is not None and existing_student.student_id != student_id


# ============================================================================
# StudentService 类
# ============================================================================


class StudentService:
    """学生管理服务类

    提供学生的增删改查功能。
    """

    @staticmethod
    async def add_student(
        query_db: AsyncSession, student_data: StudentCreateDTO, current_user: CurrentUser | None
    ) -> StudentDetailVO:
        """新增学生信息。

        Args:
            query_db: 数据库会话。
            student_data: 新增学生 DTO。
            current_user: 当前登录用户。

        Returns:
            StudentDetailVO: 创建成功的学生 VO。

        Raises:
            UserIdNotFoundException: 对应的用户不存在。
            Exception: 学号已存在等其他异常。
        """
        # 1. 校验用户是否存在
        user = await UserMapper.get_by_id(student_data.student_id, query_db)
        if not user:
            raise UserIdNotFoundException(student_data.student_id)

        # 2. 校验该用户是否已存在学生记录
        existing_student = await StudentMapper.get_by_user_id(student_data.student_id, query_db)
        if existing_student:
            raise StudentAlreadyExistsException(user_id=student_data.student_id)

        # 3. 校验学号唯一性
        if student_data.student_no and await _check_student_no_exists(student_data.student_no, query_db):
            raise StudentNoAlreadyExistsException(student_no=student_data.student_no)

        # 4. DTO → ORM
        new_student = EduStudent(
            **student_data.model_dump(exclude={"student_id"}),
            student_id=student_data.student_id,  # 确保 student_id 被正确设置
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
            create_time=datetime.now(),
        )

        # 5. 新增学生
        await StudentMapper.add_student(new_student, query_db)

        logger.info(f"新增学生成功: {student_data.real_name}")

        # 6. 返回创建后的学生 VO
        return _convert_student_orm_to_detail_vo(new_student, user_name=user.user_name)

    @staticmethod
    async def update_student(
        query_db: AsyncSession, student_data: StudentUpdateDTO, current_user: CurrentUser
    ) -> StudentDetailVO:
        """更新学生信息。

        Args:
            query_db: 数据库会话。
            student_data: 更新学生 DTO。
            current_user: 当前登录用户。

        Returns:
            StudentDetailVO: 更新后的学生 VO.

        Raises:
            UserIdNotFoundException: 学生不存在。
            Exception: 学号已存在等其他异常。
        """
        # 1. 获取目标学生
        target_student = await StudentMapper.get_by_id(student_data.student_id, query_db)
        if target_student is None:
            raise UserIdNotFoundException(student_data.student_id)

        # 2. 唯一性校验（使用目标学生的数据进行对比）
        if (
            student_data.student_no is not None
            and student_data.student_no != target_student.student_no
            and await _check_student_no_unique_for_update(student_data.student_id, student_data.student_no, query_db)
        ):
            raise StudentNoAlreadyExistsException(student_no=student_data.student_no)

        # 3. 更新目标学生
        update_data = student_data.model_dump(exclude_unset=True, exclude={"student_id"})
        for field, value in update_data.items():
            setattr(target_student, field, value)

        target_student.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_student.update_time = datetime.now()

        await StudentMapper.update(target_student, query_db)

        # 获取用户账号
        user = await UserMapper.get_by_id(student_data.student_id, query_db)
        user_name = user.user_name if user else None

        # 4. 返回更新后的学生 VO
        return _convert_student_orm_to_detail_vo(target_student, user_name=user_name)

    @staticmethod
    async def list_student(query_db: AsyncSession, query_object: StudentQueryDTO) -> PageResponse[StudentListVO]:
        """获取学生列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[StudentListVO]: 分页结果。
        """
        rows, total = await StudentMapper.get_student_list(query_db, query_object)

        # 将 ORM 对象转换为 StudentListVO
        student_list = []
        for row in rows:
            student_orm = row[0]
            user_orm = row[1]
            user_name = user_orm.user_name if user_orm else None
            student_list.append(_convert_student_orm_to_list_vo(student_orm, user_name))

        return PageResponse(rows=student_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def delete_student(
        query_db: AsyncSession, student_id_list: list[int], current_user: CurrentUser
    ) -> BatchDeleteResponse[int]:
        """删除学生信息（批量，部分成功模式）。

        Args:
            query_db: 数据库会话。
            student_id_list: 学生 ID 列表。
            current_user: 当前用户。

        Returns:
            BatchDeleteResponse[int]: 包含成功数量、失败数量和详细结果的响应对象

        Raises:
            StudentIdListEmptyException: 学生 ID 列表为空。
        """
        if not student_id_list:
            raise StudentIdListEmptyException

        results: list[DeleteResultItem[int]] = []

        for student_id in student_id_list:
            try:
                student = await StudentMapper.get_by_id(student_id, query_db)
                if not student:
                    results.append(DeleteResultItem(target_id=student_id, success=False, error="学生不存在"))
                    continue

                # 软删除学生（令 status 为 DELETED）
                student.status = SystemConstants.Status.DELETED
                student.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                student.update_time = datetime.now()
                await StudentMapper.update(student, query_db)

                results.append(DeleteResultItem(target_id=student_id, success=True, error=None))

            except Exception as e:
                results.append(DeleteResultItem(target_id=student_id, success=False, error=str(e)))

        logger.info(
            f"批量删除学生完成: "
            f"{sum(1 for r in results if r.success)} 成功, "
            f"{sum(1 for r in results if not r.success)} 失败"
        )

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def change_student_status(
        query_db: AsyncSession, student_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改学生状态。

        Args:
            query_db: 数据库会话。
            student_id: 学生 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            StudentNotFoundException: 学生不存在。
        """
        student = await StudentMapper.get_by_id(student_id, query_db)
        if not student:
            raise StudentNotFoundException(student_id=student_id)

        student.status = status
        student.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        student.update_time = datetime.now()
        await StudentMapper.update(student, query_db)
        logger.info(f"修改学生状态成功: {student_id}")

    @staticmethod
    async def get_student_detail(query_db: AsyncSession, student_id: int) -> StudentDetailVO | None:
        """获取学生详细信息。

        total_study_time 和 course_count 从 EduStudentLearningEvent 实时聚合，
        确保与学生课程首页的数据源一致。

        Args:
            query_db: 数据库会话。
            student_id: 学生 ID。

        Returns:
            StudentDetailVO | None: 学生详细信息 VO。
        """
        student = await StudentMapper.get_by_id(student_id, query_db)
        if not student:
            return None

        # 获取用户账号
        user = await UserMapper.get_by_id(student_id, query_db)
        user_name = user.user_name if user else None

        # 从 LearningEvent 实时聚合学习统计
        global_stats = await StudyAnalyticsMapper.get_student_global_stats(student_id, query_db)
        total_study_minutes = round((global_stats["total_study_seconds"] or 0) / 60) if global_stats else 0
        live_course_count = global_stats["course_count"] if global_stats else 0

        return _convert_student_orm_to_detail_vo(
            student,
            user_name=user_name,
            total_study_time=total_study_minutes,
            course_count=live_course_count,
        )

    @staticmethod
    async def get_unbound_students(
        query_db: AsyncSession, query_object: StudentQueryDTO
    ) -> PageResponse[StudentListVO]:
        """查询未绑定的学生列表（user_id 为 null 的学生）

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[StudentListVO]: 分页结果。
        """
        # 调用 Mapper 查询未绑定的学生
        rows, total = await StudentMapper.get_unbound_students(query_db, query_object, is_page=True)

        # 转换为 VO
        student_list = [_convert_student_orm_to_list_vo(student_orm=student, user_name=None) for student in rows]

        # 构建分页响应
        return PageResponse(
            rows=student_list,
            total=total,
            page=query_object.page or 1,
            size=query_object.size or 10,
        )
