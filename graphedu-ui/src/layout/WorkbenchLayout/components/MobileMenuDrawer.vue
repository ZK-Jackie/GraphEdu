<script setup lang="ts">
/**
 * MobileMenuDrawer - 非桌面端左侧导航抽屉
 *
 * 结构（参照 CommonLayout MobileDrawer）：
 * - 顶部：Logo + 项目名称
 * - 中间：导航菜单项（admin 场景）
 * - 底部：GitHub 图标 + 暗色模式切换
 *
 * 通过 appStore.mobileMenuDrawerOpen 控制开关
 */
import type { ItemType, MenuProps } from 'ant-design-vue'
import Logo from '@/components/Header/components/Logo.vue'
import GithubIcon from '@/components/Header/components/GithubIcon.vue'
import DarkModeToggle from '@/components/Header/components/DarkModeToggle.vue'
import useAppStore from '@/stores/modules/app'
import useFunctionStore from '@/stores/modules/function'
import { getActiveMenuKeys, getOpenMenuKeys } from '@/router/utils'
import { useBreakpoints } from '@/composables/useBreakpoints'

const appStore = useAppStore()
const functionStore = useFunctionStore()
const { mobileMenuDrawerOpen } = storeToRefs(appStore)
const { isDesktop } = useBreakpoints()

const router = useRouter()
const route = useRoute()

const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])

const menuItems = computed<ItemType[]>(() => {
  return functionStore.adminMenuItems
})

watch(
  () => route.matched,
  (matched) => {
    selectedKeys.value = getActiveMenuKeys(matched)
    openKeys.value = getOpenMenuKeys(matched)
  },
  { immediate: true }
)

const handleClose = () => {
  appStore.toggleMobileMenuDrawer(false)
}

const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
  router.push({ name: key as string })
  handleClose()
}

const handleOpenChange = (keys: (string | number)[]) => {
  openKeys.value = keys as string[]
}
</script>

<template>
  <a-drawer
    v-if="!isDesktop"
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

    <!-- 导航菜单 -->
    <nav class="drawer-menu">
      <a-menu
        v-model:selected-keys="selectedKeys"
        v-model:open-keys="openKeys"
        mode="inline"
        :items="menuItems"
        @click="handleMenuClick"
        @open-change="handleOpenChange"
      />
    </nav>

    <!-- 底部工具栏 -->
    <div class="drawer-footer">
      <GithubIcon class="drawer-footer-item" />
      <DarkModeToggle class="drawer-footer-item" />
    </div>
  </a-drawer>
</template>

<style scoped>
@reference "#main.css";

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
</style>
