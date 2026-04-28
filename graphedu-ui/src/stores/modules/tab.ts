import type { AppState } from '@/types/stores/app.ts'
import storage from '@/utils/storage.ts'
import { CookieSidebarStatusKey, LocalDarkModeKey } from '@/constants.ts'

const useTabStore = defineStore('tab', {
  state: (): AppState => {
    return {
      sidebarCollapsed: storage.cookies.get(CookieSidebarStatusKey) === '1',
      darkMode: storage.local.get(LocalDarkModeKey) === '1',
      device: 'desktop',
      locale: 'zh',
      mobileMenuDrawerOpen: false,
      mobileUserDrawerOpen: false,
      timeConfig: { timezone: 'Asia/Shanghai', format: '24h', relativeTime: false },
    }
  },
  actions: {},
})

export default useTabStore
