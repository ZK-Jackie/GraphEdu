/**
 * AI 聊天状态管理
 */

import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  getChatSessionsPage,
  getChatSession,
  getChatSessionMessages,
  deleteChatSession as deleteChatSessionApi,
  updateChatSession,
  sendMessageStream,
  getFirstText,
} from '@/api/education/chat'
import type {
  ChatFeature,
  ChatMessage,
  ChatMessageContent,
  ChatSessionCreateDTO,
  ChatSessionDetailVO,
  ChatSessionListVO,
} from '@/types/api/education/agent.ts'

const useChatStore = defineStore('chat', () => {
  // ========== 状态 ==========
  const sessions = ref<ChatSessionListVO[]>([])
  const currentSession = ref<ChatSessionDetailVO | null>(null)
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const switchingSession = ref(false)
  const sending = ref(false)
  const awaitingResponse = ref(false)
  const activeStreams = ref(0)

  // ========== 计算属性 ==========
  const currentConvId = computed(() => currentSession.value?.convId)
  const hasSessions = computed(() => sessions.value.length > 0)
  const currentMessages = computed(() => messages.value)

  // ========== 方法 ==========

  /**
   * 加载会话列表
   */
  async function loadSessions(courseId?: number) {
    loading.value = true
    try {
      const res = await getChatSessionsPage(courseId)
      if (res.code === 200) {
        sessions.value = res.data?.rows || []
      }
    } catch (error) {
      console.error('[Chat Store] 加载会话列表失败:', error)
      message.error('加载会话列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建新会话
   */
  async function createSession(data: ChatSessionCreateDTO) {
    loading.value = true
    try {
      const res = await (await import('@/api/education/chat')).createChatSession(data)
      if (res.code === 200) {
        const newSession = res.data
        sessions.value.unshift(newSession)
        currentSession.value = newSession
        messages.value = []
        awaitingResponse.value = false
        return newSession
      }
    } catch (error) {
      console.error('[Chat Store] 创建会话失败:', error)
      message.error('创建会话失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 切换会话
   */
  async function switchSession(convId: number) {
    if (sending.value) {
      message.warning('请等待当前消息回复完成后再切换会话')
      return
    }

    switchingSession.value = true
    try {
      const [detailRes, historyRes] = await Promise.all([getChatSession(convId), getChatSessionMessages(convId)])
      if (detailRes.code === 200) {
        currentSession.value = detailRes.data
      }
      if (historyRes.code === 200) {
        messages.value = historyRes.data || []
      }
      awaitingResponse.value = false
    } catch (error) {
      console.error('[Chat Store] 切换会话失败:', error)
      message.error('切换会话失败')
    } finally {
      switchingSession.value = false
    }
  }

  /**
   * 删除会话
   */
  async function deleteSession(convId: number) {
    try {
      const res = await deleteChatSessionApi(convId)
      if (res.code === 200) {
        const index = sessions.value.findIndex((s) => s.convId === convId)
        if (index > -1) {
          sessions.value.splice(index, 1)
        }
        // 如果删除的是当前会话，切换到第一个会话
        if (currentSession.value?.convId === convId) {
          if (sessions.value.length > 0) {
            await switchSession(sessions.value[0]!.convId)
          } else {
            currentSession.value = null
            messages.value = []
          }
        }
        message.success('会话已删除')
      }
    } catch (error) {
      console.error('[Chat Store] 删除会话失败:', error)
      message.error('删除会话失败')
      throw error
    }
  }

  /**
   * 重命名会话
   */
  async function renameSession(convId: number, title: string) {
    try {
      const res = await updateChatSession(convId, title)
      if (res.code === 200) {
        const session = sessions.value.find((s) => s.convId === convId)
        if (session) {
          session.title = title
        }
        if (currentSession.value?.convId === convId) {
          currentSession.value.title = title
        }
        message.success('会话已重命名')
      }
    } catch (error) {
      console.error('[Chat Store] 重命名会话失败:', error)
      message.error('重命名会话失败')
      throw error
    }
  }

  /**
   * 发送消息（流式响应）
   * @param contents 消息内容列表（支持多个 content，如 quote_text + text）
   * @param feature 聊天功能开关
   */
  async function sendMessage(contents: ChatMessageContent[], feature?: ChatFeature, courseId?: number) {
    sending.value = true

    let targetConvId = currentConvId.value
    if (!targetConvId) {
      const created = await createSession({ courseId: courseId ?? currentSession.value?.courseId })
      if (!created?.convId) {
        sending.value = false
        throw new Error('创建会话失败，无法发送消息')
      }
      targetConvId = created.convId
    }

    // 用户消息
    const userMessage: ChatMessage = {
      role: 0, // HUMAN
      conv_id: targetConvId,
      contents,
      feature,
      message_id: `user-${Date.now()}`,
    }
    messages.value.push(userMessage)

    // AI 占位消息（空内容，等待首条响应）
    const aiMessage: ChatMessage = {
      message_id: `placeholder-${Date.now()}`,
      conv_id: targetConvId,
      role: 1, // AI
      contents: [{ type: 'text', text: '' }],
    }
    messages.value.push(aiMessage)
    awaitingResponse.value = true
    activeStreams.value++

    try {
      await sendMessageStream({
        data: { role: 0, conv_id: targetConvId, contents, feature },
        onMessage: (msg) => {
          // 同 ID 消息：合并内容
          const msgId = String(msg.message_id ?? '')
          const existing = messages.value.find((m) => String(m.message_id) === msgId)
          if (existing) {
            const incomingText = getFirstText(msg.contents)
            if (incomingText) {
              // 同 ID + 有文本 → 追加到首个 text content
              const existingFirst = existing.contents[0]
              if (existingFirst && 'text' in existingFirst) {
                existingFirst.text += incomingText
              } else {
                // 首个 content 非 text → 整体替换
                existing.contents = msg.contents
              }
            }
            return
          }

          // 首条 assistant 消息：占位消息认领
          if (msg.role === 1 && getFirstText(aiMessage.contents) === '') {
            aiMessage.message_id = msg.message_id
            aiMessage.contents = msg.contents
            return
          }

          // thinking/tool 等新消息：追加到末尾
          messages.value.push(msg)
        },
        onComplete: () => {
          awaitingResponse.value = false
          activeStreams.value--
          if (activeStreams.value === 0) {
            sending.value = false
          }
        },
        onError: () => {
          awaitingResponse.value = false
          activeStreams.value--
          if (activeStreams.value === 0) {
            sending.value = false
          }
        },
      })
    } catch {
      // onError 回调已处理状态清理时 awaitingResponse 为 false；
      // 仅在 onError 未被调用时（如 fetchEventSource 启动前异常）补偿清理
      if (awaitingResponse.value) {
        awaitingResponse.value = false
        activeStreams.value--
        if (activeStreams.value === 0) {
          sending.value = false
        }
      }
      message.error('发送消息失败')
    }
  }

  function resetToEmptyChat() {
    currentSession.value = null
    messages.value = []
    awaitingResponse.value = false
    activeStreams.value = 0
    sending.value = false
  }

  /**
   * 清空聊天状态
   */
  function clearChat() {
    sessions.value = []
    currentSession.value = null
    messages.value = []
    awaitingResponse.value = false
    activeStreams.value = 0
    sending.value = false
  }

  return {
    // 状态
    sessions,
    currentSession,
    messages,
    loading,
    switchingSession,
    sending,
    awaitingResponse,

    // 计算属性
    currentConvId,
    hasSessions,
    currentMessages,

    // 方法
    loadSessions,
    createSession,
    switchSession,
    deleteSession,
    renameSession,
    sendMessage,
    resetToEmptyChat,
    clearChat,
  }
})

export default useChatStore
