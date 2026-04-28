<script setup lang="ts">
/**
 * 教师卡片组件
 * 显示教师基本信息
 */
import { UserOutlined } from '@ant-design/icons-vue'
import type { TeacherListVO } from '@/types/api/education/teacher.ts'

interface Props {
  /** 教师信息 */
  teacher: TeacherListVO
}

defineProps<Props>()
</script>

<template>
  <div class="teacher-card">
    <a-avatar :size="64" :src="teacher.avatarUrl" class="teacher-avatar">
      <template #icon>
        <UserOutlined />
      </template>
    </a-avatar>
    <div class="teacher-info">
      <div class="teacher-name">{{ teacher.realName }}</div>
      <div v-if="teacher.title" class="teacher-title">{{ teacher.title }}</div>
      <div v-if="teacher.faculty" class="teacher-faculty">{{ teacher.faculty }}</div>
    </div>
  </div>
</template>

<style scoped>
.teacher-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: var(--ge-bg-container);
  border: 1px solid var(--ge-border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.teacher-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--ge-primary);
}

.teacher-avatar {
  margin-bottom: 12px;
}

.teacher-info {
  text-align: center;
}

.teacher-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--ge-text-primary);
  margin-bottom: 4px;
}

.teacher-title {
  font-size: 14px;
  color: var(--ge-primary);
  margin-bottom: 4px;
}

.teacher-faculty {
  font-size: 12px;
  color: var(--ge-text-tertiary);
}
</style>
