/**
 * 通用类型定义模块
 */

/**
 * 统一响应格式
 */
export interface ResponseType<T = any> {
  /** HTTP 状态码 */
  code: number
  /** 响应消息 */
  msg: string
  /** 响应数据 */
  data: T
  /** 响应时间戳 */
  time: string
}

/**
 * 分页查询参数
 */
export interface PageQuery {
  /** 页码，从 1 开始，默认为 1 */
  page?: number
  /** 每页数量，默认为 10，最大为 100 */
  size?: number
}

/**
 * 分页响应结果
 */
export interface PageResponse<T = any> {
  /** 当前页数据列表 */
  rows: T[]
  /** 当前页码 */
  page?: number
  /** 每页数量 */
  size?: number
  /** 总记录数 */
  total: number
}

/**
 * 空响应类型
 */
export type Empty = Record<string, never>

/**
 * 批量删除结果项
 */
export interface DeleteResultItem<T = number> {
  /** 目标 ID（可以是 number 或 string 类型） */
  targetId: T
  /** 是否删除成功 */
  success: boolean
  /** 错误信息（如果删除失败） */
  error?: string | null
}

/**
 * 批量删除响应模型
 */
export interface DeleteResponse<T = number> {
  /** 成功删除的数量 */
  successCount: number
  /** 删除失败的数量 */
  failCount: number
  /** 总操作数量 */
  totalCount: number
  /** 详细结果列表 */
  results: DeleteResultItem<T>[]
}
