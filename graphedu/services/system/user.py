"""用户管理服务模块。

该模块提供用户和用户权限的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.auth import (
    RegisterEmailExistsException,
    RegisterPhonenumberExistsException,
    RegisterUsernameExistsException,
)
from graphedu.common.exceptions.services.system.user import (
    UserAvatarOwnershipException,
    UserAvatarUpdateFailedException,
    UserCannotChangeOwnPasswordException,
    UserChangeStatusFailedException,
    UserCreateFailedException,
    UserEmailAlreadyExistsException,
    UserIdentityAlreadyBoundException,
    UserIdentityMismatchException,
    UserIdentityNotBoundException,
    UserIdentityNotFoundException,
    UserIdListEmptyException,
    UserIdNotFoundException,
    UserNoPermissionException,
    UserOldPasswordIncorrectException,
    UserOnlyAdminException,
    UserPasswordUnchangeException,
    UserPhoneAlreadyExistsException,
    UserProfileUpdateFailedException,
    UserResetPasswordFailedException,
    UserUpdateRoleFailedException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.systemv2.role import RoleQueryDTO
from graphedu.common.models.dto.systemv2.user import (
    UserBindIdentityDTO,
    UserCreateDTO,
    UserProfileUpdateDTO,
    UserQueryDTO,
    UserResetPasswordDTO,
    UserUpdateDTO,
)
from graphedu.common.models.orm import SysUser
from graphedu.common.models.orm.education import EduStudent, EduTeacher
from graphedu.common.models.orm.system import SysUserRole
from graphedu.common.models.vo import RoleListVO
from graphedu.common.models.vo.base import BatchDeleteResponse, PageResponse
from graphedu.common.models.vo.systemv2.user import (
    UserBindIdentityVO,
    UserDetailVO,
    UserListVO,
    UserProfileVO,
    UserRoleListVO,
)
from graphedu.common.utils import PasswordUtil
from graphedu.mapper.education.student import StudentMapper
from graphedu.mapper.education.teacher import TeacherMapper
from graphedu.mapper.system.dept import DeptMapper
from graphedu.mapper.system.upload import UploadMapper
from graphedu.mapper.system.user import UserMapper
from graphedu.services.system.role import RoleService
from graphedu.services.system.upload import UploadService

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_user_orm_to_list_vo(user_orm: SysUser, dept_orm=None, student_orm=None, teacher_orm=None) -> UserListVO:
    """将用户 ORM 对象（和部门 ORM 对象）转换为 UserListVO。

    Args:
        user_orm: 用户 ORM 对象。
        dept_orm: 部门 ORM 对象（可选）。
        student_orm: 学生 ORM 对象（可选）。
        teacher_orm: 教师 ORM 对象（可选）。

    Returns:
        UserListVO: 用户列表项 VO。
    """
    from graphedu.common.models.vo.educationv2.student import StudentListVO
    from graphedu.common.models.vo.educationv2.teacher import TeacherListVO

    # 转换学生信息（如果存在）
    student_vo = None
    if student_orm:
        student_vo = StudentListVO.model_validate(student_orm)

    # 转换教师信息（如果存在）
    teacher_vo = None
    if teacher_orm:
        teacher_vo = TeacherListVO.model_validate(teacher_orm)

    return UserListVO(
        user_id=user_orm.user_id,
        user_name=user_orm.user_name,
        nick_name=user_orm.nick_name,
        email=user_orm.email,
        phonenumber=user_orm.phonenumber,
        avatar_file_id=user_orm.avatar_file_id,
        user_type=user_orm.user_type,
        status=user_orm.status,
        create_time=user_orm.create_time,
        dept_id=dept_orm.dept_id if dept_orm else None,
        dept_name=dept_orm.dept_name if dept_orm else None,
        student=student_vo,
        teacher=teacher_vo,
    )


def _convert_user_orm_to_detail_vo(user_orm: SysUser, dept_ids=None, role_ids=None) -> UserDetailVO:
    """将用户 ORM 对象转换为 UserDetailVO。

    Args:
        user_orm: 用户 ORM 对象。
        dept_ids: 部门 ID 列表。
        role_ids: 角色 ID 列表。

    Returns:
        UserDetailVO: 用户详细信息 VO。
    """
    return UserDetailVO(
        user_id=user_orm.user_id,
        user_name=user_orm.user_name,
        nick_name=user_orm.nick_name,
        email=user_orm.email,
        phonenumber=user_orm.phonenumber,
        avatar_file_id=user_orm.avatar_file_id,
        user_type=user_orm.user_type,
        status=user_orm.status,
        login_ip=user_orm.login_ip,
        login_date=user_orm.login_date,
        create_by=user_orm.create_by,
        create_time=user_orm.create_time,
        update_by=user_orm.update_by,
        update_time=user_orm.update_time,
        remark=user_orm.remark,
        dept_ids=dept_ids,
        role_ids=role_ids,
    )


# ============================================================================
# 内部校验函数（直接使用 ORM）
# ============================================================================


async def _check_username_exists(user_name: str, query_db: AsyncSession) -> bool:
    """校验用户名是否存在。

    Args:
        user_name: 用户名。
        query_db: 数据库会话。

    Returns:
        bool: 用户名是否存在。
    """
    return await UserMapper.is_username_exists(user_name, query_db)


async def _check_username_unique_for_update(user_id: int, user_name: str, query_db: AsyncSession) -> bool:
    """校验用户名是否唯一（编辑时用）。

    Args:
        user_id: 用户 ID。
        user_name: 用户名。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在其他用户使用该用户名）。
    """
    existing_user = await UserMapper.get_user_by_username_for_unique_check(user_name, query_db)
    return existing_user is not None and existing_user.user_id != user_id


async def _check_phonenumber_exists(phonenumber: str, query_db: AsyncSession) -> bool:
    """校验用户手机号是否存在（新增时用）。

    Args:
        phonenumber: 手机号。
        query_db: 数据库会话。

    Returns:
        bool: 手机号是否存在。
    """
    return await UserMapper.is_phonenumber_exists(phonenumber, query_db)


async def _check_phonenumber_unique_for_update(user_id: int, phonenumber: str, query_db: AsyncSession) -> bool:
    """校验用户手机号是否唯一（编辑时用）。

    Args:
        user_id: 用户 ID。
        phonenumber: 手机号。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在其他用户使用该手机号）。
    """
    if not phonenumber:
        return False
    existing_user = await UserMapper.get_user_by_phonenumber_for_unique_check(phonenumber, query_db)
    return existing_user is not None and existing_user.user_id != user_id


async def _check_email_exists(email: str, query_db: AsyncSession) -> bool:
    """校验用户邮箱是否存在（新增时用）。

    Args:
        email: 邮箱。
        query_db: 数据库会话。

    Returns:
        bool: 邮箱是否存在。
    """
    return await UserMapper.is_email_exists(email, query_db)


async def _check_email_unique_for_update(user_id: int, email: str, query_db: AsyncSession) -> bool:
    """校验用户邮箱是否唯一（编辑时用）。

    Args:
        user_id: 用户 ID。
        email: 邮箱。
        query_db: 数据库会话。

    Returns:
        bool: 是否不唯一（已存在其他用户使用该邮箱）。
    """
    if not email:
        return False
    existing_user = await UserMapper.get_user_by_email_for_unique_check(email, query_db)
    return existing_user is not None and existing_user.user_id != user_id


# ============================================================================
# UserService 类
# ============================================================================


class UserService:
    """用户管理服务类。

    提供用户的增删改查功能，支持用户权限分配和个人信息管理。
    """

    @staticmethod
    async def check_user_data_scope(query_db: AsyncSession, user_id: int, data_scope_sql: str):
        """检查用户数据权限。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            data_scope_sql: 数据权限 SQL。

        Raises:
            UserIdNotFoundException: 用户不存在。
            UserNoPermissionException: 无权限访问。
        """
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        if not data_scope_sql or data_scope_sql == "True":
            return

        check_query = text(f"SELECT 1 FROM sys_user WHERE user_id = {user_id} AND ({data_scope_sql}) LIMIT 1")
        result = await query_db.execute(check_query)
        if not result.scalar():
            raise UserNoPermissionException(user_id)

    @staticmethod
    async def add_user(
        query_db: AsyncSession, user_data: UserCreateDTO, current_user: CurrentUser | None
    ) -> UserDetailVO:
        """新增用户信息。

        Args:
            query_db: 数据库会话。
            user_data: 新增用户 DTO。
            current_user: 当前登录用户。

        Returns:
            UserDetailVO: 创建成功的用户 VO。

        Raises:
            RegisterUsernameExistsException: 用户名已存在。
            RegisterPhonenumberExistsException: 手机号已存在。
            RegisterEmailExistsException: 邮箱已存在。
            UserCreateFailedException: 用户新增失败。
        """
        # 1. 校验用户名、手机号、邮箱唯一性
        if await _check_username_exists(user_data.user_name, query_db):
            raise RegisterUsernameExistsException(user_data.user_name)
        if user_data.phonenumber and await _check_phonenumber_exists(user_data.phonenumber, query_db):
            raise RegisterPhonenumberExistsException
        if user_data.email and await _check_email_exists(user_data.email, query_db):
            raise RegisterEmailExistsException

        # 2. 密码加密
        hashed_password = PasswordUtil.hash_password(user_data.password)

        # 3. DTO → ORM
        new_user = SysUser(
            **user_data.model_dump(exclude={"dept_ids", "role_ids", "password"}),
            password=hashed_password,
            create_by=current_user.detail.user.user_id if current_user.detail.user else None,
            create_time=datetime.now(),
        )

        # 4. 新增用户
        try:
            await UserMapper.add_user(new_user, query_db)
            user_id = new_user.user_id
        except Exception as e:
            raise UserCreateFailedException(user_name=user_data.user_name) from e

        # 5. 关联部门
        dept_ids = []
        if user_data.dept_ids:
            try:
                for dept_id in user_data.dept_ids:
                    await DeptMapper.add_user_dept(user_id, dept_id, query_db)
                    dept_ids.append(dept_id)
            except Exception as e:
                raise UserCreateFailedException(user_name=user_data.user_name) from e

        # 6. 关联角色
        if user_data.role_ids:
            try:
                for role_id in user_data.role_ids:
                    user_role_orm = SysUserRole(user_id=user_id, role_id=role_id)
                    await UserMapper.add_user_role(user_role_orm, query_db)
            except Exception as e:
                raise UserCreateFailedException(user_name=user_data.user_name) from e

        # 7. 内联创建学生/教师身份记录
        if new_user.user_type == SystemConstants.UserType.STUDENT:
            await _create_student_identity(query_db, user_id, user_data, current_user)
        elif new_user.user_type == SystemConstants.UserType.TEACHER:
            await _create_teacher_identity(query_db, user_id, user_data, current_user)

        logger.info(f"新增用户成功: {user_data.user_name}")

        # 8. 返回创建后的用户 VO
        return _convert_user_orm_to_detail_vo(
            new_user, dept_ids=dept_ids if dept_ids else None, role_ids=user_data.role_ids
        )

    @staticmethod
    async def update_user(query_db: AsyncSession, user_data: UserUpdateDTO, current_user: CurrentUser) -> UserDetailVO:
        """更新用户信息。

        Args:
            query_db: 数据库会话。
            user_data: 更新用户 DTO。
            current_user: 当前登录用户。

        Returns:
            UserDetailVO: 更新后的用户 VO.

        Raises:
            UserIdNotFoundException: 用户不存在。
            UserPhoneAlreadyExistsException: 手机号已存在。
            UserEmailAlreadyExistsException: 邮箱已存在。
        """
        # 1. 获取目标用户
        target_user = await UserMapper.get_by_id(user_data.user_id, query_db)
        if target_user is None:
            raise UserIdNotFoundException(user_id=user_data.user_id)

        # 2. 唯一性校验（使用目标用户的数据进行对比）
        if user_data.phonenumber is not None and user_data.phonenumber != target_user.phonenumber:  # noqa: SIM102
            if await _check_phonenumber_unique_for_update(user_data.user_id, user_data.phonenumber, query_db):
                raise UserPhoneAlreadyExistsException(phone=user_data.phonenumber)

        if user_data.email is not None and user_data.email != target_user.email:  # noqa: SIM102
            if await _check_email_unique_for_update(user_data.user_id, user_data.email, query_db):
                raise UserEmailAlreadyExistsException(email=user_data.email)

        # 3. 更新目标用户
        update_data = user_data.model_dump(
            exclude_unset=True, exclude={"user_id", "dept_ids", "role_ids", "update_type"}
        )
        for field, value in update_data.items():
            setattr(target_user, field, value)

        target_user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_user.update_time = datetime.now()

        await UserMapper.update(target_user, query_db)

        # 4. 更新角色关联
        role_ids = user_data.role_ids
        if role_ids is not None:  # 若不为None则更新（包括空列表）
            # 删除旧的角色关联
            await UserMapper.delete_user_role_by_user_id(target_user.user_id, query_db)
            # 添加新的角色关联
            for role_id in role_ids:
                user_role_orm = SysUserRole(user_id=target_user.user_id, role_id=role_id)
                await UserMapper.add_user_role(user_role_orm, query_db)

        # 5. 更新部门关联
        dept_ids = user_data.dept_ids
        if dept_ids is not None:  # 若不为None则更新（包括空列表）
            await DeptMapper.delete_user_depts(target_user.user_id, query_db)
            for dept_id in dept_ids:
                await DeptMapper.add_user_dept(target_user.user_id, dept_id, query_db)

        # 6. 同步更新学生/教师身份信息
        await _sync_identity_on_update(query_db, target_user, user_data, current_user)

        # 7. 返回更新后的用户 VO
        return _convert_user_orm_to_detail_vo(
            target_user,
            dept_ids=dept_ids if dept_ids is not None else None,
            role_ids=role_ids if role_ids is not None else None,
        )

    @staticmethod
    async def list_user(
        query_db: AsyncSession,
        query_object: UserQueryDTO,
        data_scope_sql: str,
    ) -> PageResponse[UserListVO]:
        """获取用户列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。
            data_scope_sql: 数据权限 SQL。

        Returns:
            PageResponse[UserListVO]: 分页结果。
        """
        rows, total = await UserMapper.get_user_list(query_db, query_object, data_scope_sql, is_page=True)

        # 将 ORM 对象转换为 UserListVO
        user_list = []
        for row in rows:
            user_orm = row[0]
            dept_orm = row[1]
            student_orm = row[3]
            teacher_orm = row[4]
            user_list.append(_convert_user_orm_to_list_vo(user_orm, dept_orm, student_orm, teacher_orm))

        return PageResponse(rows=user_list, page=query_object.page, size=query_object.size, total=total)

    @staticmethod
    async def delete_user(
        query_db: AsyncSession, user_id_list: list[int], current_user: CurrentUser
    ) -> BatchDeleteResponse[int]:
        """删除用户信息（批量，部分成功模式）。

        Args:
            query_db: 数据库会话。
            user_id_list: 用户 ID 列表。
            current_user: 当前用户。

        Returns:
            DeleteResponse[int]: 包含成功数量、失败数量和详细结果的响应对象

        Raises:
            UserIdListEmptyException: 用户 ID 列表为空。
        """
        from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem

        if not user_id_list:
            raise UserIdListEmptyException

        # 检查是否删除当前登录用户（如果是，整批拒绝）
        if current_user.detail.user and current_user.detail.user.user_id in user_id_list:
            from graphedu.common.exceptions.services.system.user import UserDeleteSelfForbiddenException

            raise UserDeleteSelfForbiddenException

        results: list[DeleteResultItem[int]] = []

        for user_id in user_id_list:
            try:
                # 检查是否为管理员用户
                is_admin = await UserMapper.check_is_admin_by_user_id(user_id, query_db)
                if is_admin:
                    results.append(DeleteResultItem(target_id=user_id, success=False, error="无法删除管理员用户"))
                    continue

                # 获取用户信息
                user = await UserMapper.get_by_id(user_id, query_db)
                if not user:
                    results.append(DeleteResultItem(target_id=user_id, success=False, error="用户不存在"))
                    continue

                # 删除用户角色关联
                await UserMapper.delete_user_role_by_user_id(user_id, query_db)
                # 删除用户部门关联
                await DeptMapper.delete_user_depts(user_id, query_db)

                # 软删除用户（令 status 为 DELETED）
                user.status = SystemConstants.Status.DELETED
                user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                user.update_time = datetime.now()
                await UserMapper.update(user, query_db)

                results.append(DeleteResultItem(target_id=user_id, success=True, error=None))

            except Exception as e:
                results.append(DeleteResultItem(target_id=user_id, success=False, error=str(e)))

        logger.info(
            f"批量删除用户完成: "
            f"{sum(1 for r in results if r.success)} 成功, "
            f"{sum(1 for r in results if not r.success)} 失败"
        )

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def reset_user_password_by_admin(
        query_db: AsyncSession, user_id: int, password: str, current_user: CurrentUser
    ) -> None:
        """管理员重置用户密码。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            password: 新密码（明文）。
            current_user: 当前用户。

        Raises:
            UserOnlyAdminException: 非管理员用户。
            UserIdNotFoundException: 用户不存在。
            UserResetPasswordFailedException: 重置密码失败。
        """
        if not current_user.is_admin():
            raise UserOnlyAdminException

        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        try:
            # 密码加密
            user.password = PasswordUtil.hash_password(password)
            user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)
            logger.info(f"管理员重置用户 {user_id} 密码成功")
        except Exception as e:
            raise UserResetPasswordFailedException(reason=str(e)) from e

    @staticmethod
    async def change_user_status(query_db: AsyncSession, user_id: int, status: str, current_user: CurrentUser) -> None:
        """修改用户状态。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            UserIdNotFoundException: 用户不存在。
            UserChangeStatusFailedException: 用户状态修改失败。
        """
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        try:
            user.status = status
            user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)
            logger.info(f"修改用户状态成功: {user_id}")
        except Exception as e:
            raise UserChangeStatusFailedException(user_id=user_id) from e

    @staticmethod
    async def update_user_profile(
        query_db: AsyncSession, user_id: int, profile_data: UserProfileUpdateDTO, current_user: CurrentUser
    ) -> UserDetailVO | None:
        """更新用户个人信息。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            profile_data: 个人信息更新 DTO。
            current_user: 当前用户。

        Returns:
            UserDetailVO | None: 更新后的用户 VO。

        Raises:
            UserIdNotFoundException: 用户不存在。
            UserPhoneAlreadyExistsException: 手机号已存在。
            UserEmailAlreadyExistsException: 邮箱已存在。
            UserProfileUpdateFailedException: 用户个人信息修改失败。
        """
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        # 如果修改了手机号或邮箱，需要校验唯一性
        if profile_data.phonenumber is not None and profile_data.phonenumber != user.phonenumber:  # noqa: SIM102
            if await _check_phonenumber_unique_for_update(user_id, profile_data.phonenumber, query_db):
                raise UserPhoneAlreadyExistsException(phone=profile_data.phonenumber)

        if profile_data.email is not None and profile_data.email != user.email:  # noqa: SIM102
            if await _check_email_unique_for_update(user_id, profile_data.email, query_db):
                raise UserEmailAlreadyExistsException(email=profile_data.email)

        try:
            # 使用 model_dump(exclude_unset=True) 只更新提供的字段
            update_data = profile_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)

            # 返回更新后的用户 VO（包含头像路径）
            user_detail_vo = _convert_user_orm_to_detail_vo(user)
            # 查询头像文件路径
            avatar_path = None
            if user_detail_vo.avatar_file_id:
                avatar_file = await UploadMapper.get_by_id(user_detail_vo.avatar_file_id, query_db)
                if avatar_file:
                    avatar_path = avatar_file.file_path
            # 设置头像路径
            user_detail_vo.avatar_path = avatar_path
            return user_detail_vo
        except Exception as e:
            raise UserProfileUpdateFailedException(user_id=user_id) from e

    @staticmethod
    async def update_user_avatar(
        query_db: AsyncSession, user_id: int, avatar_file_id: int, current_user: CurrentUser
    ) -> UserDetailVO | None:
        """更新用户头像。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            avatar_file_id: 头像文件 ID。
            current_user: 当前用户。

        Returns:
            UserDetailVO | None: 更新后的用户 VO。

        Raises:
            UserIdNotFoundException: 用户不存在。
            UserAvatarOwnershipException: 头像文件所有权验证失败。
            UserAvatarUpdateFailedException: 用户头像修改失败。
        """
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        # 验证文件所有权（只有文件上传者本人或管理员可以设置）
        is_owner = await UploadService.check_file_ownership(avatar_file_id, user_id, query_db)
        if not is_owner and not current_user.is_admin():
            raise UserAvatarOwnershipException

        try:
            user.avatar_file_id = avatar_file_id
            user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)

            # 返回更新后的用户 VO（包含头像路径）
            user_detail_vo = _convert_user_orm_to_detail_vo(user)
            # 查询头像文件路径
            avatar_path = None
            if user_detail_vo.avatar_file_id:
                avatar_file = await UploadMapper.get_by_id(user_detail_vo.avatar_file_id, query_db)
                if avatar_file:
                    avatar_path = avatar_file.file_path
            # 设置头像路径
            user_detail_vo.avatar_path = avatar_path
            return user_detail_vo
        except Exception as e:
            raise UserAvatarUpdateFailedException(user_id=user_id) from e

    @staticmethod
    async def get_user_detail(query_db: AsyncSession, user_id: int | None = None):
        """获取用户详细信息（用于管理页面）。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。

        Returns:
            UserDetailVO | None: 用户详细信息 VO。
        """
        if user_id:
            return await UserService.get_user_detail_by_id(user_id, query_db)
        return None

    @staticmethod
    async def get_user_detail_by_id(user_id: int, query_db: AsyncSession):
        """获取用户详细信息。

        Args:
            user_id: 用户 ID。
            query_db: 数据库会话。

        Returns:
            UserDetailVO | None: 用户详细信息 VO。
        """
        if user_id:
            query_user = await UserMapper.get_detail_by_id(int(user_id), query_db)
            dept_ids = [row.dept_id for row in query_user["user_dept_info"]]
            role_ids = [row.role_id for row in query_user["user_role_info"]]

            # 构建 UserDetailVO
            user_detail_vo = _convert_user_orm_to_detail_vo(
                query_user["user_basic_info"], dept_ids=dept_ids, role_ids=role_ids
            )
            # 查询头像文件路径
            avatar_path = None
            if user_detail_vo.avatar_file_id:
                avatar_file = await UploadMapper.get_by_id(user_detail_vo.avatar_file_id, query_db)
                if avatar_file:
                    avatar_path = avatar_file.file_path
            # 设置头像路径
            user_detail_vo.avatar_path = avatar_path
            return user_detail_vo
        return None

    @staticmethod
    async def get_user_profile(query_db: AsyncSession, current_user: CurrentUser) -> UserProfileVO:
        """获取用户个人详细信息。

        Args:
            query_db: 数据库会话。
            current_user: 当前用户信息（从 SecurityService.get_current_user 获取）。

        Returns:
            UserProfileVO: 用户个人详细信息 VO。
        """
        # 复用 CurrentUser.detail 中的数据，避免重复查询
        detail = current_user.detail
        user_orm = detail.user

        # 提取部门信息
        dept_ids = detail.dept_ids if detail.dept_ids else []
        dept_keys = [dept.dept_key for dept in detail.depts] if detail.depts else []
        dept_names = [dept.dept_name for dept in detail.depts] if detail.depts else []

        # 提取角色信息
        role_ids = detail.role_ids if detail.role_ids else []
        role_keys = current_user.role_keys
        role_names = [role.role_name for role in detail.roles] if detail.roles else []

        # 构建 UserDetailVO（复用已有的 ORM 对象）
        user_detail_vo = _convert_user_orm_to_detail_vo(user_orm, dept_ids=dept_ids, role_ids=role_ids)

        # 转换教育信息：ORM → VO
        from graphedu.services.education.student import _convert_student_orm_to_detail_vo
        from graphedu.services.education.teacher import _convert_teacher_orm_to_detail_vo

        if detail.student_info:
            user_detail_vo.student = _convert_student_orm_to_detail_vo(detail.student_info)
        if detail.teacher_info:
            user_detail_vo.teacher = _convert_teacher_orm_to_detail_vo(detail.teacher_info)

        # 查询头像文件路径（这是唯一缺失的信息）
        avatar_path = None
        if user_detail_vo.avatar_file_id:
            avatar_file = await UploadMapper.get_by_id(user_detail_vo.avatar_file_id, query_db)
            if avatar_file:
                avatar_path = avatar_file.file_path

        # 设置头像路径
        user_detail_vo.avatar_path = avatar_path

        return UserProfileVO(
            user=user_detail_vo,
            role_keys=role_keys,
            role_names=role_names,
            dept_keys=dept_keys,
            dept_names=dept_names,
        )

    @staticmethod
    async def reset_user_password(
        query_db: AsyncSession, user_id: int, reset_data: UserResetPasswordDTO, current_user: CurrentUser
    ) -> None:
        """用户修改自己的密码。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            reset_data: 密码重置 DTO。
            current_user: 当前用户。

        Raises:
            UserCannotChangeOwnPasswordException: 不能修改其他用户密码。
            UserOldPasswordIncorrectException: 旧密码不正确。
            UserPasswordUnchangeException: 新密码不能与旧密码相同。
            UserIdNotFoundException: 用户不存在。
            UserResetPasswordFailedException: 修改密码失败。
        """
        user_info = current_user.detail.user
        if not user_info or user_info.user_id != user_id:
            raise UserCannotChangeOwnPasswordException

        # 验证旧密码
        if reset_data.old_password:
            if not PasswordUtil.verify_password(reset_data.old_password, user_info.password):
                raise UserOldPasswordIncorrectException
            if PasswordUtil.verify_password(reset_data.new_password, user_info.password):
                raise UserPasswordUnchangeException

        try:
            # 重新从数据库获取用户对象以确保是ORM对象
            user = await UserMapper.get_by_id(user_id, query_db)
            if not user:
                raise UserIdNotFoundException(user_id)

            user.password = PasswordUtil.hash_password(reset_data.new_password)
            user.update_by = user_id
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)
        except Exception as e:
            raise UserResetPasswordFailedException(reason=str(e)) from e

    @staticmethod
    async def get_user_role_list(query_db: AsyncSession, user_id: int) -> UserRoleListVO:
        """获取用户的角色关联列表。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。

        Returns:
            UserRoleListVO: 用户角色关联列表 VO。

        Raises:
            UserIdNotFoundException: 用户不存在。
        """
        user_detail = await UserService.get_user_detail_by_id(user_id, query_db)
        if not user_detail:
            raise UserIdNotFoundException(user_id)

        # 获取所有角色列表
        all_roles: PageResponse[RoleListVO] = await RoleService.get_role_list(query_db, RoleQueryDTO())

        return UserRoleListVO(
            user_id=user_id, user_name=user_detail.user_name, role_ids=user_detail.role_ids or [], roles=all_roles.rows
        )

    @staticmethod
    async def update_user_role(
        query_db: AsyncSession, user_id: int, role_ids: list[int], current_user: CurrentUser
    ) -> UserDetailVO | None:
        """更新用户角色关联。

        Args:
            query_db: 数据库会话。
            user_id: 用户 ID。
            role_ids: 角色 ID 列表。
            current_user: 当前用户。

        Returns:
            UserDetailVO | None: 更新后的用户 VO。

        Raises:
            UserIdNotFoundException: 用户不存在。
            UserUpdateRoleFailedException: 更新用户角色关联失败。
        """
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        try:
            # 删除旧的角色关联
            await UserMapper.delete_user_role_by_user_id(user_id, query_db)
            # 添加新的角色关联（直接创建ORM对象）
            for role_id in role_ids:
                user_role_orm = SysUserRole(user_id=user_id, role_id=role_id)
                await UserMapper.add_user_role(user_role_orm, query_db)
            # 返回更新后的用户 VO（只更新role_ids）
            return _convert_user_orm_to_detail_vo(user, role_ids=role_ids)
        except Exception as e:
            raise UserUpdateRoleFailedException(reason=str(e)) from e

    # ============================================================================
    # 用户身份绑定功能
    # ============================================================================
    @staticmethod
    async def bind_user_identity(
        query_db: AsyncSession,
        user_id: int,
        bind_data: UserBindIdentityDTO,
        current_user: CurrentUser,
    ) -> UserBindIdentityVO:
        """绑定用户身份（学生或教师）

        流程：
        1. 验证用户存在
        2. 检查用户是否已绑定身份（user_type 是否为 "1" 或 "2"）
        3. 根据身份类型查询 edu_student 或 edu_teacher 表
        4. 检查该身份是否已被其他用户绑定
        5. 验证 student_id/teacher_id 是否等于 user_id
        6. 更新 sys_user.user_type 字段
        7. 记录操作日志

        Args:
            query_db: 数据库会话
            user_id: 用户ID
            bind_data: 绑定数据
            current_user: 当前用户

        Returns:
            UserBindIdentityVO: 绑定结果

        Raises:
            UserIdNotFoundException: 用户不存在
            UserIdentityAlreadyBoundException: 用户已绑定身份
            UserIdentityNotFoundException: 身份信息不存在
            UserIdentityAlreadyBoundByOtherException: 身份已被其他用户绑定
            UserIdentityMismatchException: 身份ID与用户ID不匹配
        """
        # 1. 验证用户存在
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        # 2. 检查用户是否已绑定身份
        if user.user_type in (SystemConstants.UserType.STUDENT, SystemConstants.UserType.TEACHER):
            raise UserIdentityAlreadyBoundException(user_id)

        # 3. 根据身份类型查询身份信息
        identity_type = bind_data.identity_type
        if identity_type == SystemConstants.UserType.STUDENT:
            # 优先使用 student_id，否则使用 student_no 查询
            if bind_data.student_id:
                student = await StudentMapper.get_by_id(bind_data.student_id, query_db)
            else:
                student = await StudentMapper.get_student_by_no_for_binding(bind_data.student_no, query_db)

            if not student:
                raise UserIdentityNotFoundException(SystemConstants.UserType.STUDENT, bind_data.student_no)

            # 4. 检查该学生是否已被其他用户绑定（检查是否有其他user_type=1的用户拥有相同的student_id）
            # 由于edu_student表设计时student_id=user_id，这里主要验证ID匹配
            # 5. 验证 student_id 是否等于 user_id
            if student.student_id != user_id:
                raise UserIdentityMismatchException(user_id, student.student_id)

            identity_no = student.student_no
            identity_name = student.real_name
            new_user_type = SystemConstants.UserType.STUDENT  # 学生

        elif identity_type == SystemConstants.UserType.TEACHER:
            # 优先使用 teacher_id，否则使用 teacher_no 查询
            if bind_data.teacher_id:
                teacher = await TeacherMapper.get_by_id(bind_data.teacher_id, query_db)
            else:
                teacher = await TeacherMapper.get_teacher_by_no_for_binding(bind_data.teacher_no, query_db)

            if not teacher:
                raise UserIdentityNotFoundException(SystemConstants.UserType.TEACHER, bind_data.teacher_no)

            # 验证 teacher_id 是否等于 user_id
            if teacher.teacher_id != user_id:
                raise UserIdentityMismatchException(user_id, teacher.teacher_id)

            identity_no = teacher.teacher_no
            identity_name = teacher.real_name
            new_user_type = SystemConstants.UserType.TEACHER  # 教师
        else:
            raise UserIdentityNotFoundException(identity_type)

        # 6. 更新 sys_user.user_type 字段
        try:
            user.user_type = new_user_type
            user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)

            logger.info(f"用户 {user_id} 成功绑定 {identity_type} 身份: {identity_no}")

        except Exception as e:
            logger.error(f"用户 {user_id} 绑定身份失败: {e}")
            raise

        # 7. 返回绑定结果
        return UserBindIdentityVO(
            user_id=user_id,
            user_name=user.user_name,
            identity_type=identity_type,
            identity_id=user_id,
            identity_name=identity_name,
            identity_no=identity_no,
            bind_time=datetime.now(),
        )

    @staticmethod
    async def unbind_user_identity(
        query_db: AsyncSession,
        user_id: int,
        current_user: CurrentUser,
    ) -> None:
        """解绑用户身份

        将 user_type 设置为 "4"（其他），保留扩展表记录

        Args:
            query_db: 数据库会话
            user_id: 用户ID
            current_user: 当前用户

        Raises:
            UserIdNotFoundException: 用户不存在
            UserIdentityNotBoundException: 用户未绑定身份
        """
        # 1. 验证用户存在
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            raise UserIdNotFoundException(user_id)

        # 2. 检查用户是否已绑定身份
        if user.user_type not in ("1", "2"):  # 不是学生也不是教师
            raise UserIdentityNotBoundException(user_id)

        # 3. 更新 user_type 为 "4"（其他）
        try:
            old_user_type = user.user_type
            user.user_type = "4"  # 其他
            user.update_by = current_user.detail.user.user_id if current_user.detail.user else None
            user.update_time = datetime.now()
            await UserMapper.update(user, query_db)

            logger.info(f"用户 {user_id} 解绑身份成功（原类型: {old_user_type}）")

        except Exception as e:
            logger.error(f"用户 {user_id} 解绑身份失败: {e}")
            raise

    @staticmethod
    async def get_user_identity_info(
        query_db: AsyncSession,
        user_id: int,
    ) -> UserBindIdentityVO | None:
        """获取用户的身份绑定信息

        Args:
            query_db: 数据库会话
            user_id: 用户ID

        Returns:
            UserBindIdentityVO | None: 身份绑定信息，如果未绑定则返回 None
        """
        # 获取用户基本信息
        user = await UserMapper.get_by_id(user_id, query_db)
        if not user:
            return None

        # 检查用户类型
        if user.user_type == "1":  # 学生
            student = await StudentMapper.get_by_user_id(user_id, query_db)
            if student:
                return UserBindIdentityVO(
                    user_id=user_id,
                    user_name=user.user_name,
                    identity_type="student",
                    identity_id=student.student_id,
                    identity_name=student.real_name,
                    identity_no=student.student_no,
                    bind_time=student.create_time,
                )
        elif user.user_type == "2":  # 教师
            teacher = await TeacherMapper.get_by_user_id(user_id, query_db)
            if teacher:
                return UserBindIdentityVO(
                    user_id=user_id,
                    user_name=user.user_name,
                    identity_type="teacher",
                    identity_id=teacher.teacher_id,
                    identity_name=teacher.real_name,
                    identity_no=teacher.teacher_no,
                    bind_time=teacher.create_time,
                )

        # 未绑定身份或扩展表记录不存在
        return None

    @staticmethod
    async def get_available_users_for_student(query_db: AsyncSession) -> list[UserListVO]:
        """获取可关联学生的用户列表

        获取未在 edu_student 表中存在的正常状态用户，用于新增学生时选择关联用户。

        Args:
            query_db: 数据库会话。

        Returns:
            list[UserListVO]: 可关联学生的用户列表。
        """
        users = await UserMapper.get_available_for_student(query_db)
        return [_convert_user_orm_to_list_vo(user) for user in users]


# ============================================================================
# 学生/教师身份内联创建与同步辅助方法
# ============================================================================


async def _create_student_identity(
    db: AsyncSession, user_id: int, user_data: "UserCreateDTO", current_user: CurrentUser | None
) -> None:
    """创建用户时内联创建学生身份记录

    Args:
        db: 数据库会话。
        user_id: 新创建的用户ID。
        user_data: 用户创建 DTO。
        current_user: 当前操作用户。
    """
    real_name = getattr(user_data, "student_real_name", None)
    if not real_name:
        # 没有提供学生真实姓名，跳过创建（后续可通过学生管理模块创建）
        return

    student_no = getattr(user_data, "student_no", None)
    # 校验学号唯一性
    if student_no:
        from graphedu.services.education.student import _check_student_no_exists

        if await _check_student_no_exists(student_no, db):
            from graphedu.common.exceptions.services.education.student import StudentNoAlreadyExistsException

            raise StudentNoAlreadyExistsException(student_no=student_no)

    creator_id = (
        current_user.detail.user.user_id if current_user and current_user.detail and current_user.detail.user else None
    )
    new_student = EduStudent(
        student_id=user_id,  # 共享主键
        real_name=real_name,
        student_no=student_no,
        faculty=getattr(user_data, "student_faculty", None),
        major=getattr(user_data, "student_major", None),
        grade=getattr(user_data, "student_grade", None),
        class_name=getattr(user_data, "student_class_name", None),
        create_by=creator_id,
        create_time=datetime.now(),
    )
    await StudentMapper.add_student(new_student, db)


async def _create_teacher_identity(
    db: AsyncSession, user_id: int, user_data: "UserCreateDTO", current_user: CurrentUser | None
) -> None:
    """创建用户时内联创建教师身份记录

    Args:
        db: 数据库会话。
        user_id: 新创建的用户ID。
        user_data: 用户创建 DTO。
        current_user: 当前操作用户。
    """
    real_name = getattr(user_data, "teacher_real_name", None)
    if not real_name:
        return

    teacher_no = getattr(user_data, "teacher_no", None)
    # 校验工号唯一性
    if teacher_no:
        from graphedu.services.education.teacher import _check_teacher_no_exists

        if await _check_teacher_no_exists(teacher_no, db):
            from graphedu.common.exceptions.services.education.teacher import TeacherNoAlreadyExistsException

            raise TeacherNoAlreadyExistsException(teacher_no=teacher_no)

    creator_id = (
        current_user.detail.user.user_id if current_user and current_user.detail and current_user.detail.user else None
    )
    new_teacher = EduTeacher(
        teacher_id=user_id,  # 共享主键
        real_name=real_name,
        teacher_no=teacher_no,
        faculty=getattr(user_data, "teacher_faculty", None),
        title=getattr(user_data, "teacher_title", None),
        research_direction=getattr(user_data, "teacher_research_direction", None),
        create_by=creator_id,
        create_time=datetime.now(),
    )
    await TeacherMapper.add_teacher(new_teacher, db)


async def _sync_identity_on_update(
    db: AsyncSession, target_user: SysUser, user_data: "UserUpdateDTO", current_user: CurrentUser
) -> None:
    """更新用户时同步学生/教师身份信息

    根据用户的 user_type 同步更新对应的身份记录。
    如果身份记录不存在但 DTO 提供了创建字段，则自动创建。

    Args:
        db: 数据库会话。
        target_user: 目标用户 ORM 对象。
        user_data: 用户更新 DTO。
        current_user: 当前操作用户。
    """
    user_id = target_user.user_id
    user_type = target_user.user_type

    if user_type == SystemConstants.UserType.STUDENT:
        student = await StudentMapper.get_by_user_id(user_id, db)
        if student:
            # 更新已有记录
            _update_student_fields(student, user_data, current_user)
            await StudentMapper.update(student, db)
        elif getattr(user_data, "student_real_name", None):
            # 没有记录但提供了创建字段 → 新建
            await _create_student_identity(db, user_id, user_data, current_user)

    elif user_type == SystemConstants.UserType.TEACHER:
        teacher = await TeacherMapper.get_by_user_id(user_id, db)
        if teacher:
            _update_teacher_fields(teacher, user_data, current_user)
            await TeacherMapper.update(teacher, db)
        elif getattr(user_data, "teacher_real_name", None):
            await _create_teacher_identity(db, user_id, user_data, current_user)


def _update_student_fields(student: EduStudent, user_data: "UserUpdateDTO", current_user: CurrentUser) -> None:
    """根据 DTO 更新学生记录字段"""
    field_map = {
        "student_real_name": "real_name",
        "student_no": "student_no",
        "student_faculty": "faculty",
        "student_major": "major",
        "student_grade": "grade",
        "student_class_name": "class_name",
    }
    for dto_field, orm_field in field_map.items():
        value = getattr(user_data, dto_field, None)
        if value is not None:
            setattr(student, orm_field, value)
    student.update_by = current_user.detail.user.user_id if current_user.detail and current_user.detail.user else None
    student.update_time = datetime.now()


def _update_teacher_fields(teacher: EduTeacher, user_data: "UserUpdateDTO", current_user: CurrentUser) -> None:
    """根据 DTO 更新教师记录字段"""
    field_map = {
        "teacher_real_name": "real_name",
        "teacher_no": "teacher_no",
        "teacher_faculty": "faculty",
        "teacher_title": "title",
        "teacher_research_direction": "research_direction",
    }
    for dto_field, orm_field in field_map.items():
        value = getattr(user_data, dto_field, None)
        if value is not None:
            setattr(teacher, orm_field, value)
    teacher.update_by = current_user.detail.user.user_id if current_user.detail and current_user.detail.user else None
    teacher.update_time = datetime.now()
