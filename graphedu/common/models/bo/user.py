"""用户相关 BO 模块

定义了用户相关的业务对象模型，包括用户详细信息模型和当前用户信息模型
"""

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from pydantic.alias_generators import to_camel

from graphedu.common.models.orm import SysDept, SysRole, SysUser
from graphedu.common.models.orm.education import EduStudent, EduTeacher
from graphedu.common.utils.strings import SqlalchemyUtil


class UserDetail(BaseModel):
    """用户详细信息模型

    包含用户的详细信息，包括部门、角色、头像、身份信息等

    Attributes:
        dept_ids: 部门 ID 列表
        role_ids: 角色 ID 列表
        depts: 部门信息 ORM 对象列表
        roles: 角色信息 ORM 对象列表
        user: 用户信息 ORM 对象
        avatar_url: 用户头像 URL
        student_info: 学生扩展信息 ORM 对象（当 user_type=1 时有效）
        teacher_info: 教师扩展信息 ORM 对象（当 user_type=2 时有效）
    """

    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
    depts: list[SysDept] = Field(default_factory=list, description="部门信息 ORM 对象列表")
    roles: list[SysRole] = Field(default_factory=list, description="角色信息 ORM 对象列表")
    user: SysUser | None = Field(default=None, description="用户信息 ORM 对象")
    avatar_url: str | None = Field(default=None, description="用户头像URL")
    student_info: EduStudent | None = Field(default=None, description="学生扩展信息 ORM 对象")
    teacher_info: EduTeacher | None = Field(default=None, description="教师扩展信息 ORM 对象")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )

    @field_serializer("depts", "roles", mode="plain")
    def sql_model_dump_list(self, values: list[SysDept] | list[SysRole] | SysUser) -> list[dict]:
        """将 SQLAlchemy ORM 对象序列化为字典列表"""
        if isinstance(values, SysUser):
            return SqlalchemyUtil.base_to_dict(values)
        return [SqlalchemyUtil.base_to_dict(v) for v in values]

    @field_serializer("user", "student_info", "teacher_info", mode="plain")
    def sql_model_dump_single(self, value: EduStudent | EduTeacher | None) -> dict | None:
        """将可选的 SQLAlchemy ORM 对象序列化为字典"""
        if value is None:
            return None
        return SqlalchemyUtil.base_to_dict(value)

    @field_validator("depts", mode="before")
    @classmethod
    def depts_validator(cls, value: list[dict] | dict | SysDept) -> list[SysDept]:
        """将字典列表反序列化为 SQLAlchemy ORM 对象列表"""
        if not isinstance(value, list):
            value = [value]
        if all(isinstance(v, SysDept) for v in value):
            return value  # 已经是 SysDept 对象列表，无需转换
        return [SysDept(**v) for v in value]

    @field_validator("roles", mode="before")
    @classmethod
    def roles_validator(cls, value: list[dict] | dict | SysRole) -> list[SysRole]:
        """将字典列表反序列化为 SQLAlchemy ORM 对象列表"""
        if not isinstance(value, list):
            value = [value]
        if all(isinstance(v, SysRole) for v in value):
            return value  # 已经是 SysRole 对象列表，无需转换
        return [SysRole(**v) for v in value]

    @field_validator("user", mode="before")
    @classmethod
    def user_validator(cls, value: dict | SysUser) -> SysUser:
        """将字典反序列化为 SQLAlchemy ORM 对象"""
        if isinstance(value, SysUser):
            return value  # 已经是 SysUser 对象，无需转换
        return SysUser(**value)

    @field_validator("student_info", mode="before")
    @classmethod
    def student_info_validator(cls, value: dict | EduStudent | None) -> EduStudent | None:
        """将字典反序列化为 EduStudent ORM 对象"""
        if value is None or isinstance(value, EduStudent):
            return value
        return EduStudent(**value)

    @field_validator("teacher_info", mode="before")
    @classmethod
    def teacher_info_validator(cls, value: dict | EduTeacher | None) -> EduTeacher | None:
        """将字典反序列化为 EduTeacher ORM 对象"""
        if value is None or isinstance(value, EduTeacher):
            return value
        return EduTeacher(**value)


class CurrentUser(BaseModel):
    """当前用户信息模型

    表示当前登录用户的信息

    Attributes:
        session_id: 会话 ID
        permissions: 权限标识列表
        role_keys: 角色标识列表
        detail: 用户详细信息
    """

    session_id: str | None = Field(default=None, description="会话ID")
    permissions: list[str] = Field(description="function_key字符串列表")
    role_keys: list[str] = Field(description="role_key字符串列表")
    detail: UserDetail | None = Field(default=None, description="用户信息")

    model_config = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, validate_by_alias=True, serialize_by_alias=True
    )

    def is_admin(self) -> bool:
        """判断当前用户是否为管理员

        超级管理员定义：用户拥有 role_id <= 10 的角色

        Returns:
            如果用户拥有 role_id <= 10 的角色则返回 True，否则返回 False
        """
        if not self.detail or not self.detail.role_ids:
            return False
        return any(role_id <= 10 for role_id in self.detail.role_ids)
