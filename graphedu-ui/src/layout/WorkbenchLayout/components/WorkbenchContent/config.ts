import { type ComponentItemConfig, type LayoutConfig } from 'golden-layout'

/**
 * 空白布局配置（参照原始示例）
 * Golden Layout 2 不需要强制使用 stack，可以直接使用 row + component
 */
export const initConfig: LayoutConfig = {
  root: {
    type: 'row',
    content: [
      {
        type: 'component',
        title: 'Admin 首页',
        header: { show: 'top' },
        isClosable: false,
        componentType: 'RouterTemplate', // 使用路由模板
        componentState: {
          path: '/admin',
          name: 'Dashboard',
          meta: { title: '首页' },
        },
      } as ComponentItemConfig,
    ],
  },
}
