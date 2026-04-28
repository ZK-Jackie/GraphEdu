/**
 * Mock 数据核心工具
 * 通过环境变量 VITE_MOCK_ENABLED 控制开关
 */
import type { ResponseType } from '@/types/api/common'

/**
 * 判断 Mock 是否启用
 */
export function isMockEnabled(): boolean {
  return import.meta.env.VITE_MOCK_ENABLED === 'true'
}

/**
 * 包装 Mock 数据为后端统一响应格式
 */
export function mockResponse<T>(data: T): ResponseType<T> {
  return {
    code: 200,
    msg: '操作成功',
    data,
    time: new Date().toISOString(),
  }
}

/**
 * 包装分页 Mock 数据
 */
export function mockPageResponse<T>(
  rows: T[],
  total?: number
): ResponseType<{ rows: T[]; page: number; size: number; total: number }> {
  return mockResponse({
    rows,
    page: 1,
    size: 20,
    total: total ?? rows.length,
  })
}
