<script setup lang="ts">
/**
 * QuoteArea - 引用内容区域
 *
 * 功能：
 * - 灰色背景区域
 * - 显示引用数量
 * - "清空全部" 按钮
 * - 引用列表容器（限制高度 120px，超过 3 条显示滚动条）
 */

import { LinkOutlined } from '@ant-design/icons-vue'
import { Button } from 'ant-design-vue'
import QuoteItem from './QuoteItem.vue'
import type { TextQuote } from '@/stores/modules/quote'

const props = defineProps<{
  /** 引用列表 */
  quotes: readonly TextQuote[]
}>()

defineEmits<{
  /** 清空所有引用 */
  clear: []
  /** 移除指定引用 */
  remove: [id: string]
}>()
</script>

<template>
  <div v-if="quotes.length > 0" class="quotes-area">
    <div class="quotes-header">
      <span class="quotes-title">
        <LinkOutlined class="quotes-icon" />
        引用内容 ({{ quotes.length }})
      </span>
      <Button type="link" size="small" @click="$emit('clear')"> 清空全部 </Button>
    </div>

    <div class="quotes-list">
      <QuoteItem v-for="quote in quotes" :key="quote.id" :quote="quote" @remove="$emit('remove', quote.id)" />
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.quotes-area {
  @apply px-4 py-3;
  @apply bg-gray-50 dark:bg-gray-900;
  @apply border-t border-b border-gray-200 dark:border-gray-700;
}

.quotes-header {
  @apply flex items-center justify-between mb-2;
}

.quotes-title {
  @apply text-sm font-medium;
  @apply text-gray-700 dark:text-gray-300;
  @apply flex items-center;
}

.quotes-icon {
  @apply mr-1;
}

.quotes-list {
  @apply flex flex-col gap-2;
  max-height: 132px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

/* 自定义滚动条 */
.quotes-list::-webkit-scrollbar {
  width: 4px;
}

.quotes-list::-webkit-scrollbar-track {
  background: transparent;
}

.quotes-list::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600;
  border-radius: 2px;
}

.quotes-list::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}
</style>
