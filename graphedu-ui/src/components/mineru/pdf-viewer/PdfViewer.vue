<template>
  <div class="pdf-viewer-container h-full w-full flex flex-col">
    <!-- 加载中 -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <a-spin size="large" tip="加载 PDF 中..." />
    </div>

    <!-- 加载失败 -->
    <div v-else-if="loadError" class="flex-1 flex items-center justify-center">
      <a-result status="error" title="PDF 加载失败" :sub-title="loadError.message" />
    </div>

    <!-- 正常显示 -->
    <template v-else-if="totalPages > 0">
      <!-- 工具栏 -->
      <PdfToolbar
        :current-page="currentPage"
        :total-pages="totalPages"
        :scale="scale"
        :zoom-mode="zoomMode"
        @prev="onPrev"
        @next="onNext"
        @jump-to="onJumpTo"
        @zoom-in="onZoomIn"
        @zoom-out="onZoomOut"
        @update:zoom-mode="onZoomModeChange"
      />

      <!-- PDF 滚动容器 -->
      <div
        ref="scrollContainerRef"
        class="pdf-scroll-container flex-1 overflow-auto"
        @scroll="onScroll"
        @contextmenu.prevent="onContextMenu"
        @click="closeContextMenu"
      >
        <div class="pdf-pages-wrapper">
          <PdfPage
            v-for="pageNum in totalPages"
            :key="pageNum"
            :ref="(el: any) => setPageRef(pageNum, el)"
            :page-num="pageNum"
            :should-render="isPageVisible(pageNum)"
            :scale="scale"
            :pdf-page="getCachedPage(pageNum)"
            :page-size="getPageSize(pageNum)"
            :bboxes="getBboxesForPage(pageNum)"
          />
        </div>
      </div>

      <!-- 右键引用菜单 -->
      <PdfContextMenu
        :visible="contextMenuVisible"
        :position="contextMenuPosition"
        :selected-text="contextMenuText"
        :source-path="sourcePath"
        @close="closeContextMenu"
      />
    </template>

    <!-- 无来源 -->
    <div v-else class="flex-1 flex items-center justify-center">
      <a-empty description="未提供 PDF 文件" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, shallowRef, triggerRef, nextTick } from 'vue'
import PdfToolbar from './PdfToolbar.vue'
import PdfPage from './PdfPage.vue'
import PdfContextMenu from './PdfContextMenu.vue'
import { usePdfDocument, buildSourceUrl } from './usePdfDocument'
import { usePdfVirtualScroll } from './usePdfVirtualScroll'
import type { BboxItem } from './usePdfAnnotationLayer'
import type { ZoomMode, PageSize } from './types'
import type { PDFViewerState, ExtractLayerData } from '../types'
import { PDF_COLOR_PICKER } from '../constants'

/**
 * 组件属性
 */
interface Props {
  /** PDF 文件 ID（优先使用，通过后端代理避免跨域） */
  fileId?: number
  /** PDF 文件 URL（直接链接，可能有跨域问题） */
  pdfUrl?: string
  /** 当前页码（1-based，外部控制翻页） */
  curPage?: number
  /** 标注数据 */
  layerData?: Record<number, any>
  /** 课程名称（用于构建引用来源路径） */
  courseName?: string
  /** 章节名称（用于构建引用来源路径） */
  chapterName?: string
  /** 资源名称（用于构建引用来源路径） */
  resourceName?: string
}

const props = withDefaults(defineProps<Props>(), {
  curPage: 1,
  layerData: () => ({}),
})

const emit = defineEmits<{
  (e: 'pageChange', state: PDFViewerState): void
  (e: 'loaded'): void
}>()

// ─── 文档状态 ────────────────────────────────────────────────────────────

const docState = usePdfDocument()

// 把 composable 返回的 ref 展开为顶层 ref，确保模板响应式正确
const totalPages = computed(() => docState.totalPages.value)
const isLoading = computed(() => docState.isLoading.value)
const loadError = computed(() => docState.error.value)

// ─── 虚拟滚动 ────────────────────────────────────────────────────────────

const scrollContainerRef = ref<HTMLElement>()

const virtualScroll = usePdfVirtualScroll({
  totalPages: docState.totalPages,
  containerRef: scrollContainerRef,
  bufferPages: 2,
})

const currentPage = computed(() => virtualScroll.currentPage.value)

// ─── 缩放 ────────────────────────────────────────────────────────────────

const zoomMode = ref<ZoomMode>('fit-width')
const scale = ref(1)
const SCALE_STEP = 0.25

// ─── 右键菜单 ──────────────────────────────────────────────────────────────

const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuText = ref('')

/** 构建来源路径 */
const sourcePath = computed(() => {
  const parts = [props.courseName, props.chapterName, props.resourceName].filter(Boolean)
  return parts.length > 0 ? parts.join(' > ') : 'PDF 文档'
})

/** 检查当前 PDF 文档是否支持文本选中（通过检查文本层是否有内容） */
const hasTextLayer = computed(() => {
  // 如果有缓存页面就认为支持文本层（renderTextLayer 会跳过无文本的页面）
  return pageCache.value.size > 0
})

function onContextMenu(e: MouseEvent): void {
  // PDF 不支持文本时，不拦截右键
  if (!hasTextLayer.value) return

  const selection = window.getSelection()
  const text = selection?.toString().trim()

  if (text && text.length > 0) {
    contextMenuText.value = text
    contextMenuPosition.value = { x: e.clientX, y: e.clientY }
    contextMenuVisible.value = true
  }
}

function closeContextMenu(): void {
  contextMenuVisible.value = false
}

// ─── 页面数据（使用 triggerRef 确保 Map 变更触发响应式）────────────────────

const pageSizes = shallowRef<Map<number, PageSize>>(new Map())
const pageCache = shallowRef<Map<number, any>>(new Map())
const pageRefs = new Map<number, any>()

/** 从缓存获取页面，通过函数调用确保每次读取最新值 */
function getCachedPage(pageNum: number): any {
  return pageCache.value.get(pageNum) ?? null
}

function getPageSize(pageNum: number): PageSize {
  return pageSizes.value.get(pageNum) ?? { width: 612, height: 792 }
}

// ─── 标注数据格式化 ──────────────────────────────────────────────────────────

/** 将 ExtractLayerData 中当前页的标注转为 BboxItem 数组 */
function getBboxesForPage(pageNum: number): BboxItem[] {
  const pageIdx = pageNum - 1 // layerData 使用 0-based 索引
  const item = props.layerData[pageIdx]
  if (!item) return []

  const allBlocks = [...(item.preproc_blocks ?? []), ...(item.discarded_blocks ?? [])]
  return allBlocks.map((block) => ({
    type: block.type,
    bbox: block.bbox,
    color: block.color ?? PDF_COLOR_PICKER[block.type] ?? PDF_COLOR_PICKER.default,
  }))
}

// ─── ResizeObserver ───────────────────────────────────────────────────────

let resizeObserver: ResizeObserver | null = null

function setupResizeObserver(): void {
  if (!scrollContainerRef.value) return
  resizeObserver = new ResizeObserver(() => {
    recalcScale()
  })
  resizeObserver.observe(scrollContainerRef.value)
}

function recalcScale(): void {
  if (!scrollContainerRef.value) return
  const containerWidth = scrollContainerRef.value.clientWidth - 24
  if (containerWidth <= 0) return

  if (zoomMode.value === 'fit-width') {
    const size = getPageSize(1)
    if (size.width > 0) {
      scale.value = containerWidth / size.width
    }
  } else if (zoomMode.value === 'fit-page') {
    const containerHeight = scrollContainerRef.value.clientHeight - 24
    const size = getPageSize(1)
    if (size.width > 0 && size.height > 0) {
      const scaleW = containerWidth / size.width
      const scaleH = containerHeight / size.height
      scale.value = Math.min(scaleW, scaleH)
    }
  }
}

// ─── 可见性判断 ────────────────────────────────────────────────────────────

function isPageVisible(pageNum: number): boolean {
  const { start, end } = virtualScroll.visibleRange.value
  const idx = pageNum - 1
  const visible = idx >= start && idx <= end
  return visible
}

// ─── 页面 ref 管理 ────────────────────────────────────────────────────────

function setPageRef(pageNum: number, el: any): void {
  if (!el) return
  const domEl = el.$el ?? el
  if (!(domEl instanceof HTMLElement)) return
  pageRefs.set(pageNum, el)
  virtualScroll.registerPageElement(pageNum, domEl)
}

// ─── 页面缓存加载 ─────────────────────────────────────────────────────────

async function ensurePageCached(pageNum: number): Promise<void> {
  if (pageCache.value.has(pageNum)) return
  try {
    const page = await docState.getPage(pageNum)
    const viewport = page.getViewport({ scale: 1 })
    pageSizes.value.set(pageNum, { width: viewport.width, height: viewport.height })
    pageCache.value.set(pageNum, page)
    // 手动触发响应式更新，让模板重新读取 Map
    triggerRef(pageSizes)
    triggerRef(pageCache)
  } catch {
    // 页面加载失败不影响其他页面
  }
}

// ─── 加载 PDF ──────────────────────────────────────────────────────────────

let loadVersion = 0

async function loadPdf(): Promise<void> {
  const source = buildSourceUrl(props.fileId, props.pdfUrl)
  if (!source) return

  // 用版本号防止异步竞态
  const version = ++loadVersion

  await docState.loadDocument(source)
  if (version !== loadVersion) return

  if (docState.pdfDoc.value) {
    // 清空旧缓存
    pageCache.value.clear()
    pageSizes.value.clear()

    // 预加载前几页以获取尺寸
    const pagesToPreload = Math.min(3, docState.totalPages.value)
    for (let i = 1; i <= pagesToPreload; i++) {
      await ensurePageCached(i)
      if (version !== loadVersion) return
    }

    // 计算初始缩放
    await nextTick()
    recalcScale()

    emit('loaded')
  }
}

// ─── 工具栏事件处理 ────────────────────────────────────────────────────────

function onPrev(): void {
  if (currentPage.value > 1) {
    virtualScroll.scrollToPage(currentPage.value - 1)
  }
}

function onNext(): void {
  if (currentPage.value < totalPages.value) {
    virtualScroll.scrollToPage(currentPage.value + 1)
  }
}

function onJumpTo(page: number): void {
  virtualScroll.scrollToPage(page)
}

function onZoomIn(): void {
  zoomMode.value = 'manual'
  scale.value = Math.min(scale.value + SCALE_STEP, 5)
}

function onZoomOut(): void {
  zoomMode.value = 'manual'
  scale.value = Math.max(scale.value - SCALE_STEP, 0.25)
}

function onZoomModeChange(mode: ZoomMode): void {
  zoomMode.value = mode
  recalcScale()
}

// ─── 滚动事件 ──────────────────────────────────────────────────────────────

let lastEmittedPage = 0

function onScroll(): void {
  const page = currentPage.value
  if (page !== lastEmittedPage && page > 0) {
    lastEmittedPage = page
    emit('pageChange', {
      page,
      totalPages: totalPages.value,
    })
  }
}

// ─── 外部页码控制 ──────────────────────────────────────────────────────────

watch(
  () => props.curPage,
  (newPage) => {
    if (newPage && newPage > 0 && newPage !== currentPage.value) {
      virtualScroll.scrollToPage(newPage)
    }
  }
)

// ─── 监听可见范围变化，预加载页面 ─────────────────────────────────────────

watch(
  () => virtualScroll.visibleRange.value,
  async (range) => {
    for (let i = range.start + 1; i <= range.end + 1; i++) {
      await ensurePageCached(i)
    }
  }
)

// ─── 监听 fileId/pdfUrl 变化重新加载 ─────────────────────────────────────

watch([() => props.fileId, () => props.pdfUrl], () => {
  loadPdf()
})

// ─── 生命周期 ──────────────────────────────────────────────────────────────

onMounted(() => {
  loadPdf()
  setupResizeObserver()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  docState.destroy()
  pageCache.value.clear()
  for (const pageNum of pageRefs.keys()) {
    virtualScroll.unregisterPageElement(pageNum)
  }
})

// ─── 暴露方法 ──────────────────────────────────────────────────────────────

function setPage(page: number): void {
  virtualScroll.scrollToPage(page)
}

defineExpose({ setPage })
</script>

<style scoped>
@reference '#main.css';

.pdf-scroll-container {
  background: var(--ge-bg-page);
}

.pdf-scroll-container :deep(::-webkit-scrollbar) {
  width: 8px;
}

.pdf-scroll-container :deep(::-webkit-scrollbar-track) {
  background: transparent;
}

.pdf-scroll-container :deep(::-webkit-scrollbar-thumb) {
  background: var(--ge-text-disabled);
  border-radius: 4px;
}

.pdf-scroll-container :deep(::-webkit-scrollbar-thumb:hover) {
  background: var(--ge-text-tertiary);
}

.pdf-pages-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  min-height: 100%;
  width: max-content;
  min-width: 100%;
}
</style>
