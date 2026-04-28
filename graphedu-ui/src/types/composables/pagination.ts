/**
 * 分页查询同步到 URL 的 Composable 类型定义
 */

/**
 * 分页同步配置选项
 */
export interface PaginationQuerySyncOptions {
  /** URL 中页码参数的键名，默认 'page' */
  pageKey?: string
  /** URL 中每页条数参数的键名，默认 'size' */
  sizeKey?: string
  /** 是否同步搜索条件到 URL，默认 true */
  syncSearchParams?: boolean
  /** 需要同步到 URL 的搜索参数键名数组，默认同步所有非分页参数 */
  searchParamKeys?: string[]
  /** 默认页码，默认 1 */
  defaultPage?: number
  /** 默认每页条数，默认 10 */
  defaultSize?: number
  /** 是否防抖更新 URL，默认 true */
  debounceUrlUpdate?: boolean
  /** 防抖延迟（毫秒），默认 300 */
  debounceDelay?: number
  /** 当 URL 变化时是否触发 fetch，默认 true */
  fetchOnRouteChange?: boolean
}

/**
 * 分页同步返回值
 */
export interface PaginationQuerySyncReturn<T extends Record<string, any>> {
  /** 响应式查询参数 */
  queryParams: T
  /** 重置页码到默认值 */
  resetPage: () => void
  /** 重置所有参数到默认值 */
  resetAll: () => void
  /** 手动触发数据获取 */
  fetch: () => void | Promise<void>
}
