<script setup lang="ts">
/**
 * ChatHeader - 聊天组件顶部标题栏
 *
 * 功能：
 * - 显示/编辑会话标题（点击标题进入编辑态，blur 保存）
 * - 刷新当前会话消息
 * - 右侧操作按钮（会话列表、全屏、关闭）
 */

import { ref, watch, nextTick } from 'vue'
import {
  HistoryOutlined,
  ExpandOutlined,
  CompressOutlined,
  ReloadOutlined,
  CloseOutlined,
  EditOutlined,
} from '@ant-design/icons-vue'
import { Tooltip, Input } from 'ant-design-vue'

const props = defineProps<{
  /** 是否全屏状态 */
  isFullscreen?: boolean
  /** 当前会话标题 */
  sessionTitle?: string
  /** 是否有活跃会话（无会话时不可编辑） */
  hasActiveSession?: boolean
}>()

const emit = defineEmits<{
  /** 切换到会话列表 */
  toggleSessions: []
  /** 切换全屏 */
  toggleFullscreen: []
  /** 刷新当前会话 */
  refresh: []
  /** 关闭聊天窗口 */
  close: []
  /** 重命名会话 */
  rename: [title: string]
}>()

const isEditing = ref(false)
const editTitle = ref('')
const inputRef = ref<InstanceType<typeof Input> | null>(null)

const startEdit = () => {
  if (!props.hasActiveSession) return
  editTitle.value = props.sessionTitle || ''
  isEditing.value = true
  nextTick(() => (inputRef.value as any)?.focus())
}

const confirmEdit = () => {
  const trimmed = editTitle.value.trim()
  if (trimmed && trimmed !== props.sessionTitle) {
    emit('rename', trimmed)
  }
  isEditing.value = false
}

const cancelEdit = () => {
  isEditing.value = false
}

// 会话切换时退出编辑态
watch(
  () => props.sessionTitle,
  () => {
    isEditing.value = false
  }
)
</script>

<template>
  <div class="chat-header">
    <!-- 正常态：点击进入编辑 -->
    <h2
      v-if="!isEditing"
      class="chat-title"
      :class="{ editable: hasActiveSession }"
      :title="hasActiveSession ? '点击修改标题' : sessionTitle || 'AI 学习助手'"
      @click="startEdit"
    >
      {{ sessionTitle || 'AI 学习助手' }}
      <EditOutlined v-if="hasActiveSession" class="edit-hint" />
    </h2>

    <!-- 编辑态 -->
    <div v-else class="chat-title-edit" @click.stop>
      <Input
        ref="inputRef"
        v-model:value="editTitle"
        size="small"
        class="title-input"
        @blur="confirmEdit"
        @keyup.enter="confirmEdit"
        @keyup.esc="cancelEdit"
      />
    </div>

    <div class="chat-actions">
      <!-- 刷新按钮 -->
      <Tooltip title="刷新">
        <button class="action-btn" @click="$emit('refresh')">
          <ReloadOutlined />
        </button>
      </Tooltip>

      <!-- 会话列表按钮 -->
      <Tooltip title="会话列表">
        <button class="action-btn" @click="$emit('toggleSessions')">
          <HistoryOutlined />
        </button>
      </Tooltip>

      <!-- 展开/收起按钮 -->
      <Tooltip :title="isFullscreen ? '收起' : '展开'">
        <button class="action-btn" @click="$emit('toggleFullscreen')">
          <CompressOutlined v-if="isFullscreen" />
          <ExpandOutlined v-else />
        </button>
      </Tooltip>

      <!-- 关闭按钮 -->
      <Tooltip title="关闭">
        <button class="action-btn close-btn" @click="$emit('close')">
          <CloseOutlined />
        </button>
      </Tooltip>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.chat-header {
  @apply flex items-center justify-between px-6 py-4;
  @apply border-b border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
  @apply rounded-t-xl;
}

.chat-title {
  @apply m-0 text-base font-semibold;
  @apply text-gray-900 dark:text-gray-100;
  @apply flex-1 min-w-0 truncate;
  @apply text-left;
}

.chat-title.editable {
  @apply cursor-pointer;
  @apply hover:text-blue-600 dark:hover:text-blue-400;
}

.edit-hint {
  @apply ml-1.5 text-xs opacity-0 transition-opacity;
}

.chat-title.editable:hover .edit-hint {
  @apply opacity-60;
}

.chat-title-edit {
  @apply flex-1 min-w-0 mr-3;
}

.title-input {
  @apply font-semibold;
}

.chat-actions {
  @apply flex items-center gap-1;
  @apply flex-shrink-0;
}

.action-btn {
  @apply flex items-center justify-center;
  @apply w-9 h-9 rounded-lg;
  @apply text-gray-600 dark:text-gray-400;
  @apply hover:bg-gray-100 dark:hover:bg-gray-700;
  @apply transition-colors cursor-pointer;
  border: none;
  outline: none;
}

.action-btn:hover {
  @apply text-gray-900 dark:text-gray-100;
}

.action-btn.close-btn:hover {
  @apply bg-red-50 dark:bg-red-900/20;
  @apply text-red-500 dark:text-red-400;
}
</style>
