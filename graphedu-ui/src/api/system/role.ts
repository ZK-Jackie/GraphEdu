/**
 * 角色管理相关 API
 * 对应后端：graphedu/api/services/system/role.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  RoleQueryDTO,
  RoleCreateDTO,
  RoleUpdateDTO,
  RoleStatusChangeDTO,
  RoleDatascopeChangeDTO,
  RoleUserQueryDTO,
  RoleListVO,
  RoleDetailVO,
  RoleDeptVO,
} from '@/types/api/system/role.ts'
import type { UserListVO } from '@/types/api/system/user.ts'

/**
 * 获取角色列表（分页）
 * GET /system/role/list
 */
export function getRoleList(query: RoleQueryDTO): Promise<ResponseType<PageResponse<RoleListVO>>> {
  return request({
    url: '/system/role/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增角色
 * POST /system/role
 */
export function addRole(data: RoleCreateDTO): Promise<ResponseType<RoleDetailVO>> {
  return request({
    url: '/system/role',
    method: 'post',
    data,
  })
}

/**
 * 修改角色
 * PUT /system/role
 */
export function updateRole(data: RoleUpdateDTO): Promise<ResponseType<RoleDetailVO>> {
  return request({
    url: '/system/role',
    method: 'put',
    data,
  })
}

/**
 * 修改角色状态
 * PUT /system/role/status
 */
export function changeRoleStatus(data: RoleStatusChangeDTO): Promise<ResponseType<RoleDetailVO>> {
  return request({
    url: '/system/role/status',
    method: 'put',
    data,
  })
}

/**
 * 修改角色数据权限范围
 * PUT /system/role/dataScope
 */
export function updateRoleDataScope(data: RoleDatascopeChangeDTO): Promise<ResponseType<RoleDetailVO>> {
  return request({
    url: '/system/role/dataScope',
    method: 'put',
    data,
  })
}

/**
 * 删除角色（支持批量）
 * DELETE /system/role/{role_ids}
 */
export function deleteRole(roleIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/role/${roleIds}`,
    method: 'delete',
  })
}

/**
 * 获取角色详细信息（含功能权限）
 * GET /system/role/{role_id}
 */
export function getRoleDetail(roleId: number): Promise<ResponseType<RoleDetailVO>> {
  return request({
    url: `/system/role/${roleId}`,
    method: 'get',
  })
}

/**
 * 获取角色的部门树（用于数据权限配置）
 * GET /system/role/deptTree/{role_id}
 */
export function getRoleDeptTree(roleId: number): Promise<ResponseType<RoleDeptVO>> {
  return request({
    url: `/system/role/deptTree/${roleId}`,
    method: 'get',
  })
}

/**
 * 获取角色已分配的用户列表（分页）
 * GET /system/role/authUser/allocatedList
 */
export function getRoleAllocatedUserList(query: RoleUserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
  return request({
    url: '/system/role/authUser/allocatedList',
    method: 'get',
    params: query,
  })
}

/**
 * 获取角色未分配的用户列表（分页）
 * GET /system/role/authUser/unallocatedList
 */
export function getRoleUnallocatedUserList(query: RoleUserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
  return request({
    url: '/system/role/authUser/unallocatedList',
    method: 'get',
    params: query,
  })
}

/**
 * 批量授权用户到角色
 * PUT /system/role/authUser/grant
 */
export function addRoleUsers(roleId: number, userIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/role/authUser/grant',
    method: 'put',
    params: {
      roleId: roleId,
      userIds: userIds,
    },
  })
}

/**
 * 取消单个用户的角色授权
 * PUT /system/role/authUser/revoke
 */
export function removeRoleUser(roleId: number, userId: number): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/role/authUser/revoke',
    method: 'put',
    params: {
      roleId: roleId,
      userId: userId,
    },
  })
}

/**
 * 批量取消用户的角色授权
 * PUT /system/role/authUser/revokeAll
 */
export function removeRoleUsers(roleId: number, userIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/role/authUser/revokeAll',
    method: 'put',
    params: {
      roleId: roleId,
      userIds: userIds,
    },
  })
}
