import type { App } from 'vue'
import { vPermit } from './permit'

/**
 * 全局注册自定义指令
 */
export default function installDirectives(app: App) {
  app.directive('permit', vPermit)
}
