<script setup lang="ts">
/**
 * SessionList - 会话列表（全屏覆盖式）
 *
 * 功能：
 * - 左上角返回按钮
 * - 中间标题 "会话列表"
 * - 右上角新建会话按钮
 * - 会话列表（可滚动，按时间排序）
 */

import { LeftOutlined, PlusOutlined, MoreOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { Modal, Spin } from 'ant-design-vue'
import SessionItem from './SessionItem.vue'

import type { ChatSessionListVO } from '@/types/api/education/agent.ts'

const props = defineProps<{
  /** 会话列表 */
  sessions: ChatSessionListVO[]
  /** 当前选中的会话 ID */
  activeConvId?: number
  /** 是否正在加载 */
  loading?: boolean
}>()

const emit = defineEmits<{
  /** 返回聊天页面 */
  back: []
  /** 切换会话 */
  switch: [convId: number]
  /** 创建会话 */
  create: []
  /** 删除会话 */
  delete: [convId: number]
  /** 重命名会话 */
  rename: [convId: number, title: string]
}>()

// 编辑状态
const editingSessionId = ref<number | null>(null)
const editingTitle = ref('')

// 菜单点击处理
const handleMenuClick = (session: ChatSessionListVO, info: { key: string }) => {
  const { key } = info
  if (key === 'rename') {
    startRename(session)
  } else if (key === 'delete') {
    confirmDelete(session)
  }
}

// 开始重命名
const startRename = (session: ChatSessionListVO) => {
  editingSessionId.value = session.convId
  editingTitle.value = session.title || '新对话'
}

// 确认重命名
const confirmRename = () => {
  if (!editingSessionId.value || !editingTitle.value.trim()) {
    return
  }
  emit('rename', editingSessionId.value, editingTitle.value.trim())
  editingSessionId.value = null
  editingTitle.value = ''
}

// 取消重命名
const cancelRename = () => {
  editingSessionId.value = null
  editingTitle.value = ''
}

// 确认删除
const confirmDelete = (session: ChatSessionListVO) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个对话吗？',
    okText: '确认',
    cancelText: '取消',
    onOk: () => {
      emit('delete', session.convId)
    },
  })
}
</script>

<template>
  <div class="session-list">
    <!-- 顶部导航栏 -->
    <div class="session-list-header">
      <button class="back-btn" @click="$emit('back')">
        <LeftOutlined />
        <span>返回</span>
      </button>

      <h2 class="session-list-title">会话列表</h2>

      <button class="create-btn" @click="$emit('create')">
        <PlusOutlined />
        <span>新建</span>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="session-list-content">
      <div v-if="loading" class="loading-state">
        <Spin size="large" />
        <p class="loading-text">正在加载会话...</p>
      </div>

      <div v-if="sessions.length === 0 && !loading" class="empty-state">
        <p class="empty-text">暂无会话记录</p>
        <button class="empty-create-btn" @click="$emit('create')">
          <PlusOutlined />
          创建第一个对话
        </button>
      </div>

      <SessionItem
        v-else-if="!loading"
        v-for="session in sessions"
        :key="session.convId"
        :session="session"
        :active="session.convId === activeConvId"
        :editing="editingSessionId === session.convId"
        :editing-title="editingTitle"
        @click="$emit('switch', session.convId)"
        @update-editing-title="editingTitle = $event"
        @confirm-rename="confirmRename"
        @cancel-rename="cancelRename"
      >
        <template #menu>
          <a-dropdown :trigger="['click']">
            <button class="session-menu-btn">
              <MoreOutlined />
            </button>
            <template #overlay>
              <a-menu @click="(info: any) => handleMenuClick(session, info)">
                <a-menu-item key="rename">
                  <template #icon><EditOutlined /></template>
                  修改标题
                </a-menu-item>
                <a-menu-item key="delete" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </template>
      </SessionItem>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.session-list {
  @apply flex flex-col h-full;
  @apply bg-white dark:bg-gray-800;
}

/* 顶部导航栏 */
.session-list-header {
  @apply flex items-center justify-between px-6 py-4;
  @apply border-b border-gray-200 dark:border-gray-700;
}

.back-btn,
.create-btn {
  @apply flex items-center gap-1 px-3 py-2;
  @apply rounded-lg;
  @apply text-gray-600 dark:text-gray-400;
  @apply hover:bg-gray-100 dark:hover:bg-gray-700;
  @apply transition-colors cursor-pointer;
  border: none;
  outline: none;
}

.session-list-title {
  @apply m-0 text-lg font-semibold;
  @apply text-gray-900 dark:text-gray-100;
}

/* 会话列表内容 */
.session-list-content {
  @apply flex-1 overflow-y-auto;
  @apply px-4 py-2;
}

.loading-state {
  @apply h-full flex flex-col items-center justify-center;
  @apply text-gray-500 dark:text-gray-400;
}

.loading-text {
  @apply mt-3 mb-0 text-sm;
}

/* 自定义滚动条 */
.session-list-content::-webkit-scrollbar {
  width: 6px;
}

.session-list-content::-webkit-scrollbar-track {
  background: transparent;
}

.session-list-content::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600;
  border-radius: 3px;
}

.session-list-content::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}

/* 空状态 */
.empty-state {
  @apply flex flex-col items-center justify-center;
  @apply py-20;
}

.empty-text {
  @apply text-gray-500 dark:text-gray-400;
  @apply mb-4;
}

.empty-create-btn {
  @apply flex items-center gap-2 px-4 py-2;
  @apply rounded-lg;
  @apply bg-blue-500 hover:bg-blue-600;
  @apply text-white;
  @apply transition-colors cursor-pointer;
  border: none;
  outline: none;
}

.session-menu-btn {
  @apply flex items-center justify-center;
  @apply w-8 h-8 rounded;
  @apply text-gray-400 hover:text-gray-600 dark:hover:text-gray-300;
  @apply hover:bg-gray-100 dark:hover:bg-gray-700;
  @apply transition-colors cursor-pointer;
  border: none;
  background: transparent;
  outline: none;
}
</style>
