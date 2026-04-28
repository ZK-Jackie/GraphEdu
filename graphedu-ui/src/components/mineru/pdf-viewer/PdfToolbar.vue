<template>
  <div class="pdf-toolbar">
    <!-- 左侧：翻页 -->
    <div class="toolbar-left">
      <a-button size="small" :disabled="currentPage <= 1" @click="emit('prev')">
        <template #icon><LeftOutlined /></template>
      </a-button>

      <div class="page-input">
        <a-input-number
          :value="currentPage"
          :min="1"
          :max="totalPages"
          size="small"
          :controls="false"
          style="width: 48px; text-align: center"
          @change="onPageInput"
        />
        <span class="page-total">/ {{ totalPages }}</span>
      </div>

      <a-button size="small" :disabled="currentPage >= totalPages" @click="emit('next')">
        <template #icon><RightOutlined /></template>
      </a-button>
    </div>

    <!-- 右侧：缩放 -->
    <div class="toolbar-right">
      <a-button
        size="small"
        @click="emit('update:zoomMode', 'fit-page')"
        :type="zoomMode === 'fit-page' ? 'primary' : 'default'"
      >
        <template #icon><ExpandOutlined /></template>
      </a-button>

      <a-button
        size="small"
        @click="emit('update:zoomMode', 'fit-width')"
        :type="zoomMode === 'fit-width' ? 'primary' : 'default'"
      >
        <template #icon><ColumnWidthOutlined /></template>
      </a-button>

      <a-divider type="vertical" />

      <a-button size="small" :disabled="scale <= minScale" @click="emit('zoomOut')">
        <template #icon><ZoomOutOutlined /></template>
      </a-button>

      <span class="scale-display">{{ scalePercent }}%</span>

      <a-button size="small" :disabled="scale >= maxScale" @click="emit('zoomIn')">
        <template #icon><ZoomInOutlined /></template>
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  LeftOutlined,
  RightOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  ExpandOutlined,
  ColumnWidthOutlined,
} from '@ant-design/icons-vue'
import type { ZoomMode } from './types'

/**
 * 组件属性
 */
interface Props {
  /** 当前页码（1-based） */
  currentPage: number
  /** 总页数 */
  totalPages: number
  /** 当前缩放比例 */
  scale: number
  /** 缩放模式 */
  zoomMode: ZoomMode
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'prev'): void
  (e: 'next'): void
  (e: 'jumpTo', page: number): void
  (e: 'zoomIn'): void
  (e: 'zoomOut'): void
  (e: 'update:zoomMode', mode: ZoomMode): void
}>()

const minScale = 0.25
const maxScale = 5

const scalePercent = computed(() => Math.round(props.scale * 100))

function onPageInput(val: any): void {
  const page = Number(val)
  if (page >= 1 && page <= props.totalPages) {
    emit('jumpTo', page)
  }
}
</script>

<style scoped>
@reference '#main.css';

.pdf-toolbar {
  @apply flex items-center justify-between px-3 py-1.5;
  flex-shrink: 0;
  background: var(--ge-bg-container);
  border-bottom: 1px solid var(--ge-border-color);
}

.toolbar-left,
.toolbar-right {
  @apply flex items-center gap-1.5;
}

.page-input {
  @apply flex items-center gap-1;
}

.page-total {
  @apply text-xs;
  color: var(--ge-text-secondary);
}

.scale-display {
  @apply text-xs w-10 text-center;
  color: var(--ge-text-secondary);
}
</style>
