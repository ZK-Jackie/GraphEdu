/**
 * AI 聊天相关 API
 */

import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common'
import type { PageResponse } from '@/types/api/common'
import { ViteEnv } from '@/constants'
import { getToken } from '@/utils/token'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import type {
  ChatMessage,
  ChatMessageContent,
  ChatSessionCreateDTO,
  ChatSessionDetailVO,
  ChatSessionListVO,
} from '@/types/api/education/agent.ts'
import { isMockEnabled, mockPageResponse, mockResponse } from '@/mock'
import { MOCK_CONV_ID } from '@/mock/chat'
import * as mockChat from '@/mock/chat'

// ============================================================================
// 内部辅助函数
// ============================================================================

/**
 * 从 contents 中提取首条文本内容
 */
function getFirstText(contents: ChatMessageContent[]): string {
  const item = contents?.[0]
  if (!item) return ''
  if (item.type === 'text') return item.text
  if (item.type === 'quote_text' && item.quote_text) return item.quote_text.content || ''
  if (item.type === 'question_option' && item.question_option) return JSON.stringify(item.question_option)
  return ''
}

/**
 * 将后端 SSE 原始数据直接透传，返回 ChatMessage（snake_case）
 */
function parseSSEToChatMessage(raw: any): ChatMessage {
  const contents = raw.contents ?? []
  return {
    role: raw.role ?? 0,
    contents,
    user_id: raw.user_id,
    conv_id: raw.conv_id,
    message_id: raw.message_id,
  }
}

// ============================================================================
// API 函数
// ============================================================================

/**
 * 获取当前用户的会话列表
 * GET /education/chat/sessions
 */
export function getChatSessions(courseId?: number): Promise<ResponseType<ChatSessionListVO[]>> {
  return request({
    url: '/education/chat/sessions',
    method: 'get',
    params: { courseId },
  })
}

export function getChatSessionsPage(courseId?: number): Promise<ResponseType<PageResponse<ChatSessionListVO>>> {
  if (isMockEnabled()) {
    const rows = mockChat.getMockSessionList()
    return Promise.resolve(mockPageResponse(rows, rows.length))
  }
  return request({
    url: '/education/chat/sessions',
    method: 'get',
    params: { courseId },
  })
}

/**
 * 创建新会话
 * POST /education/chat/sessions
 */
export function createChatSession(data: ChatSessionCreateDTO): Promise<ResponseType<ChatSessionDetailVO>> {
  return request({
    url: '/education/chat/sessions',
    method: 'post',
    data,
  })
}

/**
 * 获取会话详情及消息历史
 * GET /education/chat/sessions/{conv_id}
 */
export function getChatSession(convId: number): Promise<ResponseType<ChatSessionDetailVO>> {
  if (isMockEnabled() && convId === MOCK_CONV_ID) return Promise.resolve(mockResponse(mockChat.getMockSessionDetail()))
  return request({
    url: `/education/chat/sessions/${convId}`,
    method: 'get',
  })
}

/**
 * 获取会话消息历史
 * GET /education/chat/sessions/{conv_id}/messages
 */
export function getChatSessionMessages(convId: number): Promise<ResponseType<ChatMessage[]>> {
  if (isMockEnabled() && convId === MOCK_CONV_ID)
    return Promise.resolve(mockResponse(mockChat.getMockSessionMessages()))
  return request({
    url: `/education/chat/sessions/${convId}/messages`,
    method: 'get',
  })
}

/**
 * 删除会话
 * DELETE /education/chat/sessions/{conv_id}
 */
export function deleteChatSession(convId: number): Promise<ResponseType<void>> {
  return request({
    url: `/education/chat/sessions/${convId}`,
    method: 'delete',
  })
}

/**
 * 更新会话标题
 * PUT /education/chat/sessions/{conv_id}
 */
export function updateChatSession(convId: number, title: string): Promise<ResponseType<void>> {
  return request({
    url: `/education/chat/sessions/${convId}`,
    method: 'put',
    data: { title },
  })
}

/**
 * 发送消息（流式响应）
 * POST /education/chat/messages/stream
 *
 * 使用 @microsoft/fetch-event-source 处理 SSE 流式响应。
 * 对同类文本消息做缓冲合并，减少 Vue 响应式更新频率。
 */
export function sendMessageStream(params: {
  data: ChatMessage
  onMessage: (message: ChatMessage) => void
  onComplete?: (payload?: { conv_id?: number }) => void
  onError?: (error: Error) => void
}): Promise<void> {
  const { data, onMessage, onComplete, onError } = params

  // ---- 文本缓冲：按 message_id 聚合同 ID 的文本片段，定时刷出 ----
  const flushInterval = 60 // ms
  const textBuffer = new Map<string, string>() // msgId -> 累积文本
  const msgCache = new Map<string, ChatMessage>() // msgId -> 最新原始消息（用于非文本字段）
  let flushTimer: ReturnType<typeof setInterval> | null = null

  function startFlushLoop() {
    if (flushTimer) return
    flushTimer = setInterval(flushBuffer, flushInterval)
  }

  function flushBuffer() {
    if (textBuffer.size === 0) return
    for (const [msgId, accumulated] of textBuffer) {
      const base = msgCache.get(msgId)
      if (!base) continue
      const merged: ChatMessage = {
        ...base,
        contents: [{ type: 'text' as const, text: accumulated }],
      }
      onMessage(merged)
    }
    textBuffer.clear()
  }

  function stopFlushLoop() {
    if (flushTimer) {
      clearInterval(flushTimer)
      flushTimer = null
    }
    flushBuffer() // 最终刷出剩余内容
  }

  // ---- 非文本消息直接透传（如 tool、question_option） ----
  function handleNonTextMessage(msg: ChatMessage) {
    flushBuffer() // 先刷出缓冲，保证时序
    onMessage(msg)
  }

  // ---- SSE 超时控制 ----
  const SSE_TIMEOUT = 5 * 60 * 1000 // 5 分钟
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), SSE_TIMEOUT)

  return fetchEventSource(`${ViteEnv.VITE_API_BASE_URL}/education/chat/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify(data),
    signal: controller.signal,
    openWhenHidden: true,
    onmessage(event) {
      let parsed: any
      try {
        parsed = JSON.parse(event.data)
      } catch {
        console.error('Failed to parse SSE data:', event.data)
        return
      }

      if (parsed.type === 'message' || parsed.type === 'tool' || parsed.type === 'thought_chain') {
        const msg = parseSSEToChatMessage(parsed.data || {})
        const msgId = String(msg.message_id ?? '')
        const incomingText = getFirstText(msg.contents)

        if (incomingText && (parsed.type === 'message' || parsed.type === 'thought_chain')) {
          // 文本类消息：缓冲合并
          textBuffer.set(msgId, (textBuffer.get(msgId) ?? '') + incomingText)
          msgCache.set(msgId, msg)
          startFlushLoop()
        } else {
          // 非文本消息（tool 等）：直接透传
          handleNonTextMessage(msg)
        }
      } else if (parsed.type === 'end') {
        stopFlushLoop()
        clearTimeout(timeoutId)
        const boundConvId = parsed.data?.conv_id
        onComplete?.({
          conv_id: typeof boundConvId === 'number' ? boundConvId : undefined,
        })
      } else if (parsed.type === 'error') {
        stopFlushLoop()
        clearTimeout(timeoutId)
        onError?.(new Error(parsed.data?.message || '发送失败'))
      }
    },
    onerror(error) {
      stopFlushLoop()
      clearTimeout(timeoutId)
      const sseError = error instanceof Error ? error : new Error('连接失败')
      onError?.(sseError)
      throw sseError
    },
    onclose() {
      stopFlushLoop()
      clearTimeout(timeoutId)
      onComplete?.()
    },
  })
}

export { getFirstText }
