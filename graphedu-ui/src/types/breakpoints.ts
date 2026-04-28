/**
 * 设备类型
 */
export type DeviceType = 'mobile' | 'tablet' | 'desktop'

/**
 * 断点状态
 */
export interface BreakpointState {
  /** 当前设备类型 */
  device: DeviceType
  /** 是否为移动端 (< 768px) */
  isMobile: boolean
  /** 是否为平板端 (768px - 1023px) */
  isTablet: boolean
  /** 是否为桌面端 (≥ 1024px) */
  isDesktop: boolean
  /** 是否为移动端或平板端 */
  isMobileOrTablet: boolean
  /** 是否应该使用抽屉模式 */
  shouldUseDrawer: boolean
}
