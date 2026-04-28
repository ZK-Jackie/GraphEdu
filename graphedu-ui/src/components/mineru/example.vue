<!--
  MinerU PDF 查看器使用示例

  在你的页面中使用此组件：
-->

<template>
  <div class="mineru-demo-page h-screen p-4 bg-gray-50">
    <div class="h-full flex flex-col gap-4">
      <!-- 标题栏 -->
      <div class="bg-white rounded-lg shadow-sm p-4">
        <h1 class="text-2xl font-bold text-gray-800">MinerU PDF 查看器示例</h1>
        <p class="text-gray-600 mt-2">基于 MinerU 项目的 Vue 3 移植版本，支持 PDF 查看、标注和 Markdown 对比渲染</p>
      </div>

      <!-- 查看器容器 -->
      <div class="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
        <MinerUViewer pdf-url="/sample.pdf" :markdown-content="markdownPages" :layer-data="layerData" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MinerUViewer } from './index.ts'
import type { ExtractLayerData } from './types'

// Markdown 内容（按页分割）
const markdownPages = ref<string[]>([
  // 第一页
  `# 第一章：引言

这是第一页的内容。PDF 查看器支持以下功能：

- ✅ PDF 渲染和显示
- ✅ 页面标注和识别框
- ✅ Markdown 对比显示
- ✅ 双向同步滚动

## 1.1 功能特性

本组件基于 Mozilla PDF.js 构建，提供完整的 PDF 查看功能。`,

  // 第二页
  `# 第二章：使用指南

## 2.1 基础用法

\`\`\`vue
<MinerUViewer
  pdf-url="/path/to/file.pdf"
  :markdown-content="markdownPages"
/>
\`\`\`

## 2.2 高级配置

支持自定义标注数据、颜色配置等功能。

> 这是一个引用示例。

**粗体** 和 *斜体* 文本样式支持。`,

  // 第三页
  `# 第三章：API 参考

## 组件 Props

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pdfUrl | string | 是 | PDF 文件 URL |
| markdownContent | string[] | 否 | Markdown 内容 |
| layerData | ExtractLayerData | 否 | 标注数据 |

## 示例代码

\`\`\`typescript
const layerData: ExtractLayerData = {
  0: {
    preproc_blocks: [
      {
        type: 'title',
        bbox: [0.1, 0.1, 0.9, 0.2],
        color: { line: 'rgba(121, 124, 255, 1)', fill: 'rgba(121, 124, 255, 0.4)' }
      }
    ]
  }
}
\`\`\`

## 数学公式

行内公式：$E = mc^2$

块级公式：

$$
\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}
$$`,

  // 第四页
  `# 第四章：常见问题

## Q1: 如何自定义标注颜色？

可以通过修改 \`src/components/mineru/constants/index.ts\` 中的 \`PDF_COLOR_PICKER\` 配置。

## Q2: 支持哪些标注类型？

支持以下类型：

1. **title** - 标题（蓝色）
2. **text** - 正文（粉色）
3. **image** - 图片（绿色）
4. **table** - 表格（黄色）
5. **formula** - 公式（橙色）
6. **discarded** - 废弃内容（灰色）

## Q3: 如何处理大文件？

建议分页加载，或者使用 Web Worker 进行后台处理。`,
])

// 标注数据示例
const layerData = ref<ExtractLayerData>({
  0: {
    preproc_blocks: [
      {
        type: 'title',
        bbox: [0.1, 0.08, 0.9, 0.15],
        color: { line: 'rgba(121, 124, 255, 1)', fill: 'rgba(121, 124, 255, 0.4)' },
      },
      {
        type: 'text',
        bbox: [0.1, 0.18, 0.9, 0.35],
        color: { line: 'rgba(230, 122, 171, 1)', fill: 'rgba(230, 122, 171, 0.4)' },
      },
      {
        type: 'text',
        bbox: [0.1, 0.38, 0.5, 0.5],
        color: { line: 'rgba(230, 122, 171, 1)', fill: 'rgba(230, 122, 171, 0.4)' },
      },
    ],
    discarded_blocks: [],
  },
  1: {
    preproc_blocks: [
      {
        type: 'title',
        bbox: [0.1, 0.08, 0.9, 0.13],
        color: { line: 'rgba(121, 124, 255, 1)', fill: 'rgba(121, 124, 255, 0.4)' },
      },
      {
        type: 'text',
        bbox: [0.1, 0.15, 0.9, 0.25],
        color: { line: 'rgba(230, 122, 171, 1)', fill: 'rgba(230, 122, 171, 0.4)' },
      },
    ],
    discarded_blocks: [],
  },
  2: {
    preproc_blocks: [
      {
        type: 'title',
        bbox: [0.1, 0.08, 0.9, 0.13],
        color: { line: 'rgba(121, 124, 255, 1)', fill: 'rgba(121, 124, 255, 0.4)' },
      },
      {
        type: 'table',
        bbox: [0.15, 0.25, 0.85, 0.55],
        color: { line: 'rgba(255, 193, 7, 1)', fill: 'rgba(255, 193, 7, 0.4)' },
      },
    ],
    discarded_blocks: [],
  },
  3: {
    preproc_blocks: [
      {
        type: 'title',
        bbox: [0.1, 0.08, 0.9, 0.13],
        color: { line: 'rgba(121, 124, 255, 1)', fill: 'rgba(121, 124, 255, 0.4)' },
      },
      {
        type: 'text',
        bbox: [0.1, 0.15, 0.9, 0.7],
        color: { line: 'rgba(230, 122, 171, 1)', fill: 'rgba(230, 122, 171, 0.4)' },
      },
    ],
    discarded_blocks: [],
  },
})
</script>

<style scoped>
.mineru-demo-page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
