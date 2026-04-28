<script setup lang="ts">
import VueOfficeDocx from '@vue-office/docx'
import VueOfficeExcel from '@vue-office/excel'
import VueOfficePptx from '@vue-office/pptx'
import '@vue-office/docx/lib/index.css'
import '@vue-office/excel/lib/index.css'
import { useResourceProgress } from '@/composables/useResourceProgress'
import { ViteEnv } from '@/constants'

/**
 * Office 文档预览面板
 * 在 ChapterResource.vue 的 Golden Layout 中展示 Word/Excel/PPT 类型资源
 *
 * 使用 vue-office 库实现文档预览，通过后端代理接口获取文件内容（ArrayBuffer）
 * 避免 OSS 跨域问题
 *
 * 集成 useResourceProgress 追踪阅读时长（vue-office 不暴露精确位置信息）
 */
const props = defineProps<{
  /** 资料 ID */
  resourceId: number
  /** 资料名称（Tab 标题，供调试用） */
  resourceName?: string
  /** 文件 ID（由后端 fileId 字段提供，优先使用） */
  fileId?: number
  /** 文件 URL（由后端 fileUrl 字段提供，降级使用） */
  fileUrl?: string
  /** 资源类型（word/excel/pptx） */
  officeType?: 'word' | 'excel' | 'pptx'
  /** Golden Layout 注入的 refId（内部使用）*/
  refId?: number
}>()

// 状态
const documentSrc = ref<string | ArrayBuffer>('')
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')

// ─── 进度追踪（vue-office 不暴露页码/滚动位置，打开即算完成） ──────────────────────────────
const { startTracking } = useResourceProgress({
  resourceId: props.resourceId,
  resourceType: 'document',
  enabled: !!(props.fileId || props.fileUrl),
})

/**
 * 获取文件 URL（优先使用代理，降级使用直接 URL）
 */
function getFileUrl(): string {
  if (props.fileId) {
    return `${ViteEnv.VITE_API_BASE_URL}/common/proxy/file/${props.fileId}`
  }
  if (props.fileUrl) {
    return props.fileUrl
  }
  return ''
}

/**
 * 通过代理接口获取文件 ArrayBuffer
 */
async function fetchFileAsArrayBuffer(): Promise<ArrayBuffer> {
  const url = getFileUrl()
  if (!url) {
    throw new Error('无有效的文件地址')
  }
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`文件加载失败: ${response.status}`)
  }
  return await response.arrayBuffer()
}

/**
 * 渲染完成回调
 */
function onRendered() {
  isLoading.value = false
  // 文档渲染完成，开始计时
  startTracking()
}

/**
 * 渲染失败回调
 */
function onError(e: any) {
  console.error('[ChapterOfficePanel] 渲染失败', e)
  isLoading.value = false
  hasError.value = true
  errorMessage.value = e?.message || '文档渲染失败，请检查文件格式是否正确'
}

onMounted(async () => {
  try {
    documentSrc.value = await fetchFileAsArrayBuffer()
  } catch (e: any) {
    console.error('[ChapterOfficePanel] 加载文件失败', e)
    hasError.value = true
    errorMessage.value = e?.message || '加载文件失败'
    isLoading.value = false
  }
})
</script>

<template>
  <div class="chapter-office-panel h-full w-full flex flex-col">
    <!-- 加载中 -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <a-spin size="large" tip="正在加载文档..." />
    </div>

    <!-- 加载失败 -->
    <div v-else-if="hasError" class="flex-1 flex items-center justify-center">
      <a-result status="error" title="文档加载失败" :sub-title="errorMessage" />
    </div>

    <!-- Word 文档预览 -->
    <div v-else-if="officeType === 'word' && documentSrc" class="office-viewer flex-1 overflow-auto">
      <VueOfficeDocx :src="documentSrc" @rendered="onRendered" @error="onError" />
    </div>

    <!-- Excel 表格预览 -->
    <div v-else-if="officeType === 'excel' && documentSrc" class="office-viewer flex-1 overflow-auto">
      <VueOfficeExcel :src="documentSrc" @rendered="onRendered" @error="onError" />
    </div>

    <!-- PPT 演示文稿预览 -->
    <div v-else-if="officeType === 'pptx' && documentSrc" class="office-viewer flex-1 overflow-auto">
      <VueOfficePptx :src="documentSrc" @rendered="onRendered" @error="onError" />
    </div>

    <!-- 无效状态 -->
    <div v-else class="flex-1 flex items-center justify-center">
      <a-result status="warning" title="无法预览" sub-title="该资料尚未上传文件或文件格式不支持" />
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.chapter-office-panel {
  background: var(--ge-bg-container);
}

.office-viewer {
  @apply p-2;
}
</style>
