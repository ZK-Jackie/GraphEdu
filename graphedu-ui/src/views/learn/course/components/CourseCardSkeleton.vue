<script setup lang="ts">
/**
 * 课程卡片骨架屏组件
 * 用于课程加载时显示占位内容，提升用户体验
 */
interface Props {
  /** 骨架屏数量，默认 6 */
  count?: number
}

withDefaults(defineProps<Props>(), {
  count: 6,
})
</script>

<template>
  <div class="skeleton-grid">
    <div v-for="i in count" :key="i" class="skeleton-card">
      <div class="skeleton-body">
        <!-- 封面图骨架 -->
        <a-skeleton-image class="skeleton-cover" active />

        <!-- 课程信息骨架 -->
        <div class="skeleton-content">
          <a-skeleton-input active class="skeleton-title" />
          <a-skeleton-input active size="small" class="skeleton-code" />
          <div class="skeleton-meta">
            <a-skeleton-input active size="small" class="skeleton-meta-item" />
            <a-skeleton-input active size="small" class="skeleton-meta-item" />
          </div>
          <div class="skeleton-stats">
            <a-skeleton-input active size="small" class="skeleton-stat" />
            <a-skeleton-input active size="small" class="skeleton-stat" />
          </div>
        </div>
      </div>

      <!-- 按钮骨架 -->
      <div class="skeleton-actions">
        <a-skeleton-button active block class="skeleton-button" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 骨架屏网格布局 - 与课程卡片网格一致 */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

/* 骨架卡片容器 */
.skeleton-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 上半部分：封面 + 信息 */
.skeleton-body {
  display: flex;
  flex-direction: column;
}

/* 封面图骨架 */
.skeleton-cover {
  width: 100%;
  height: 180px;
}

.skeleton-cover :deep(.ant-skeleton-image) {
  width: 100%;
  height: 100%;
}

.skeleton-cover :deep(.ant-skeleton-image-img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 课程信息骨架 */
.skeleton-content {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 课程名称骨架 */
.skeleton-title {
  width: 80%;
  margin-bottom: 8px;
}

.skeleton-title :deep(.ant-skeleton-input) {
  height: 22px;
}

/* 课程代码骨架 */
.skeleton-code {
  width: 40%;
  margin-bottom: 12px;
}

.skeleton-code :deep(.ant-skeleton-input) {
  height: 14px;
}

/* 元信息骨架 */
.skeleton-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.skeleton-meta-item {
  width: 60%;
}

.skeleton-meta-item :deep(.ant-skeleton-input) {
  height: 14px;
}

/* 统计信息骨架 */
.skeleton-stats {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.skeleton-stat {
  width: 80px;
}

.skeleton-stat :deep(.ant-skeleton-input) {
  height: 14px;
}

/* 按钮骨架 */
.skeleton-actions {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
}

.skeleton-button {
  height: 32px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .skeleton-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .skeleton-body {
    flex-direction: row;
  }

  .skeleton-cover {
    width: 120px;
    height: auto;
    min-height: 100px;
    flex-shrink: 0;
  }

  .skeleton-content {
    padding: 10px 12px;
    min-width: 0;
  }

  .skeleton-title {
    width: 70%;
    margin-bottom: 6px;
  }

  .skeleton-code {
    margin-bottom: 6px;
  }

  .skeleton-meta {
    flex-direction: row;
    gap: 8px;
    margin-bottom: 6px;
  }

  .skeleton-meta-item {
    width: 40%;
  }

  .skeleton-actions {
    padding: 8px 12px;
  }
}
</style>
