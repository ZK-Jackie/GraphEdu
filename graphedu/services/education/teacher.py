"""教师管理服务模块

该模块提供教师信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.teacher import (
    TeacherIdListEmptyException,
    TeacherNoAlreadyExistsException,
    TeacherNotFoundException,
)
from graphedu.common.exceptions.services.system.user import UserIdNotFoundException
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.teacher import TeacherCreateDTO, TeacherQueryDTO, TeacherUpdateDTO
from graphedu.common.models.orm.education import EduTeacher
from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem, PageResponse
from graphedu.common.models.vo.educationv2.teacher import TeacherDetailVO, TeacherListVO
from graphedu.mapper.education.teacher import TeacherMapper
from graphedu.mapper.system.user import UserMapper

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_teacher_orm_to_list_vo(teacher_orm: EduTeacher, user_name: str | None = None) -> TeacherListVO:
    """将教师 ORM 对象转换为 TeacherListVO。

    Args:
        teacher_orm: 教师 ORM 对象。
        user_name: 用户账号（可选）。

    Returns:
        TeacherListVO: 教师列表项 VO。
    """
    return TeacherListVO(
        teacher_id=teacher_orm.teacher_id,
        real_name=teacher_orm.real_name,
        teacher_no=teacher_orm.teacher_no,
        faculty=teacher_orm.faculty,
        title=teacher_orm.title,
        max_student_count=teacher_orm.max_student_count,
        current_student_count=teacher_orm.current_student_count,
        status=teacher_orm.status,
        create_time=teacher_orm.create_time,
        user_id=teacher_orm.teacher_id,
        user_name=user_name,
        avatar_file_id=None,  # 如果需要头像信息，需要额外查询
    )


def _convert_teacher_orm_to_detail_vo(teacher_orm: EduTeacher, user_name: str | None = None) -> TeacherDetailVO:
    """将教师 ORM 对象转换为 TeacherDetailVO。

    Args:
        teacher_orm: 教师 ORM 对象。
        user_name: 用户账号（可选）。

    Returns:
        TeacherDetailVO: 教师详细信息 VO。
    """
    return TeacherDetailVO(
        teacher_id=teacher_orm.teacher_id,
        real_name=teacher_orm.real_name,
        teacher_no=teacher_orm.teacher_no,
        faculty=teacher_orm.faculty,
        title=teacher_orm.title,
        research_direction=teacher_orm.research_direction,
        max_student_count=teacher_orm.max_student_count,
        current_student_count=teacher_orm.current_student_count,
        description=teacher_orm.description,
        status=teacher_orm.status,
        create_by=teacher_orm.create_by,
        create_time=teacher_orm.create_time,
        update_by=teacher_orm.update_by,
        update_time=teacher_orm.update_time,
        user_id=teacher_orm.teacher_id,
        user_name=user_name,
        avatar_file_id=None,  # 如果需要头像信息，需要额外查询
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_teacher_no_exists(teacher_no: str, query_db: AsyncSession) -> bool:
    """校验工号是否存在。

    Args:
        teacher_no: 工号。
        query_db: 数据库会话。

    Returns:
        bool: 工号是否存在。
    """
    return await TeacherMapper.is_teacher_no_exists(teacher_no, query_db)


async def _check_teacher_no_unique_for_update(teacher_id: int, teacher_no: str, query_db: AsyncSession) -> bool:
    """校验工号是否唯一（编辑时用）。

    Args:
        teacher_id: 教师 ID。
        teacher_no: 工号。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在其他教师使用该工号）。
    """
    if not teacher_no:
        return False
    existing_teacher = await TeacherMapper.get_teacher_by_no_for_unique_check(teacher_no, query_db)
    return existing_teacher is not None and existing_teacher.teacher_id != teacher_id


# ============================================================================
# TeacherService 类
# ============================================================================


class TeacherService:
    """教师管理服务类

    提供教师的增删改查功能。
    """

    @staticmethod
    async def add_teacher(
        query_db: AsyncSession, teacher_data: TeacherCreateDTO, current_user: CurrentUser | None
    ) -> TeacherDetailVO:
        """新增教师信息。

        Args:
            query_db: 数据库会话。
            teacher_data: 新增教师 DTO。
            current_user: 当前登录用户。

        Returns:
            TeacherDetailVO: 创建成功的教师 VO。

        Raises:
            UserIdNotFoundException: 对应的用户不存在。
            Exception: 工号已存在等其他异常。
        """
        # 1. 校验用户是否存在
        user = await UserMapper.get_by_id(teacher_data.teacher_id, query_db)
        if not user:
            raise UserIdNotFoundException(teacher_data.teacher_id)

        # 2. 校验工号唯一性
        if teacher_data.teacher_no and await _check_teacher_no_exists(teacher_data.teacher_no, query_db):
            raise TeacherNoAlreadyExistsException(teacher_no=teacher_data.teacher_no)

        # 3. DTO → ORM
        new_teacher = EduTeacher(
            **teacher_data.model_dump(exclude={"teacher_id"}),
            teacher_id=teacher_data.teacher_id,  # 确保 teacher_id 被正确设置
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
            create_time=datetime.now(),
        )

        # 4. 新增教师
        await TeacherMapper.add_teacher(new_teacher, query_db)

        logger.info(f"新增教师成功: {teacher_data.real_name}")

        # 5. 返回创建后的教师 VO
        return _convert_teacher_orm_to_detail_vo(new_teacher, user_name=user.user_name)

    @staticmethod
    async def update_teacher(
        query_db: AsyncSession, teacher_data: TeacherUpdateDTO, current_user: CurrentUser
    ) -> TeacherDetailVO:
        """更新教师信息。

        Args:
            query_db: 数据库会话。
            teacher_data: 更新教师 DTO。
            current_user: 当前登录用户。

        Returns:
            TeacherDetailVO: 更新后的教师 VO.

        Raises:
            UserIdNotFoundException: 教师不存在。
            Exception: 工号已存在等其他异常。
        """
        # 1. 获取目标教师
        target_teacher = await TeacherMapper.get_by_id(teacher_data.teacher_id, query_db)
        if target_teacher is None:
            raise UserIdNotFoundException(teacher_data.teacher_id)

        # 2. 唯一性校验（使用目标教师的数据进行对比）
        if (
            teacher_data.teacher_no is not None
            and teacher_data.teacher_no != target_teacher.teacher_no
            and await _check_teacher_no_unique_for_update(teacher_data.teacher_id, teacher_data.teacher_no, query_db)
        ):
            raise TeacherNoAlreadyExistsException(teacher_no=teacher_data.teacher_no)

        # 3. 更新目标教师
        update_data = teacher_data.model_dump(exclude_unset=True, exclude={"teacher_id"})
        for field, value in update_data.items():
            setattr(target_teacher, field, value)

        target_teacher.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_teacher.update_time = datetime.now()

        await TeacherMapper.update(target_teacher, query_db)

        # 获取用户账号
        user = await UserMapper.get_by_id(teacher_data.teacher_id, query_db)
        user_name = user.user_name if user else None

        # 4. 返回更新后的教师 VO
        return _convert_teacher_orm_to_detail_vo(target_teacher, user_name=user_name)

    @staticmethod
    async def list_teacher(query_db: AsyncSession, query_object: TeacherQueryDTO) -> PageResponse[TeacherListVO]:
        """获取教师列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[TeacherListVO]: 分页结果。
        """
        rows, total = await TeacherMapper.get_teacher_list(query_db, query_object)

        # 将 ORM 对象转换为 TeacherListVO
        teacher_list = []
        for row in rows:
            teacher_orm = row[0]
            user_orm = row[1]
            user_name = user_orm.user_name if user_orm else None
            teacher_list.append(_convert_teacher_orm_to_list_vo(teacher_orm, user_name))

        return PageResponse(rows=teacher_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def delete_teacher(
        query_db: AsyncSession, teacher_id_list: list[int], current_user: CurrentUser
    ) -> BatchDeleteResponse[int]:
        """删除教师信息（批量，部分成功模式）。

        Args:
            query_db: 数据库会话。
            teacher_id_list: 教师 ID 列表。
            current_user: 当前用户。

        Returns:
            BatchDeleteResponse[int]: 包含成功数量、失败数量和详细结果的响应对象

        Raises:
            TeacherIdListEmptyException: 教师 ID 列表为空。
        """
        if not teacher_id_list:
            raise TeacherIdListEmptyException

        results: list[DeleteResultItem[int]] = []

        for teacher_id in teacher_id_list:
            try:
                teacher = await TeacherMapper.get_by_id(teacher_id, query_db)
                if not teacher:
                    results.append(DeleteResultItem(target_id=teacher_id, success=False, error="教师不存在"))
                    continue

                # 软删除教师（令 status 为 DELETED）
                teacher.status = SystemConstants.Status.DELETED
                teacher.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                teacher.update_time = datetime.now()
                await TeacherMapper.update(teacher, query_db)

                results.append(DeleteResultItem(target_id=teacher_id, success=True, error=None))

            except Exception as e:
                results.append(DeleteResultItem(target_id=teacher_id, success=False, error=str(e)))

        logger.info(
            f"批量删除教师完成: "
            f"{sum(1 for r in results if r.success)} 成功, "
            f"{sum(1 for r in results if not r.success)} 失败"
        )

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def change_teacher_status(
        query_db: AsyncSession, teacher_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改教师状态。

        Args:
            query_db: 数据库会话。
            teacher_id: 教师 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            TeacherNotFoundException: 教师不存在。
        """
        teacher = await TeacherMapper.get_by_id(teacher_id, query_db)
        if not teacher:
            raise TeacherNotFoundException(teacher_id=teacher_id)

        teacher.status = status
        teacher.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        teacher.update_time = datetime.now()
        await TeacherMapper.update(teacher, query_db)
        logger.info(f"修改教师状态成功: {teacher_id}")

    @staticmethod
    async def get_teacher_detail(query_db: AsyncSession, teacher_id: int) -> TeacherDetailVO | None:
        """获取教师详细信息。

        Args:
            query_db: 数据库会话。
            teacher_id: 教师 ID。

        Returns:
            TeacherDetailVO | None: 教师详细信息 VO。
        """
        teacher = await TeacherMapper.get_by_id(teacher_id, query_db)
        if not teacher:
            return None

        # 获取用户账号
        user = await UserMapper.get_by_id(teacher_id, query_db)
        user_name = user.user_name if user else None

        return _convert_teacher_orm_to_detail_vo(teacher, user_name=user_name)

    @staticmethod
    async def get_unbound_teachers(
        query_db: AsyncSession, query_object: TeacherQueryDTO
    ) -> PageResponse[TeacherListVO]:
        """查询未绑定的教师列表（user_id 为 null 的教师）

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[TeacherListVO]: 分页结果。
        """
        # 调用 Mapper 查询未绑定的教师
        rows, total = await TeacherMapper.get_unbound_teachers(query_db, query_object, is_page=True)

        # 转换为 VO
        teacher_list = [_convert_teacher_orm_to_list_vo(teacher_orm=teacher, user_name=None) for teacher in rows]

        # 构建分页响应
        return PageResponse(
            rows=teacher_list,
            total=total,
            page=query_object.page or 1,
            size=query_object.size or 10,
        )
