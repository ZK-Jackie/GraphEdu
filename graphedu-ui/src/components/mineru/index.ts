/**
 * MinerU PDF 查看器和标注组件
 *
 * @example
 * ```vue
 * <template>
 *   <MinerUViewer
 *     pdf-url="/path/to/file.pdf"
 *     :markdown-content="markdownPages"
 *     :layer-data="layerData"
 *   />
 * </template>
 *
 * <script setup lang="ts">
 * import MinerUViewer, { pipelineMiddleToLayerData, vlmModelJsonToLayerData } from '@/components/mineru'
 *
 * // pipeline 后端：传入 middle.json 的 pdf_info 数组
 * const layerData = pipelineMiddleToLayerData(middleJson.pdf_info)
 *
 * // VLM 后端：传入 model.json 和每页尺寸
 * // const layerData = vlmModelJsonToLayerData(modelJson, pageSizes)
 * </script>
 * ```
 */

import PdfExtraction from './pdf-extraction/PdfExtraction.vue'
import PdfViewer from './pdf-viewer/PdfViewer.vue'
import MdViewer from './md-viewer/MdViewer.vue'
import UrlMarkdown from './md-viewer/UrlMarkdown.vue'
import { useMdStore } from './stores/mdStore'

export { PdfExtraction, PdfViewer, MdViewer, UrlMarkdown, useMdStore }

export { default as MinerUViewer } from './MinerUViewer.vue'

// 导出类型
export * from './types'

// 导出常量
export * from './constants'
