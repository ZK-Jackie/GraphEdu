<script setup lang="ts">
import { MenuUnfoldOutlined } from '@ant-design/icons-vue'
import Logo from '@/components/Header/components/Logo.vue'
import GithubIcon from '@/components/Header/components/GithubIcon.vue'
import DarkModeToggle from '@/components/Header/components/DarkModeToggle.vue'
import UserAvatar from '@/components/Header/components/UserAvatar.vue'
import { useBreakpoints } from '@/composables/useBreakpoints'
import useAppStore from '@/stores/modules/app'

const { isDesktop } = useBreakpoints()
const appStore = useAppStore()

/**
 * 处理移动端菜单按钮点击
 */
const handleMobileMenuClick = () => {
  appStore.toggleMobileMenuDrawer(true)
}

/**
 * 处理移动端用户头像点击
 */
const handleMobileUserClick = () => {
  appStore.toggleMobileUserDrawer(true)
}
</script>

<template>
  <nav class="header-nav">
    <!-- 左侧区域：移动端显示汉堡图标，非移动端显示完整 Logo -->
    <div class="nav-left">
      <button v-if="!isDesktop" class="mobile-menu-btn" @click="handleMobileMenuClick">
        <MenuUnfoldOutlined />
      </button>
      <Logo v-else />
    </div>

    <!-- 右侧区域：非桌面端只显示头像，桌面端显示完整工具栏 -->
    <div v-if="isDesktop" class="nav-right">
      <button class="nav-item">
        <GithubIcon />
      </button>
      <a-divider type="vertical" class="nav-divider" />
      <button class="nav-item">
        <DarkModeToggle />
      </button>
      <a-divider type="vertical" class="nav-divider" />
      <UserAvatar class="nav-item" />
    </div>
    <button v-else class="mobile-user-btn" @click="handleMobileUserClick">
      <UserAvatar class="nav-item" />
    </button>
  </nav>
</template>

<style scoped>
@reference "#main.css";

.header-nav {
  @apply shadow-md pt-2 pb-1 px-5 flex justify-between items-center;
  background: var(--ge-bg-container);
}

.nav-left {
  @apply flex items-center h-full;
}

.nav-right {
  @apply flex items-center h-full;
}

.nav-item {
  @apply h-full w-auto rounded-md p-2 hover:bg-gray-200 dark:hover:bg-gray-700 cursor-pointer flex items-center justify-center;
}

.nav-divider {
  @apply h-6 bg-gray-500 dark:bg-gray-600;
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  @apply flex items-center justify-center w-10 h-10 rounded-md;
  @apply text-gray-700 dark:text-gray-300;
  @apply hover:bg-gray-200 dark:hover:bg-gray-700;
  @apply transition-colors duration-200;
  border: none;
  outline: none;
  font-size: 1.25rem;
}

/* 移动端用户按钮 */
.mobile-user-btn {
  @apply flex items-center justify-center;
  border: none;
  outline: none;
  background: transparent;
  padding: 0.5rem;
}

.mobile-user-btn:hover {
  @apply bg-gray-200 dark:bg-gray-700 rounded-md;
  transition: background-color 0.2s;
}
</style>
