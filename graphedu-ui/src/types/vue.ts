import 'vue-router'
import type { ECharts } from 'echarts/core'
import type { RouterMeta as AppRouterMeta } from '@/types/api/common/auth.ts'

declare module 'vue' {
  interface ComponentCustomProperties {
    $echarts: ECharts
  }
}

declare module 'vue-router' {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface RouteMeta extends AppRouterMeta {}
}

export {}
