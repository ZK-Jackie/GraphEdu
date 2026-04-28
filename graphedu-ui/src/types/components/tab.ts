import type { RouterMeta } from '@/types/components/router.ts'

export interface Tab {
  title: string
  path: string
  name?: string
  meta?: RouterMeta
  // 缓存控制
  cached?: boolean // 添加：是否已缓存

  // 唯一标识（如果需要支持同一页面多次打开）
  refId?: string // computed from path + query
  query?: Record<string, any>

  // 状态管理
  isActive?: boolean
}
