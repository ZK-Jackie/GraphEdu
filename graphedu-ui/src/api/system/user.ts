/**
 * 用户管理相关 API
 * 对应后端：graphedu/api/services/system/user.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  UserQueryDTO,
  UserCreateDTO,
  UserUpdateDTO,
  UserPasswordResetDTO,
  UserStatusChangeDTO,
  UserProfileUpdateDTO,
  UserRoleUpdateDTO,
  UserDetailVO,
  UserProfileVO,
  UserRoleListVO,
  UserListVO,
} from '@/types/api/system/user.ts'
import type { DeptTreeVO } from '@/types/api/system/dept.ts'
import type { StudentListVO, StudentQueryDTO } from '@/types/api/education/student.ts'
import type { TeacherListVO, TeacherQueryDTO } from '@/types/api/education/teacher.ts'

/**
 * 获取部门树（用于用户管理页面的部门筛选）
 * GET /system/user/deptTree
 */
export function getUserDeptTree(params?: { parent_id?: number }): Promise<ResponseType<DeptTreeVO[]>> {
  return request({
    url: '/system/user/deptTree',
    method: 'get',
    params: params,
  })
}

/**
 * 获取用户列表（分页）
 * GET /system/user/list
 */
export function getUserList(query: UserQueryDTO): Promise<ResponseType<PageResponse>> {
  return request({
    url: '/system/user/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增用户
 * POST /system/user
 */
export function addUser(data: UserCreateDTO): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: '/system/user',
    method: 'post',
    data: data,
  })
}

/**
 * 修改用户
 * PUT /system/user
 */
export function updateUser(data: UserUpdateDTO): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: '/system/user',
    method: 'put',
    data: data,
  })
}

/**
 * 删除用户（支持批量删除）
 * DELETE /system/user/{user_ids}
 */
export function deleteUser(userIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/user/${userIds}`,
    method: 'delete',
  })
}

/**
 * 管理员重置用户密码
 * PUT /system/user/resetPwd
 */
export function resetUserPwd(data: UserPasswordResetDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/user/resetPwd',
    method: 'put',
    data: data,
  })
}

/**
 * 修改用户状态
 * PUT /system/user/changeStatus
 */
export function changeUserStatus(data: UserStatusChangeDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/user/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取当前登录用户的个人信息
 * GET /system/user/profile
 */
export function getUserProfile(): Promise<ResponseType<UserProfileVO>> {
  return request({
    url: '/system/user/profile',
    method: 'get',
  })
}

/**
 * 修改当前登录用户的个人信息
 * PUT /system/user/profile
 */
export function updateUserProfile(data: UserProfileUpdateDTO): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: '/system/user/profile',
    method: 'put',
    data: data,
  })
}

/**
 * 修改当前登录用户的头像
 * PUT /system/user/profile/avatar
 */
export function updateUserAvatar(avatarFileId: number): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: '/system/user/profile/avatar',
    method: 'put',
    data: { avatarFileId: avatarFileId },
  })
}

/**
 * 修改当前登录用户的密码
 * PUT /system/user/profile/updatePwd
 */
export function updateUserPassword(data: {
  old_password?: string
  new_password?: string
}): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/user/profile/updatePwd',
    method: 'put',
    data,
  })
}

/**
 * 获取用户详细信息（包括角色、部门等）
 * GET /system/user/{user_id}
 */
export function getUserDetail(userId?: number): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: `/system/user/${userId || ''}`,
    method: 'get',
  })
}

/**
 * 获取用户的角色关联信息
 * GET /system/user/authRole/{user_id}
 */
export function getUserRoleList(userId: number): Promise<ResponseType<UserRoleListVO>> {
  return request({
    url: `/system/user/authRole/${userId}`,
    method: 'get',
  })
}

/**
 * 更新用户的角色关联
 * PUT /system/user/authRole
 */
export function updateUserRole(data: UserRoleUpdateDTO): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: '/system/user/authRole',
    method: 'put',
    data,
  })
}

/**
 * 获取可关联学生的用户列表
 * GET /system/user/available-for-student
 */
export function getAvailableUsersForStudent(): Promise<ResponseType<UserListVO[]>> {
  return request({
    url: '/system/user/available-for-student',
    method: 'get',
  })
}

/**
 * 获取未绑定的学生列表
 * GET /system/user/unbound-students
 */
export function getUnboundStudents(params?: StudentQueryDTO): Promise<ResponseType<PageResponse<StudentListVO>>> {
  return request({
    url: '/system/user/unbound-students',
    method: 'get',
    params,
  })
}

/**
 * 获取未绑定的教师列表
 * GET /system/user/unbound-teachers
 */
export function getUnboundTeachers(params?: TeacherQueryDTO): Promise<ResponseType<PageResponse<TeacherListVO>>> {
  return request({
    url: '/system/user/unbound-teachers',
    method: 'get',
    params,
  })
}
