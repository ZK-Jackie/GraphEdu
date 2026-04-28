<!-- TablePageLayout.vue -->
<template>
  <div
    ref="containerRef"
    class="table-page-layout"
    :class="{
      'page-scroll': activeScrollBehavior === 'page',
      'table-scroll': activeScrollBehavior === 'table',
    }"
  >
    <!-- 搜索区域 -->
    <div v-if="$slots.search" class="search-section" ref="searchSectionRef">
      <!-- 标题栏：始终可见 -->
      <div class="search-header">
        <span class="search-header-title">
          <SearchOutlined class="search-header-icon" />
          {{ t('common.search') }}
        </span>
        <span class="search-header-toggle" @click="toggleSearchCollapse">
          {{ isSearchCollapsed ? t('common.expand') : t('common.collapse') }}
          <DownOutlined v-if="isSearchCollapsed" />
          <UpOutlined v-else />
        </span>
      </div>
      <!-- 表单内容：可折叠 -->
      <div
        class="search-body"
        :class="{ collapsed: isSearchCollapsed, 'no-transition': skipTransition }"
        ref="searchContentRef"
      >
        <slot name="search"></slot>
      </div>
    </div>

    <!-- 表格卡片 -->
    <a-card :bordered="false" class="table-card">
      <!-- 操作按钮插槽（卡片标题区域） -->
      <template v-if="$slots.actions" #title>
        <slot name="actions"></slot>
      </template>

      <!-- 表格主体插槽 -->
      <div class="table-wrapper">
        <slot name="table" :scroll-y="tableScrollY"></slot>
      </div>

      <!-- 分页器插槽（卡片底部） -->
      <div v-if="$slots.pagination" class="pagination-container">
        <slot name="pagination"></slot>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { SearchOutlined, DownOutlined, UpOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import { useAdaptiveTable } from '@/composables/useAdaptiveTable'

const { t } = useI18n()

interface TablePageLayoutProps {
  /**
   * 页面滚动行为
   *
   * - auto 模式下根据表格内容高度自动切换，超过阈值则启用页面滚动模式，反之启用表格内滚动模式。
   * - page 模式下表格高度自适应，页面滚动；
   * - table 模式下表格高度固定，表格内滚动；
   */
  scrollBehavior?: 'page' | 'table' | 'auto'
  /**
   * 页面高度阈值，单位为像素。当窗口高度低于此值时，表格使用固定高度。
   * 默认值为 450px（适合小屏幕笔记本）。
   */
  shortThreshold?: number
  /**
   * 阈值模式下表格的固定高度，单位为像素。
   * 当窗口高度小于 shortThreshold 时使用此值。
   * 默认值为 200px。
   */
  shortThresholdTableHeight?: number
}

const props = withDefaults(defineProps<TablePageLayoutProps>(), {
  scrollBehavior: 'auto',
  shortThreshold: 450,
  shortThresholdTableHeight: 200,
})

const containerRef = useTemplateRef('containerRef')
const searchSectionRef = useTemplateRef('searchSectionRef')
const searchContentRef = useTemplateRef('searchContentRef')

const isSearchCollapsed = ref(false)
const hasSearchOverflow = ref(false)
const skipTransition = ref(true)

const { tableScrollY, isContainerTooShort, recalc } = useAdaptiveTable({
  containerRef,
  subtractRefs: [
    '.search-section',
    '.table-card .ant-card-head',
    '.pagination-container',
    '.table-wrapper .ant-table-thead',
    10,
  ],
  shortThreshold: toRef(() => props.shortThreshold).value,
  shortThresholdTableHeight: toRef(() => props.shortThresholdTableHeight).value,
})

const activeScrollBehavior = computed(() => {
  if (props.scrollBehavior === 'page') return 'page'
  if (props.scrollBehavior === 'table') return 'table'
  return isContainerTooShort.value ? 'page' : 'table'
})

/** 检测搜索表单是否有溢出内容（超过一行） */
let isMeasuring = false

const detectSearchOverflow = () => {
  if (isMeasuring) return
  const el = searchContentRef.value
  if (!el) return

  isMeasuring = true
  // 需要展开态测量真实高度
  const wasCollapsed = isSearchCollapsed.value
  if (wasCollapsed) {
    skipTransition.value = true
    isSearchCollapsed.value = false
  }

  nextTick(() => {
    const formEl = el.querySelector('.ant-form') as HTMLElement | null
    if (formEl) {
      // 一行表单项高度约 40px
      hasSearchOverflow.value = formEl.scrollHeight > 40
      if (hasSearchOverflow.value) {
        isSearchCollapsed.value = true
      }
    }
    nextTick(() => {
      skipTransition.value = false
      isMeasuring = false
    })
  })
}

/** 切换搜索折叠状态 */
const toggleSearchCollapse = () => {
  isSearchCollapsed.value = !isSearchCollapsed.value
  setTimeout(() => {
    recalc()
  }, 350)
}

let resizeTimer: ReturnType<typeof setTimeout> | null = null

const handleWindowResize = () => {
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(detectSearchOverflow, 100)
}

onMounted(() => {
  nextTick(detectSearchOverflow)
  window.addEventListener('resize', handleWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  if (resizeTimer) clearTimeout(resizeTimer)
})
</script>

<style scoped>
@reference "#main.css";

.table-page-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 10px;
}

/* ===== 搜索区域 ===== */
.search-section {
  flex-shrink: 0;
  margin-bottom: 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

/* 标题栏 */
.search-header {
  @apply flex items-center justify-between px-4 py-2;
  background: rgba(0, 0, 0, 0.02);
}

.search-header-title {
  @apply flex items-center gap-2 text-sm font-medium text-gray-600;
}

.search-header-icon {
  @apply text-gray-400;
}

.search-header-toggle {
  @apply flex items-center gap-1 text-xs text-gray-400 cursor-pointer;
}

.search-header-toggle:hover {
  @apply text-blue-500;
}

/* 表单内容：可折叠 */
.search-body {
  overflow: hidden;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}

.search-body:not(.no-transition) {
  transition: max-height 0.3s ease;
}

.search-body.collapsed {
  max-height: 0;
  border-top-color: transparent;
}

/* 搜索卡片内部 padding */
:deep(.search-section .ant-card) {
  border: none;
  border-radius: 0;
  box-shadow: none;
}

:deep(.search-section .ant-card-body) {
  padding: 12px 20px;
}

/* ===== 表格卡片 ===== */
.table-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

:deep(.table-card .ant-card) {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

:deep(.table-card .ant-card-head) {
  flex-shrink: 0;
}

:deep(.table-card .ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pagination-container {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: 10px;
  padding-bottom: 10px;
}

/* ---------- 页面滚动模式 ---------- */

.table-page-layout.page-scroll {
  overflow: scroll;
}

.page-scroll .table-card,
.page-scroll :deep(.table-card .ant-card),
.page-scroll :deep(.table-card .ant-card-body) {
  height: auto;
  flex: none;
  min-height: auto;
}

.page-scroll .table-wrapper {
  flex: none;
  min-height: auto;
  overflow: visible;
}
</style>
