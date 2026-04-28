<script setup lang="ts">
/**
 * WorkbenchLayout - 工作台布局
 *
 * 包含顶部导航栏、左侧菜单栏和主内容区域的完整布局
 * 主内容区域使用 Golden Layout 实现多标签页和可拖拽面板
 *
 * 响应式布局：
 * - 桌面端（≥1024px）：固定侧边栏，完整功能
 * - 平板端（768-1023px）：抽屉式导航，汉堡菜单触发
 * - 移动端（<768px）：完全抽屉式，汉堡菜单
 */
import { useBreakpoints } from '@/composables/useBreakpoints'
import useAppStore from '@/stores/modules/app'
import Header from '@/components/Header/index.vue'
import { WorkbenchSider, WorkbenchContent, MobileMenuDrawer, MobileUserDrawer } from './components/index.ts'

const { isMobile, device } = useBreakpoints()
const appStore = useAppStore()

// 监听设备类型变化，同步到 appStore
watch(
  device,
  (newDevice) => {
    appStore.updateDevice(newDevice)
  },
  { immediate: true }
)
</script>

<template>
  <div class="workbench-layout">
    <Header class="workbench-layout-header" :show-menu="false" />
    <div class="workbench-layout-body">
      <WorkbenchSider class="workbench-layout-body-sider" />
      <WorkbenchContent class="workbench-layout-body-content" :class="{ 'mobile-content': isMobile }" />
    </div>
    <!-- 非桌面端抽屉组件（平板+移动端） -->
    <MobileMenuDrawer />
    <MobileUserDrawer />
  </div>
</template>

<style scoped>
@reference "#main.css";

.workbench-layout {
  @apply h-screen flex flex-col w-full;
  background: var(--ge-bg-page);
  /* 确保布局占满整个视口 */
  overflow: hidden;
}

.workbench-layout-header {
  @apply top-0 left-0 w-full z-50 h-20;
  /* 固定高度，防止压缩 */
  flex-shrink: 0;
}

.workbench-layout-body {
  @apply flex flex-1 h-full w-full;
  /* 关键：允许 body 部分占据剩余空间 */
  overflow: hidden;
  min-height: 0; /* 修复 flex 子元素高度问题 */
}

.workbench-layout-body-sider {
  @apply h-full z-50;
  /* 固定宽度，防止压缩 */
  flex-shrink: 0;
}

.workbench-layout-body-content {
  @apply m-2 p-4 flex-1 rounded-lg shadow-md;
  background: var(--ge-bg-container);
  /* 关键：移除 padding，让 Golden Layout 完全控制内部空间 */
  padding: 0 !important;
  /* 确保内容区域能被 Golden Layout 填满 */
  overflow: hidden;
  /* 修复 flex 子元素宽度问题 */
  min-width: 0;
  /* 关键：设置高度为视口高度减去 header 的高度，确保内容区域能正确填满剩余空间 */
  height: calc(100vh - calc(var(--spacing) * 20));
}

/* 移动端内容区域 */
.workbench-layout-body-content.mobile-content {
  margin-bottom: 0;
}
</style>
