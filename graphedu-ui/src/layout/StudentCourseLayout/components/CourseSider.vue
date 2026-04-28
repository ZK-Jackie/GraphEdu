<script setup lang="ts">
import { getChapterTree } from '@/api/education/chapter.ts'
import {
  BookOutlined,
  EditOutlined,
  AppstoreOutlined,
  ApartmentOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons-vue'
import CourseChapterMenuItem from './CourseChapterMenuItem.vue'
import { useRoute } from 'vue-router'
import type { ChapterTreeVO } from '@/types/api/chapter.ts'

/**
 * 组件 Props
 */
const props = defineProps<{
  /** 课程 ID */
  courseId: string | number
}>()

/**
 * 当前侧边栏模式：'chapter' = 章节目录，'more' = 更多
 */
const mode = ref<'chapter' | 'more'>('chapter')

/**
 * 章节树数据
 */
const chapterTree = ref<ChapterTreeVO[]>([])
const treeLoading = ref(true)

/**
 * 当前选中的菜单项 key
 */
const selectedKeys = ref<string[]>([])

/**
 * 已展开的子菜单 key
 */
const openKeys = ref<string[]>([])

const emit = defineEmits<{
  /**
   * 请求在 CourseContent 中打开一个路由
   */
  (e: 'openRoute', path: string, title: string): void
  /**
   * 章节被选中时触发
   */
  (e: 'chapterSelect', chapterId: number): void
}>()

/**
 * 加载章节树
 */
onMounted(async () => {
  if (!props.courseId) return
  try {
    const res = await getChapterTree(Number(props.courseId))
    if (res.code === 200) {
      chapterTree.value = res.data ?? []
      // 默认展开第一级有子章节的条目（sub-menu key 为 `sub-{id}`）
      openKeys.value = chapterTree.value
        .filter((c: ChapterTreeVO) => c.children?.length)
        .map((c: ChapterTreeVO) => `sub-${c.chapterId}`)
    }
  } catch (err) {
    console.error('[CourseSider] 加载章节树失败', err)
  } finally {
    treeLoading.value = false
  }
})

/**
 * 点击章节菜单项
 */
const handleChapterSelect = (info: { key: string | number }) => {
  const key = String(info.key)
  selectedKeys.value = [key]
  // key 格式：chapter-{chapterId}
  const chapterId = key.replace('chapter-', '')
  const chapter = findChapter(chapterTree.value, Number(chapterId))
  if (!chapter) return
  const path = `/course/learn/${props.courseId}/chapter/${chapterId}`
  emit('openRoute', path, chapter.chapterName)
  emit('chapterSelect', Number(chapterId))
}

/**
 * 在章节树中查找章节
 */
const findChapter = (tree: ChapterTreeVO[], chapterId: number): ChapterTreeVO | null => {
  for (const node of tree) {
    if (node.chapterId === chapterId) return node
    if (node.children?.length) {
      const found = findChapter(node.children, chapterId)
      if (found) return found
    }
  }
  return null
}

/**
 * 固定的"更多"菜单项（响应式，依赖 props.courseId）
 */
const moreMenuItems = computed(() => [
  {
    key: 'more-knowledge-graph',
    label: '课程知识图谱',
    icon: ApartmentOutlined,
    path: `/course/learn/${props.courseId}/knowledge-graph`,
  },
  {
    key: 'more-learning-path',
    label: '学习路径',
    icon: NodeIndexOutlined,
    path: `/course/learn/${props.courseId}/learning-path`,
  },
  {
    key: 'more-exercises',
    label: '习题',
    icon: EditOutlined,
    path: `/course/learn/${props.courseId}/exercises`,
  },
])

const handleMoreSelect = (info: { key: string | number }) => {
  const key = String(info.key)
  selectedKeys.value = [key]
  const item = moreMenuItems.value.find((m) => m.key === key)
  if (!item) return
  emit('openRoute', item.path, item.label)
}

/**
 * 切换侧边栏模式
 */
const toggleMode = () => {
  mode.value = mode.value === 'chapter' ? 'more' : 'chapter'
  selectedKeys.value = []
}

// ─── 监听路由变化，同步侧边栏高亮 ────────────────────────────────────

const route = useRoute()

/**
 * 根据当前路由路径计算对应的菜单 key 和 mode
 */
const syncSelectedFromRoute = (path: string) => {
  // 匹配章节路由：/course/learn/{courseId}/chapter/{chapterId}
  const chapterMatch = path.match(/\/chapter\/(\d+)/)
  if (chapterMatch) {
    mode.value = 'chapter'
    selectedKeys.value = [`chapter-${chapterMatch[1]}`]
    return
  }

  // 匹配”更多”菜单路由
  const moreKeyMap: Record<string, string> = {
    '/knowledge-graph': 'more-knowledge-graph',
    '/learning-path': 'more-learning-path',
    '/exercises': 'more-exercises',
  }
  for (const [suffix, key] of Object.entries(moreKeyMap)) {
    if (path.endsWith(suffix)) {
      mode.value = 'more'
      selectedKeys.value = [key]
      return
    }
  }

  // 未能匹配则清空高亮
  selectedKeys.value = []
}

watch(
  () => route.path,
  (newPath) => {
    syncSelectedFromRoute(newPath)
  },
  { immediate: true }
)
</script>

<template>
  <div class="course-sider">
    <!-- 菜单内容区 -->
    <div class="sider-menu-area">
      <!-- 章节目录 -->
      <template v-if="mode === 'chapter'">
        <div v-if="treeLoading" class="p-4">
          <a-skeleton active :paragraph="{ rows: 6 }" />
        </div>

        <template v-else-if="chapterTree.length">
          <a-menu
            v-model:selectedKeys="selectedKeys"
            v-model:openKeys="openKeys"
            mode="inline"
            class="chapter-menu"
            @select="handleChapterSelect"
          >
            <CourseChapterMenuItem
              v-for="chapter in chapterTree"
              :key="`chapter-${chapter.chapterId}`"
              :chapter="chapter"
            />
          </a-menu>
        </template>

        <div v-else class="flex flex-col items-center justify-center h-full py-12 text-gray-400">
          <BookOutlined class="text-3xl mb-2" />
          <span class="text-sm">暂无章节</span>
        </div>
      </template>

      <!-- 更多菜单 -->
      <template v-else>
        <a-menu v-model:selectedKeys="selectedKeys" mode="inline" class="more-menu" @select="handleMoreSelect">
          <a-menu-item v-for="item in moreMenuItems" :key="item.key">
            <template #icon>
              <component :is="item.icon" />
            </template>
            {{ item.label }}
          </a-menu-item>
        </a-menu>
      </template>
    </div>

    <!-- 底部切换器 -->
    <div class="sider-switcher" @click="toggleMode">
      <span class="switcher-label">
        {{ mode === 'chapter' ? '章节目录' : '更多' }}
      </span>
      <div class="switcher-action">
        <span class="switcher-hint">
          {{ mode === 'chapter' ? '切换到更多' : '切换到章节目录' }}
        </span>
        <AppstoreOutlined v-if="mode === 'chapter'" class="switcher-icon" />
        <BookOutlined v-else class="switcher-icon" />
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.course-sider {
  @apply flex flex-col h-full overflow-hidden;
}

.sider-menu-area {
  @apply flex-1 overflow-y-auto overflow-x-hidden;
  /* 纤细滚动条 */
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}

.sider-menu-area::-webkit-scrollbar {
  width: 4px;
}

.sider-menu-area::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 2px;
}

/* 章节/更多菜单样式 */
:deep(.chapter-menu),
:deep(.more-menu) {
  border-inline-end: none !important;
  background: transparent !important;
}

:deep(.chapter-menu .ant-menu-item),
:deep(.more-menu .ant-menu-item) {
  @apply text-sm;
}

:deep(.chapter-item-title) {
  @apply text-sm truncate;
  max-width: 160px;
  display: inline-block;
}

/* 底部切换器 */
.sider-switcher {
  @apply flex items-center justify-between px-3 py-2.5
    border-t border-gray-100 dark:border-gray-700
    bg-gray-50 dark:bg-gray-800/50
    cursor-pointer select-none
    hover:bg-gray-100 dark:hover:bg-gray-700/40 transition-colors;
  flex-shrink: 0;
}

.switcher-label {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-300;
}

.switcher-action {
  @apply flex items-center gap-1.5;
}

.switcher-hint {
  @apply text-xs text-gray-400 dark:text-gray-500;
}

.switcher-icon {
  @apply text-gray-400 dark:text-gray-500 text-sm;
}
</style>
