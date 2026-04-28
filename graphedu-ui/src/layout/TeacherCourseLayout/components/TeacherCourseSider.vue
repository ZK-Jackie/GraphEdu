<script setup lang="ts">
import {
  HomeOutlined,
  GlobalOutlined,
  BookOutlined,
  FolderOpenOutlined,
  ShareAltOutlined,
  RobotOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'

/**
 * 组件 Props
 */
const props = defineProps<{
  /** 课程 ID */
  courseId: string | number
}>()

const emit = defineEmits<{
  (e: 'openRoute', path: string, title: string): void
}>()

/**
 * 教师侧边栏固定菜单项（响应式，依赖 props.courseId）
 */
const menuItems = computed(() => [
  {
    key: `teacher-home-${props.courseId}`,
    label: '首页',
    icon: HomeOutlined,
    path: `/course/manage/${props.courseId}`,
  },
  {
    key: `teacher-portal-${props.courseId}`,
    label: '课程门户设置',
    icon: GlobalOutlined,
    path: `/course/manage/${props.courseId}/portal`,
  },
  {
    key: `teacher-chapters-${props.courseId}`,
    label: '章节设置',
    icon: BookOutlined,
    path: `/course/manage/${props.courseId}/chapter`,
  },
  {
    key: `teacher-resources-${props.courseId}`,
    label: '课程资源设置',
    icon: FolderOpenOutlined,
    path: `/course/manage/${props.courseId}/resource`,
  },
  {
    key: `teacher-knowledge-graph-${props.courseId}`,
    label: '课程知识图谱管理',
    icon: ShareAltOutlined,
    path: `/course/manage/${props.courseId}/knowledge-graph`,
  },
  {
    key: `teacher-semantic-graph-${props.courseId}`,
    label: 'AI 问答知识图谱管理',
    icon: RobotOutlined,
    path: `/course/manage/${props.courseId}/semantic-graph`,
  },
  {
    key: `teacher-students-${props.courseId}`,
    label: '学生管理',
    icon: TeamOutlined,
    path: `/course/manage/${props.courseId}/student`,
  },
])

const selectedKeys = ref<string[]>([])
const route = useRoute()

/**
 * 路由变化时同步高亮对应菜单项
 */
watch(
  () => route.path,
  (path) => {
    // 按路径长度降序排列，确保最长（最具体）的路径优先匹配
    const matched = [...menuItems.value]
      .sort((a, b) => b.path.length - a.path.length)
      .find((m) => path.startsWith(m.path))
    selectedKeys.value = matched ? [matched.key] : []
  },
  { immediate: true }
)

const handleSelect = ({ key }: { key: string | number }) => {
  const keyStr = String(key)
  const item = menuItems.value.find((m) => m.key === keyStr)
  if (!item) return
  selectedKeys.value = [keyStr]
  emit('openRoute', item.path, item.label)
}
</script>

<template>
  <div class="teacher-sider">
    <div class="sider-menu-area">
      <a-menu v-model:selectedKeys="selectedKeys" mode="inline" class="teacher-menu" @select="handleSelect">
        <a-menu-item v-for="item in menuItems" :key="item.key">
          <template #icon>
            <component :is="item.icon" />
          </template>
          {{ item.label }}
        </a-menu-item>
      </a-menu>
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.teacher-sider {
  @apply flex flex-col h-full overflow-hidden;
}

.sider-menu-area {
  @apply flex-1 overflow-y-auto overflow-x-hidden;
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

:deep(.teacher-menu) {
  border-inline-end: none !important;
  background: transparent !important;
}

:deep(.teacher-menu .ant-menu-item) {
  @apply text-sm;
}

/* 选中项强调色改为绿色调（教师端标识色） */
:deep(.teacher-menu .ant-menu-item-selected) {
  background-color: rgba(16, 185, 129, 0.1) !important;
}

:deep(.teacher-menu .ant-menu-item-selected .ant-menu-title-content),
:deep(.teacher-menu .ant-menu-item-selected .anticon) {
  @apply text-emerald-600 dark:text-emerald-400;
}
</style>
