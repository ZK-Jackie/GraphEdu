/// <reference types="vite/client" />
import compression from 'vite-plugin-compression'
import type { PluginOption } from 'vite'
export default function createCompressionImports(env: ImportMetaEnv, _command: string): PluginOption[] {
  const compressList = env.VITE_BUILD_COMPRESS.split(',')
  const compressPlugins = []
  if (compressList.includes('gzip')) {
    compressPlugins.push(
      compression({
        ext: '.gz',
        deleteOriginFile: false,
      })
    )
  }
  if (compressList.includes('brotli')) {
    compressPlugins.push(
      compression({
        ext: '.br',
        algorithm: 'brotliCompress',
        deleteOriginFile: false,
      })
    )
  }
  return compressPlugins
}
