/**
 * Markdown 内容状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ExtractLayerData } from '../types'
import { DEFAULT_MD_PREVIEW_TYPE } from '../constants'

export const useMdStore = defineStore('mineru-md', () => {
  // 状态
  const mdContent = ref<string[]>([])
  const displayType = ref<'preview' | 'code'>(DEFAULT_MD_PREVIEW_TYPE)
  const layerData = ref<ExtractLayerData>({})

  // 计算属性
  /**
   * 所有 Markdown 内容（带锚点）
   */
  const allMdContentWithAnchor = computed(() => {
    return getContentWithAnchors(mdContent.value)
  })

  /**
   * 所有 Markdown 内容（不带锚点）
   */
  const allMdContent = computed(() => {
    return mdContent.value.join('\n\n')
  })

  // 方法
  /**
   * 设置 Markdown 内容
   */
  function setMdContent(content: string[]) {
    mdContent.value = content
  }

  /**
   * 设置显示类型
   */
  function setDisplayType(type: 'preview' | 'code') {
    displayType.value = type
  }

  /**
   * 设置标注数据
   */
  function setLayerData(data: ExtractLayerData) {
    layerData.value = data
  }

  /**
   * 为每页 Markdown 添加锚点
   */
  function getContentWithAnchors(data: string[]): string {
    if (!data || data.length === 0) return ''

    return data
      .map((content, index) => {
        const anchorTag = `<span id="md-anchor-${index}" style="display:none;"></span>`
        return `${anchorTag}\n\n${content}`
      })
      .join('\n\n')
  }

  /**
   * 重置状态
   */
  function reset() {
    mdContent.value = []
    displayType.value = DEFAULT_MD_PREVIEW_TYPE
    layerData.value = {}
  }

  return {
    // 状态
    mdContent,
    displayType,
    layerData,

    // 计算属性
    allMdContentWithAnchor,
    allMdContent,

    // 方法
    setMdContent,
    setDisplayType,
    setLayerData,
    reset,
  }
})
