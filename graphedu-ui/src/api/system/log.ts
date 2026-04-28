/**
 * 日志管理相关 API
 * 对应后端：graphedu/api/services/system/log.py
 */
import request from '@/utils/request'
import type { ResponseType, Empty, PageResponse } from '@/types/api/common.ts'
import type {
  OperLogQueryDTO,
  OperLogListVO,
  OperLogDetailVO,
  LoginLogQueryDTO,
  LoginLogListVO,
  // UnlockUserDTO,
} from '@/types/api/system/log.ts'

// ============== 操作日志管理接口 ==============

/**
 * 获取操作日志列表（分页）
 * GET /monitor/log/operation/list
 */
export function getOperationLogList(query: OperLogQueryDTO): Promise<ResponseType<PageResponse<OperLogListVO>>> {
  return request({
    url: '/monitor/log/operation/list',
    method: 'get',
    params: query,
  })
}

/**
 * 清空操作日志
 * DELETE /monitor/log/operation/clean
 */
export function clearOperationLog(): Promise<ResponseType<Empty>> {
  return request({
    url: '/monitor/log/operation/clean',
    method: 'delete',
  })
}

/**
 * 删除操作日志（支持批量删除）
 * DELETE /monitor/log/operation/{oper_ids}
 */
export function deleteOperationLog(operIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/monitor/log/operation/${operIds}`,
    method: 'delete',
  })
}

/**
 * 获取操作日志详情
 * GET /monitor/log/operation/{oper_id}
 */
export function getOperationLogDetail(operId: number): Promise<ResponseType<OperLogDetailVO>> {
  return request({
    url: `/monitor/log/operation/${operId}`,
    method: 'get',
  })
}

// ============== 登录日志管理接口 ==============

/**
 * 获取登录日志列表（分页）
 * GET /monitor/log/login/list
 */
export function getLoginLogList(query: LoginLogQueryDTO): Promise<ResponseType<PageResponse<LoginLogListVO>>> {
  return request({
    url: '/monitor/log/login/list',
    method: 'get',
    params: query,
  })
}

/**
 * 清空登录日志
 * DELETE /monitor/log/login/clean
 */
export function clearLoginLog(): Promise<ResponseType<Empty>> {
  return request({
    url: '/monitor/log/login/clean',
    method: 'delete',
  })
}

/**
 * 删除登录日志（支持批量删除）
 * DELETE /monitor/log/login/{info_ids}
 */
export function deleteLoginLog(infoIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/monitor/log/login/${infoIds}`,
    method: 'delete',
  })
}

/**
 * 解锁用户账户
 * GET /monitor/log/login/unlock/{user_name}
 */
export function unlockUser(userName: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/monitor/log/login/unlock/${userName}`,
    method: 'get',
  })
}
