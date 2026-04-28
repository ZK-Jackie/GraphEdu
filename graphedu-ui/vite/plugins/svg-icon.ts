/// <reference types="vite/client" />
import { createSvgIconsPlugin } from './vite-plugin-svg-icons-plus'
import * as path from 'node:path'
import type { PluginOption } from 'vite'
/**
 * 使用零依赖 SVG 图标插件
 */
export default function createSvgIcon(env: ImportMetaEnv, command: string): PluginOption {
  return createSvgIconsPlugin({
    // Ant Design 图标目录
    iconDirs: [path.resolve(process.cwd(), 'node_modules/@ant-design/icons-svg/inline-namespaced-svg')],
    // Symbol ID 模板
    symbolId: 'icon-[dir]-[name]',
    // 是否优化（开发时关闭以加快速度，构建时开启）
    optimize: command === 'build',
    // 自定义 DOM ID
    domId: '__svg_icons_dom__',
    // 注入位置
    inject: 'body-last',
  })
}
