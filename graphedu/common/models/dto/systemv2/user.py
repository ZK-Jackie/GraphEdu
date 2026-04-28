"""用户管理相关 DTO 模块

本模块定义了用户管理相关的数据传输对象，包括：

- **UserLoginByUsernameDTO**: 用户名登录 DTO
- **UserLoginResponseDTO**: 登录响应 DTO
- **UserRegisterByUsernameDTO**: 用户名注册 DTO
- **UserProfileDTO**: 用户信息 DTO
- **UserResetPasswordDTO**: 重置密码 DTO
- **UserQueryDTO**: 用户查询 DTO
- **UserCreateDTO**: 创建用户 DTO
- **UserUpdateDTO**: 更新用户 DTO
- **UserPasswordResetDTO**: 管理员重置密码 DTO
- **UserStatusChangeDTO**: 修改用户状态 DTO
- **UserAvatarUpdateDTO**: 更新头像 DTO
- **UserProfileUpdateDTO**: 更新个人信息 DTO
- **UserRoleQueryDTO**: 用户角色查询 DTO
- **UserRoleUpdateDTO**: 更新用户角色 DTO
"""

from datetime import datetime
import re
from typing import Literal

from pydantic import Field, model_validator

from graphedu.common.exceptions.services.system.auth import (
    RegisterIllegalDoublePasswordException,
    RegisterIllegalPasswordException,
)
from graphedu.common.models.bo import UserDetail
from graphedu.common.models.dto.base import DTO, PageQuery


# ============================================================================
# 用户基础信息 (sys_user)
# ============================================================================
class UserLoginByUsernameDTO(DTO):
    """用户名登录 DTO

    用于用户通过用户名和密码登录

    Attributes:
        user_name: 用户名称
        password: 用户密码
        code: 验证码（可选）
        uuid: 会话编号（可选）
        login_info: 登录信息，前端无需传递
        captcha_enabled: 是否启用验证码，前端无需传递
    """

    user_name: str = Field(description="用户名称")
    password: str = Field(description="用户密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="会话编号")
    login_info: dict | None = Field(default=None, description="登录信息，前端无需传递")
    captcha_enabled: bool | None = Field(default=None, description="是否启用验证码，前端无需传递")


class UserLoginByStudentNoDTO(DTO):
    """学号登录 DTO

    用于学生通过学号和密码登录

    Attributes:
        student_no: 学号
        password: 用户密码
        code: 验证码（可选）
        uuid: 会话编号（可选）
        login_info: 登录信息，前端无需传递
        captcha_enabled: 是否启用验证码，前端无需传递
    """

    student_no: str = Field(description="学号")
    password: str = Field(description="用户密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="会话编号")
    login_info: dict | None = Field(default=None, description="登录信息，前端无需传递")
    captcha_enabled: bool | None = Field(default=None, description="是否启用验证码，前端无需传递")


class UserLoginByTeacherNoDTO(DTO):
    """工号登录 DTO

    用于教师通过工号和密码登录

    Attributes:
        teacher_no: 工号
        password: 用户密码
        code: 验证码（可选）
        uuid: 会话编号（可选）
        login_info: 登录信息，前端无需传递
        captcha_enabled: 是否启用验证码，前端无需传递
    """

    teacher_no: str = Field(description="工号")
    password: str = Field(description="用户密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="会话编号")
    login_info: dict | None = Field(default=None, description="登录信息，前端无需传递")
    captcha_enabled: bool | None = Field(default=None, description="是否启用验证码，前端无需传递")


class UserLoginByPhoneDTO(DTO):
    """手机号登录 DTO

    用于用户通过手机号和密码登录

    Attributes:
        phonenumber: 手机号码
        password: 用户密码
        code: 验证码（可选）
        uuid: 会话编号（可选）
        login_info: 登录信息，前端无需传递
        captcha_enabled: 是否启用验证码，前端无需传递
    """

    phonenumber: str = Field(description="手机号码")
    password: str = Field(description="用户密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="会话编号")
    login_info: dict | None = Field(default=None, description="登录信息，前端无需传递")
    captcha_enabled: bool | None = Field(default=None, description="是否启用验证码，前端无需传递")


class UserLoginResponseDTO(DTO):
    """登录响应 DTO

    用于返回登录成功后的 token 信息

    Attributes:
        access_token: 访问令牌
        token_type: 令牌类型（默认 Bearer）
        expires_in: 令牌过期时间（秒）
    """

    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int | None = Field(default=None, description="令牌过期时间，单位秒")


class UserRegisterByUsernameDTO(DTO):
    """用户名注册 DTO

    用于用户通过用户名和密码注册

    Attributes:
        username: 用户名称
        password: 用户密码
        confirm_password: 用户二次确认密码
        code: 验证码（可选）
        uuid: 会话编号（可选）
    """

    username: str = Field(description="用户名称")
    password: str = Field(description="用户密码")
    confirm_password: str = Field(description="用户二次确认密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="会话编号")

    @model_validator(mode="after")
    def password_legality_validator(self) -> "UserRegisterByUsernameDTO":
        """验证密码合法性

        检查密码是否包含非法字符

        Returns:
            验证通过的用户对象

        Raises:
            RegisterIllegalPasswordException: 密码包含非法字符
        """
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        raise RegisterIllegalPasswordException(reason="密码不能包含非法字符：< > \" ' \\ |")


class UserProfileDTO(DTO):
    """用户信息 DTO

    用于返回用户的详细信息

    Attributes:
        user: 用户详细信息
        role_keys: 用户角色标识列表
        dept_keys: 用户部门标识列表
    """

    user: UserDetail = Field(description="用户详细信息")
    role_keys: list[str] | None = Field(default=None, description="用户角色标识列表")
    dept_keys: list[str] | None = Field(default=None, description="用户部门标识列表")


class UserResetPasswordDTO(DTO):
    """重置密码 DTO

    用于用户重置自己的密码

    Attributes:
        old_password: 旧密码（可选）
        new_password: 新密码（可选）
        sms_code: 短信验证码（可选）
    """

    old_password: str | None = Field(default=None, description="旧密码")
    new_password: str | None = Field(default=None, description="新密码")
    sms_code: str | None = Field(default=None, description="短信验证码")

    @model_validator(mode="after")
    def check_new_password(self) -> "UserResetPasswordDTO":
        """验证新密码合法性

        检查新密码是否包含非法字符

        Returns:
            验证通过的重置密码对象

        Raises:
            RegisterIllegalPasswordException: 密码包含非法字符
        """
        pattern = r"""^[^<>"'|\\]+$"""
        if self.new_password is None or re.match(pattern, self.new_password):
            return self
        raise RegisterIllegalPasswordException(reason="密码不能包含非法字符：< > \" ' \\ |")


# ============================================================================
# 用户查询相关 DTO
# ============================================================================
class UserQueryDTO(PageQuery):
    """用户查询 DTO"""

    user_id: int | None = Field(default=None, description="用户ID")
    user_name: str | None = Field(default=None, description="用户账号")
    nick_name: str | None = Field(default=None, description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
    user_types: list[str] = Field(
        default_factory=list, description="用户类型列表，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）"
    )
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


# ============================================================================
# 用户创建/更新相关 DTO
# ============================================================================
class UserCreateDTO(DTO):
    """创建用户 DTO

    用于管理员创建新用户

    Attributes:
        user_name: 用户账号
        nick_name: 用户昵称
        password: 用户密码
        email: 用户邮箱（可选）
        phonenumber: 手机号码（可选）
        user_type: 用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）
        status: 账号状态（0正常 1停用）
        remark: 备注（可选）
        role_ids: 角色 ID 列表（可选）
        dept_ids: 部门 ID 列表（可选）
    """

    user_name: str = Field(description="用户账号")
    nick_name: str = Field(description="用户昵称")
    password: str = Field(description="用户密码")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
    user_type: str = Field(default="4", description="用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）")
    status: Literal["0", "1"] = Field(default="0", description="对照sys_data_status（0正常 1停用）")
    remark: str | None = Field(default=None, description="备注")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    # 内联学生信息字段（当 user_type=1 时使用）
    student_real_name: str | None = Field(default=None, description="学生真实姓名（内联创建）")
    student_no: str | None = Field(default=None, description="学号（内联创建）")
    student_faculty: str | None = Field(default=None, description="学院")
    student_major: str | None = Field(default=None, description="专业")
    student_grade: str | None = Field(default=None, description="年级")
    student_class_name: str | None = Field(default=None, description="班级")
    # 内联教师信息字段（当 user_type=2 时使用）
    teacher_real_name: str | None = Field(default=None, description="教师真实姓名（内联创建）")
    teacher_no: str | None = Field(default=None, description="工号（内联创建）")
    teacher_faculty: str | None = Field(default=None, description="所属学院")
    teacher_title: str | None = Field(default=None, description="职称")
    teacher_research_direction: str | None = Field(default=None, description="研究方向")

    @model_validator(mode="after")
    def check_password(self) -> "UserCreateDTO":
        """验证密码合法性

        检查密码是否包含非法字符

        Returns:
            验证通过的用户对象

        Raises:
            RegisterIllegalPasswordException: 密码包含非法字符
        """
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        raise RegisterIllegalPasswordException(reason="密码不能包含非法字符：< > \" ' \\ |")


class UserUpdateDTO(DTO):
    """更新用户 DTO

    用于管理员更新用户信息

    Attributes:
        user_id: 用户 ID（必需）
        nick_name: 用户昵称（可选）
        email: 用户邮箱（可选）
        phonenumber: 手机号码（可选）
        avatar_file_id: 头像文件 ID（可选）
        status: 账号状态（可选）
        remark: 备注（可选）
        login_ip: 最后登录 IP（可选）
        login_date: 最后登录时间（可选）
        role_ids: 角色 ID 列表（可选）
        dept_ids: 部门 ID 列表（可选）
        update_type: 更新类型（basic/password/status/avatar_url）
    """

    user_id: int = Field(description="用户ID")
    nick_name: str | None = Field(default=None, description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
    avatar_file_id: int | None = Field(default=None, description="头像文件ID")
    status: str | None = Field(default=None, description="帐号状态")
    remark: str | None = Field(default=None, description="备注")
    login_ip: str | None = Field(default="", description="最后登录IP")
    login_date: datetime | None = Field(default=None, description="最后登录时间")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    update_type: Literal["basic", "password", "status", "avatar_url"] | None = Field(
        default="basic",
        description="更新类型，basic-基本信息, password-密码, status-状态（登录状态、账户状态）, avatar_url-头像",
    )
    # 内联学生信息字段（当 user_type=1 时使用）
    student_real_name: str | None = Field(default=None, description="学生真实姓名")
    student_no: str | None = Field(default=None, description="学号")
    student_faculty: str | None = Field(default=None, description="学院")
    student_major: str | None = Field(default=None, description="专业")
    student_grade: str | None = Field(default=None, description="年级")
    student_class_name: str | None = Field(default=None, description="班级")
    # 内联教师信息字段（当 user_type=2 时使用）
    teacher_real_name: str | None = Field(default=None, description="教师真实姓名")
    teacher_no: str | None = Field(default=None, description="工号")
    teacher_faculty: str | None = Field(default=None, description="所属学院")
    teacher_title: str | None = Field(default=None, description="职称")
    teacher_research_direction: str | None = Field(default=None, description="研究方向")


class UserPasswordResetDTO(DTO):
    """管理员重置用户密码 DTO

    用于管理员重置指定用户的密码

    Attributes:
        user_id: 用户 ID
        password: 新密码
    """

    user_id: int = Field(description="用户ID")
    password: str = Field(description="新密码")

    @model_validator(mode="after")
    def check_password(self) -> "UserPasswordResetDTO":
        """验证密码合法性

        检查密码是否包含非法字符

        Returns:
            验证通过的重置密码对象

        Raises:
            RegisterIllegalPasswordException: 密码包含非法字符
        """
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        raise RegisterIllegalPasswordException(reason="密码不能包含非法字符：< > \" ' \\ |")


class UserStatusChangeDTO(DTO):
    """修改用户状态 DTO

    用于启用或停用用户账号

    Attributes:
        user_id: 用户 ID
        status: 账号状态（0正常 1停用）
    """

    user_id: int = Field(description="用户ID")
    status: Literal["0", "1"] = Field(description="对照sys_data_status（0正常 1停用）")


class UserAvatarUpdateDTO(DTO):
    """更新用户头像 DTO

    用于用户更新自己的头像

    Attributes:
        avatar_file_id: 头像文件 ID
    """

    avatar_file_id: int = Field(description="头像文件ID")


class UserProfileUpdateDTO(DTO):
    """更新个人信息 DTO

    用于用户更新自己的基本信息

    Attributes:
        nick_name: 用户昵称（可选）
        email: 用户邮箱（可选）
        phonenumber: 手机号码（可选）
        remark: 备注（可选）
    """

    nick_name: str | None = Field(default=None, description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
    remark: str | None = Field(default=None, description="备注")


# ============================================================================
# 用户角色关联相关 DTO
# ============================================================================
class UserRoleQueryDTO(DTO):
    """用户角色查询 DTO

    用于查询用户的角色信息

    Attributes:
        user_id: 用户 ID
    """

    user_id: int = Field(description="用户ID")


class UserRoleUpdateDTO(DTO):
    """更新用户角色关联 DTO

    用于更新用户的角色关联

    Attributes:
        user_id: 用户 ID
        role_ids: 角色 ID 列表
    """

    user_id: int = Field(description="用户ID")
    role_ids: list[int] = Field(description="角色ID列表")


# ============================================================================
# 用户身份绑定相关 DTO
# ============================================================================
class UserBindIdentityDTO(DTO):
    """用户身份绑定 DTO

    用于用户绑定学生或教师身份

    Attributes:
        identity_type: 身份类型（student 或 teacher）
        student_id: 学生ID（可选）
        student_no: 学号（可选）
        teacher_id: 教师ID（可选）
        teacher_no: 工号（可选）
    """

    identity_type: Literal["student", "teacher"] = Field(description="身份类型")
    student_id: int | None = Field(default=None, description="学生ID")
    student_no: str | None = Field(default=None, description="学号")
    teacher_id: int | None = Field(default=None, description="教师ID")
    teacher_no: str | None = Field(default=None, description="工号")

    @model_validator(mode="after")
    def validate_identity_fields(self) -> "UserBindIdentityDTO":
        """验证身份字段

        根据身份类型验证必需的字段

        Returns:
            验证通过的用户身份绑定 DTO

        Raises:
            ValueError: 身份字段验证失败
        """
        if self.identity_type == "student":
            if not self.student_id and not self.student_no:
                raise ValueError("绑定学生身份时，必须提供 student_id 或 student_no")
        elif self.identity_type == "teacher" and not self.teacher_id and not self.teacher_no:
            raise ValueError("绑定教师身份时，必须提供 teacher_id 或 teacher_no")
        return self


# ============================================================================
# 忘记密码相关 DTO
# ============================================================================
class ForgotPasswordSendCodeDTO(DTO):
    """忘记密码 - 发送短信验证码 DTO

    用于用户请求发送密码重置短信验证码

    Attributes:
        phonenumber: 手机号码
    """

    phonenumber: str = Field(description="手机号码")


class ForgotPasswordResetDTO(DTO):
    """忘记密码 - 重置密码 DTO

    用于用户通过短信验证码重置密码

    Attributes:
        phonenumber: 手机号码
        sms_code: 短信验证码
        new_password: 新密码
        confirm_password: 确认新密码
    """

    phonenumber: str = Field(description="手机号码")
    sms_code: str = Field(description="短信验证码")
    new_password: str = Field(description="新密码")
    confirm_password: str = Field(description="确认新密码")

    @model_validator(mode="after")
    def check_passwords_match(self) -> "ForgotPasswordResetDTO":
        """验证两次密码是否一致"""
        if self.new_password != self.confirm_password:
            raise RegisterIllegalDoublePasswordException
        return self

    @model_validator(mode="after")
    def check_new_password_legality(self) -> "ForgotPasswordResetDTO":
        """验证新密码合法性"""
        pattern = r"""^[^<>"'|\\]+$"""
        if self.new_password is None or re.match(pattern, self.new_password):
            return self
        raise RegisterIllegalPasswordException(reason="密码不能包含非法字符：< > \" ' \\ |")
