import { useMediaQuery } from '@vueuse/core'
import type { DeviceType } from '@/types/breakpoints'

/**
 * 响应式断点检测 Composable
 *
 * 使用 @vueuse/core 的 useMediaQuery 进行响应式断点检测
 * 断点策略：
 * - 移动端（Mobile）: < 768px (md断点以下)
 * - 平板（Tablet）: 768px - 1023px (md-lg之间)
 * - 桌面端（Desktop）: ≥ 1024px (lg断点及以上)
 *
 * @returns {Object} 断点状态和相关工具函数
 */
export function useBreakpoints() {
  // 移动端：小于 768px
  const isMobile = useMediaQuery('(max-width: 767px)')

  // 平板端：768px - 1023px
  const isTablet = useMediaQuery('(min-width: 768px) and (max-width: 1023px)')

  // 桌面端：大于等于 1024px
  const isDesktop = useMediaQuery('(min-width: 1024px)')

  /**
   * 当前设备类型
   */
  const device = computed<DeviceType>(() => {
    if (isMobile.value) return 'mobile'
    if (isTablet.value) return 'tablet'
    return 'desktop'
  })

  /**
   * 是否为移动端或平板端
   */
  const isMobileOrTablet = computed(() => isMobile.value || isTablet.value)

  /**
   * 是否应该使用抽屉模式
   * - 平板端：展开时使用抽屉模式
   * - 移动端：完全使用抽屉模式
   */
  const shouldUseDrawer = computed(() => isMobile.value || isTablet.value)

  return {
    isMobile,
    isTablet,
    isDesktop,
    device,
    isMobileOrTablet,
    shouldUseDrawer,
  }
}
