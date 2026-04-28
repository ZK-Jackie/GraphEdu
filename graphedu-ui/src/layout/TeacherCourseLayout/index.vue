<script setup lang="ts">
/**
 * TeacherCourseLayout - 教师课程设计布局
 *
 * 整体结构：
 *   ┌──────────────── Header ──────────────────┐
 *   │ ┌──────────────┐  ┌─────────────────────┐│
 *   │ │TeacherCourse │  │                     ││
 *   │ │    Cover     │  │   CourseContent     ││
 *   │ │──────────────│  │   (Golden Layout)   ││
 *   │ │TeacherCourse │  │                     ││
 *   │ │    Sider     │  │                     ││
 *   │ │  (固定菜单)  │  │                     ││
 *   │ └──────────────┘  └─────────────────────┘│
 *   └───────────────────────────────────────────┘
 *
 * - 左侧面板圆角，不贴紧边界，可折叠
 * - 菜单项：首页、课程门户设置、章节设置、习题设置、资源设置
 * - 路由格式：/admin/course/{courseId}/xxx（admin 场景）
 */
import Header from '@/components/Header/index.vue'
import { useBreakpoints } from '@/composables/useBreakpoints'
import type { DeviceType } from '@/types/breakpoints'
import useAppStore from '@/stores/modules/app'
import { RightOutlined } from '@ant-design/icons-vue'
import { TeacherCourseCover, TeacherCourseSider, CourseContent } from './components/index.ts'

defineOptions({
  name: 'TeacherCourseLayout',
})

const { device } = useBreakpoints()
const appStore = useAppStore()
watch(device, (d: DeviceType) => appStore.updateDevice(d), { immediate: true })

// 从路由参数读取课程 ID（admin 场景路由格式：/admin/course/:courseId/...）
const route = useRoute()
const courseId = computed(() => (route.params.id as string) || (route.params.courseId as string) || '0')

// 左侧面板折叠状态
const isCollapsed = ref(false)

// CourseContent 组件实例
const contentRef = ref<InstanceType<typeof CourseContent> | null>(null)

const handleOpenRoute = async (path: string, title: string) => {
  await contentRef.value?.openRoute(path, title)
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<template>
  <div class="teacher-course-layout">
    <Header class="teacher-course-layout-header" :show-menu="false" />

    <div class="teacher-course-layout-body">
      <!-- 左侧面板 -->
      <div class="left-panel" :class="{ collapsed: isCollapsed }">
        <TeacherCourseCover :is-collapsed="isCollapsed" :course-id="courseId" @toggle-collapse="toggleCollapse" />
        <TeacherCourseSider class="flex-1 min-h-0" :course-id="courseId" @open-route="handleOpenRoute" />
      </div>

      <!-- 折叠时的展开标签 -->
      <Transition name="slide-in">
        <button v-if="isCollapsed" class="expand-tab" title="展开课程面板" @click="toggleCollapse">
          <RightOutlined class="text-xs" />
        </button>
      </Transition>

      <!-- 右侧内容区 -->
      <div class="right-panel" v-if="courseId != undefined">
        <CourseContent ref="contentRef" :course-id="courseId" class="h-full w-full" />
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.teacher-course-layout {
  @apply h-screen flex flex-col w-full overflow-hidden;
  background: var(--ge-bg-page);
}

.teacher-course-layout-header {
  @apply top-0 left-0 w-full z-50 h-20;
  flex-shrink: 0;
}

.teacher-course-layout-body {
  @apply relative flex flex-1 overflow-hidden;
  padding: 12px;
  gap: 12px;
  min-height: 0;
}

/* 左侧面板 */
.left-panel {
  @apply flex flex-col rounded-xl shadow-md overflow-hidden;
  background: var(--ge-bg-container);
  width: 256px;
  flex-shrink: 0;
  min-height: 0;
  transition:
    width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.left-panel.collapsed {
  width: 0;
  opacity: 0;
}

/* 展开标签（折叠时显示） */
.expand-tab {
  @apply absolute z-20 flex items-center justify-center
    rounded-r-lg shadow-md
    transition-colors cursor-pointer;
  background: var(--ge-bg-container);
  border: 1px solid var(--ge-border-color);
  color: var(--ge-text-secondary);
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 48px;
  border-left: none;
}

.expand-tab:hover {
  background: var(--ge-bg-elevated);
}

.slide-in-enter-active,
.slide-in-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.slide-in-enter-from,
.slide-in-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(-4px);
}

/* 右侧内容区 */
.right-panel {
  @apply flex-1 rounded-xl shadow-md overflow-hidden;
  background: var(--ge-bg-container);
  min-width: 0;
  height: calc(100vh - calc(var(--spacing) * 20) - 24px);
}
</style>
