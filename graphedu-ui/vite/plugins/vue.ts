import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import type { PluginOption } from 'vite'

export default function createVueImports(command: string): PluginOption[] {
  const plugins: PluginOption[] = [vue(), tailwindcss()]
  if (command === 'serve') {
    plugins.push(vueDevTools())
  }
  return plugins
}
