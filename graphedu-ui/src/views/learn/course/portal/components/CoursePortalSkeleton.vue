<script setup lang="ts">
 /**
 * 课程门户页骨架屏
 * 用于课程详情加载时的占位显示
 */
</script>

<template>
  <div class="course-portal-skeleton">
    <!-- 英雄区骨架 -->
    <div class="skeleton-hero">
      <div class="skeleton-hero-cover">
        <a-skeleton-image class="skeleton-cover-img" :active="true" />
      </div>
      <div class="skeleton-hero-content">
        <a-skeleton-input :active="true" class="skeleton-title" />
        <a-skeleton-input :active="true" class="skeleton-subtitle" size="small" />
        <div class="skeleton-stats">
          <a-skeleton-button :active="true" size="small" />
          <a-skeleton-button :active="true" size="small" />
        </div>
        <a-skeleton-button :active="true" class="skeleton-cta" size="large" />
      </div>
    </div>

    <!-- 课程描述骨架 -->
    <div class="skeleton-section">
      <a-skeleton-input :active="true" class="skeleton-section-title" size="small" />
      <a-skeleton paragraph :rows="3" :active="true" />
    </div>

    <!-- 教师列表骨架 -->
    <div class="skeleton-section">
      <a-skeleton-input :active="true" class="skeleton-section-title" size="small" />
      <div class="skeleton-cards">
        <div v-for="i in 3" :key="`teacher-${i}`" class="skeleton-card">
          <a-skeleton-avatar :active="true" :size="64" />
          <a-skeleton-input :active="true" size="small" />
          <a-skeleton-input :active="true" size="small" />
        </div>
      </div>
    </div>

    <!-- 教材列表骨架 -->
    <div class="skeleton-section">
      <a-skeleton-input :active="true" class="skeleton-section-title" size="small" />
      <div class="skeleton-cards">
        <div v-for="i in 3" :key="`book-${i}`" class="skeleton-card">
          <a-skeleton-image class="skeleton-book-cover" :active="true" />
          <a-skeleton-input :active="true" size="small" />
          <a-skeleton-input :active="true" size="small" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.course-portal-skeleton {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 英雄区骨架 */
.skeleton-hero {
  display: flex;
  gap: 24px;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.skeleton-hero-cover {
  flex-shrink: 0;
}

.skeleton-cover-img {
  width: 320px;
  height: 180px;
  border-radius: 8px;
}

.skeleton-hero-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-title {
  width: 60%;
  height: 32px;
}

.skeleton-subtitle {
  width: 40%;
}

.skeleton-stats {
  display: flex;
  gap: 16px;
}

.skeleton-cta {
  width: 160px;
  align-self: flex-start;
}

/* 通用区块样式 */
.skeleton-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.skeleton-section-title {
  width: 120px;
  margin-bottom: 16px;
}

/* 卡片网格 */
.skeleton-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.skeleton-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.skeleton-book-cover {
  width: 80px;
  height: 120px;
  border-radius: 4px;
}

/* 响应式 */
@media (max-width: 1023px) {
  .skeleton-hero {
    flex-direction: column;
  }

  .skeleton-cover-img {
    width: 100%;
    max-width: 400px;
  }

  .skeleton-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .skeleton-cards {
    grid-template-columns: 1fr;
  }

  .skeleton-hero {
    padding: 16px;
  }

  .skeleton-section {
    padding: 16px;
  }
}
</style>
