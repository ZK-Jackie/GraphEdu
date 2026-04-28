import AutoImport from 'unplugin-auto-import/vite'
import type { PluginOption } from 'vite'

export default function createAutoImport(): PluginOption {
  return AutoImport({
    imports: ['vue', 'vue-router', 'pinia'],
    dts: './src/types/generated/auto-imports.d.ts',
    // 在 Vue 模板中也可以使用自动导入的 API
    vueTemplate: true
  })
}
