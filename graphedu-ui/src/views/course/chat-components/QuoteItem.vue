<script setup lang="ts">
/**
 * QuoteItem - 单条引用（灰色长条）
 *
 * 功能：
 * - 白色背景卡片
 * - 显示来源信息（小字灰色）
 * - 显示引用文本（斜体，最多 3 行）
 * - 右侧删除按钮（×）
 * - 悬停效果
 */

import { CloseOutlined } from '@ant-design/icons-vue'
import type { TextQuote } from '@/stores/modules/quote'

defineProps<{
  /** 引用数据 */
  quote: TextQuote
}>()

defineEmits<{
  /** 移除引用 */
  remove: []
}>()
</script>

<template>
  <div class="quote-item">
    <div class="quote-source">{{ quote.source }}</div>
    <div class="quote-text">"{{ quote.text }}"</div>
    <button class="quote-remove" @click="$emit('remove')" title="移除此引用">
      <CloseOutlined />
    </button>
  </div>
</template>

<style scoped>
@reference '#main.css';

.quote-item {
  @apply relative rounded-lg p-3;
  @apply bg-white dark:bg-gray-800;
  @apply border border-gray-200 dark:border-gray-600;
  @apply transition-shadow;
}

.quote-item:hover {
  @apply shadow-sm;
}

.quote-source {
  @apply text-xs mb-1;
  @apply text-gray-500 dark:text-gray-400;
}

.quote-text {
  @apply text-sm pr-6 italic;
  @apply text-gray-700 dark:text-gray-300;
  @apply line-clamp-3;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.quote-remove {
  @apply absolute top-2 right-2;
  @apply text-gray-400 hover:text-red-500;
  @apply transition-colors;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  outline: none;
}

.quote-remove:hover {
  @apply bg-gray-100 dark:bg-gray-700;
}
</style>
