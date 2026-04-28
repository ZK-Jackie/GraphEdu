<script setup lang="ts">
import PdfViewer from '@/components/mineru/pdf-viewer/PdfViewer.vue'
import { useResourceProgress } from '@/composables/useResourceProgress'

/**
 * PDF 资源面板
 * 在 ChapterResource.vue 的 Golden Layout 中展示 PDF 类型资源
 * 使用代理接口避免 OSS 跨域问题
 *
 * 集成 useResourceProgress 追踪阅读进度，支持断点续学
 */
const props = defineProps<{
  /** 资料 ID */
  resourceId: number
  /** 资料名称（Tab 标题，供调试用） */
  resourceName?: string
  /** 文件 ID（由后端 fileId 字段提供，优先使用） */
  fileId?: number
  /** 文件 URL（由后端 fileUrl 字段提供，可能跨域） */
  fileUrl?: string
  /** Golden Layout 注入的 refId（内部使用）*/
  refId?: number
  /** 课程名称（用于构建引用来源路径） */
  courseName?: string
  /** 章节名称（用于构建引用来源路径） */
  chapterName?: string
}>()

// ─── 进度追踪 ──────────────────────────────────────────────────────────────

const pdfViewerRef = ref<InstanceType<typeof PdfViewer> | null>(null)
const currentPage = ref(1)

const { position, initialized, startTracking, reportImmediate } = useResourceProgress({
  resourceId: props.resourceId,
  resourceType: 'pdf',
  enabled: !!(props.fileId || props.fileUrl),
})

/** PdfViewer 页码变化回调 */
function onPageChange(state: { page: number; totalPages?: number }) {
  currentPage.value = state.page
  position.value = { page: state.page, total_pages: state.totalPages }

  // 触及末页 → 立即上报
  if (state.totalPages && state.page >= state.totalPages) {
    reportImmediate()
  }
}

/** PDF 加载完成 */
function onPdfLoaded() {
  // 资源加载完成，开始计时
  startTracking()

  // 断点续学恢复完成后，跳转到上次阅读位置
  watch(
    initialized,
    (ready) => {
      if (ready && position.value?.page && position.value.page > 1) {
        pdfViewerRef.value?.setPage(position.value.page)
      }
    },
    { once: true }
  )
  // 如果 initialized 已经为 true（恢复已完成），直接跳转
  if (initialized.value && position.value?.page && position.value.page > 1) {
    pdfViewerRef.value?.setPage(position.value.page)
  }
}
</script>

<template>
  <div class="chapter-pdf-panel h-full w-full flex flex-col">
    <!-- 优先使用 fileId 代理（避免跨域），降级使用 fileUrl -->
    <PdfViewer
      v-if="props.fileId || props.fileUrl"
      ref="pdfViewerRef"
      :file-id="props.fileId"
      :pdf-url="props.fileUrl"
      :course-name="props.courseName"
      :chapter-name="props.chapterName"
      :resource-name="props.resourceName"
      @page-change="onPageChange"
      @loaded="onPdfLoaded"
    />

    <!-- 无文件 ID 和 URL：错误提示 -->
    <div v-else class="flex-1 flex items-center justify-center">
      <a-result status="warning" title="无法加载 PDF" sub-title="该资料尚未上传文件或文件链接无效" />
    </div>
  </div>
</template>

<style scoped>
.chapter-pdf-panel {
  background: var(--ge-bg-container);
}
</style>
