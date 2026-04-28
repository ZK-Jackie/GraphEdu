<script setup lang="ts">
/**
 * 课程门户英雄区组件
 * 显示课程封面、标题、统计信息和主操作按钮
 */
import { useRouter } from 'vue-router'
import {
  BookOutlined,
  UserOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ArrowLeftOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import type { CourseDetailVO } from '@/types/api/education/course.ts'

interface Props {
  /** 课程详情 */
  course: CourseDetailVO
  /** 是否已加入课程 */
  isJoined?: boolean
  /** 学习进度 */
  progress?: number
  /** 加入课程加载状态 */
  joining?: boolean
  /** 当前用户是否可以管理该课程（是该课程教师或管理员） */
  canManage?: boolean
  /** 当前用户是否是学生 */
  isStudent?: boolean
}

interface Emits {
  /** 加入课程事件 */
  (e: 'join'): void
  /** 开始学习事件 */
  (e: 'startLearning'): void
  /** 管理课程事件 */
  (e: 'manageCourse'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()

const difficultyLabelMap: Record<string, string> = {
  '1': '初级',
  '2': '中级',
  '3': '高级',
}

const difficultyColorMap: Record<string, string> = {
  '1': 'green',
  '2': 'orange',
  '3': 'red',
}

const difficultyLabel = computed(() => {
  if (!props.course.difficultyLevel) return '未设置'
  return difficultyLabelMap[props.course.difficultyLevel] || '未设置'
})

const difficultyColor = computed(() => {
  if (!props.course.difficultyLevel) return 'default'
  return difficultyColorMap[props.course.difficultyLevel] || 'default'
})
</script>

<template>
  <div class="course-portal-hero">
    <!-- 课程封面 -->
    <div class="hero-cover">
      <img v-if="course.coverUrl" :src="course.coverUrl" :alt="course.courseName" class="cover-image" />
      <div v-else class="cover-placeholder">
        <BookOutlined class="placeholder-icon" />
      </div>
    </div>

    <!-- 课程信息 -->
    <div class="hero-content">
      <!-- 课程标题和徽章 -->
      <div class="course-header">
        <h1 class="course-title">{{ course.courseName }}</h1>
        <div class="course-badges">
          <a-tag v-if="course.courseCode" color="blue">{{ course.courseCode }}</a-tag>
          <a-tag v-if="course.faculty" color="purple">{{ course.faculty }}</a-tag>
          <a-tag v-if="course.category" color="cyan">{{ course.category }}</a-tag>
          <a-tag :color="difficultyColor">{{ difficultyLabel }}</a-tag>
          <a-tag :color="course.isPublic === 'Y' ? 'green' : 'orange'">
            {{ course.isPublic === 'Y' ? $t('education.portal.publicCourse') : $t('education.portal.privateCourse') }}
          </a-tag>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="course-stats">
        <div class="stat-item">
          <UserOutlined class="stat-icon" />
          <span class="stat-label">{{ $t('education.course.students') }}</span>
          <span class="stat-value">{{ course.studentCount }}</span>
        </div>
        <div class="stat-item">
          <EyeOutlined class="stat-icon" />
          <span class="stat-label">{{ $t('education.course.views') }}</span>
          <span class="stat-value">{{ course.viewCount }}</span>
        </div>
        <div class="stat-item" v-if="typeof course.totalHours === 'number'">
          <BookOutlined class="stat-icon" />
          <span class="stat-label">总学时</span>
          <span class="stat-value">{{ course.totalHours }}h</span>
        </div>
      </div>

      <div v-if="course.tags && course.tags.length" class="course-tags-row">
        <a-tag v-for="tag in course.tags" :key="tag" color="processing">{{ tag }}</a-tag>
      </div>

      <!-- 学习进度 (已加入时显示) -->
      <div v-if="isJoined && progress !== undefined" class="learning-progress">
        <div class="progress-header">
          <span class="progress-label">{{ $t('common.learningProgress') }}</span>
          <span class="progress-value">{{ progress }}%</span>
        </div>
        <a-progress :percent="progress" :show-info="false" stroke-color="#52c41a" />
      </div>

      <!-- 主操作按钮 -->
      <div class="hero-actions">
        <!-- 学生按钮：加入课程 / 继续学习 -->
        <a-button
          v-if="isStudent"
          :type="isJoined ? 'primary' : 'default'"
          size="large"
          :loading="joining"
          @click="isJoined ? emit('startLearning') : emit('join')"
          class="main-action-btn"
        >
          <template #icon>
            <PlayCircleOutlined v-if="isJoined" />
            <PlusOutlined v-else />
          </template>
          {{
            isJoined
              ? progress && progress > 0
                ? $t('common.continueLearning')
                : $t('common.startLearning')
              : $t('common.joinCourse')
          }}
        </a-button>

        <!-- 教师/管理员按钮：管理课程 -->
        <a-button v-if="canManage" type="primary" size="large" @click="emit('manageCourse')" class="main-action-btn">
          <template #icon><SettingOutlined /></template>
          管理课程
        </a-button>

        <a-button size="large" @click="router.back()">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          {{ $t('education.portal.backToList') }}
        </a-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.course-portal-hero {
  display: flex;
  gap: 24px;
  background: var(--ge-bg-container);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.hero-cover {
  flex-shrink: 0;
  width: 320px;
}

.cover-image {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 8px;
}

.cover-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--ge-primary) 0%, var(--ge-primary-hover) 100%);
  border-radius: 8px;
}

.placeholder-icon {
  font-size: 64px;
  color: rgba(255, 255, 255, 0.8);
}

.hero-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.course-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.course-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--ge-text-primary);
  margin: 0;
  line-height: 1.3;
}

.course-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.course-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.course-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-icon {
  color: var(--ge-text-tertiary);
  font-size: 14px;
}

.stat-label {
  color: var(--ge-text-tertiary);
  font-size: 13px;
}

.stat-value {
  color: var(--ge-text-primary);
  font-weight: 600;
  font-size: 16px;
}

.learning-progress {
  padding: 12px 16px;
  background: var(--ge-primary-light);
  border: 1px solid var(--ge-primary-focus);
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 13px;
  color: var(--ge-primary);
  font-weight: 500;
}

.progress-value {
  font-size: 14px;
  color: var(--ge-primary);
  font-weight: 600;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.main-action-btn {
  min-width: 140px;
}

/* 响应式 */
@media (max-width: 1023px) {
  .course-portal-hero {
    flex-direction: column;
  }

  .hero-cover {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
  }

  .course-title {
    font-size: 24px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .main-action-btn {
    width: 100%;
  }
}

@media (max-width: 767px) {
  .course-portal-hero {
    padding: 16px;
    gap: 16px;
  }

  .course-title {
    font-size: 20px;
  }

  .course-stats {
    gap: 16px;
  }
}
</style>
