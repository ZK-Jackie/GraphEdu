import type { App, ComponentPublicInstance } from 'vue'
import { SystemMessage } from '@/utils/message'

/**
 * 全局错误处理插件
 *
 * 功能：
 * 1. 捕获全局错误（Vue 错误、Promise 错误、全局异常）
 * 2. 使用 SystemMessage 展示错误提示
 * 3. 提供 Vue 插件安装钩子
 *
 * @example
 * ```typescript
 * // main.ts
 * import { createPluginErrorHandler } from '@/plugins/error'
 *
 * const app = createApp(App)
 * app.use(createPluginErrorHandler())
 * ```
 */
export function createPluginErrorHandler() {
  /**
   * 统一错误处理逻辑
   */
  const handleError = (error: Error | unknown, context?: string) => {
    console.error('❌ Error:', error, context ? `\nContext: ${context}` : '')

    // 提取错误信息
    const errorMessage = error instanceof Error ? error.message : String(error)

    // 显示用户提示
    SystemMessage({
      theme: 'error',
      content: errorMessage,
      options: { duration: 5 },
    })
  }

  /**
   * Vue 全局错误处理器
   */
  const vueErrorHandler = (err: unknown, _instance: ComponentPublicInstance | null, info: string) => {
    handleError(err, `Vue: ${info}`)
  }

  /**
   * 处理未捕获的 Promise 错误
   */
  const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
    event.preventDefault()
    handleError(event.reason, 'Unhandled Promise Rejection')
  }

  /**
   * 处理全局错误（如未捕获的异常）
   */
  const handleGlobalError = (event: ErrorEvent) => {
    event.preventDefault()
    handleError(event.error ?? event.message, 'Global Error')
  }

  return {
    install(app: App) {
      // 注册 Vue 错误处理器
      app.config.errorHandler = vueErrorHandler

      // 注册全局错误监听器
      window.addEventListener('unhandledrejection', handleUnhandledRejection)
      window.addEventListener('error', handleGlobalError)

      console.log('✅ Global Error Handler Plugin installed')
    },

    uninstall() {
      // 清理事件监听器
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
      window.removeEventListener('error', handleGlobalError)
    },
  }
}

export default createPluginErrorHandler
