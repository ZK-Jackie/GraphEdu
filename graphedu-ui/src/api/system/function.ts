/**
 * 功能权限管理相关 API
 * 对应后端：graphedu/api/services/system/function.py
 */
import request from '@/utils/request'
import type { ResponseType, Empty } from '@/types/api/common.ts'
import type {
  FunctionQueryDTO,
  FunctionCreateDTO,
  FunctionUpdateDTO,
  FunctionTreeVO,
  FunctionTreeBriefVO,
  FunctionDetailVO,
  RoleFunctionTreeVO,
} from '@/types/api/system/function.ts'

/**
 * 获取功能树（用于下拉选择）
 * GET /system/function/treeselect
 */
export function getFunctionTreeSelect(params?: { parentId?: number }): Promise<ResponseType<FunctionTreeBriefVO[]>> {
  return request({
    url: '/system/function/treeselect',
    method: 'get',
    params: { ...params },
  })
}

/**
 * 获取角色功能树（用于分配权限）
 * GET /system/function/roleFunctionTreeselect/{role_id}
 */
export function getRoleFunctionTree(roleId: number): Promise<ResponseType<RoleFunctionTreeVO>> {
  return request({
    url: `/system/function/roleFunctionTreeselect/${roleId}`,
    method: 'get',
  })
}

/**
 * 获取功能列表（树形结构）
 * GET /system/function/list
 */
export function getFunctionList(query?: FunctionQueryDTO): Promise<ResponseType<FunctionTreeVO[]>> {
  return request({
    url: '/system/function/list',
    method: 'get',
    params: query,
  })
}

/**
 * 异步加载功能子节点
 * GET /system/function/listLazy
 */
export function getFunctionListLazy(
  parentId: number,
  scene: string | null = null
): Promise<ResponseType<FunctionTreeVO[]>> {
  return request({
    url: '/system/function/listLazy',
    method: 'get',
    params: { parentId, scene },
  })
}

/**
 * 新增功能
 * POST /system/function
 */
export function addFunction(data: FunctionCreateDTO): Promise<ResponseType<FunctionDetailVO>> {
  return request({
    url: '/system/function',
    method: 'post',
    data,
  })
}

/**
 * 修改功能
 * PUT /system/function
 */
export function updateFunction(data: FunctionUpdateDTO): Promise<ResponseType<FunctionDetailVO>> {
  return request({
    url: '/system/function',
    method: 'put',
    data,
  })
}

/**
 * 删除功能（支持批量删除）
 * DELETE /system/function/{function_ids}
 */
export function deleteFunction(functionIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/function/${functionIds}`,
    method: 'delete',
  })
}

/**
 * 获取功能详细信息
 * GET /system/function/{function_id}
 */
export function getFunctionDetail(functionId: number): Promise<ResponseType<FunctionDetailVO>> {
  return request({
    url: `/system/function/${functionId}`,
    method: 'get',
  })
}
