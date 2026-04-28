/**
 * 通用类型定义
 * 包含 API 响应、分页等通用类型
 */

// ============================================================================
// API 响应类型
// ============================================================================

/**
 * API 统一响应结构
 */
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

/**
 * 分页查询参数
 */
export interface PageQuery {
  page?: number
  size?: number
}

/**
 * 分页响应结果
 */
export interface PageResponse<T = any> {
  rows: T[]
  page: number
  size: number
  total: number
}

// ============================================================================
// 验证码相关类型
// ============================================================================

/**
 * 验证码响应
 */
export interface CaptchaResponse {
  uuid: string
  img: string
  code?: string | number
  captchaEnabled: boolean
}

// ============================================================================
// 状态枚举类型
// ============================================================================

/**
 * 通用状态：0-正常 1-停用
 */
export type StatusType = '0' | '1'

/**
 * 可见状态：0-隐藏 1-显示
 */
export type VisibleType = '0' | '1'

/**
 * 删除标志：0-存在 2-删除
 */
export type DelFlagType = '0' | '2'

/**
 * 路由缓存：0-不缓存 1-缓存
 */
export type RouteCacheType = '0' | '1'

/**
 * 是否外链：0-否 1-是
 */
export type RouteExternalType = '0' | '1'

// ============================================================================
// 基础实体类型
// ============================================================================

/**
 * 基础实体接口（包含公共字段）
 */
export interface BaseEntity {
  createBy?: number
  createTime?: string
  updateBy?: number
  updateTime?: string
  remark?: string
}
