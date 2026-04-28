<script setup lang="ts">
/**
 * ChatMessages - 聊天消息列表区域
 *
 * 功能：
 * - 复用 ant-design-x-vue 的 BubbleList 组件
 * - 气泡式消息显示（用户在右，AI在左）
 * - Markdown 内容渲染
 * - 自动滚动到最新消息
 */
import { BubbleList } from 'ant-design-x-vue'
import type { BubbleListProps } from 'ant-design-x-vue'
import { RobotOutlined, ToolOutlined, UserOutlined } from '@ant-design/icons-vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import type { VNode } from 'vue'
import useAppStore from '@/stores/modules/app'
import QuestionOptionMessage from './QuestionOptionMessage.vue'
import type { ChatMessage, ChatMessageContent } from '@/types/api/education/agent.ts'

const props = defineProps<{
  /** 消息列表 */
  messages: ChatMessage[]
  /** 是否正在发送 */
  loading?: boolean
  /** 是否正在切换会话并加载历史 */
  switching?: boolean
  /** 是否正在等待 AI 首条响应 */
  awaitingResponse?: boolean
}>()

const isEmpty = computed(() => !props.loading && !props.switching && props.messages.length === 0)

const appStore = useAppStore()

// Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
})

// 渲染 Markdown 内容
const renderMarkdown = (content: string) => {
  const html = md.render(content)
  return DOMPurify.sanitize(html)
}

/** 将 ChatMessage 的 role 数字映射为 BubbleList 的角色字符串 */
function roleToKey(role: number | undefined): string {
  if (role === 0) return 'user'
  if (role === 1) return 'assistant'
  if (role === 2) return 'thinking'
  if (role === 3) return 'tool'
  if (role === 4) return 'system'
  return 'assistant'
}

/** 从 ChatMessageContent 中提取文本 */
function getContentText(content: ChatMessageContent): string {
  if ('text' in content && content.text != null) return content.text
  if ('quote_text' in content && content.quote_text) return content.quote_text.content || ''
  if ('question_option' in content && content.question_option) return JSON.stringify(content.question_option)
  return ''
}

/** 根据 ChatMessageContent 类型渲染内容 */
function renderContentItem(content: ChatMessageContent) {
  if (content.type === 'question_option' && 'question_option' in content) {
    const opt = content.question_option
    return h(QuestionOptionMessage, {
      content: JSON.stringify(opt),
      metadata: opt ? { questionOption: opt } : null,
      exerciseId: opt?.exercise_id ?? opt?.exerciseId ?? null,
    })
  }

  if (content.type === 'quote_text' && 'quote_text' in content && content.quote_text) {
    const qt = content.quote_text
    const children: VNode[] = []
    if (qt.quotes?.length) {
      for (const q of qt.quotes) {
        children.push(
          h('blockquote', { class: 'quote-block' }, [
            h('div', { class: 'markdown-content', innerHTML: renderMarkdown(q) }),
          ])
        )
      }
      // 引用来源标注
      if (qt.source) {
        children.push(
          h('div', { class: 'quote-source' }, [
            h('span', { class: 'quote-source-label' }, '来源：'),
            h('span', null, qt.source),
          ])
        )
      }
    }
    if (qt.content) {
      children.push(h('div', { class: 'markdown-content', innerHTML: renderMarkdown(qt.content) }))
    }
    return h('div', { class: 'quote-text-content' }, children)
  }

  const text = getContentText(content)
  return h('div', {
    class: 'markdown-content',
    innerHTML: renderMarkdown(text),
  })
}

/** 渲染整个消息的 contents */
function renderMessageContents(contents: ChatMessageContent[]) {
  const items = contents?.length ? contents.map((c) => renderContentItem(c)) : []
  return h('div', items)
}

// 消息角色配置
const messageRoles: BubbleListProps['roles'] = {
  user: {
    placement: 'end' as const,
    avatar: { icon: h(UserOutlined), style: { background: '#87d068' } },
    messageRender: (content: any) => {
      if (typeof content === 'string') {
        return h('div', {
          class: 'markdown-content',
          innerHTML: renderMarkdown(content),
        })
      }
      // 从 contents 渲染（支持 quote_text + text 等多内容）
      if (content.contents?.length) {
        return renderMessageContents(content.contents)
      }
      const text = content.text || ''
      return h('div', {
        class: 'markdown-content',
        innerHTML: renderMarkdown(text),
      })
    },
  },
  thinking: {
    placement: 'start' as const,
    avatar: { icon: h(RobotOutlined), style: { background: '#e6f7ff', color: '#1890ff' } },
    messageRender: (content: any) => {
      const text = typeof content === 'string' ? content : content.text || ''
      return h('div', { class: 'thinking-message' }, [
        h('div', { class: 'thinking-header' }, [h('span', { class: 'thinking-label' }, '💭 思考中')]),
        h('div', {
          class: 'thinking-content markdown-content',
          innerHTML: renderMarkdown(text),
        }),
      ])
    },
  },
  assistant: {
    placement: 'start' as const,
    avatar: { icon: h(RobotOutlined), style: { background: '#fde3cf' } },
    messageRender: (content: any) => {
      if (typeof content === 'string') {
        return h('div', {
          class: 'markdown-content',
          innerHTML: renderMarkdown(content),
        })
      }

      // 从 contents 渲染
      if (content.contents?.length) {
        return renderMessageContents(content.contents)
      }

      const text = content.text || ''
      if (!text) return h('div')
      return h('div', {
        class: 'markdown-content',
        innerHTML: renderMarkdown(text),
      })
    },
  },
  tool: {
    placement: 'start' as const,
    avatar: { icon: h(ToolOutlined), style: { background: '#fde68a', color: '#7c2d12' } },
    messageRender: (content: any) => {
      let messageBody

      if (typeof content === 'string') {
        messageBody = h('div', {
          class: 'markdown-content',
          innerHTML: renderMarkdown(content),
        })
      } else if (content.contents) {
        messageBody = renderMessageContents(content.contents)
      } else {
        const text = content.text || ''
        messageBody = h('div', {
          class: 'markdown-content',
          innerHTML: renderMarkdown(text),
        })
      }

      return h('div', { class: 'tool-message-card' }, [
        h('div', { class: 'tool-message-title' }, '工具消息'),
        h('div', { class: 'tool-message-body' }, [messageBody]),
      ])
    },
  },
}

// 消息列表项
const messageItems = computed(() =>
  props.messages.map((msg, idx) => ({
    key: msg.message_id,
    role: roleToKey(msg.role),
    content: {
      text: msg.contents?.[0] ? getContentText(msg.contents[0]) : '',
      contents: msg.contents,
    },
    loading: props.awaitingResponse && msg.role === 1 && idx === props.messages.length - 1,
  }))
)

// 自动滚动由 BubbleList 的 auto-scroll 属性处理
</script>

<template>
  <div class="chat-messages" :class="{ 'is-dark': appStore.darkMode }">
    <div v-if="switching" class="loading-state">
      <a-spin size="large" />
      <p class="loading-text">正在加载历史消息...</p>
    </div>
    <div v-if="isEmpty" class="empty-state">
      <h3 class="empty-title">欢迎使用 AI 学习助手</h3>
      <p class="empty-desc">你可以提问课程概念、总结章节重点、解释题目思路，也可以结合引用内容做针对性答疑。</p>
      <ul class="empty-list">
        <li>支持上下文续聊，自动记住当前会话讨论内容</li>
        <li>支持知识图谱和课程内容相关问答</li>
        <li>支持引用文本后进行精确追问</li>
      </ul>
    </div>
    <BubbleList v-else-if="!switching" :roles="messageRoles" :items="messageItems" :auto-scroll="true" />
  </div>
</template>

<style scoped>
@reference '#main.css';

.chat-messages {
  @apply flex-1 overflow-y-auto px-6 py-4;
  min-height: 0;
  background-color: theme('colors.gray.50');
}

.loading-state {
  @apply h-full flex flex-col items-center justify-center;
  @apply text-gray-500 dark:text-gray-400;
}

.loading-text {
  @apply mt-3 mb-0 text-sm;
}

.empty-state {
  @apply h-full flex flex-col justify-center;
  @apply rounded-xl border border-dashed border-gray-300 dark:border-gray-600;
  @apply bg-white/80 dark:bg-gray-800/70;
  @apply px-5 py-6;
}

.empty-title {
  @apply m-0 mb-2 text-base font-semibold text-gray-900 dark:text-gray-100;
}

.empty-desc {
  @apply m-0 mb-3 text-sm text-gray-600 dark:text-gray-300 leading-6;
}

.empty-list {
  @apply m-0 pl-5 text-sm text-gray-600 dark:text-gray-300 leading-6;
}

.dark .chat-messages {
  background-color: theme('colors.gray.900');
}

/* 自定义滚动条 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}

/* Markdown 内容样式 */
.markdown-content {
  @apply prose prose-sm dark:prose-invert max-w-none;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  @apply mt-4 mb-2 font-semibold;
}

.markdown-content :deep(p) {
  @apply my-2;
}

.markdown-content :deep(code) {
  @apply px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-sm;
}

.markdown-content :deep(pre) {
  @apply p-4 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-x-auto;
}

.markdown-content :deep(pre code) {
  @apply bg-transparent p-0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  @apply ml-6 my-2;
}

.markdown-content :deep(li) {
  @apply my-1;
}

.markdown-content :deep(a) {
  @apply text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300;
}

.markdown-content :deep(blockquote) {
  @apply border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic;
}

/* 引用消息样式 */
.quote-text-content {
  @apply flex flex-col gap-2;
}

.quote-block {
  @apply border-l-4 border-blue-300 dark:border-blue-600 pl-3 py-1 m-0;
  @apply bg-blue-50/50 dark:bg-blue-900/20 rounded-r-md;
}

.quote-source {
  @apply text-xs text-gray-500 dark:text-gray-400 italic;
}

.quote-source-label {
  @apply font-medium not-italic;
}

/* Thinking 消息样式 */
.thinking-message {
  @apply rounded-lg border border-blue-200 bg-blue-50 px-4 py-3;
}

.thinking-header {
  @apply mb-2 flex items-center gap-2;
}

.thinking-label {
  @apply text-xs font-semibold text-blue-700;
}

.thinking-content {
  @apply text-sm text-gray-700;
}

.dark .thinking-message {
  @apply border-blue-800 bg-blue-900/20;
}

.dark .thinking-label {
  @apply text-blue-300;
}

.dark .thinking-content {
  @apply text-gray-300;
}

/* 工具消息样式 */
.tool-message-card {
  @apply w-full rounded-lg border;
  border-color: #fbbf24;
  background: #fffbeb;
  @apply px-3 py-2;
}

.tool-message-title {
  @apply text-xs font-semibold mb-2;
  color: #92400e;
}

.tool-message-body {
  @apply text-sm;
}

.dark .tool-message-card {
  border-color: #a16207;
  background: rgba(146, 64, 14, 0.2);
}

.dark .tool-message-title {
  color: #fbbf24;
}
</style>
