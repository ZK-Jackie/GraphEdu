<script setup lang="ts">
import { getCourseDetail } from '@/api/education/course.ts'
import { LeftOutlined } from '@ant-design/icons-vue'
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

watch(
  () => props.courseId,
  async (newId) => {
    if (!newId) return
    loading.value = true
    try {
      const res = await getCourseDetail(Number(newId))
      if (res.code === 200) {
        courseInfo.value = res.data
      }
    } catch (err) {
      console.error('[CourseCover] 加载课程信息失败', err)
    } finally {
      loading.value = false
    }
  },
  { immediate: true }
)

const handleCoverClick = () => {
  router.push(`/learn/course/${props.courseId}/portal`)
}
</script>

<template>
  <!-- 课程封面区域 -->
  <div class="course-cover">
    <!-- 封面图 + 课程名叠加 -->
    <div class="course-cover-image" @click="handleCoverClick">
      <!-- 加载骨架 -->
      <div v-if="loading" class="cover-skeleton" />

      <!-- 封面图片（使用 img 标签确保可靠显示） -->
      <img
        v-if="!loading && courseInfo?.coverUrl"
        :src="courseInfo.coverUrl"
        :alt="courseInfo.courseName"
        class="cover-img"
      />

      <!-- 渐变蒙版 + 课程名 -->
      <div v-if="!loading" class="cover-overlay">
        <div class="cover-title text-white font-semibold text-sm leading-snug line-clamp-2 px-3 pb-3">
          {{ courseInfo?.courseName || '课程学习' }}
        </div>
      </div>

      <!-- 右上角返回图标提示 -->
      <div v-if="!loading" class="cover-back-hint">
        <a-tooltip title="返回课程门户">
          <div class="back-icon-wrap">
            <LeftOutlined class="text-white text-xs" />
          </div>
        </a-tooltip>
      </div>
    </div>

    <!-- 底部折叠按钮行 -->
    <div class="cover-collapse-bar" @click="emit('toggleCollapse')">
      <span class="text-xs text-gray-700 dark:text-gray-300 select-none">
        {{ isCollapsed ? '展开面板' : '收起面板' }}
      </span>
      <component :is="isCollapsed ? 'MenuUnfoldOutlined' : 'MenuFoldOutlined'" class="collapse-icon" />
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.course-cover {
  @apply flex flex-col flex-shrink-0;
}

.course-cover-image {
  @apply relative h-40 cursor-pointer overflow-hidden;
  background-color: #4f46e5;
  background-image: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
  border-radius: 0.75rem 0.75rem 0 0;
  transition: opacity 0.2s;
}

.course-cover-image:hover {
  opacity: 0.9;
}

.cover-img {
  @apply absolute inset-0 w-full h-full;
  object-fit: cover;
}

.cover-skeleton {
  @apply absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse;
}

.cover-overlay {
  @apply absolute inset-0 flex flex-col justify-end;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.65) 0%, transparent 60%);
}

.cover-back-hint {
  @apply absolute top-2 right-2 z-10;
}

.back-icon-wrap {
  @apply w-6 h-6 flex items-center justify-center rounded-full bg-black/30 hover:bg-black/50 transition-colors cursor-pointer;
}

.cover-collapse-bar {
  @apply flex items-center justify-between px-3 py-1.5 border-b border-gray-100 dark:border-gray-700
    bg-gray-50 dark:bg-gray-800/50 cursor-pointer select-none
    hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors;
}

.collapse-icon {
  @apply text-gray-600 dark:text-gray-300 text-sm;
}

.cover-collapse-bar:hover .collapse-icon {
  @apply text-blue-500;
}
</style>
