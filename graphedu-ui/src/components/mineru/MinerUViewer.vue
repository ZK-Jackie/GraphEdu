<template>
  <PdfExtraction :task-info="taskInfo" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PdfExtraction from './pdf-extraction/PdfExtraction.vue'
import type { TaskInfo } from './types'

/**
 * MinerU PDF 查看器主入口组件
 *
 * 支持 pipeline 和 VLM 两种后端输出，layerData 通过工具函数转换后传入：
 * - pipeline middle.json → pipelineMiddleToLayerData(pdfInfo)
 * - VLM model.json      → vlmModelJsonToLayerData(modelJson, pageSizes)
 *
 * @example
 * ```vue
 * <MinerUViewer
 *   pdf-url="/path/to/file.pdf"
 *   :markdown-content="['# Page 1', '## Page 2']"
 *   :layer-data="layerData"
 * />
 * ```
 */
interface Props {
  /** PDF 文件 URL */
  pdfUrl: string
  /**
   * 每页的 Markdown 内容字符串数组（已加载好的内容，非 URL）
   * 数组 index 与 PDF 页码一一对应（0-based）
   */
  markdownContent?: string[]
  /** 标注数据（ExtractLayerData 格式，使用工具函数从 middle.json 或 model.json 转换） */
  layerData?: TaskInfo['layerData']
}

const props = withDefaults(defineProps<Props>(), {
  markdownContent: () => [],
  layerData: () => ({}),
})

const taskInfo = computed<TaskInfo>(() => ({
  pdfUrl: props.pdfUrl,
  markdownContent: props.markdownContent,
  layerData: props.layerData,
}))
</script>
