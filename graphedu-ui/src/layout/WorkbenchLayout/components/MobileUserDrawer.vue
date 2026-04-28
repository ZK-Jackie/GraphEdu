<script setup lang="ts">
/**
 * MobileUserDrawer - 非桌面端右侧用户信息抽屉
 *
 * 结构（参照 CommonLayout MobileDrawer 的 flex 布局风格）：
 * - 顶部：用户头像 + 用户名
 * - 中间：用户菜单项（userInfo 场景）
 * - 底部：退出登录按钮
 *
 * 通过 appStore.mobileUserDrawerOpen 控制开关
 */
import type { MenuProps } from 'ant-design-vue'
import { LogoutOutlined } from '@ant-design/icons-vue'
import useUserStore from '@/stores/modules/user'
import useAppStore from '@/stores/modules/app'
import useFunctionStore from '@/stores/modules/function'
import { useBreakpoints } from '@/composables/useBreakpoints'

const userStore = useUserStore()
const appStore = useAppStore()
const functionStore = useFunctionStore()
const { mobileUserDrawerOpen } = storeToRefs(appStore)
const { isDesktop } = useBreakpoints()

const router = useRouter()
const route = useRoute()

const { avatar, token } = storeToRefs(userStore)
const userName = computed(() => userStore.userName)
const isLogin = computed(() => !!token?.value)

const handleClose = () => {
  appStore.toggleMobileUserDrawer(false)
}

interface SimpleMenuItem {
  key?: string | number
  icon?: any
  label?: string
  children?: SimpleMenuItem[]
}

const userInfoMenuItems = computed<SimpleMenuItem[]>(() =>
  (functionStore.userInfoMenuItems ?? [])
    .filter((item: any): item is Record<string, any> => item != null && 'key' in item)
    .map((item: any) => ({
      key: item.key,
      icon: item.icon,
      label: item.label,
      children: (item.children ?? []).map((child: any) => ({
        key: child.key,
        icon: child.icon,
        label: child.label,
      })),
    }))
)

const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
  if (key === route.name) {
    handleClose()
    return
  }
  router.push({ name: key as string })
  handleClose()
}

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <a-drawer
    v-if="!isDesktop"
    :open="mobileUserDrawerOpen"
    placement="right"
    :width="280"
    :closable="true"
    :body-style="{ display: 'flex', flexDirection: 'column', padding: 0 }"
    @close="handleClose"
  >
    <template v-if="isLogin">
      <!-- 用户头像区域 -->
      <div class="user-header">
        <img :src="avatar" alt="avatar" class="user-avatar" />
        <div class="user-name">{{ userName }}</div>
      </div>

      <!-- 用户菜单 -->
      <nav class="user-menu">
        <a-menu @click="handleMenuClick">
          <template v-for="item in userInfoMenuItems" :key="item.key">
            <a-menu-item v-if="!item.children && item.key" :key="String(item.key)">
              <template v-if="item.icon" #icon>
                <component :is="item.icon" />
              </template>
              {{ item.label }}
            </a-menu-item>
            <a-sub-menu v-else-if="item.children && item.children.length > 0" :key="String(item.key)">
              <template v-if="item.icon" #icon>
                <component :is="item.icon" />
              </template>
              <template #title>{{ item.label }}</template>
              <a-menu-item v-for="child in item.children" :key="String(child.key)">
                <template v-if="child.icon" #icon>
                  <component :is="child.icon" />
                </template>
                {{ child.label }}
              </a-menu-item>
            </a-sub-menu>
          </template>
        </a-menu>
      </nav>

      <!-- 底部退出登录 -->
      <div class="user-footer">
        <button class="logout-btn" @click="handleLogout">
          <LogoutOutlined />
          <span>退出登录</span>
        </button>
      </div>
    </template>
    <div v-else class="login-prompt">
      <a-button type="primary" block href="/login"> 登录 / 注册 </a-button>
    </div>
  </a-drawer>
</template>

<style scoped>
@reference "#main.css";

.user-header {
  @apply flex flex-col items-center justify-center px-4 py-6;
  @apply border-b border-gray-200 dark:border-gray-700;
}

.user-avatar {
  @apply w-16 h-16 object-cover rounded-full mb-3;
}

.user-name {
  @apply text-base font-semibold text-gray-800 dark:text-gray-200;
}

.user-menu {
  @apply flex-1 overflow-y-auto py-2;
}

.user-footer {
  @apply px-4 py-3 border-t border-gray-200 dark:border-gray-700;
  flex-shrink: 0;
}

.logout-btn {
  @apply flex items-center justify-center gap-2 w-full py-2 rounded-md;
  @apply text-red-500 hover:text-red-600;
  @apply hover:bg-red-50 dark:hover:bg-red-900/20;
  @apply transition-colors duration-200;
  border: none;
  outline: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.875rem;
}

.login-prompt {
  @apply flex items-center justify-center py-6;
}
</style>
