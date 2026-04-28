<script setup lang="ts">
/**
 * SemanticGraphHeader - 语义知识图谱页面头部
 *
 * 包含标题、统计摘要卡片和操作按钮。
 */
import { ReloadOutlined, PlusOutlined } from '@ant-design/icons-vue'

interface Props {
  totalTasks: number
  runningCount: number
  enabledCount: number
  loading?: boolean
}

interface Emits {
  (e: 'refresh'): void
  (e: 'create'): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>

<template>
  <div class="header-wrapper">
    <div class="header-content">
      <!-- 左侧：标题和副标题 -->
      <div class="header-left">
        <h2 class="header-title">语义知识图谱</h2>
        <p class="header-subtitle">管理课程的 GraphRAG 语义索引构建任务</p>
      </div>

      <!-- 中间：统计卡片 -->
      <div class="header-stats">
        <div class="stat-chip">
          <span class="stat-value">{{ totalTasks }}</span>
          <span class="stat-label">总任务</span>
        </div>
        <div class="stat-chip stat-chip--amber">
          <span class="stat-value">{{ runningCount }}</span>
          <span class="stat-label">运行中</span>
        </div>
        <div class="stat-chip stat-chip--green">
          <span class="stat-value">{{ enabledCount }}</span>
          <span class="stat-label">已启用</span>
        </div>
      </div>

      <!-- 右侧：操作按钮 -->
      <a-space>
        <a-button :loading="loading" @click="$emit('refresh')">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="$emit('create')">
          <template #icon><PlusOutlined /></template>
          新建图谱
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.header-wrapper {
  @apply px-6 py-4;
  @apply bg-gradient-to-r from-blue-50/60 to-white dark:from-gray-800/40 dark:to-transparent;
  @apply border-b border-gray-100 dark:border-gray-700/50;
}

.header-content {
  @apply flex items-center justify-between gap-4 flex-wrap;
}

.header-left {
  @apply flex flex-col gap-0.5;
}

.header-title {
  @apply text-lg font-semibold text-gray-900 dark:text-gray-100 m-0;
}

.header-subtitle {
  @apply text-sm text-gray-500 dark:text-gray-400 m-0;
}

.header-stats {
  @apply flex items-center gap-3;
}

.stat-chip {
  @apply flex items-center gap-1.5 px-3 py-1.5 rounded-lg;
  @apply bg-blue-50 dark:bg-blue-900/20;
}

.stat-chip--amber {
  @apply bg-amber-50 dark:bg-amber-900/20;
}

.stat-chip--green {
  @apply bg-green-50 dark:bg-green-900/20;
}

.stat-value {
  @apply text-base font-semibold text-gray-800 dark:text-gray-200;
}

.stat-label {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

@media (max-width: 767px) {
  .header-content {
    @apply flex-col items-start;
  }

  .header-stats {
    @apply w-full;
  }
}
</style>
