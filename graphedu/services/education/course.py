"""课程管理服务模块

该模块提供课程信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.course import (
    CourseCodeAlreadyExistsException,
    CourseIdListEmptyException,
    CourseNotFoundException,
)
from graphedu.common.exceptions.services.education.teacher import TeacherNotFoundException
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.course import CourseCreateDTO, CourseQueryDTO, CourseUpdateDTO
from graphedu.common.models.orm.education import EduCourse
from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem, PageResponse
from graphedu.common.models.vo.educationv2.course import CourseDetailVO, CourseListVO
from graphedu.common.models.vo.educationv2.teacher import TeacherListVO
from graphedu.common.resource import AioS3Client
from graphedu.mapper.education.course import CourseMapper
from graphedu.mapper.education.course_teacher import CourseTeacherMapper
from graphedu.mapper.education.student_course import StudentCourseMapper
from graphedu.mapper.education.teacher import TeacherMapper
from graphedu.services.system.upload import UploadService

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_course_orm_to_list_vo(course_orm: EduCourse) -> CourseListVO:
    """将课程 ORM 对象转换为 CourseListVO。

    Args:
        course_orm: 课程 ORM 对象。

    Returns:
        CourseListVO: 课程列表项 VO。
    """
    # 处理 tags 字段（从 JSONB 转换为 list）
    tags_list = None
    if course_orm.tags is not None:
        if isinstance(course_orm.tags, list):
            tags_list = course_orm.tags
        elif isinstance(course_orm.tags, dict):
            tags_list = list(course_orm.tags.keys()) if course_orm.tags else None

    return CourseListVO(
        course_id=course_orm.course_id,
        course_code=course_orm.course_code,
        course_name=course_orm.course_name,
        faculty=course_orm.faculty,
        cover_file_id=course_orm.cover_file_id,
        cover_url=None,  # 如果需要封面URL，需要额外查询
        # 课程扩展信息
        category=course_orm.category,
        difficulty_level=course_orm.difficulty_level,
        total_hours=course_orm.total_hours,
        tags=tags_list,
        # 课程状态
        status=course_orm.status,
        is_public=course_orm.is_public,
        student_count=course_orm.student_count,
        view_count=course_orm.view_count,
        create_time=course_orm.create_time,
        teacher_id=None,  # 如果需要教师信息，需要额外查询
        teacher_name=None,
    )


def _convert_course_orm_to_detail_vo(course_orm: EduCourse) -> CourseDetailVO:
    """将课程 ORM 对象转换为 CourseDetailVO。

    Args:
        course_orm: 课程 ORM 对象。

    Returns:
        CourseDetailVO: 课程详细信息 VO。
    """
    # 处理 tags 字段（从 JSONB 转换为 list）
    tags_list = None
    if course_orm.tags is not None:
        if isinstance(course_orm.tags, list):
            tags_list = course_orm.tags
        elif isinstance(course_orm.tags, dict):
            tags_list = list(course_orm.tags.keys()) if course_orm.tags else None

    return CourseDetailVO(
        course_id=course_orm.course_id,
        course_code=course_orm.course_code,
        course_name=course_orm.course_name,
        faculty=course_orm.faculty,
        description=course_orm.description,
        cover_file_id=course_orm.cover_file_id,
        cover_url=None,  # 如果需要封面URL，需要额外查询
        # 课程扩展信息
        category=course_orm.category,
        difficulty_level=course_orm.difficulty_level,
        total_hours=course_orm.total_hours,
        course_outline=course_orm.course_outline,
        target_audience=course_orm.target_audience,
        learning_goals=course_orm.learning_goals,
        tags=tags_list,
        # 课程状态
        status=course_orm.status,
        is_public=course_orm.is_public,
        student_count=course_orm.student_count,
        view_count=course_orm.view_count,
        create_by=course_orm.create_by,
        create_time=course_orm.create_time,
        update_by=course_orm.update_by,
        update_time=course_orm.update_time,
        teacher_ids=None,  # 如果需要教师信息，需要额外查询
        teachers=None,
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_course_code_exists(course_code: str, query_db: AsyncSession) -> bool:
    """校验课程代码是否存在。

    Args:
        course_code: 课程代码。
        query_db: 数据库会话。

    Returns:
        bool: 课程代码是否存在。
    """
    existing_course = await CourseMapper.get_course_by_code_for_unique_check(course_code, query_db)
    return existing_course is not None


async def _check_course_code_unique_for_update(course_id: int, course_code: str, query_db: AsyncSession) -> bool:
    """校验课程代码是否唯一（编辑时用）。

    Args:
        course_id: 课程 ID。
        course_code: 课程代码。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在其他课程使用该代码）。
    """
    if not course_code:
        return False
    existing_course = await CourseMapper.get_course_by_code_for_unique_check(course_code, query_db)
    return existing_course is not None and existing_course.course_id != course_id


async def _check_course_permission(course_id: int, current_user: CurrentUser, query_db: AsyncSession) -> None:
    """检查用户是否有权限操作该课程。

    Args:
        course_id: 课程 ID。
        current_user: 当前用户。
        query_db: 数据库会话。

    Raises:
        CourseNoPermissionException: 无权限。
    """
    from graphedu.common.exceptions.services.education.course import CourseNoPermissionException
    from graphedu.mapper.education.course_teacher import CourseTeacherMapper

    # 管理员拥有全部权限
    if current_user.is_admin():
        return

    # 检查是否为教师
    if not current_user.detail or not current_user.detail.teacher_info:
        raise CourseNoPermissionException(course_id=course_id)

    teacher_id = current_user.detail.teacher_info.teacher_id

    # 检查教师是否教授该课程
    course_teacher = await CourseTeacherMapper.get_by_ids(course_id, teacher_id, query_db)
    if not course_teacher:
        raise CourseNoPermissionException(course_id=course_id)


# ============================================================================
# CourseService 类
# ============================================================================


class CourseService:
    """课程管理服务类

    提供课程的增删改查功能。
    """

    @staticmethod
    async def add_course(
        query_db: AsyncSession,
        course_data: CourseCreateDTO,
        current_user: CurrentUser | None,
        s3_client: AioS3Client | None = None,
    ) -> CourseDetailVO:
        """新增课程信息。

        如果 course_data.teacher_ids 非空，则在同一事务中完成教师绑定。

        Args:
            query_db: 数据库会话。
            course_data: 新增课程 DTO。
            current_user: 当前登录用户。
            s3_client: S3 客户端（可选，用于获取封面 URL）。

        Returns:
            CourseDetailVO: 创建成功的课程 VO。

        Raises:
            CourseCodeAlreadyExistsException: 课程代码已存在。
            TeacherNotFoundException: 教师不存在（当提供 teacher_ids 时）。
        """
        # 1. 校验课程代码唯一性
        if await _check_course_code_exists(course_data.course_code, query_db):
            raise CourseCodeAlreadyExistsException(course_code=course_data.course_code)

        # 2. 校验教师是否存在（如果提供了 teacher_ids）
        if course_data.teacher_ids:
            for teacher_id in course_data.teacher_ids:
                teacher = await TeacherMapper.get_by_id(teacher_id, query_db)
                if not teacher:
                    raise TeacherNotFoundException(teacher_id=teacher_id)

        # 3. DTO → ORM（排除 teacher_ids）
        course_fields = course_data.model_dump(exclude={"teacher_ids"})
        new_course = EduCourse(
            **course_fields,
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
            create_time=datetime.now(),
        )

        # 4. 新增课程
        await CourseMapper.add_course(new_course, query_db)
        course_id = new_course.course_id

        # 5. 绑定教师（在同一事务中）
        if course_data.teacher_ids:
            for teacher_id in course_data.teacher_ids:
                await CourseTeacherMapper.bind_teacher(course_id, teacher_id, query_db)
            logger.info(f"新增课程成功（包含关联）: {course_data.course_name}, 教师: {len(course_data.teacher_ids)} 人")
        else:
            logger.info(f"新增课程成功: {course_data.course_name}")

        # 6. 返回创建后的课程 VO（使用优化后的查询方法）
        return await CourseService.get_course_detail(query_db, course_id, s3_client)

    @staticmethod
    async def update_course(
        query_db: AsyncSession,
        course_data: CourseUpdateDTO,
        current_user: CurrentUser,
        s3_client: AioS3Client | None = None,
    ) -> CourseDetailVO:
        """更新课程信息。

        Args:
            query_db: 数据库会话。
            course_data: 更新课程 DTO。
            current_user: 当前登录用户。
            s3_client: S3 客户端（可选，用于获取封面 URL）。

        Returns:
            CourseDetailVO: 更新后的课程 VO.

        Raises:
            CourseNotFoundException: 课程不存在。
            CourseCodeAlreadyExistsException: 课程代码已存在。
            CourseNoPermissionException: 无权限操作该课程。
        """
        # 1. 获取目标课程
        target_course = await CourseMapper.get_by_id(course_data.course_id, query_db)
        if target_course is None:
            raise CourseNotFoundException(course_id=course_data.course_id)

        # 2. 权限检查
        await _check_course_permission(course_data.course_id, current_user, query_db)

        # 2. 唯一性校验（使用目标课程的数据进行对比）
        if (
            course_data.course_code is not None
            and course_data.course_code != target_course.course_code
            and await _check_course_code_unique_for_update(course_data.course_id, course_data.course_code, query_db)
        ):
            raise CourseCodeAlreadyExistsException(course_code=course_data.course_code)

        # 3. 更新目标课程
        update_data = course_data.model_dump(exclude_unset=True, exclude={"course_id"})
        for field, value in update_data.items():
            setattr(target_course, field, value)

        target_course.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_course.update_time = datetime.now()

        await CourseMapper.update(target_course, query_db)

        # 4. 返回更新后的完整课程 VO（含教师、书籍关联信息）
        return await CourseService.get_course_detail(query_db, target_course.course_id, s3_client)

    @staticmethod
    async def list_course(
        query_db: AsyncSession, query_object: CourseQueryDTO, s3_client: AioS3Client | None = None
    ) -> PageResponse[CourseListVO]:
        """获取课程列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。
            s3_client: S3 客户端（可选，用于获取封面 URL）。

        Returns:
            PageResponse[CourseListVO]: 分页结果。
        """
        rows, total = await CourseMapper.get_course_list(query_db, query_object, is_page=True)

        # 批量查询实际学生数量（从选课表动态统计，避免冗余计数器不准确）
        course_ids = [row[0].course_id for row in rows]
        student_count_map = await StudentCourseMapper.batch_get_student_count(course_ids, query_db)

        # 将 ORM 对象转换为 CourseListVO
        course_list = []
        for row in rows:
            course_orm, teacher_id, teacher_name = row
            # 用动态统计的学生数覆盖 ORM 中的冗余字段
            course_orm.student_count = student_count_map.get(course_orm.course_id, 0)
            course_vo = _convert_course_orm_to_list_vo(course_orm)
            # 填充教师信息
            course_vo.teacher_id = teacher_id
            course_vo.teacher_name = teacher_name
            course_list.append(course_vo)

        # 批量获取封面 URL
        if s3_client:
            cover_file_ids = [course.cover_file_id for course in course_list if course.cover_file_id]
            if cover_file_ids:
                url_map = await UploadService.get_file_url_map(cover_file_ids, query_db, s3_client)
                for course in course_list:
                    if course.cover_file_id:
                        course.cover_url = url_map.get(course.cover_file_id)

        return PageResponse(rows=course_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def delete_course(
        query_db: AsyncSession, course_id_list: list[int], current_user: CurrentUser
    ) -> BatchDeleteResponse[int]:
        """删除课程信息（批量，部分成功模式）。

        Args:
            query_db: 数据库会话。
            course_id_list: 课程 ID 列表。
            current_user: 当前用户。

        Returns:
            BatchDeleteResponse[int]: 包含成功数量、失败数量和详细结果的响应对象

        Raises:
            CourseIdListEmptyException: 课程 ID 列表为空。
        """
        if not course_id_list:
            raise CourseIdListEmptyException

        results: list[DeleteResultItem[int]] = []

        for course_id in course_id_list:
            try:
                # 权限检查
                await _check_course_permission(course_id, current_user, query_db)

                course = await CourseMapper.get_by_id(course_id, query_db)
                if not course:
                    results.append(DeleteResultItem(target_id=course_id, success=False, error="课程不存在"))
                    continue

                # 1. 清理关联数据（在软删除前清理）
                # 解绑所有教师
                await CourseTeacherMapper.unbind_all_teachers(course_id, query_db)
                # 注意：学生选课记录保留作为历史记录，不删除

                # 2. 软删除课程（令 status 为 DELETED）
                course.status = SystemConstants.Status.DELETED
                course.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                course.update_time = datetime.now()
                await CourseMapper.update(course, query_db)

                results.append(DeleteResultItem(target_id=course_id, success=True, error=None))

            except Exception as e:
                results.append(DeleteResultItem(target_id=course_id, success=False, error=str(e)))

        logger.info(
            f"批量删除课程完成: "
            f"{sum(1 for r in results if r.success)} 成功, "
            f"{sum(1 for r in results if not r.success)} 失败"
        )

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def change_course_status(
        query_db: AsyncSession, course_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改课程状态。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            CourseNotFoundException: 课程不存在。
            CourseNoPermissionException: 无权限操作该课程。
        """
        # 权限检查
        await _check_course_permission(course_id, current_user, query_db)

        course = await CourseMapper.get_by_id(course_id, query_db)
        if not course:
            raise CourseNotFoundException(course_id=course_id)

        course.status = status
        course.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        course.update_time = datetime.now()
        await CourseMapper.update(course, query_db)
        logger.info(f"修改课程状态成功: {course_id}")

    @staticmethod
    async def get_course_detail(
        query_db: AsyncSession, course_id: int, s3_client: AioS3Client | None = None
    ) -> CourseDetailVO | None:
        """获取课程详细信息（优化版，使用 JOIN 查询）

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            s3_client: S3 客户端（可选，用于获取封面 URL）。

        Returns:
            CourseDetailVO | None: 课程详细信息 VO（包含教师信息）。
        """
        # 使用新的 JOIN 查询方法，一次性获取课程、教师
        course, teachers = await CourseMapper.get_course_detail_with_relations(course_id, query_db)

        if not course:
            return None

        # 动态统计实际学生数量
        student_count_map = await StudentCourseMapper.batch_get_student_count([course.course_id], query_db)
        course.student_count = student_count_map.get(course.course_id, 0)

        # 转换为 VO
        course_vo = _convert_course_orm_to_detail_vo(course)

        # 获取课程封面 URL
        if s3_client and course_vo.cover_file_id:
            course_vo.cover_url = await UploadService.get_file_url(course_vo.cover_file_id, query_db, s3_client)

        # 填充教师信息
        teacher_list = []
        teacher_ids = []
        for teacher in teachers:
            teacher_list.append(
                TeacherListVO(
                    teacher_id=teacher.teacher_id,
                    real_name=teacher.real_name,
                    teacher_no=teacher.teacher_no,
                    faculty=teacher.faculty,
                    title=teacher.title,
                    max_student_count=teacher.max_student_count,
                    current_student_count=teacher.current_student_count,
                    status=teacher.status,
                    create_time=teacher.create_time,
                    user_id=teacher.teacher_id,  # teacher_id == user_id
                )
            )
            teacher_ids.append(teacher.teacher_id)

        course_vo.teachers = teacher_list
        course_vo.teacher_ids = teacher_ids

        return course_vo

    @staticmethod
    async def bind_teachers(
        query_db: AsyncSession, course_id: int, teacher_ids: list[int], current_user: CurrentUser
    ) -> None:
        """为课程绑定教师（管理员操作）。

        Args:
            query_db: 数据库会话。
            course_id: 课程ID。
            teacher_ids: 教师ID列表。
            current_user: 当前用户。

        Raises:
            CourseNotFoundException: 课程不存在。
            TeacherNotFoundException: 教师不存在。
            CourseNoPermissionException: 无权限操作该课程。
        """
        # 1. 权限检查
        await _check_course_permission(course_id, current_user, query_db)

        # 2. 检查课程是否存在
        course = await CourseMapper.get_by_id(course_id, query_db)
        if not course:
            raise CourseNotFoundException(course_id=course_id)

        # 3. 检查教师是否存在并绑定
        for teacher_id in teacher_ids:
            teacher = await TeacherMapper.get_by_id(teacher_id, query_db)
            if not teacher:
                raise TeacherNotFoundException(teacher_id=teacher_id)

            # 绑定教师
            await CourseTeacherMapper.bind_teacher(course_id, teacher_id, query_db)

        logger.info(f"为课程 {course_id} 绑定教师成功: {teacher_ids}")

    @staticmethod
    async def unbind_teachers(
        query_db: AsyncSession, course_id: int, teacher_ids: list[int], current_user: CurrentUser
    ) -> None:
        """解绑课程的教师（管理员操作）。

        Args:
            query_db: 数据库会话。
            course_id: 课程ID。
            teacher_ids: 教师ID列表。
            current_user: 当前用户。

        Raises:
            CourseNotFoundException: 课程不存在。
            CourseNoPermissionException: 无权限操作该课程。
        """
        # 1. 权限检查
        await _check_course_permission(course_id, current_user, query_db)

        # 2. 检查课程是否存在
        course = await CourseMapper.get_by_id(course_id, query_db)
        if not course:
            raise CourseNotFoundException(course_id=course_id)

        # 3. 解绑教师
        for teacher_id in teacher_ids:
            await CourseTeacherMapper.unbind_teacher(course_id, teacher_id, query_db)

        logger.info(f"解绑课程 {course_id} 的教师成功: {teacher_ids}")

    @staticmethod
    async def get_course_teachers(query_db: AsyncSession, course_id: int) -> list[TeacherListVO]:
        """获取课程绑定的教师列表。

        Args:
            query_db: 数据库会话。
            course_id: 课程ID。

        Returns:
            list[TeacherListVO]: 教师列表。

        Raises:
            CourseNotFoundException: 课程不存在。
        """
        # 1. 检查课程是否存在
        course = await CourseMapper.get_by_id(course_id, query_db)
        if not course:
            raise CourseNotFoundException(course_id=course_id)

        # 2. 获取教师列表
        rows, _ = await CourseTeacherMapper.get_course_teacher_list(course_id, query_db)

        # 3. 转换为 VO
        teacher_list = []
        for teacher in rows:
            teacher_list.append(
                TeacherListVO(
                    teacher_id=teacher.teacher_id,
                    real_name=teacher.real_name,
                    teacher_no=teacher.teacher_no,
                    faculty=teacher.faculty,
                    title=teacher.title,
                    max_student_count=teacher.max_student_count,
                    current_student_count=teacher.current_student_count,
                    status=teacher.status,
                    create_time=teacher.create_time,
                    user_id=teacher.teacher_id,  # teacher_id == user_id
                )
            )

        return teacher_list

    @staticmethod
    async def list_my_courses(
        query_db: AsyncSession,
        query_object: CourseQueryDTO,
        current_user: CurrentUser,
        s3_client: AioS3Client | None = None,
    ) -> "PageResponse[CourseListVO]":
        """获取当前登录教师的课程列表（分页）。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数（复用 CourseQueryDTO，teacher_id 由后端注入）。
            current_user: 当前登录用户（需为教师）。
            s3_client: S3 客户端（用于生成封面 URL）。

        Returns:
            PageResponse[CourseListVO]: 分页课程列表。
        """
        from graphedu.common.exceptions.services.education.course import CourseNoPermissionException

        if not current_user.detail or not current_user.detail.teacher_info:
            raise CourseNoPermissionException(course_id=0)

        teacher_id = current_user.detail.teacher_info.teacher_id
        rows, total = await CourseMapper.get_teacher_course_list(query_db, teacher_id, query_object, is_page=True)

        # 批量查询实际学生数量
        course_ids = [row[0].course_id for row in rows]
        student_count_map = await StudentCourseMapper.batch_get_student_count(course_ids, query_db)

        course_list: list[CourseListVO] = []
        for row in rows:
            course_orm, tid, teacher_name = row
            course_orm.student_count = student_count_map.get(course_orm.course_id, 0)
            course_vo = _convert_course_orm_to_list_vo(course_orm)
            course_vo.teacher_id = tid
            course_vo.teacher_name = teacher_name
            course_list.append(course_vo)

        if s3_client and course_list:
            cover_file_ids = [c.cover_file_id for c in course_list if c.cover_file_id]
            if cover_file_ids:
                url_map = await UploadService.get_file_url_map(cover_file_ids, query_db, s3_client)
                for course in course_list:
                    if course.cover_file_id:
                        course.cover_url = url_map.get(course.cover_file_id)

        return PageResponse(rows=course_list, page=query_object.page, size=query_object.size, total=total)
