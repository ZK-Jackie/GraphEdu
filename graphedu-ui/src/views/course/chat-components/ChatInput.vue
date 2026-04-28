<script setup lang="ts">
/**
 * ChatInput - 聊天输入区域
 *
 * 功能：
 * - 使用 ant-design-x-vue 的 Sender 输入组件
 * - 配置控制区（横向排列）
 * - 联网搜索开关
 * - 图数据库检索开关
 */

import { GlobalOutlined, ApiOutlined, BulbOutlined, BookOutlined } from '@ant-design/icons-vue'
import { Switch, Tooltip } from 'ant-design-vue'
import { Sender } from 'ant-design-x-vue'

/** 配置状态 */
export interface ChatConfig {
  /** 联网搜索 */
  webSearch: boolean
  /** 图数据库检索（对应后端 graphrag） */
  graphrag: boolean
  /** 思考模式 */
  thinkingMode: boolean
  /** 关联课程章节 */
  linkChapter: boolean
}

const props = defineProps<{
  /** 是否正在发送 */
  loading?: boolean
  /** 配置状态 */
  config: ChatConfig
  /** 当前是否有可用的章节 ID */
  chapterAvailable?: boolean
  /** 当前课程是否有可用的知识图谱 */
  graphAvailable?: boolean
}>()

const emit = defineEmits<{
  /** 更新配置 */
  'update:config': [config: ChatConfig]
  /** 发送消息 */
  submit: [content: string]
  /** 取消输入 */
  cancel: []
}>()

// 发送消息
const handleSubmit = (nextContent?: string) => {
  const content = (nextContent || '').trim()
  if (!content || props.loading) {
    return
  }
  emit('submit', content)
}

// 更新配置
const updateConfig = <K extends keyof ChatConfig>(key: K, value: ChatConfig[K]) => {
  emit('update:config', {
    ...props.config,
    [key]: value,
  })
}
</script>

<template>
  <div class="chat-input">
    <!-- 输入框区域 -->
    <Sender
      class="chat-sender"
      :loading="loading"
      :disabled="loading"
      :placeholder="loading ? 'AI 正在思考中...' : '向 AI 学习助手提问...'"
      :on-submit="handleSubmit"
      :on-cancel="() => emit('cancel')"
    />

    <!-- 配置控制区 -->
    <div class="config-panel">
      <div class="config-item">
        <GlobalOutlined class="config-icon" />
        <span class="config-label">联网搜索</span>
        <Switch
          :checked="config.webSearch"
          size="small"
          @change="(checked: any) => updateConfig('webSearch', checked)"
        />
      </div>

      <div class="config-item" :class="{ disabled: !graphAvailable }">
        <ApiOutlined class="config-icon" />
        <span class="config-label">图数据库检索</span>
        <Tooltip
          :title="!graphAvailable ? '当前课程未启用知识图谱' : undefined"
          placement="topRight"
          :getPopupContainer="(trigger: HTMLElement) => trigger.parentElement!"
        >
          <Switch
            :checked="config.graphrag"
            :disabled="!graphAvailable"
            size="small"
            @change="(checked: any) => updateConfig('graphrag', checked)"
          />
        </Tooltip>
      </div>

      <div class="config-item">
        <BulbOutlined class="config-icon" />
        <span class="config-label">深度思考</span>
        <Switch
          :checked="config.thinkingMode"
          size="small"
          @change="(checked: any) => updateConfig('thinkingMode', checked)"
        />
      </div>

      <div class="config-item" :class="{ disabled: !chapterAvailable }">
        <BookOutlined class="config-icon" />
        <span class="config-label">关联章节</span>
        <Tooltip
          :title="!chapterAvailable ? '请先在左侧选择章节' : undefined"
          placement="topRight"
          :getPopupContainer="(trigger: HTMLElement) => trigger.parentElement!"
        >
          <Switch
            :checked="config.linkChapter && chapterAvailable"
            :disabled="!chapterAvailable"
            size="small"
            @change="(checked: any) => updateConfig('linkChapter', checked)"
          />
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.chat-input {
  @apply px-6 py-4;
  @apply bg-white dark:bg-gray-800;
  @apply border-t border-gray-200 dark:border-gray-700;
  @apply rounded-b-xl;
  @apply relative shrink-0;
  z-index: 2;
}

.chat-sender {
  @apply mb-3;
}

.chat-sender :deep(.ant-sender) {
  @apply bg-gray-50 dark:bg-gray-700;
  @apply border border-gray-200 dark:border-gray-600;
  border-radius: 10px;
}

.chat-sender :deep(.ant-sender-textarea) {
  @apply text-gray-900 dark:text-gray-100;
}

/* 配置控制区 */
.config-panel {
  @apply flex items-center gap-4;
  @apply pt-2 pb-3;
  @apply border-t border-gray-100 dark:border-gray-700;
  @apply overflow-x-auto;
  flex-wrap: nowrap;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}

.config-panel::-webkit-scrollbar {
  height: 3px;
}

.config-panel::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 2px;
}

.config-item {
  @apply flex items-center gap-1.5;
  @apply text-xs;
  @apply text-gray-600 dark:text-gray-400;
  @apply shrink-0 whitespace-nowrap;
}

.config-icon {
  @apply text-sm;
}

.config-label {
  @apply text-xs;
}

.config-item.disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
