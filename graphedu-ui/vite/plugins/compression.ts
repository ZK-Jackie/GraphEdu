/// <reference types="vite/client" />
import { compression } from 'vite-plugin-compression2'
import type { PluginOption } from 'vite'
export default function createCompressionImports(env: ImportMetaEnv, _command: string): PluginOption[] {
  const compressList = env.VITE_BUILD_COMPRESS.split(',')
  const algorithms = []
  if (compressList.includes('gzip')) algorithms.push('gzip')
  if (compressList.includes('brotli')) algorithms.push('brotliCompress')
  if (!algorithms.length) return []
  return [
    compression({
      algorithms,
      deleteOriginalAssets: false,
    }),
  ]
}
