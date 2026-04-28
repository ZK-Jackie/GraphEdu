import type { App } from 'vue'
import { echarts } from './echarts'
import { i18n } from './i18n'
import { createPluginErrorHandler } from './error'

// https://github1s.com/vuejs/core/blob/main/packages/runtime-core/src/apiCreateApp.ts#L295-L311
export default function installPlugins(app: App) {
  // 全局错误处理（必须在最前面，以便捕获所有错误）
  app.use(createPluginErrorHandler)

  // echarts 图表库
  app.config.globalProperties.$echarts = echarts as any

  // i18n 国际化
  app.use(i18n)
}
