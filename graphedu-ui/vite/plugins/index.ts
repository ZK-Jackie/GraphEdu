/// <reference types="vite/client" />
import createAutoImport from './auto-import'
import createSvgIcon from './svg-icon'
import createCompressionImports from './compression'
import createVueImports from './vue'
import createAntdvImport from './antdv-import'
import createGitInfoPlugin from './vite-plugin-git-info'
import type { PluginOption } from 'vite'

export default function createVitePlugins(env: ImportMetaEnv, command: string): PluginOption[] {
  const vitePlugins: PluginOption[] = []
  vitePlugins.push(...createVueImports(command))
  vitePlugins.push(createAutoImport())
  vitePlugins.push(createSvgIcon(env, command))
  vitePlugins.push(createGitInfoPlugin())
  vitePlugins.push(...createCompressionImports(env, command))
  vitePlugins.push(...createAntdvImport())

  return vitePlugins
}
