<script setup lang="ts">
/**
 * StudentCourseLayout - 学生课程学习布局
 *
 * 整体结构：
 *   ┌──────────────── Header ─────────────────┐
 *   │ ┌─────────────┐  ┌──────────────────────┐│
 *   │ │ CourseCover │  │                      ││
 *   │ │─────────────│  │   CourseContent      ││
 *   │ │ CourseSider │  │   (Golden Layout)    ││
 *   │ │             │  │                      ││
 *   │ │   [切换器]  │  │                      ││
 *   │ └─────────────┘  └──────────────────────┘│
 *   └────────────────────────────────────────── ┘
 *
 * 左侧面板：有圆角、不贴紧左边界（带 padding），可折叠
 * 中心区域：Golden Layout 多标签，复用 WorkbenchLayout 方案
 * 右侧聊天：AI 助手聊天面板，自定义展开/收起（非抽屉）
 */
import StudentCourseHeader from './components/StudentCourseHeader.vue'
import { useBreakpoints } from '@/composables/useBreakpoints'
import type { DeviceType } from '@/types/breakpoints'
import useAppStore from '@/stores/modules/app'
import { RightOutlined, CommentOutlined } from '@ant-design/icons-vue'
import { CourseCover, CourseSider, CourseContent } from './components/index.ts'
import CourseChat from '@/views/course/CourseChat.vue'

const router = useRouter()

defineOptions({
  name: 'StudentCourseLayout',
})

// 设备类型适配
const { device, isMobile } = useBreakpoints()
const appStore = useAppStore()
watch(device, (d: DeviceType) => appStore.updateDevice(d), { immediate: true })

// 从路由参数中读取课程 ID（响应式，会随路由变化自动更新）
const route = useRoute()
const courseId = computed(() => (route.params.id as string) || (route.params.courseId as string) || '0')

// 左侧面板折叠状态
const isCollapsed = ref(false)

// 聊天组件状态
const chatVisible = ref(false)

// 当前选中的章节 ID
const activeChapterId = ref<number | undefined>(undefined)

// CourseContent 组件实例，用于接收来自 CourseSider 的打开路由请求
const contentRef = ref<InstanceType<typeof CourseContent> | null>(null)

/**
 * CourseSider 触发打开路由时，转发给 CourseContent
 */
const handleOpenRoute = async (path: string, title: string) => {
  await contentRef.value?.openRoute(path, title)
}

/**
 * 切换折叠状态
 */
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

/**
 * 切换聊天组件
 */
function toggleChat() {
  chatVisible.value = !chatVisible.value
}

/**
 * 关闭聊天组件
 */
function closeChat() {
  chatVisible.value = false
}

/**
 * CourseSider 章节选中回调
 */
const handleChapterSelect = (chapterId: number) => {
  activeChapterId.value = chapterId
}

/**
 * 注册课程子路由（知识图谱、学习路径页面）
 * 这些页面需要作为父路由的子路由注册，才能在 Golden Layout 标签页中渲染
 */
function registerCourseChildRoutes() {
  const parentRoute = route.matched[0]
  if (!parentRoute?.name) return

  const childRoutes = [
    {
      path: 'knowledge-graph',
      name: 'StudentCourseKnowledgeGraph',
      component: () => import('@/views/course/CourseKnowledgeGraphPage.vue'),
      meta: { title: '课程知识图谱' },
    },
    {
      path: 'learning-path',
      name: 'StudentCourseLearningPath',
      component: () => import('@/views/course/CourseLearningPathPage.vue'),
      meta: { title: '学习路径' },
    },
  ]

  for (const child of childRoutes) {
    if (!router.hasRoute(child.name)) {
      router.addRoute(parentRoute.name as string, child)
    }
  }
}

onMounted(() => {
  registerCourseChildRoutes()
})
</script>

<template>
  <div class="student-course-layout">
    <!-- 顶部导航，使用专用的 StudentCourseHeader -->
    <StudentCourseHeader class="student-course-layout-header" :course-id="Number(courseId)" />

    <!-- 主体区域 -->
    <div class="student-course-layout-body">
      <!-- 左侧面板（可折叠，有圆角，不贴紧左边界） -->
      <div class="left-panel" :class="{ collapsed: isCollapsed }">
        <CourseCover :is-collapsed="isCollapsed" :course-id="courseId" @toggle-collapse="toggleCollapse" />
        <CourseSider
          class="flex-1 overflow-hidden"
          :course-id="courseId"
          @open-route="handleOpenRoute"
          @chapter-select="handleChapterSelect"
        />
      </div>

      <!-- 折叠时浮现的「展开」小标签，始终可触达 -->
      <Transition name="slide-in">
        <button v-if="isCollapsed" class="expand-tab" title="展开课程面板" @click="toggleCollapse">
          <RightOutlined class="text-xs" />
        </button>
      </Transition>

      <div class="content-chat-container" :class="{ 'chat-open-desktop': chatVisible && !isMobile }">
        <!-- 中心内容区（Golden Layout 多标签） -->
        <div class="right-panel" v-if="courseId != undefined">
          <CourseContent ref="contentRef" :course-id="courseId" class="h-full w-full" />
        </div>

        <!-- 聊天组件：桌面端压缩中心区，移动端全屏覆盖 -->
        <Transition name="chat-slide">
          <CourseChat
            v-if="chatVisible"
            :course-id="Number(courseId)"
            :chapter-id="activeChapterId"
            :mobile-overlay="isMobile"
            @close="closeChat"
            class="chat-component"
          />
        </Transition>
      </div>

      <!-- 聊天开关按钮（圆形悬浮） -->
      <Transition name="fade-scale">
        <button v-if="!chatVisible" class="chat-toggle-button" title="打开 AI 助手" @click="toggleChat">
          <CommentOutlined />
        </button>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

/* ── 整体布局 ── */
.student-course-layout {
  @apply h-screen flex flex-col w-full overflow-hidden;
  background: theme('colors.gray.100');
}

.dark .student-course-layout {
  background: theme('colors.gray.900');
}

/* ── Header ── */
.student-course-layout-header {
  @apply top-0 left-0 w-full z-50 h-20;
  flex-shrink: 0;
}

/* ── 主体 ── */
.student-course-layout-body {
  @apply relative flex flex-1 overflow-hidden;
  padding: 12px;
  gap: 12px;
  min-height: 0;
}

.content-chat-container {
  @apply relative flex flex-1 min-w-0 min-h-0;
}

/* ── 左侧面板 ── */
.left-panel {
  @apply flex flex-col bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden;
  width: 256px;
  flex-shrink: 0;
  transition:
    width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.left-panel.collapsed {
  width: 0;
  opacity: 0;
}

/* ── 展开标签（仅折叠时显示） ── */
.expand-tab {
  @apply absolute z-20 flex items-center justify-center
  bg-white dark:bg-gray-800
  border border-gray-200 dark:border-gray-600
  rounded-r-lg shadow-md
  hover:bg-gray-50 dark:hover:bg-gray-700
  text-gray-500 dark:text-gray-400
  transition-colors cursor-pointer;
  left: 12px; /* 与 padding-left 对齐 */
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 48px;
  border-left: none;
}

/* ── 展开标签动画 ── */
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

/* ── 聊天组件 ── */
.chat-component {
  @apply h-full z-30;
  @apply flex-shrink-0;
  width: clamp(360px, 28vw, 440px);
}

/* ── 聊天开关按钮（圆形悬浮） ── */
.chat-toggle-button {
  @apply absolute z-20 flex items-center justify-center;
  @apply w-12 h-12 rounded-full;
  @apply bg-blue-500 hover:bg-blue-600;
  @apply text-white shadow-lg;
  @apply transition-all cursor-pointer;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.chat-toggle-button:hover {
  @apply scale-110;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
}

/* ── 聊天组件滑入动画 ── */
.chat-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 1, 1);
}

.chat-slide-enter-from {
  opacity: 0;
  transform: translateX(24px);
}

.chat-slide-leave-to {
  opacity: 0;
  transform: translateX(24px);
}

/* ── 淡入缩放动画（按钮） ── */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: translateY(-50%) scale(0.8);
}

/* ── 右侧内容区 ── */
.right-panel {
  @apply flex-1 bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden;
  min-width: 0;
  min-height: 0;
  height: 100%;
}

@media (max-width: 767px) {
  .chat-component {
    @apply absolute inset-0 w-full h-full;
    max-width: none;
  }
}
</style>
