import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'
import { AntDesignXVueResolver } from 'ant-design-x-vue/resolver'
import type { PluginOption } from 'vite'

export default function createAntdvImport(): PluginOption[] {
  return [
    Components({
      resolvers: [
        AntDesignVueResolver({
          importStyle: false,
        }),
      ],
      dts: './src/types/generated/antdv.components.d.ts',
    }),
    Components({
      resolvers: [AntDesignXVueResolver()],
      dts: './src/types/generated/antdxv.components.d.ts',
    }),
  ]
}
