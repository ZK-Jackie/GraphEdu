<script setup lang="ts">
import { getCourseDetail } from '@/api/education/course.ts'
import { EditOutlined, LeftOutlined } from '@ant-design/icons-vue'
import type { CourseDetailVO } from '@/types/api/education/course.ts'

/**
 * 组件 Props
 */
const props = defineProps<{
  /** 是否折叠左侧面板 */
  isCollapsed: boolean
  /** 课程 ID */
  courseId: string | number
}>()

const emit = defineEmits<{
  (e: 'toggleCollapse'): void
}>()

const router = useRouter()

const courseInfo = ref<CourseDetailVO | null>(null)
const loading = ref(true)
const isHovered = ref(false)

watch(
  () => props.courseId,
  async (newId) => {
    if (!newId) return
    loading.value = true
    try {
      const res = await getCourseDetail(Number(newId))
      if (res.code === 200) courseInfo.value = res.data
    } catch (err) {
      console.error('[TeacherCourseCover] 加载课程信息失败', err)
    } finally {
      loading.value = false
    }
  },
  { immediate: true }
)

/**
 * 点击封面 → 跳到课程门户页
 */
const handleCoverClick = () => {
  router.push(`/learn/course/${props.courseId}/portal`)
}
</script>

<template>
  <div class="teacher-course-cover">
    <!-- 封面图区域 -->
    <div class="cover-image" @mouseenter="isHovered = true" @mouseleave="isHovered = false" @click="handleCoverClick">
      <!-- 加载骨架 -->
      <div v-if="loading" class="cover-skeleton" />

      <!-- 封面图片（使用 img 标签确保可靠显示） -->
      <img
        v-if="!loading && courseInfo?.coverUrl"
        :src="courseInfo.coverUrl"
        :alt="courseInfo.courseName"
        class="cover-img"
      />

      <template v-if="!loading">
        <!-- 课程名称（始终显示在上方） -->
        <div class="cover-title-bar">
          <span class="cover-title-text">{{ courseInfo?.courseName || '课程设计' }}</span>
        </div>

        <!-- 悬停遮罩 + 编辑提示 -->
        <Transition name="fade">
          <div v-if="isHovered" class="cover-hover-overlay">
            <div class="cover-hover-tip">
              <EditOutlined class="mr-1.5" />
              <span>课程门户</span>
            </div>
          </div>
        </Transition>
      </template>

      <!-- 返回课程管理（右上角） -->
      <a-tooltip v-if="!loading" title="返回课程管理" placement="right">
        <div class="back-btn" @click.stop="router.push('/admin/education/course')">
          <LeftOutlined class="text-xs" />
        </div>
      </a-tooltip>
    </div>

    <!-- 折叠控制行 -->
    <div class="cover-collapse-bar" @click="emit('toggleCollapse')">
      <span class="collapse-label">
        {{ isCollapsed ? '展开面板' : '收起面板' }}
      </span>
      <component :is="isCollapsed ? 'MenuUnfoldOutlined' : 'MenuFoldOutlined'" class="collapse-icon" />
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.teacher-course-cover {
  @apply flex flex-col flex-shrink-0;
}

/* 封面图主体 */
.cover-image {
  @apply relative h-40 cursor-pointer overflow-hidden select-none;
  background-color: #059669;
  background-image: linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%);
  border-radius: 0.75rem 0.75rem 0 0;
  transition: transform 0.2s ease;
}

.cover-img {
  @apply absolute inset-0 w-full h-full;
  object-fit: cover;
}

.cover-skeleton {
  @apply absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse;
}

/* 课程名称：叠加在图片上方，始终可见 */
.cover-title-bar {
  @apply absolute top-0 inset-x-0 px-3 pt-3;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.55) 0%, transparent 100%);
  padding-bottom: 1.5rem;
  z-index: 1;
}

.cover-title-text {
  @apply text-white font-semibold text-sm leading-snug line-clamp-2;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* 悬停遮罩 */
.cover-hover-overlay {
  @apply absolute inset-0 flex items-center justify-center;
  background: rgba(0, 0, 0, 0.45);
}

.cover-hover-tip {
  @apply flex items-center text-white text-sm font-medium
    bg-white/20 backdrop-blur-sm px-4 py-1.5 rounded-full;
}

/* 返回按钮（右上角） */
.back-btn {
  @apply absolute top-2 right-2 z-10
    w-6 h-6 flex items-center justify-center
    rounded-full bg-black/30 hover:bg-black/50
    text-white cursor-pointer transition-colors;
}

/* 折叠控制行 */
.cover-collapse-bar {
  @apply flex items-center justify-between px-3 py-1.5
    border-b border-gray-100 dark:border-gray-700
    bg-gray-50 dark:bg-gray-800/50
    cursor-pointer select-none
    hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors;
}

.collapse-label {
  @apply text-xs text-gray-700 dark:text-gray-300;
}

.collapse-icon {
  @apply text-gray-600 dark:text-gray-300 text-sm;
}

.cover-collapse-bar:hover .collapse-icon {
  @apply text-emerald-500;
}

/* 悬停遮罩淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
