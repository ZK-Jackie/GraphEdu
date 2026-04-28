import obfuscator from 'rollup-plugin-obfuscator'
import type { PluginOption } from 'vite'

export default function createObfuscator(command: string): PluginOption {
  if (command !== 'build') return []

  return obfuscator({
    options: {
      compact: true,
      controlFlowFlattening: true,
      controlFlowFlatteningThreshold: 0.5,
      deadCodeInjection: true,
      deadCodeInjectionThreshold: 0.2,
      stringArray: true,
      stringArrayRotate: true,
      stringArrayShuffle: true,
      splitStrings: true,
      splitStringsChunkLength: 10,
    },
  })
}
