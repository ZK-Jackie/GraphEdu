<template>
  <div ref="wrapperRef" class="url-markdown-wrapper min-h-25">
    <div class="md-viewer-wrap">
      <div :class="['md-content text-[0.75rem]', markdownClass]" v-html="renderedHtml" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { marked } from 'marked'
import markedKatex from 'marked-katex-extension'
import DOMPurify from 'dompurify'
import 'katex/dist/katex.min.css'

/**
 * 组件属性
 */
interface Props {
  /** Markdown 内容（可包含 $...$ 行内公式 和 $$...$$ 块级公式） */
  content?: string
  /** 自定义类名 */
  markdownClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  content: '',
  markdownClass: '',
})

/**
 * 初始化 marked，注册 KaTeX 扩展
 * - 支持 `$...$`  行内公式（对应原版 remarkMath + rehypeKatex）
 * - 支持 `$$...$$` 块级公式
 * - 支持 GFM 语法（表格、任务列表等）
 */
const initMarked = (() => {
  let initialized = false
  return () => {
    if (initialized) return
    initialized = true

    // GFM + 换行支持
    marked.setOptions({ breaks: true, gfm: true })

    // KaTeX 数学公式扩展
    marked.use(
      markedKatex({
        throwOnError: false, // 公式解析失败时不抛出，降级显示原始文本
        output: 'html', // 输出 HTML（对应原版 rehype-katex 行为）
        nonStandard: true, // 允许非标准 LaTeX
      })
    )
  }
})()

/**
 * DOMPurify 允许的标签表
 * 相比默认配置额外添加了 KaTeX HTML 输出所用的元素
 */
const SAFE_TAGS = [
  // 标准 Markdown 元素
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'p',
  'br',
  'strong',
  'em',
  'u',
  's',
  'del',
  'code',
  'pre',
  'blockquote',
  'ul',
  'ol',
  'li',
  'a',
  'img',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
  'hr',
  'div',
  'span',
  'sup',
  'sub',
  'input',
  'label',
  // KaTeX HTML 输出需要的元素
  'svg',
  'g',
  'path',
  'line',
  'rect',
  'circle',
  'use',
  'defs',
  'clipPath',
  // KaTeX MathML 备用输出
  'math',
  'mrow',
  'mi',
  'mn',
  'mo',
  'ms',
  'mtext',
  'mspace',
  'msup',
  'msub',
  'msubsup',
  'mfrac',
  'msqrt',
  'mroot',
  'mover',
  'munder',
  'munderover',
  'semantics',
  'annotation',
  'mtable',
  'mtr',
  'mtd',
  'mstyle',
  'mpadded',
  'mphantom',
]

const SAFE_ATTRS = [
  'href',
  'src',
  'alt',
  'title',
  'class',
  'id',
  'style',
  'target',
  'rel',
  'checked',
  'type',
  'disabled',
  // SVG 属性
  'xmlns',
  'd',
  'viewBox',
  'fill',
  'stroke',
  'stroke-width',
  'stroke-linecap',
  'stroke-linejoin',
  'cx',
  'cy',
  'r',
  'x',
  'y',
  'x1',
  'y1',
  'x2',
  'y2',
  'width',
  'height',
  'transform',
  'preserveAspectRatio',
  'clip-path',
  // KaTeX 属性
  'aria-hidden',
  'focusable',
  'role',
]

/**
 * 将 Markdown 渲染为安全 HTML
 * 1. 用 marked + KaTeX 扩展渲染成 HTML
 * 2. 用 DOMPurify 移除脚本等危险内容（保留 KaTeX 输出）
 */
const renderedHtml = computed(() => {
  if (!props.content) return ''

  initMarked()

  const html = marked.parse(props.content) as string

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: SAFE_TAGS,
    ALLOWED_ATTR: SAFE_ATTRS,
    ALLOW_DATA_ATTR: true, // allowdata-token-index 等 KaTeX 自定义属性
  })
})

// 生命周期（预先初始化，避免首次渲染时有延迟）
onMounted(() => {
  initMarked()
})
</script>

<style scoped>
/* ── Markdown 主题变量（亮色默认）── */
.url-markdown-wrapper {
  position: relative;

  --md-heading-border: #eaecef;
  --md-code-bg: rgba(175, 184, 193, 0.2);
  --md-pre-bg: #f6f8fa;
  --md-blockquote-color: #656d76;
  --md-blockquote-border: #d0d7de;
  --md-table-border: #d0d7de;
  --md-table-header-bg: #f6f8fa;
  --md-table-row-bg: #ffffff;
  --md-table-row-alt-bg: #f6f8fa;
  --md-link-color: #0969da;
  --md-hr-bg: #d0d7de;
}

/* ── 暗色模式覆盖 ── */
:global(.dark) .url-markdown-wrapper {
  --md-heading-border: #303030;
  --md-code-bg: rgba(110, 118, 129, 0.4);
  --md-pre-bg: #161b22;
  --md-blockquote-color: #8b949e;
  --md-blockquote-border: #30363d;
  --md-table-border: #30363d;
  --md-table-header-bg: #1c2128;
  --md-table-row-bg: #1f1f1f;
  --md-table-row-alt-bg: #161b22;
  --md-link-color: var(--ge-primary);
  --md-hr-bg: #30363d;
}

.md-content {
  background: var(--ge-bg-container);
  color: var(--ge-text-primary);
}

.md-viewer-wrap :deep(h1),
.md-viewer-wrap :deep(h2),
.md-viewer-wrap :deep(h3),
.md-viewer-wrap :deep(h4),
.md-viewer-wrap :deep(h5),
.md-viewer-wrap :deep(h6) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
  color: var(--ge-text-primary);
}

.md-viewer-wrap :deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid var(--md-heading-border);
  padding-bottom: 0.3em;
}

.md-viewer-wrap :deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid var(--md-heading-border);
  padding-bottom: 0.3em;
}

.md-viewer-wrap :deep(h3) {
  font-size: 1.25em;
}

.md-viewer-wrap :deep(p) {
  margin-top: 0;
  margin-bottom: 1em;
  color: var(--ge-text-primary);
}

.md-viewer-wrap :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: var(--md-code-bg);
  border-radius: 6px;
  font-family:
    ui-monospace,
    SFMono-Regular,
    SF Mono,
    Menlo,
    Consolas,
    Liberation Mono,
    monospace;
}

.md-viewer-wrap :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: var(--md-pre-bg);
  border-radius: 6px;
  margin-bottom: 1em;
}

.md-viewer-wrap :deep(pre code) {
  padding: 0;
  background-color: transparent;
  border-radius: 0;
}

.md-viewer-wrap :deep(blockquote) {
  padding: 0 1em;
  color: var(--md-blockquote-color);
  border-left: 0.25em solid var(--md-blockquote-border);
  margin: 0 0 1em 0;
}

.md-viewer-wrap :deep(ul),
.md-viewer-wrap :deep(ol) {
  padding-left: 2em;
  margin-bottom: 1em;
}

.md-viewer-wrap :deep(table) {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 1em;
  width: 100%;
}

.md-viewer-wrap :deep(table th),
.md-viewer-wrap :deep(table td) {
  padding: 6px 13px;
  border: 1px solid var(--md-table-border);
}

.md-viewer-wrap :deep(table th) {
  font-weight: 600;
  background-color: var(--md-table-header-bg);
}

.md-viewer-wrap :deep(table tr) {
  background-color: var(--md-table-row-bg);
  border-top: 1px solid var(--md-table-border);
}

.md-viewer-wrap :deep(table tr:nth-child(2n)) {
  background-color: var(--md-table-row-alt-bg);
}

.md-viewer-wrap :deep(img) {
  max-width: 100%;
  height: auto;
}

.md-viewer-wrap :deep(a) {
  color: var(--md-link-color);
  text-decoration: none;
}

.md-viewer-wrap :deep(a:hover) {
  text-decoration: underline;
}

.md-viewer-wrap :deep(hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: var(--md-hr-bg);
  border: 0;
}

/* 代码块样式 */
.md-viewer-wrap :deep(.code-block) {
  background-color: var(--md-pre-bg);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family:
    ui-monospace,
    SFMono-Regular,
    SF Mono,
    Menlo,
    Consolas,
    Liberation Mono,
    monospace;
  font-size: 13px;
  line-height: 1.45;
}

.md-viewer-wrap :deep(.code-block code) {
  background-color: transparent;
  padding: 0;
}

/* KaTeX 块级公式水平滚动，防止超宽溢出 */
.md-viewer-wrap :deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  margin: 1em 0;
}
</style>
