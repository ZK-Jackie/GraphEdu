<script setup lang="ts">
/**
 * 教师列表区域组件
 */
import TeacherCard from './TeacherCard.vue'

import type { TeacherListVO } from '@/types/api/education/teacher.ts'

interface Props {
  /** 教师列表 */
  teachers?: TeacherListVO[]
  /** 加载状态 */
  loading?: boolean
}

defineProps<Props>()
</script>

<template>
  <div class="teacher-section">
    <div class="section-header">
      <h3 class="section-title">{{ $t('education.portal.teachers') }}</h3>
    </div>

    <a-spin :spinning="loading">
      <div v-if="teachers && teachers.length > 0" class="teacher-grid">
        <TeacherCard v-for="teacher in teachers" :key="teacher.teacherId" :teacher="teacher" />
      </div>
      <a-empty v-else :description="$t('education.portal.noTeachers')" />
    </a-spin>
  </div>
</template>

<style scoped>
.teacher-section {
  background: var(--ge-bg-container);
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ge-text-primary);
  margin: 0;
}

.teacher-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 1023px) {
  .teacher-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .teacher-section {
    padding: 16px;
  }

  .teacher-grid {
    grid-template-columns: 1fr;
  }
}
</style>
