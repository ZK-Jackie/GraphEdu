<script setup lang="ts">
/**
 * SessionItem - 会话项组件
 *
 * 功能：
 * - 显示会话标题
 * - 显示最后消息时间
 * - 选中状态高亮
 * - 编辑状态
 */
import { Input } from 'ant-design-vue'

import type { ChatSessionListVO } from '@/types/api/education/agent.ts'

const props = defineProps<{
  /** 会话数据 */
  session: ChatSessionListVO
  /** 是否选中 */
  active?: boolean
  /** 是否正在编辑 */
  editing?: boolean
  /** 编辑中的标题 */
  editingTitle?: string
}>()

const emit = defineEmits<{
  /** 点击会话 */
  click: []
  /** 更新编辑中的标题 */
  'update-editing-title': [title: string]
  /** 确认重命名 */
  confirmRename: []
  /** 取消重命名 */
  cancelRename: []
}>()

defineSlots<{
  /** 操作菜单 */
  menu?: () => void
}>()

// 本地编辑状态
const localEditTitle = ref(props.editingTitle || '')
const editInputRef = ref<InstanceType<typeof Input> | null>(null)

// 监听编辑状态变化，自动聚焦输入框
watch(
  () => props.editing,
  (isEditing) => {
    if (isEditing) {
      localEditTitle.value = props.editingTitle || ''
      nextTick(() => {
        (editInputRef.value as any)?.focus()
      })
    }
  }
)

// 更新编辑标题
const handleUpdateEditTitle = (e: Event) => {
  const target = e.target as HTMLInputElement
  localEditTitle.value = target.value
  emit('update-editing-title', target.value)
}

// 确认编辑
const handleConfirmEdit = () => {
  if (localEditTitle.value.trim()) {
    emit('confirmRename')
  }
}

// 取消编辑
const handleCancelEdit = () => {
  emit('cancelRename')
}

// 格式化时间（详细：日期 + 时分）
const formatTime = (timeStr: string) => {
  const time = new Date(timeStr)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - time.getTime()) / (1000 * 60 * 60 * 24))

  const timeStr_ = time.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  const dateStr_ = time.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })

  if (diffDays === 0) {
    return `今天 ${timeStr_}`
  }
  if (diffDays === 1) {
    return `昨天 ${timeStr_}`
  }
  if (diffDays < 7) {
    return `${dateStr_} ${timeStr_}`
  }
  const fullDate = time.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' })
  return `${fullDate} ${timeStr_}`
}
</script>

<template>
  <div class="session-item" :class="{ active }" @click="!editing && $emit('click')">
    <!-- 正常状态 -->
    <template v-if="!editing">
      <div class="session-item-main">
        <h3 class="session-title">{{ session.title || '新对话' }}</h3>
        <p class="session-time">{{ formatTime(session.lastMessageTime) }}</p>
      </div>

      <div class="session-item-actions" @click.stop>
        <span class="session-id">#{{ session.convId }}</span>
        <slot name="menu" />
      </div>
    </template>

    <!-- 编辑状态 -->
    <template v-else>
      <div class="session-edit-wrapper" @click.stop>
        <Input
          ref="editInputRef"
          :value="localEditTitle"
          placeholder="请输入对话标题"
          size="small"
          class="session-edit-input"
          @input="handleUpdateEditTitle"
          @blur="handleConfirmEdit"
          @keyup.enter="handleConfirmEdit"
          @keyup.esc="handleCancelEdit"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
@reference '#main.css';

.session-item {
  @apply flex items-center justify-between px-4 py-3;
  @apply rounded-lg;
  @apply transition-colors cursor-pointer;
  @apply hover:bg-gray-50 dark:hover:bg-gray-700;
}

.session-item.active {
  @apply bg-blue-50 dark:bg-blue-900/20;
  @apply border border-blue-200 dark:border-blue-800;
}

.session-item-main {
  @apply flex-1 min-w-0;
}

.session-title {
  @apply m-0 text-sm font-medium truncate;
  @apply text-gray-900 dark:text-gray-100;
}

.session-time {
  @apply m-0 text-xs mt-1;
  @apply text-gray-500 dark:text-gray-400;
}

.session-item-actions {
  @apply flex items-center gap-1;
  @apply ml-2;
}

.session-id {
  @apply text-xs;
  @apply text-gray-400 dark:text-gray-500;
  @apply font-mono;
  user-select: none;
}

/* 编辑状态 */
.session-edit-wrapper {
  @apply flex items-center gap-2 w-full;
}

.session-edit-input {
  @apply flex-1;
}
</style>
