<script setup lang="ts">
/**
 * MobileDrawer - 移动端左侧导航抽屉
 *
 * 结构（从上到下）：
 * - 顶部：Logo + 项目名称
 * - 中间：导航菜单项（web 场景，仅登录态有数据）
 * - 底部：GitHub 图标 + 暗色模式切换 + 登录/注册（未登录时）
 *
 * 通过 appStore.mobileMenuDrawerOpen 控制开关
 */
import type { MenuProps } from 'ant-design-vue'
import { LoginOutlined, UserAddOutlined } from '@ant-design/icons-vue'
import Logo from '@/components/Header/components/Logo.vue'
import GithubIcon from '@/components/Header/components/GithubIcon.vue'
import DarkModeToggle from '@/components/Header/components/DarkModeToggle.vue'
import useAppStore from '@/stores/modules/app'
import useUserStore from '@/stores/modules/user'
import useFunctionStore from '@/stores/modules/function'
import { getActiveMenuKeys } from '@/router/utils'
import { useBreakpoints } from '@/composables/useBreakpoints'

const appStore = useAppStore()
const userStore = useUserStore()
const functionStore = useFunctionStore()
const router = useRouter()
const route = useRoute()

const { mobileMenuDrawerOpen } = storeToRefs(appStore)
const { isMobile } = useBreakpoints()

const isLoggedIn = computed(() => !!userStore.token)

const selectedKeys = ref<string[]>([])

const menuItems = computed(() => functionStore.webMenuItems)

watch(
  () => route.matched,
  (matched) => {
    selectedKeys.value = getActiveMenuKeys(matched)
  },
  { immediate: true }
)

const handleClose = () => {
  appStore.toggleMobileMenuDrawer(false)
}

const handleMenuClick: MenuProps['onClick'] = ({ item }) => {
  router.push({ path: item.path as string })
  handleClose()
}

const goTo = (path: string) => {
  router.push(path)
  handleClose()
}
</script>

<template>
  <a-drawer
    v-if="isMobile"
    :open="mobileMenuDrawerOpen"
    placement="left"
    :width="280"
    :closable="true"
    :body-style="{ display: 'flex', flexDirection: 'column', padding: 0 }"
    @close="handleClose"
  >
    <!-- 顶部 Logo -->
    <div class="drawer-logo">
      <Logo />
    </div>

    <!-- 导航菜单（仅登录态有数据） -->
    <nav v-if="isLoggedIn && menuItems.length" class="drawer-menu">
      <a-menu v-model:selected-keys="selectedKeys" mode="inline" :items="menuItems" @click="handleMenuClick" />
    </nav>

    <!-- 底部工具栏 -->
    <div class="drawer-footer">
      <template v-if="!isLoggedIn">
        <button class="drawer-auth-btn" @click="goTo('/login')">
          <LoginOutlined />
          <span>登录</span>
        </button>
        <button class="drawer-auth-btn" @click="goTo('/register')">
          <UserAddOutlined />
          <span>注册</span>
        </button>
      </template>
      <GithubIcon class="drawer-footer-item" />
      <DarkModeToggle class="drawer-footer-item" />
    </div>
  </a-drawer>
</template>

<style scoped>
@reference '#main.css';

.drawer-logo {
  @apply flex items-center px-4 py-4 border-b border-gray-200 dark:border-gray-700;
}

.drawer-menu {
  @apply flex-1 overflow-y-auto py-2;
}

.drawer-footer {
  @apply flex items-center justify-center gap-6 px-4 py-3 border-t border-gray-200 dark:border-gray-700;
  flex-shrink: 0;
}

.drawer-footer-item {
  @apply px-2 py-1;
}

.drawer-auth-btn {
  @apply flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm
    text-gray-700 dark:text-gray-300
    border-none bg-transparent cursor-pointer
    hover:bg-gray-100 dark:hover:bg-gray-700
    transition-colors;
}
</style>
