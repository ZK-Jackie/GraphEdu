/**
 * 部门管理相关 API
 * 对应后端：graphedu/api/services/system/dept.py
 */
import request from '@/utils/request'
import type { ResponseType, Empty } from '@/types/api/common.ts'
import type { DeptQueryDTO, DeptCreateDTO, DeptUpdateDTO, DeptTreeVO, DeptDetailVO } from '@/types/api/system/dept.ts'
import type { UserListVO } from '@/types/api/system/user.ts'

/**
 * 获取完整部门树形列表
 * GET /system/dept/list
 */
export function getDeptList(query?: DeptQueryDTO): Promise<ResponseType<DeptTreeVO[]>> {
  return request({
    url: '/system/dept/list',
    method: 'get',
    params: query,
  })
}

/**
 * 异步加载部门子节点（只返回指定父级的直接子节点）
 * GET /system/dept/listLazy
 */
export function getDeptListLazy(parentId: number): Promise<ResponseType<DeptTreeVO[]>> {
  return request({
    url: '/system/dept/listLazy',
    method: 'get',
    params: { parentId },
  })
}

/**
 * 获取排除指定部门及其子部门的部门树（用于编辑时选择父部门）
 * GET /system/dept/list/exclude/{dept_id}
 */
export function getDeptExcludeTree(deptId: number): Promise<ResponseType<DeptTreeVO[]>> {
  return request({
    url: `/system/dept/list/exclude/${deptId}`,
    method: 'get',
  })
}

/**
 * 新增部门
 * POST /system/dept
 */
export function addDept(data: DeptCreateDTO): Promise<ResponseType<DeptDetailVO>> {
  return request({
    url: '/system/dept',
    method: 'post',
    data,
  })
}

/**
 * 修改部门
 * PUT /system/dept
 */
export function updateDept(data: DeptUpdateDTO): Promise<ResponseType<DeptDetailVO>> {
  return request({
    url: '/system/dept',
    method: 'put',
    data,
  })
}

/**
 * 删除部门（支持批量）
 * DELETE /system/dept/{dept_ids}
 */
export function deleteDept(deptIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/dept/${deptIds}`,
    method: 'delete',
  })
}

/**
 * 获取某一部门详细信息
 * GET /system/dept/{dept_id}
 */
export function getDeptDetail(deptId: number): Promise<ResponseType<DeptDetailVO>> {
  return request({
    url: `/system/dept/${deptId}`,
    method: 'get',
  })
}

/**
 * 获取部门用户列表
 * GET /system/dept/{dept_id}/users
 */
export function getDeptUsers(deptId: number): Promise<ResponseType<UserListVO[]>> {
  return request({
    url: `/system/dept/${deptId}/users`,
    method: 'get',
  })
}

/**
 * 移除用户部门关联
 * DELETE /system/dept/{dept_id}/users/{user_id}
 */
export function removeUserFromDept(deptId: number, userId: number): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/dept/${deptId}/users/${userId}`,
    method: 'delete',
  })
}
