<template>
  <div class="pdf-extraction-wrapper h-full w-full">
    <!-- 工具栏 -->
    <div class="toolbar flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">PDF 对比视图</span>
        <a-tag v-if="pdfState.page > 0" color="blue"> 页码: {{ pdfState.page }} </a-tag>
      </div>

      <div class="flex items-center gap-2">
        <a-button size="small" @click="toggleFullScreen">
          <template #icon>
            <FullscreenOutlined v-if="!fullScreen" />
            <FullscreenExitOutlined v-else />
          </template>
          {{ fullScreen ? '退出全屏' : '全屏' }}
        </a-button>

        <a-button size="small" @click="resetView">
          <template #icon>
            <ReloadOutlined />
          </template>
          重置
        </a-button>
      </div>
    </div>

    <!-- 内容区域：flex-1 占据工具栏之外的剩余高度，overflow-hidden 防止溢出 -->
    <div
      :class="[
        'content flex-1 overflow-hidden transition-all duration-300',
        fullScreen ? 'grid grid-cols-1' : 'grid grid-cols-2',
      ]"
    >
      <!-- 左侧 PDF -->
      <div :class="['pdf-container relative border-r border-gray-200', fullScreen ? 'hidden' : 'min-w-[50%]']">
        <PdfViewer
          v-if="taskInfo.pdfUrl"
          ref="pdfViewerRef"
          :pdf-url="taskInfo.pdfUrl"
          :cur-page="pdfState.page"
          :layer-data="taskInfo.layerData"
          @page-change="handlePdfPageChange"
          @loaded="handlePdfLoaded"
        />
        <a-empty v-else description="暂无 PDF 文件" class="absolute inset-0 flex items-center justify-center" />
      </div>

      <!-- 右侧 Markdown -->
      <div :class="['md-container bg-white', fullScreen ? 'w-full' : 'min-w-[50%]']">
        <MdViewer v-if="markdownPages.length > 0" :cur-page="pdfState.page" @page-change="handleMdPageChange" />
        <a-empty v-else description="暂无 Markdown 内容" class="absolute inset-0 flex items-center justify-center" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { FullscreenOutlined, FullscreenExitOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import PdfViewer from '../pdf-viewer/PdfViewer.vue'
import MdViewer from '../md-viewer/MdViewer.vue'
import { useMdStore } from '../stores/mdStore'
import type { PDFViewerState, TaskInfo } from '../types'

/**
 * 组件属性
 */
interface Props {
  /** 任务信息 */
  taskInfo: TaskInfo
}

const props = defineProps<Props>()

// store
const mdStore = useMdStore()

/**
 * 兼容新旧字段：优先使用 markdownContent，回退到 markdownUrl
 */
const markdownPages = computed(() => props.taskInfo.markdownContent ?? props.taskInfo.markdownUrl ?? [])

// refs
const pdfViewerRef = ref<InstanceType<typeof PdfViewer>>()

// 状态
const fullScreen = ref(false)
const pdfState = reactive<PDFViewerState>({
  page: 1,
})

// 方法
/**
 * 处理 PDF 页面变化
 */
function handlePdfPageChange(state: PDFViewerState) {
  pdfState.page = state.page
}

/**
 * 处理 PDF 加载完成（可在此时重置页码等）
 */
function handlePdfLoaded() {
  // 保留 hook，供外部扩展
}

/**
 * 切换全屏模式
 */
function toggleFullScreen() {
  fullScreen.value = !fullScreen.value
}

/**
 * 重置视图
 */
function resetView() {
  fullScreen.value = false
  pdfState.page = 1
  if (pdfViewerRef.value) {
    pdfViewerRef.value.setPage(1)
  }
}

/**
 * 处理 Markdown 滚动驱动 PDF 页面切换
 */
function handleMdPageChange(page: number) {
  if (page !== pdfState.page && page > 0) {
    pdfState.page = page
    pdfViewerRef.value?.setPage(page)
  }
}

// 监听 taskInfo 变化，动态更新 store（支持外部数据异步加载完成后更新）
watch(
  markdownPages,
  (pages) => {
    mdStore.setMdContent(pages)
  },
  { immediate: true }
)

watch(
  () => props.taskInfo.layerData,
  (data) => {
    if (data) mdStore.setLayerData(data)
  },
  { immediate: true }
)

// 生命周期
onMounted(() => {
  // MdViewer 的 pageChange 通过 emit 直接传递，无需全局事件
})

onUnmounted(() => {
  // 清理 store
  mdStore.reset()
})
</script>

<style scoped>
.pdf-extraction-wrapper {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  flex-shrink: 0;
}

.content {
  flex: 1;
  overflow: hidden;
}

.pdf-container,
.md-container {
  height: 100%;
  overflow: hidden;
  position: relative;
}
</style>
