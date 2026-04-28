<script setup lang="ts">
import UrlMarkdown from '@/components/mineru/md-viewer/UrlMarkdown.vue'
import useQuoteStore from '@/stores/modules/quote'
import { LinkOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useResourceProgress } from '@/composables/useResourceProgress'
import { ViteEnv } from '@/constants'

/**
 * 文本资源面板
 * 在 ChapterResource.vue 的 Golden Layout 中展示文本类型资源
 *
 * 组件从文件获取文本内容，支持 .md 和 .txt 格式
 */
const props = defineProps<{
  /** 资料 ID */
  resourceId: number
  /** 资料名称（Tab 标题，供调试用） */
  resourceName?: string
  /** Golden Layout 注入的 refId（内部使用）*/
  refId?: number
  /** 课程名称（从 ChapterResource 传递） */
  courseName?: string
  /** 章节名称（从 ChapterResource 传递） */
  chapterName?: string
  /** 文件 ID（优先使用，通过后端代理） */
  fileId?: number
  /** 文件 URL（直接链接，降级使用） */
  fileUrl?: string
}>()

const quoteStore = useQuoteStore()

const content = ref('')
const isLoading = ref(true)
const hasError = ref(false)

// 右键菜单状态
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const selectedText = ref('')

/**
 * 获取资源 URL 扩展名（从 props.resourceUrl 末尾提取）
 */
function getResourceUrlExtension(): string {
  const url = props.fileUrl || ''
  if (!url) return 'txt'
  const match = url.match(/\.(\w+)(?:\?|$)/i)
  return match?.[1]?.toLowerCase() ?? 'txt'
}

/**
 * 判断是否为 Markdown 文件（检查 resourceUrl 末尾是否以 .md 结尾）
 */
const isMarkdown = computed(() => getResourceUrlExtension() === 'md')

/**
 * 判断是否为支持的文本文件（检查 resourceUrl 末尾是否以 .md 或 .txt 结尾）
 */
const isSupportedTextFile = computed(() => {
  const ext = getResourceUrlExtension()
  return ext === 'md' || ext === 'txt'
})

/**
 * 构建代理 URL（优先使用代理接口，避免跨域）
 */
function buildProxyUrl(): string {
  // 优先使用 fileId 构建代理 URL
  if (props.fileId) {
    return `${ViteEnv.VITE_API_BASE_URL}/common/proxy/file/${props.fileId}`
  }
  // 降级使用直接 URL（可能跨域）
  if (props.fileUrl) {
    return props.fileUrl
  }
  return ''
}

/**
 * 从文件获取内容
 */
async function fetchFileContent(): Promise<string> {
  const url = buildProxyUrl()
  if (!url) {
    throw new Error('无效的文件地址')
  }

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`文件加载失败: ${response.status}`)
  }
  return await response.text()
}

onMounted(async () => {
  try {
    content.value = await fetchFileContent()
    // 内容加载完成，开始计时
    startTracking()
  } catch (e) {
    console.error('[ChapterTextPanel] 加载文件失败', e)
    hasError.value = true
  } finally {
    isLoading.value = false
  }

  // 添加全局点击监听，用于关闭右键菜单
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 构建来源路径
function buildSourcePath(): string {
  const courseName = props.courseName || '课程'
  const chapterName = props.chapterName || '章节'
  const resourceName = props.resourceName || '资源'
  return `${courseName} > ${chapterName} > ${resourceName}`
}

// 右键菜单处理
function handleContextMenu(e: MouseEvent) {
  const selection = window.getSelection()
  const text = selection?.toString().trim()

  if (text && text.length > 0) {
    e.preventDefault()
    selectedText.value = text
    contextMenuPosition.value = { x: e.clientX, y: e.clientY }
    contextMenuVisible.value = true
  }
}

// 添加引用
function handleQuote() {
  const source = buildSourcePath()
  quoteStore.addQuote(selectedText.value, source)
  contextMenuVisible.value = false
  message.success('已添加引用，可在聊天框中查看')
}

// 点击其他地方关闭菜单
function handleClickOutside() {
  contextMenuVisible.value = false
}

// ─── 进度追踪 ──────────────────────────────────────────────────────────────

const scrollContainerRef = ref<HTMLElement | null>(null)

const { position, initialized, startTracking, reportImmediate } = useResourceProgress({
  resourceId: props.resourceId,
  resourceType: 'text',
  enabled: !!(props.fileId || props.fileUrl),
})

/** 节流标记 */
let lastScrollUpdateTime = 0
const SCROLL_THROTTLE_MS = 2000
/** text 完成度阈值，与 useResourceProgress 内部保持一致 */
const TEXT_COMPLETION_THRESHOLD = 85

/** 监听滚动事件，计算阅读进度百分比 */
function onScroll(e: Event) {
  const el = e.target as HTMLElement
  if (!el) return

  const now = Date.now()
  if (now - lastScrollUpdateTime < SCROLL_THROTTLE_MS) return
  lastScrollUpdateTime = now

  const scrollHeight = el.scrollHeight - el.clientHeight
  const scrollPercent = scrollHeight > 0 ? Math.round((el.scrollTop / scrollHeight) * 100) : 0

  position.value = { scroll_percent: scrollPercent }

  // 触及底部 → 立即上报
  if (scrollPercent >= TEXT_COMPLETION_THRESHOLD) {
    reportImmediate()
  }
}

/** 断点续学：恢复滚动位置 */
watch(initialized, (ready) => {
  if (ready && position.value?.scroll_percent && scrollContainerRef.value) {
    const el = scrollContainerRef.value
    const scrollHeight = el.scrollHeight - el.clientHeight
    el.scrollTop = (scrollHeight * position.value.scroll_percent) / 100
  }
})
</script>

<template>
  <div
    ref="scrollContainerRef"
    class="chapter-text-panel h-full w-full overflow-auto"
    @contextmenu="handleContextMenu"
    @scroll="onScroll"
  >
    <!-- 加载中 -->
    <div v-if="isLoading" class="flex items-center justify-center h-full">
      <a-spin size="large" />
    </div>

    <!-- 加载失败 -->
    <div v-else-if="hasError" class="flex items-center justify-center h-full">
      <a-result status="error" title="加载失败" sub-title="获取文本内容时发生错误，请刷新页面重试" />
    </div>

    <!-- 内容为空 -->
    <div v-else-if="!content" class="flex items-center justify-center h-full">
      <a-empty description="该资料暂无文本内容" />
    </div>

    <!-- Markdown 文件渲染 -->
    <div v-else-if="isMarkdown" class="p-6 max-w-4xl mx-auto">
      <UrlMarkdown :content="content" />
    </div>

    <!-- 纯文本文件渲染 -->
    <div v-else class="p-6 max-w-4xl mx-auto">
      <pre class="text-content">{{ content }}</pre>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenuVisible"
        class="quote-context-menu"
        :style="{
          left: contextMenuPosition.x + 'px',
          top: contextMenuPosition.y + 'px',
        }"
      >
        <div class="context-menu-item" @click="handleQuote">
          <LinkOutlined />
          引用此文本
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
@reference "#main.css";

.chapter-text-panel {
  background: var(--ge-bg-container);
}

/* 纯文本内容样式 */
.text-content {
  @apply whitespace-pre-wrap font-mono text-sm;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  line-height: 1.6;
  margin: 0;
  padding: 0;
  color: var(--ge-text-primary);
}

/* 右键菜单样式 */
.quote-context-menu {
  @apply fixed z-[9999] rounded-lg shadow-lg py-1 min-w-40;
  background: var(--ge-bg-elevated);
  border: 1px solid var(--ge-border-color);
}

.context-menu-item {
  @apply flex items-center gap-2 px-4 py-2 text-sm cursor-pointer transition-colors;
  color: var(--ge-text-primary);
}

.context-menu-item:hover {
  color: var(--ge-primary);
  background: var(--ge-primary-light);
}
</style>
