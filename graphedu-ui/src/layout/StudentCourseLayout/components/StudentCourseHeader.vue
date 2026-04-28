<script setup lang="ts">
/**
 * StudentCourseHeader - 学生课程学习布局专用头部导航栏
 *
 * 设计思路：
 * - 复用原有 Header 的左侧（Logo）和右侧（工具按钮）
 * - 中央区域集成知识图谱和学习路径组件，支持切换
 * - 保持与原有 Header 相同的视觉风格和交互
 */
import { Divider } from 'ant-design-vue'
import GithubIcon from '@/components/Header/components/GithubIcon.vue'
import DarkModeToggle from '@/components/Header/components/DarkModeToggle.vue'
import UserAvatar from '@/components/Header/components/UserAvatar.vue'
import Logo from '@/components/Header/components/Logo.vue'
import CourseKnowledgeGraph from '@/layout/StudentCourseLayout/components/CourseKnowledgeGraph.vue'
import CourseLearningPath from '@/layout/StudentCourseLayout/components/CourseLearningPath.vue'

interface Props {
  courseId: number | string
}

defineProps<Props>()

// 中部视图切换：知识图谱 / 学习路径
const activeView = ref<'knowledgeGraph' | 'learningPath'>('knowledgeGraph')
</script>

<template>
  <nav class="student-course-header">
    <!-- 左侧：Logo -->
    <div class="header-left">
      <Logo class="header-logo" />
    </div>

    <!-- 中央：知识图谱 / 学习路径 -->
    <div class="header-center">
      <!-- 切换标签 -->
      <div class="view-switcher">
        <button
          class="switcher-tab"
          :class="{ active: activeView === 'knowledgeGraph' }"
          @click="activeView = 'knowledgeGraph'"
        >
          知识图谱
        </button>
        <button
          class="switcher-tab"
          :class="{ active: activeView === 'learningPath' }"
          @click="activeView = 'learningPath'"
        >
          学习路径
        </button>
      </div>
      <!-- 条件渲染：v-show 保持状态 -->
      <CourseKnowledgeGraph v-show="activeView === 'knowledgeGraph'" :course-id="Number(courseId)" />
      <CourseLearningPath v-show="activeView === 'learningPath'" :course-id="Number(courseId)" />
    </div>

    <!-- 右侧：工具按钮 -->
    <div class="header-right">
      <GithubIcon class="nav-item" />
      <Divider type="vertical" class="nav-divider" />
      <DarkModeToggle class="nav-item" />
      <Divider type="vertical" class="nav-divider" />
      <UserAvatar class="nav-item" />
    </div>
  </nav>
</template>

<style scoped>
@reference '#main.css';

.student-course-header {
  @apply shadow-md pt-2 pb-1 px-5 flex justify-between items-center;
  background: var(--ge-bg-container);
  gap: 16px;
}

.header-left {
  @apply flex items-center;
}

.header-center {
  @apply flex-1 flex justify-center items-center gap-2;
  max-width: 860px;
  min-width: 0;
}

.header-right {
  @apply flex items-center h-full;
}

.nav-item {
  @apply px-2 h-10 rounded-md
  cursor-pointer
  flex items-center justify-center
  border-none bg-transparent
  transition-all duration-200 ease-out;
}

.nav-item:hover {
  background: var(--ge-bg-elevated);
}

.nav-divider {
  @apply h-6;
  background: var(--ge-border-color);
}

/* 切换标签 */
.view-switcher {
  @apply flex-shrink-0 flex items-center gap-0.5 rounded-full p-0.5;
  background: var(--ge-bg-elevated);
}

.switcher-tab {
  @apply px-3 py-1 text-xs rounded-full cursor-pointer;
  @apply border-none bg-transparent;
  @apply transition-all duration-200 ease-out;
  color: var(--ge-text-tertiary);
  white-space: nowrap;
}

.switcher-tab:hover {
  color: var(--ge-text-primary);
}

.switcher-tab.active {
  background: var(--ge-bg-container);
  color: var(--ge-primary);
  @apply shadow-sm font-medium;
}
</style>
