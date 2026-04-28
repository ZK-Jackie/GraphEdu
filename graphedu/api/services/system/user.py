"""系统用户管理 API 控制器

本模块提供用户管理相关的 REST API 接口，包括用户的增删改查、密码管理、
角色分配、个人信息修改等功能。

主要接口：
- 部门树查询：获取用户管理页面的部门筛选树
- 用户列表：分页查询用户列表，支持多条件筛选
- 用户管理：新增、修改、删除用户
- 密码管理：管理员重置密码、用户修改个人密码
- 状态管理：启用/停用用户账号
- 个人信息：查询/修改个人信息、修改头像
- 角色管理：查询/更新用户角色关联

所有接口均支持数据权限控制，非管理员用户只能操作权限范围内的数据。
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.student import StudentQueryDTO
from graphedu.common.models.dto.educationv2.teacher import TeacherQueryDTO
from graphedu.common.models.dto.systemv2.user import (
    UserBindIdentityDTO,
    UserCreateDTO,
    UserPasswordResetDTO,
    UserProfileUpdateDTO,
    UserQueryDTO,
    UserResetPasswordDTO,
    UserRoleUpdateDTO,
    UserStatusChangeDTO,
    UserUpdateDTO,
)
from graphedu.common.models.vo import DeptTreeVO
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.student import StudentListVO
from graphedu.common.models.vo.educationv2.teacher import TeacherListVO
from graphedu.common.models.vo.systemv2.user import (
    UserBindIdentityVO,
    UserDetailVO,
    UserListVO,
    UserProfileVO,
    UserRoleListVO,
)
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.security.aspect.data_scope import GetDataScope
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.dept import DeptService
from graphedu.services.system.role import RoleService
from graphedu.services.system.user import UserService

user_controller = APIRouter(prefix="/system/user", dependencies=[Depends(SecurityService.get_current_user)])


@user_controller.get(
    "/deptTree",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:list"))],
    response_model=ResponseType[list[DeptTreeVO]],
)
async def get_system_user_dept_tree(
    parent_id: int | None = Query(None, description="父部门ID，0或None表示根节点"),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """获取部门树（用于用户管理页面的部门筛选）"""
    dept_tree = await DeptService.get_dept_children(query_db, data_scope_sql, parent_id)
    return ResponseUtil.success(data=dept_tree)


# ============================================================================
# 用户列表查询
# ============================================================================
@user_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:list"))],
    response_model=ResponseType[PageResponse[UserListVO]],
)
async def get_system_user_list(
    query: UserQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """获取用户列表（分页）"""
    # https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#query-parameter-list-multiple-values-with-defaults
    user_page_result: PageResponse[UserListVO] = await UserService.list_user(query_db, query, data_scope_sql)
    return ResponseUtil.success(data=user_page_result)


# ============================================================================
# 用户新增
# ============================================================================
@user_controller.post(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:user:add"))], response_model=ResponseType[UserDetailVO]
)
@SystemLog(
    title="用户管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"dept_data_scope_sql", "role_data_scope_sql", "current_user"},
)
async def add_system_user(
    user_data: UserCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    dept_data_scope_sql: str = Depends(GetDataScope("SysDept")),
    role_data_scope_sql: str = Depends(GetDataScope("SysRole")),
):
    """新增用户"""
    if not current_user.is_admin():
        if user_data.dept_ids:
            for dept_id in user_data.dept_ids:
                await DeptService.check_dept_data_scope(query_db, dept_id, dept_data_scope_sql)
        if user_data.role_ids:
            for role_id in user_data.role_ids:
                await RoleService.check_role_data_scope(query_db, role_id, role_data_scope_sql)

    result_vo = await UserService.add_user(query_db, user_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 用户修改
# ============================================================================
@user_controller.put(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:user:edit"))], response_model=ResponseType[UserDetailVO]
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_system_user(
    user_data: UserUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope("SysUser")),
    dept_data_scope_sql: str = Depends(GetDataScope("SysDept")),
    role_data_scope_sql: str = Depends(GetDataScope("SysRole")),
):
    """修改用户"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, current_user.detail.user.user_id, user_data_scope_sql)
        if user_data.dept_ids:
            for dept_id in user_data.dept_ids:
                await DeptService.check_dept_data_scope(query_db, dept_id, dept_data_scope_sql)
        if user_data.role_ids:
            for role_id in user_data.role_ids:
                await RoleService.check_role_data_scope(query_db, role_id, role_data_scope_sql)

    result_vo = await UserService.update_user(query_db, user_data, current_user)

    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 用户删除
# ============================================================================
@user_controller.delete(
    "/{user_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.DELETE)
async def delete_system_user(
    user_ids: str = Path(..., pattern="^[0-9,]+$", description="用户ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """删除用户（支持批量删除，返回详细结果）"""
    user_id_list = [int(uid) for uid in user_ids.split(",") if uid]

    if not current_user.is_admin():
        for user_id in user_id_list:
            await UserService.check_user_data_scope(query_db, user_id, data_scope_sql)

    result = await UserService.delete_user(query_db, user_id_list, current_user)

    return ResponseUtil.success(data=result)


# ============================================================================
# 重置用户密码（管理员操作）
# ============================================================================
@user_controller.put(
    "/resetPwd",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:resetPwd"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.UPDATE)
async def reset_system_user_pwd(
    reset_data: UserPasswordResetDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """管理员重置用户密码"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, reset_data.user_id, data_scope_sql)

    await UserService.reset_user_password_by_admin(query_db, reset_data.user_id, reset_data.password, current_user)

    return ResponseUtil.success()


# ============================================================================
# 修改用户状态
# ============================================================================
@user_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.UPDATE)
async def change_system_user_status(
    status_data: UserStatusChangeDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """修改用户状态"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, status_data.user_id, data_scope_sql)

    await UserService.change_user_status(query_db, status_data.user_id, status_data.status, current_user)

    return ResponseUtil.success()


# ============================================================================
# 获取个人信息
# ============================================================================
@user_controller.get("/profile", response_model=ResponseType[UserProfileVO])
async def query_system_user_profile(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取当前登录用户的个人信息"""
    profile_result = await UserService.get_user_profile(query_db, current_user)
    return ResponseUtil.success(data=profile_result)


# ============================================================================
# 修改个人信息
# ============================================================================
@user_controller.put("/profile", response_model=ResponseType[UserDetailVO])
@SystemLog(title="个人信息", business_type=SysConst.BusinessType.UPDATE)
async def change_system_user_profile(
    profile_data: UserProfileUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改当前登录用户的个人信息"""
    user_id = current_user.detail.user.user_id
    result_vo = await UserService.update_user_profile(query_db, user_id, profile_data, current_user)

    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 修改用户头像
# ============================================================================
@user_controller.put("/profile/avatar", response_model=ResponseType[UserDetailVO])
@SystemLog(title="个人信息", business_type=SysConst.BusinessType.UPDATE)
async def update_system_user_avatar(
    avatar_file_id: int = Body(..., embed=True, description="头像文件ID"),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改当前登录用户的头像"""
    user_id = current_user.detail.user.user_id

    result_vo = await UserService.update_user_avatar(query_db, user_id, avatar_file_id, current_user)

    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 修改个人密码
# ============================================================================
@user_controller.put("/profile/updatePwd", response_model=ResponseType[Empty])
@SystemLog(title="个人信息", business_type=SysConst.BusinessType.UPDATE)
async def reset_system_user_password(
    reset_data: UserResetPasswordDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改当前登录用户的密码"""
    user_id = current_user.detail.user.user_id

    await UserService.reset_user_password(query_db, user_id, reset_data, current_user)

    return ResponseUtil.success()


# ============================================================================
# 获取用户详情
# ============================================================================
@user_controller.get(
    "/{user_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:query"))],
    response_model=ResponseType[UserDetailVO],
)
async def query_detail_system_user(
    user_id: int | None = None,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """获取用户详细信息（包括角色、部门等）"""
    if user_id and not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, user_id, data_scope_sql)

    detail_result = await UserService.get_user_detail(query_db, user_id)
    return ResponseUtil.success(data=detail_result)


# ============================================================================
# 获取用户角色关联信息
# ============================================================================
@user_controller.get(
    "/authRole/{user_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:query"))],
    response_model=ResponseType[UserRoleListVO],
)
async def get_system_user_role_list(
    user_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """获取用户的角色关联信息"""
    role_result = await UserService.get_user_role_list(query_db, user_id)
    return ResponseUtil.success(data=role_result)


# ============================================================================
# 更新用户角色关联
# ============================================================================
@user_controller.put(
    "/authRole",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:edit"))],
    response_model=ResponseType[UserDetailVO],
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.GRANT)
async def update_system_user_role(
    role_data: UserRoleUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope("SysUser")),
    role_data_scope_sql: str = Depends(GetDataScope("SysRole")),
):
    """更新用户的角色关联"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, role_data.user_id, user_data_scope_sql)
        for role_id in role_data.role_ids:
            await RoleService.check_role_data_scope(query_db, role_id, role_data_scope_sql)

    result_vo = await UserService.update_user_role(query_db, role_data.user_id, role_data.role_ids, current_user)

    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 用户身份绑定（用户自己操作）
# ============================================================================


@user_controller.post("/profile/bindIdentity", response_model=ResponseType[UserBindIdentityVO])
@SystemLog(title="个人信息", business_type=SysConst.BusinessType.GRANT)
async def bind_user_identity_self(
    bind_data: UserBindIdentityDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """当前登录用户绑定自己的身份（学生或教师）"""
    user_id = current_user.detail.user.user_id
    result = await UserService.bind_user_identity(query_db, user_id, bind_data, current_user)
    return ResponseUtil.success(data=result)


@user_controller.delete("/profile/bindIdentity", response_model=ResponseType[Empty])
@SystemLog(title="个人信息", business_type=SysConst.BusinessType.DELETE)
async def unbind_user_identity_self(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """当前登录用户解绑自己的身份"""
    user_id = current_user.detail.user.user_id
    await UserService.unbind_user_identity(query_db, user_id, current_user)
    return ResponseUtil.success()


@user_controller.get("/profile/identity", response_model=ResponseType[UserBindIdentityVO])
async def get_user_identity_info_self(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取当前登录用户的身份绑定信息"""
    user_id = current_user.detail.user.user_id
    result = await UserService.get_user_identity_info(query_db, user_id)
    return ResponseUtil.success(data=result)


# ============================================================================
# 用户身份绑定（管理员操作）
# ============================================================================


@user_controller.post(
    "/{user_id}/bindIdentity",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:edit"))],
    response_model=ResponseType[UserBindIdentityVO],
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.GRANT)
async def bind_user_identity_admin(
    user_id: int,
    bind_data: UserBindIdentityDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """管理员为指定用户绑定身份（学生或教师）"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, user_id, user_data_scope_sql)

    result = await UserService.bind_user_identity(query_db, user_id, bind_data, current_user)
    return ResponseUtil.success(data=result)


@user_controller.delete(
    "/{user_id}/bindIdentity",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="用户管理", business_type=SysConst.BusinessType.DELETE)
async def unbind_user_identity_admin(
    user_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """管理员解绑指定用户的身份"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, user_id, user_data_scope_sql)

    await UserService.unbind_user_identity(query_db, user_id, current_user)
    return ResponseUtil.success()


@user_controller.get(
    "/{user_id}/identity",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:query"))],
    response_model=ResponseType[UserBindIdentityVO],
)
async def get_user_identity_info_admin(
    user_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """管理员获取指定用户的身份绑定信息"""
    if not current_user.is_admin():
        await UserService.check_user_data_scope(query_db, user_id, user_data_scope_sql)

    result = await UserService.get_user_identity_info(query_db, user_id)
    return ResponseUtil.success(data=result)


# ============================================================================
# 获取可关联学生的用户列表
# ============================================================================


@user_controller.get(
    "/available-for-student",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:list"))],
    response_model=ResponseType[list[UserListVO]],
)
async def get_available_users_for_student(
    query_db: AsyncSession = Depends(get_db),
):
    """获取可关联学生的用户列表（未在 edu_student 表中存在的正常状态用户）"""
    users = await UserService.get_available_users_for_student(query_db)
    return ResponseUtil.success(data=users)


# ============================================================================
# 查询未绑定的学生/教师记录
# ============================================================================


@user_controller.get(
    "/unbound-students",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:list"))],
    response_model=ResponseType[PageResponse[StudentListVO]],
)
async def get_unbound_students(
    query: StudentQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """查询未绑定的学生列表（user_id 为 null 的学生）

    用于用户管理页面中选择学生进行绑定
    """
    from graphedu.services.education.student import StudentService

    page_result = await StudentService.get_unbound_students(query_db, query)
    return ResponseUtil.success(data=page_result)


@user_controller.get(
    "/unbound-teachers",
    dependencies=[Depends(CheckUserInterfacePermit("system:user:list"))],
    response_model=ResponseType[PageResponse[TeacherListVO]],
)
async def get_unbound_teachers(
    query: TeacherQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """查询未绑定的教师列表（user_id 为 null 的教师）

    用于用户管理页面中选择教师进行绑定
    """
    from graphedu.services.education.teacher import TeacherService

    page_result = await TeacherService.get_unbound_teachers(query_db, query)
    return ResponseUtil.success(data=page_result)
