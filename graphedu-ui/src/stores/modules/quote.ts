/**
 * 文本引用状态管理
 * @description 管理用户从课程内容中选择并引用的文本片段
 */

import { ref, readonly } from 'vue'

import type { ChatMessageContent } from '@/types/api/education/agent.ts'

/**
 * 文本引用项
 */
export interface TextQuote {
  /** 唯一ID */
  id: string
  /** 引用的文本内容 */
  text: string
  /** 来源路径（格式：课程 > 章节 > 小节 > 资源） */
  source: string
  /** 添加时间戳 */
  timestamp: number
}

const useQuoteStore = defineStore('quote', () => {
  // ========== 状态 ==========
  const quotes = ref<TextQuote[]>([])

  // ========== 方法 ==========

  /**
   * 添加引用
   */
  function addQuote(text: string, source: string) {
    // 限制引用长度，避免过长
    const maxLength = 500
    const truncatedText = text.length > maxLength ? text.substring(0, maxLength) + '...' : text

    quotes.value.push({
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      text: truncatedText,
      source,
      timestamp: Date.now(),
    })
  }

  /**
   * 移除指定引用
   */
  function removeQuote(id: string) {
    const index = quotes.value.findIndex((q) => q.id === id)
    if (index > -1) quotes.value.splice(index, 1)
  }

  /**
   * 清空所有引用
   */
  function clearQuotes() {
    quotes.value = []
  }

  /**
   * 将引用转换为 ChatMessageContent（quote_text 类型，包含引用和用户文本两个 content）
   */
  function toMessageContents(content: string): ChatMessageContent[] | undefined {
    if (quotes.value.length === 0) return undefined
    // 合并所有引用的来源为一条信息（用分号分隔）
    const sources = quotes.value.map((q) => q.source).filter((s): s is string => !!s)
    const mergedSource = sources.length > 0 ? sources.join('；') : null
    return [
      {
        type: 'quote_text',
        quote_text: { quotes: quotes.value.map((q) => q.text), content: null, source: mergedSource },
      },
      { type: 'text', text: content },
    ]
  }

  return {
    // 状态（只读）
    quotes: readonly(quotes),

    // 方法
    addQuote,
    removeQuote,
    clearQuotes,
    toMessageContents,
  }
})

export default useQuoteStore
