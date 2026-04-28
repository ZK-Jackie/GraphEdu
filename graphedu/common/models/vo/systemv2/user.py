"""用户管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.vo.base import VO
from graphedu.common.models.vo.educationv2.student import StudentDetailVO, StudentListVO
from graphedu.common.models.vo.educationv2.teacher import TeacherDetailVO, TeacherListVO
from graphedu.common.models.vo.systemv2.dept import DeptDetailVO
from graphedu.common.models.vo.systemv2.role import RoleDetailVO


class UserInfoVO(VO):
    """用户简要信息 VO"""

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    user_type: str = Field(description="用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）")
    status: str = Field(description="帐号状态（0正常 1停用）")
    avatar_file_id: int | None = Field(default=None, description="头像文件ID")


class UserDetailVO(VO):
    """用户详细信息 VO，比 ORM 少 password，多关联信息"""

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
    avatar_file_id: int | None = Field(default=None, description="头像文件ID")
    avatar_path: str | None = Field(default=None, description="头像文件路径")
    user_type: str = Field(description="用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    login_ip: str | None = Field(default=None, description="最后登录IP")
    login_date: datetime | None = Field(default=None, description="最后登录时间")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")

    # 关联信息
    dept_ids: list[int] | None = Field(default=None, description="部门ID列表")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")
    # 学生/教师绑定信息（所有用户类型统一使用这些字段）
    student: StudentDetailVO | None = Field(default=None, description="关联的学生信息（最多1个）")
    teacher: TeacherDetailVO | None = Field(default=None, description="关联的教师信息（最多1个）")


class UserListVO(VO):
    """用户列表项 VO"""

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="登录账号")
    nick_name: str = Field(description="用户昵称")
    email: str | None = Field(default=None, description="用户邮箱")
    phonenumber: str | None = Field(default=None, description="手机号码")
    avatar_file_id: int | None = Field(default=None, description="头像文件ID")
    user_type: str = Field(description="用户类型，对照 sys_user_type（1学生, 2教师, 3管理员, 4其他）")
    status: str = Field(description="帐号状态（0正常 1停用）")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联的部门信息（从查询结果中获取）
    dept_id: int | None = Field(default=None, description="主部门ID")
    dept_name: str | None = Field(default=None, description="主部门名称")
    # 学生/教师绑定信息（用于列表显示）
    student: StudentListVO | None = Field(default=None, description="关联的学生信息（最多1个）")
    teacher: TeacherListVO | None = Field(default=None, description="关联的教师信息（最多1个）")


class UserProfileVO(VO):
    """用户个人信息 VO"""

    user: UserDetailVO = Field(description="用户详细信息")
    role_keys: list[str] | None = Field(default=None, description="用户角色标识列表")
    role_names: list[str] | None = Field(default=None, description="用户角色名称列表")
    dept_keys: list[str] | None = Field(default=None, description="用户部门标识列表")
    dept_names: list[str] | None = Field(default=None, description="用户部门名称列表")


class UserRoleVO(VO):
    """用户的角色列表 VO"""

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="用户账号")
    role_ids: list[int] = Field(description="角色ID列表")
    roles: list = Field(default_factory=list, description="所有角色列表")


# 临时响应类型（用于需要返回字典数据的场景）
class UserRoleListVO(VO):
    """用户角色列表响应 VO"""

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="用户名称")
    role_ids: list[int] = Field(description="用户当前角色ID列表")
    roles: list = Field(default_factory=list, description="所有角色列表")


class AuthCurrentUserDetailVO(VO):
    """认证后的当前用户详细信息 VO"""

    dept_ids: list[int] = Field(default_factory=list, description="部门ID列表")
    role_ids: list[int] = Field(default_factory=list, description="角色ID列表")
    depts: list[DeptDetailVO] = Field(default_factory=list, description="部门信息 ORM 对象列表")
    roles: list[RoleDetailVO] = Field(default_factory=list, description="角色信息 ORM 对象列表")
    user: UserDetailVO = Field(description="用户信息 ORM 对象")
    avatar_url: str | None = Field(default=None, description="用户头像URL")
    student: StudentDetailVO | None = Field(default=None, description="学生信息", validation_alias="student_info")
    teacher: TeacherDetailVO | None = Field(default=None, description="教师信息", validation_alias="teacher_info")


class AuthCurrentUserVO(VO):
    """认证后的当前用户信息 VO"""

    session_id: str | None = Field(default=None, description="会话ID")
    permissions: list[str] = Field(description="function_key字符串列表")
    role_keys: list[str] = Field(description="role_key字符串列表")
    detail: AuthCurrentUserDetailVO = Field(description="用户信息")


class UserBindIdentityVO(VO):
    """用户身份绑定信息 VO"""

    user_id: int = Field(description="用户ID")
    user_name: str = Field(description="用户账号")
    identity_type: Literal["student", "teacher"] | None = Field(default=None, description="身份类型")
    identity_id: int | None = Field(default=None, description="身份ID")
    identity_name: str | None = Field(default=None, description="身份姓名")
    identity_no: str | None = Field(default=None, description="身份编号")
    bind_time: datetime | None = Field(default=None, description="绑定时间")
