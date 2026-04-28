import { reactive, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { PaginationQuerySyncOptions, PaginationQuerySyncReturn } from '@/types/composables/pagination.ts'
import type { PageQuery } from '@/types/api/common.ts'

/**
 * 从 URL query 中解析参数值
 * @param value - URL 参数值
 * @param type - 目标类型 ('string' | 'number' | 'boolean' | 'array')
 */
function parseUrlValue(value: string | undefined, type: 'string' | 'number' | 'boolean' | 'array'): any {
  if (value === undefined || value === '') return undefined

  switch (type) {
    case 'number':
      return Number(value)
    case 'boolean':
      return value === 'true'
    case 'array':
      try {
        const parsed = JSON.parse(value)
        return Array.isArray(parsed) ? parsed : value.split(',')
      } catch {
        return value.split(',')
      }
    default:
      return value
  }
}

/**
 * 将值转换为 URL 字符串
 * @param value - 要转换的值
 */
function stringifyUrlValue(value: any): string | undefined {
  if (value === undefined || value === null || value === '') return undefined

  if (Array.isArray(value)) {
    return value.length > 0 ? JSON.stringify(value) : undefined
  }

  return String(value)
}

/**
 * 推断值的类型
 */
function inferType(value: any): 'string' | 'number' | 'boolean' | 'array' {
  if (Array.isArray(value)) return 'array'
  if (typeof value === 'number') return 'number'
  if (typeof value === 'boolean') return 'boolean'
  return 'string'
}

/**
 * 默认配置
 */
const DEFAULT_OPTIONS: Required<PaginationQuerySyncOptions> = {
  pageKey: 'page',
  sizeKey: 'size',
  syncSearchParams: true,
  searchParamKeys: [],
  defaultPage: 1,
  defaultSize: 10,
  debounceUrlUpdate: true,
  debounceDelay: 300,
  fetchOnRouteChange: true,
}

/**
 * 分页查询同步到 URL 的 Composable Hook
 *
 * @param defaultParams - 默认查询参数（包含分页参数）
 * @param fetchFn - 获取数据的函数
 * @param options - 配置选项
 * @returns 分页同步对象
 *
 * @example
 * ```ts
 * const { queryParams, resetPage, resetAll, fetch } = usePaginationQuery(
 *   {
 *     page: 1,
 *     size: 10,
 *     userName: undefined,
 *     status: undefined,
 *   },
 *   getList,
 *   {
 *     syncSearchParams: true,
 *     debounceUrlUpdate: true,
 *   }
 * )
 * ```
 */
export function usePaginationQuery<T extends PageQuery & Record<string, any> = PageQuery & Record<string, any>>(
  defaultParams: T,
  fetchFn: () => void | Promise<void>,
  options: PaginationQuerySyncOptions = {}
): PaginationQuerySyncReturn<T> {
  const route = useRoute()
  const router = useRouter()

  // 合并配置
  const config = { ...DEFAULT_OPTIONS, ...options }

  // 保存初始默认值（用于重置）
  const initialDefaults = { ...defaultParams }

  // 创建响应式查询参数
  const queryParams = reactive<T>({ ...defaultParams }) as T

  // 防抖定时器
  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  /**
   * 从 URL 初始化查询参数
   */
  const initFromUrl = () => {
    const query = route.query

    // 设置分页参数
    const pageParam = query[config.pageKey]
    const sizeParam = query[config.sizeKey]

    if (pageParam !== undefined) {
      queryParams.page = parseUrlValue(pageParam as string, 'number')
    } else {
      queryParams.page = initialDefaults.page ?? config.defaultPage
    }

    if (sizeParam !== undefined) {
      queryParams.size = parseUrlValue(sizeParam as string, 'number')
    } else {
      queryParams.size = initialDefaults.size ?? config.defaultSize
    }

    // 设置搜索参数
    if (config.syncSearchParams) {
      Object.keys(initialDefaults).forEach((key) => {
        if (key === config.pageKey || key === config.sizeKey) return

        // 如果指定了 searchParamKeys，只同步指定的参数
        if (config.searchParamKeys.length > 0 && !config.searchParamKeys.includes(key)) {
          return
        }

        const urlValue = query[key]
        if (urlValue !== undefined) {
          const type = inferType(initialDefaults[key])
          ;(queryParams as Record<string, any>)[key] = parseUrlValue(urlValue as string, type)
        }
      })
    }
  }

  /**
   * 更新 URL（带防抖）
   */
  const updateUrl = () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }

    const doUpdate = () => {
      const newQuery: Record<string, string> = {}

      // 添加分页参数
      if (queryParams.page !== undefined && queryParams.page !== config.defaultPage) {
        newQuery[config.pageKey] = String(queryParams.page)
      }

      if (queryParams.size !== undefined && queryParams.size !== config.defaultSize) {
        newQuery[config.sizeKey] = String(queryParams.size)
      }

      // 添加搜索参数
      if (config.syncSearchParams) {
        Object.keys(queryParams).forEach((key) => {
          if (key === config.pageKey || key === config.sizeKey) return

          // 如果指定了 searchParamKeys，只同步指定的参数
          if (config.searchParamKeys.length > 0 && !config.searchParamKeys.includes(key)) {
            return
          }

          const value = queryParams[key]
          const stringValue = stringifyUrlValue(value)

          if (stringValue !== undefined) {
            newQuery[key] = stringValue
          }
        })
      }

      // 使用 replace 避免历史记录堆积
      router.replace({ query: newQuery }).catch((err) => {
        // 忽略重复导航错误
        if (err.name !== 'NavigationDuplicated') {
          console.error('[usePaginationQuery] URL 更新失败:', err)
        }
      })
    }

    if (config.debounceUrlUpdate) {
      debounceTimer = setTimeout(doUpdate, config.debounceDelay)
    } else {
      doUpdate()
    }
  }

  /**
   * 重置页码
   */
  const resetPage = () => {
    queryParams.page = initialDefaults.page ?? config.defaultPage
  }

  /**
   * 重置所有参数
   */
  const resetAll = () => {
    Object.keys(initialDefaults).forEach((key) => {
      ;(queryParams as Record<string, any>)[key] = initialDefaults[key]
    })
    // 清空 URL 中的所有参数
    router.replace({ query: {} }).catch(() => {})
  }

  /**
   * 手动触发数据获取
   */
  const fetch = () => {
    return fetchFn()
  }

  // 监听查询参数变化，同步到 URL
  watch(
    () => ({ ...queryParams }),
    () => {
      updateUrl()
    },
    { deep: true }
  )

  // 监听路由 query 变化，同步到查询参数
  watch(
    () => route.query,
    (newQuery) => {
      // 检查是否需要更新（避免循环更新）
      let needUpdate = false

      // 检查分页参数
      const pageParam = newQuery[config.pageKey]
      const sizeParam = newQuery[config.sizeKey]

      const pageValue = pageParam ? parseUrlValue(pageParam as string, 'number') : config.defaultPage
      const sizeValue = sizeParam ? parseUrlValue(sizeParam as string, 'number') : config.defaultSize

      if (pageValue !== queryParams.page || sizeValue !== queryParams.size) {
        needUpdate = true
      }

      // 检查搜索参数
      if (config.syncSearchParams) {
        Object.keys(initialDefaults).forEach((key) => {
          if (key === config.pageKey || key === config.sizeKey) return

          if (config.searchParamKeys.length > 0 && !config.searchParamKeys.includes(key)) {
            return
          }

          const urlValue = newQuery[key]
          const currentValue = queryParams[key]

          if (urlValue !== undefined) {
            const type = inferType(initialDefaults[key])
            const parsedValue = parseUrlValue(urlValue as string, type)
            if (parsedValue !== currentValue) {
              needUpdate = true
            }
          } else if (currentValue !== undefined && currentValue !== initialDefaults[key]) {
            needUpdate = true
          }
        })
      }

      // 如果需要更新，同步参数并触发 fetch
      if (needUpdate) {
        const pageParam = newQuery[config.pageKey]
        const sizeParam = newQuery[config.sizeKey]

        queryParams.page = pageParam
          ? parseUrlValue(pageParam as string, 'number')
          : (initialDefaults.page ?? config.defaultPage)

        queryParams.size = sizeParam
          ? parseUrlValue(sizeParam as string, 'number')
          : (initialDefaults.size ?? config.defaultSize)

        if (config.syncSearchParams) {
          Object.keys(initialDefaults).forEach((key) => {
            if (key === config.pageKey || key === config.sizeKey) return

            if (config.searchParamKeys.length > 0 && !config.searchParamKeys.includes(key)) {
              return
            }

            const urlValue = newQuery[key]
            if (urlValue !== undefined) {
              const type = inferType(initialDefaults[key])
              ;(queryParams as Record<string, any>)[key] = parseUrlValue(urlValue as string, type)
            } else {
              ;(queryParams as Record<string, any>)[key] = initialDefaults[key]
            }
          })
        }

        if (config.fetchOnRouteChange) {
          fetch()
        }
      }
    },
    { deep: true }
  )

  // 初始化：从 URL 读取参数
  onMounted(() => {
    initFromUrl()
  })

  return {
    queryParams,
    resetPage,
    resetAll,
    fetch,
  }
}

export default usePaginationQuery
