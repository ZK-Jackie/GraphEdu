<script setup lang="ts">
/**
 * CourseChat - 课程 AI 聊天组件（重构版）
 *
 * 功能：
 * - 会话管理（创建、切换、删除、重命名）
 * - 消息发送与接收
 * - 思维链展示
 * - Markdown 渲染
 * - 流式响应
 * - 文本引用
 * - 配置控制（联网搜索、图数据库检索）
 *
 * 架构：
 * - 使用自定义组件替代 ant-design-x-vue 的 Conversations
 * - 全屏覆盖式会话列表
 * - 气泡式消息显示
 * - 灰色长条引用区域
 */

import { ref, onMounted, watch, computed } from 'vue'
import useChatStore from '@/stores/modules/chat'
import useQuoteStore from '@/stores/modules/quote'
import { getVisibleKnowledgeGraphList } from '@/api/education/knowledge-graph'
import { isMockEnabled } from '@/mock'
import type { ChatConfig } from './chat-components/ChatInput.vue'

// 子组件
import ChatHeader from './chat-components/ChatHeader.vue'
import ChatMessages from './chat-components/ChatMessages.vue'
import QuoteArea from './chat-components/QuoteArea.vue'
import ChatInput from './chat-components/ChatInput.vue'
import SessionList from './chat-components/SessionList.vue'

const props = defineProps<{
  /** 课程 ID（用于加载课程相关的聊天会话） */
  courseId?: number
  /** 当前关联的章节 ID（用于题库查询等章节级功能） */
  chapterId?: number
  /** 是否为移动端覆盖模式 */
  mobileOverlay?: boolean
}>()

const emit = defineEmits<{
  /** 关闭聊天窗口 */
  close: []
}>()

// ========== 路由 ==========

const route = useRoute()

// 从 URL 路径中提取 chapterId：匹配 .../chapter/{chapterId}
const chapterIdFromUrl = computed(() => {
  const match = route.path.match(/\/chapter\/(\d+)/)
  return match ? Number(match[1]) : undefined
})

// 实际使用的 chapterId：以 URL 为唯一来源，确保切换标签页后状态同步
const effectiveChapterId = computed(() => chapterIdFromUrl.value)

// ========== 状态 ==========

// 视图状态：chat（聊天页面） | sessions（会话列表）
const viewState = ref<'chat' | 'sessions'>('chat')

// 全屏状态
const isFullscreen = ref(false)

// 配置状态
const config = ref<ChatConfig>({
  webSearch: false,
  graphrag: false,
  thinkingMode: false,
  linkChapter: false,
})

// 知识图谱可用性
const graphAvailable = ref(false)

const sessionsLoaded = ref(false)

const checkGraphAvailability = async () => {
  if (!props.courseId) {
    graphAvailable.value = false
    return
  }
  try {
    const res = await getVisibleKnowledgeGraphList(props.courseId)
    graphAvailable.value = (res.data?.rows?.length ?? 0) > 0
  } catch {
    graphAvailable.value = false
  }
}

// ========== Store ==========

const chatStore = useChatStore()
const quoteStore = useQuoteStore()

// ========== 计算属性 ==========

// 当前消息列表（包含流式响应）
const displayMessages = computed(() => chatStore.currentMessages)
const currentSessionTitle = computed(() => chatStore.currentSession?.title || 'AI 学习助手')

// ========== 事件处理 ==========

// 切换到会话列表
const handleToggleSessions = () => {
  viewState.value = 'sessions'
  if (!sessionsLoaded.value && !chatStore.loading) {
    void chatStore.loadSessions(props.courseId).then(() => {
      sessionsLoaded.value = true
    })
  }
}

// 切换全屏
const handleToggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

// 刷新当前会话
const handleRefresh = () => {
  if (chatStore.currentConvId) {
    void chatStore.switchSession(chatStore.currentConvId)
  }
}

// 发送消息
const handleSubmit = async (content: string) => {
  if (!content.trim() || chatStore.sending) {
    return
  }
  // 获取引用内容并转换为 ChatMessageContent[]
  const quoteContents = quoteStore.toMessageContents(content)
  // 构造 contents：有引用时使用引用+文本，无引用时使用纯文本
  const contents = quoteContents ?? [{ type: 'text' as const, text: content }]
  // 将 ChatConfig 转换为后端 ChatFeature 格式
  const feature = {
    graphrag: config.value.graphrag,
    web_search: config.value.webSearch ? ('enable' as const) : ('disable' as const),
    thinking_mode: config.value.thinkingMode ? ('enable' as const) : ('disable' as const),
    ...(config.value.linkChapter && effectiveChapterId.value ? { chapter_id: effectiveChapterId.value } : {}),
  }
  await chatStore.sendMessage(contents, feature, props.courseId)
  // 发送后清空引用
  quoteStore.clearQuotes()
}

// 创建新会话
const handleCreateSession = async () => {
  await chatStore.createSession({ courseId: props.courseId })
  // 创建后返回聊天页面
  viewState.value = 'chat'
}

// 切换会话
const handleSwitchSession = (convId: number) => {
  viewState.value = 'chat'
  void chatStore.switchSession(convId)
}

// 删除会话
const handleDeleteSession = async (convId: number) => {
  await chatStore.deleteSession(convId)
}

// 重命名会话
const handleRenameSession = async (convId: number, title: string) => {
  await chatStore.renameSession(convId, title)
}

// 重命名当前会话标题
const handleRenameCurrentSession = async (title: string) => {
  if (chatStore.currentConvId) {
    await chatStore.renameSession(chatStore.currentConvId, title)
  }
}

// 监听课程 ID 变化，重新加载会话
watch(
  () => props.courseId,
  () => {
    sessionsLoaded.value = false
    chatStore.resetToEmptyChat()
    config.value.linkChapter = false
    void checkGraphAvailability()
  }
)

// 监听有效的章节 ID 变化，清空章节关联
watch(effectiveChapterId, () => {
  if (!effectiveChapterId.value) {
    config.value.linkChapter = false
  }
})

// ========== 生命周期 ==========

onMounted(async () => {
  chatStore.resetToEmptyChat()
  await checkGraphAvailability()

  // Mock 模式：自动加载并切换到 mock 会话
  if (isMockEnabled()) {
    try {
      await chatStore.loadSessions(props.courseId)
      sessionsLoaded.value = true
      if (chatStore.sessions.length > 0) {
        await chatStore.switchSession(chatStore.sessions[0]!.convId)
      }
    } catch {
      // 忽略 mock 加载失败
    }
  }
})
</script>

<template>
  <div class="course-chat" :class="{ fullscreen: isFullscreen, 'mobile-overlay': props.mobileOverlay }">
    <!-- 聊天页面 -->
    <Transition name="slide-fade" mode="out-in">
      <div v-if="viewState === 'chat'" key="chat" class="chat-view">
        <!-- 顶部标题栏 -->
        <ChatHeader
          :is-fullscreen="isFullscreen"
          :session-title="currentSessionTitle"
          :has-active-session="!!chatStore.currentConvId"
          @toggle-sessions="handleToggleSessions"
          @toggle-fullscreen="handleToggleFullscreen"
          @refresh="handleRefresh"
          @rename="handleRenameCurrentSession"
          @close="emit('close')"
        />

        <!-- 消息列表区域 -->
        <ChatMessages
          :messages="displayMessages"
          :loading="chatStore.sending"
          :switching="chatStore.switchingSession"
          :awaiting-response="chatStore.awaitingResponse"
          class="chat-messages"
        />

        <!-- 引用内容区域 -->
        <QuoteArea
          :quotes="quoteStore.quotes"
          @clear="quoteStore.clearQuotes"
          @remove="quoteStore.removeQuote"
          class="quote-area"
        />

        <!-- 输入区域 -->
        <ChatInput
          :loading="chatStore.sending"
          :config="config"
          :chapter-available="!!effectiveChapterId"
          :graph-available="graphAvailable"
          @update:config="config = $event"
          @submit="handleSubmit"
          @cancel="() => {}"
          class="chat-input-area"
        />
      </div>

      <!-- 会话列表页面 -->
      <SessionList
        v-else
        key="sessions"
        :sessions="chatStore.sessions"
        :active-conv-id="chatStore.currentConvId"
        :loading="chatStore.loading"
        @back="viewState = 'chat'"
        @switch="handleSwitchSession"
        @create="handleCreateSession"
        @delete="handleDeleteSession"
        @rename="handleRenameSession"
        class="session-list-view"
      />
    </Transition>
  </div>
</template>

<style scoped>
@reference '#main.css';

/* 主容器 */
.course-chat {
  @apply relative;
  @apply flex flex-col;
  @apply bg-white dark:bg-gray-800;
  @apply rounded-xl shadow-xl;
  @apply h-full w-full;
  min-height: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  overflow: hidden;
}

.course-chat.fullscreen {
  @apply absolute inset-0 rounded-xl;
  z-index: 110;
}

.course-chat.mobile-overlay {
  @apply rounded-xl;
}

/* 聊天页面 */
.chat-view {
  @apply flex flex-col h-full;
  min-height: 0;
}

.chat-messages {
  @apply flex-1;
  min-height: 0;
}

.quote-area {
  @apply flex-shrink-0;
}

.chat-input-area {
  @apply flex-shrink-0;
}

/* 会话列表页面 */
.session-list-view {
  @apply h-full min-h-0;
  @apply rounded-xl;
  overflow: hidden;
}

/* 视图切换动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 深色模式适配 */
.dark .course-chat {
  @apply shadow-2xl;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
}

@media (max-width: 767px) {
  .course-chat {
    @apply rounded-none;
  }

  .course-chat.mobile-overlay {
    @apply rounded-xl;
  }
}
</style>
