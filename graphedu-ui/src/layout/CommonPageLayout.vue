<script setup lang="ts">
/**
 * 通用页面布局组件
 * 用于统一页面结构，包含页面标题和内容区域
 * 使用固定高度，内容区域不允许滚动（滚动由外层布局控制）
 * 主要用于 CommonLayout 内部
 */
interface Props {
  /** 页面标题 */
  title?: string
  /** 页面副标题 */
  subtitle?: string
}

withDefaults(defineProps<Props>(), {
  title: '',
  subtitle: '',
})
</script>

<template>
  <div class="common-page-layout">
    <!-- 页面标题 -->
    <div v-if="title || subtitle || $slots.actions" class="page-header">
      <div class="page-header-text">
        <h1 v-if="title" class="page-title">{{ title }}</h1>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="page-header-actions">
        <slot name="actions" />
      </div>
    </div>

    <!-- 内容区域 - 固定高度、不滚动 -->
    <div class="page-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.common-page-layout {
  display: flex;
  flex-direction: column;
  /* 使用 flex: 1 占满父容器，而不是 height: 100% */
  flex: 1 1 0;
  min-height: 0;
  padding: 24px;
  background: var(--ge-bg-page);
  overflow: hidden;
}

.page-header {
  flex: 0 0 auto;
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header-text {
  flex: 1;
  min-width: 0;
}

.page-header-actions {
  flex-shrink: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--ge-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--ge-text-secondary);
  margin: 0;
}

.page-content {
  flex: 1 1 0;
  min-height: 0;
  overflow: auto;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .common-page-layout {
    padding: 16px;
  }
}
</style>
