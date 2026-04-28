/**
 * 时间配置
 */
export interface TimeConfig {
  /** 时间格式 */
  format: string
  /** 是否使用相对时间（如"3分钟前"） */
  relativeTime: boolean
  /** 时区（auto表示使用浏览器本地时区） */
  timezone: string
}

export interface AppState {
  sidebarCollapsed: boolean
  darkMode: boolean
  device: 'mobile' | 'tablet' | 'desktop'
  locale: string
  /** 移动端左侧菜单抽屉是否打开 */
  mobileMenuDrawerOpen: boolean
  /** 移动端右侧用户信息抽屉是否打开 */
  mobileUserDrawerOpen: boolean
  /** 时间配置 */
  timeConfig: TimeConfig
}
