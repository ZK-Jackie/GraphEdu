import type { AppState, TimeConfig } from '@/types/stores/app.ts'
import { i18n } from '@/plugins/i18n.ts'
import storage from '@/utils/storage.ts'
import { CookieSidebarStatusKey, LocalDarkModeKey, LocalLocaleKey, LocalTimeConfigKey } from '@/constants.ts'

// 默认时间配置
const DEFAULT_TIME_CONFIG: TimeConfig = {
  format: 'YYYY-MM-DD HH:mm:ss',
  relativeTime: false,
  timezone: 'auto',
}

const useAppStore = defineStore('app', {
  state: (): AppState => {
    return {
      sidebarCollapsed: storage.cookies.get(CookieSidebarStatusKey) === '1',
      darkMode: storage.local.get(LocalDarkModeKey) === '1',
      device: 'desktop',
      locale: storage.local.get(LocalLocaleKey) ?? 'zh',
      mobileMenuDrawerOpen: false,
      mobileUserDrawerOpen: false,
      timeConfig: storage.local.getJSON(LocalTimeConfigKey) ?? DEFAULT_TIME_CONFIG,
    }
  },
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
      if (this.sidebarCollapsed) {
        storage.cookies.set(CookieSidebarStatusKey, '1')
      } else {
        storage.cookies.set(CookieSidebarStatusKey, '0')
      }
    },
    toggleDarkMode() {
      this.darkMode = !this.darkMode
      if (this.darkMode) {
        storage.local.set(LocalDarkModeKey, '1')
      } else {
        storage.local.set(LocalDarkModeKey, '0')
      }
      // 同步更新 DOM class
      document.documentElement.classList.toggle('dark', this.darkMode)
    },
    // 初始化暗色模式（应用启动时调用）
    initDarkMode() {
      document.documentElement.classList.toggle('dark', this.darkMode)
    },
    // 更新界面语言
    updateLocale(newLocale: string) {
      // https://vue-i18n.intlify.dev/guide/essentials/scope.html#local-scope-1
      this.locale = newLocale
      storage.local.set(LocalLocaleKey, newLocale)
      // 同步更新i18n
      i18n.global.locale.value = newLocale as 'zh' | 'en'
    },
    // 初始化语言（应用启动时调用）
    initLocale() {
      i18n.global.locale.value = this.locale as 'zh' | 'en'
    },
    // 更新时间配置
    updateTimeConfig(newConfig: Partial<TimeConfig>) {
      this.timeConfig = { ...this.timeConfig, ...newConfig }
      storage.local.setJSON(LocalTimeConfigKey, this.timeConfig)
    },
    // 初始化时间配置（应用启动时调用）
    initTimeConfig() {
      // 时间配置已在state中初始化
      // 这里可以添加额外的初始化逻辑
    },
    // 更新设备类型
    updateDevice(newDevice: 'mobile' | 'tablet' | 'desktop') {
      this.device = newDevice
      // 当切换到移动端或平板端时，自动折叠侧边栏
      if (newDevice === 'mobile' || newDevice === 'tablet') {
        this.sidebarCollapsed = true
      }
    },
    // 切换移动端左侧菜单抽屉
    toggleMobileMenuDrawer(open?: boolean) {
      this.mobileMenuDrawerOpen = open ?? !this.mobileMenuDrawerOpen
    },
    // 切换移动端右侧用户信息抽屉
    toggleMobileUserDrawer(open?: boolean) {
      this.mobileUserDrawerOpen = open ?? !this.mobileUserDrawerOpen
    },
  },
})

export default useAppStore
