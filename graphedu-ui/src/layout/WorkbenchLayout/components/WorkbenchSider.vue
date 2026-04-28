<script setup lang="ts">
import type { ItemType, MenuProps } from 'ant-design-vue'
import useAppStore from '@/stores/modules/app'
import useFunctionStore from '@/stores/modules/function'
import { getActiveMenuKeys, getOpenMenuKeys } from '@/router/utils'
import { useBreakpoints } from '@/composables/useBreakpoints'

const appStore = useAppStore()
const functionStore = useFunctionStore()
const { sidebarCollapsed, darkMode } = storeToRefs(appStore)
const { isDesktop } = useBreakpoints()

const router = useRouter()
const route = useRoute()

// 当前选中的菜单项
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])

/**
 * 切换侧边栏折叠状态
 */
const toggleCollapsed = () => {
  appStore.toggleSidebar()
}

/**
 * 获取菜单项
 */
const menuItems = computed<ItemType[]>(() => {
  return functionStore.adminMenuItems
})

/**
 * 根据当前路由更新选中的菜单项
 */
watch(
  () => route.matched,
  (matched) => {
    selectedKeys.value = getActiveMenuKeys(matched)
    openKeys.value = getOpenMenuKeys(matched)
  },
  { immediate: true }
)

/**
 * 菜单点击事件
 */
const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
  router.push({ name: key as string })
}

/**
 * 子菜单展开/收起事件
 */
const handleOpenChange = (keys: (string | number)[]) => {
  openKeys.value = keys as string[]
}
</script>

<template>
  <!-- 桌面端：固定侧边栏 -->
  <div v-if="isDesktop" class="sider" :class="{ collapsed: sidebarCollapsed }">
    <a-menu
      v-model:selected-keys="selectedKeys"
      v-model:open-keys="openKeys"
      :theme="darkMode ? 'dark' : 'light'"
      mode="inline"
      class="sider-menu"
      :inline-collapsed="sidebarCollapsed"
      :items="menuItems"
      @click="handleMenuClick"
      @open-change="handleOpenChange"
    />
    <button class="sider-toggle" :class="{ collapsed: sidebarCollapsed }" @click="toggleCollapsed">
      <span class="toggle-arrow"></span>
    </button>
  </div>
</template>

<style scoped>
@reference "#main.css";

.sider {
  @apply h-full flex flex-col border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800;
  width: 200px;
  transition: width 0.3s ease;
}

/* 折叠状态 */
.sider.collapsed {
  width: 80px;
}

.sider-menu {
  @apply flex-1 overflow-y-auto overflow-x-hidden border-r-0;
  /* 自定义滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

/* WebKit 浏览器滚动条样式 */
.sider-menu::-webkit-scrollbar {
  width: 6px;
}

.sider-menu::-webkit-scrollbar-track {
  background: transparent;
}

.sider-menu::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.sider-menu::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

.sider-toggle {
  @apply w-full h-20 flex items-center justify-center cursor-pointer
  bg-white dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
  transition-[width] duration-300 flex-shrink-0;
  transition-timing-function: cubic-bezier(0.2, 0, 0, 1);
  border: none;
  outline: none;
  border-top: 1px solid rgb(229 231 235); /* gray-200 */
}

.dark .sider-toggle {
  border-top: 1px solid rgb(55 65 81); /* gray-700 */
}

/**/
.toggle-arrow {
  @apply relative inline-block text-gray-700 dark:text-gray-300;
  width: 0.75rem;
  height: calc(0.75rem * 1.4142); /* .75rem * √2 */
  transition: transform 0.3s ease-in-out;
}

/* 上箭头 */
.toggle-arrow::before {
  content: '';
  @apply absolute top-0 left-0;
  width: 100%;
  height: 1px;
  background: currentColor;
  transform: rotate(45deg);
  transform-origin: left center;
}

/* 下箭头 */
.toggle-arrow::after {
  content: '';
  @apply absolute bottom-0 left-0;
  width: 100%;
  height: 1px;
  background: currentColor;
  transform: rotate(-45deg);
  transform-origin: left center;
}

/* 折叠时旋转 180 度 */
.sider-toggle.collapsed .toggle-arrow {
  transform: rotate(-180deg);
}
</style>
