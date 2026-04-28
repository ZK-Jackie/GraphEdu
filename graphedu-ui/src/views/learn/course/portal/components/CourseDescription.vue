<script setup lang="ts">
/**
 * 课程描述组件
 * 显示课程详细描述和元数据
 */
import dayjs from 'dayjs'
import { useI18n } from 'vue-i18n'
import type { CourseDetailVO } from '@/types/api/education/course.ts'

interface Props {
  /** 课程详情 */
  course: CourseDetailVO
  /** 加载状态 */
  loading?: boolean
}

defineProps<Props>()

const { t } = useI18n()
</script>

<template>
  <div class="course-description">
    <div class="section-header">
      <h3 class="section-title">{{ $t('education.course.description') }}</h3>
    </div>

    <a-spin :spinning="loading">
      <div v-if="course.description" class="description-content">
        {{ course.description }}
      </div>
      <a-empty v-else :description="$t('common.noData')" />

      <div v-if="course.courseOutline" class="extra-section">
        <h4 class="extra-title">课程大纲</h4>
        <div class="description-content">{{ course.courseOutline }}</div>
      </div>

      <div v-if="course.targetAudience" class="extra-section">
        <h4 class="extra-title">适用人群</h4>
        <div class="description-content">{{ course.targetAudience }}</div>
      </div>

      <div v-if="course.learningGoals" class="extra-section">
        <h4 class="extra-title">学习目标</h4>
        <div class="description-content">{{ course.learningGoals }}</div>
      </div>

      <div v-if="course.tags && course.tags.length" class="tags-wrap">
        <a-tag v-for="tag in course.tags" :key="tag" color="processing">{{ tag }}</a-tag>
      </div>

      <div class="course-meta">
        <div class="meta-item">
          <span class="meta-label">{{ $t('education.portal.courseCreated') }}:</span>
          <span class="meta-value">{{ course.createTime ? dayjs(course.createTime).format('YYYY-MM-DD') : '-' }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">{{ $t('education.portal.courseUpdated') }}:</span>
          <span class="meta-value">{{ course.updateTime ? dayjs(course.updateTime).format('YYYY-MM-DD') : '-' }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">
            <a-tag :color="course.isPublic === 'Y' ? 'green' : 'orange'">
              {{ course.isPublic === 'Y' ? $t('education.portal.publicCourse') : $t('education.portal.privateCourse') }}
            </a-tag>
          </span>
        </div>
      </div>
    </a-spin>
  </div>
</template>

<style scoped>
.course-description {
  background: var(--ge-bg-container);
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ge-text-primary);
  margin: 0;
}

.description-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--ge-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 20px;
}

.extra-section {
  margin-bottom: 8px;
}

.extra-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ge-text-primary);
  margin: 0 0 8px;
}

.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.course-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--ge-border-color);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.meta-label {
  color: var(--ge-text-tertiary);
}

.meta-value {
  color: var(--ge-text-primary);
  font-weight: 500;
}

@media (max-width: 767px) {
  .course-description {
    padding: 16px;
  }

  .course-meta {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
