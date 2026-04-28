/**
 * MinerU 组件类型定义
 */

export type ExtractTaskType = 'pdf' | 'formula-detect' | 'formula-extract' | 'table-recogn'

export const EXTRACTOR_TYPE_LIST = {
  table: 'table',
  formula: 'formula',
  pdf: 'PDF',
} as const

export enum FORMULA_TYPE {
  extract = 'extract',
  detect = 'detect',
}

export enum MD_PREVIEW_TYPE {
  preview = 'preview',
  code = 'code',
}

/**
 * PDF 查看器状态
 */
export interface PDFViewerState {
  page: number
  totalPages?: number
}

/**
 * 标注框类型
 *
 * Pipeline 后端类型：title | plain_text | abandon | figure | figure_caption |
 *   table | table_caption | table_footnote | isolate_formula | formula_caption |
 *   embedding | isolated | text
 *
 * VLM 后端新增类型：header | footer | page_number | aside_text | page_footnote |
 *   list | code | image_caption | image_footnote | table_body |
 *   image_body | interline_equation
 *
 * 内部归一化类型（middle.json 二级块类型）：image_body | image_caption |
 *   image_footnote | table_body | table_caption | table_footnote
 */
export type BboxType =
  // pipeline 后端原始类型
  | 'title'
  | 'text'
  | 'plain_text'
  | 'abandon'
  | 'discarded'
  | 'image'
  | 'figure'
  | 'figure_caption'
  | 'table'
  | 'table_body'
  | 'table_caption'
  | 'table_footnote'
  | 'formula'
  | 'isolate_formula'
  | 'formula_caption'
  | 'interline_equation'
  | 'image_body'
  | 'image_caption'
  | 'image_footnote'
  | 'embedding'
  | 'isolated'
  // VLM 后端新增类型
  | 'header'
  | 'footer'
  | 'page_number'
  | 'aside_text'
  | 'page_footnote'
  | 'list'
  | 'code'
  | 'code_body'
  | 'code_caption'
  | 'ref_text'
  | (string & {}) // 允许未知类型，降级使用 default 颜色

/**
 * 标注框颜色配置
 */
export interface BboxColor {
  line: string
  fill: string
}

/**
 * 单个标注框
 *
 * bbox 坐标系：
 * - Pipeline 后端（middle.json preproc_blocks / discarded_blocks）：绝对像素坐标 [x0, y0, x1, y1]
 * - VLM 后端 model.json：相对百分比坐标（0-1），需要乘以 page_size 转换为像素坐标后再传入
 *
 * layer.js 使用绝对像素坐标绘图，因此调用方须确保传入的是像素坐标。
 */
export interface Bbox {
  type: BboxType
  bbox: [number, number, number, number]
  /** 颜色可选，未设置时由 PDF_COLOR_PICKER 按 type 自动映射 */
  color?: BboxColor
}

/**
 * middle.json 单页原始数据结构
 *
 * 适用于 pipeline 和 VLM 后端，直接对应 middle.json 的 pdf_info 数组元素。
 */
export interface MiddlePageInfo {
  /** 页面 0-based 索引 */
  page_idx: number
  /** 页面尺寸 [width, height]（像素） */
  page_size: [number, number]
  /** 预处理块（含 bbox 绝对像素坐标） */
  preproc_blocks?: Array<{ type: string; bbox: number[]; [key: string]: any }>
  /** 丢弃块 */
  discarded_blocks?: Array<{ type: string; bbox: number[]; [key: string]: any }>
  /** 分段后内容块 */
  para_blocks?: Array<{ type: string; bbox: number[]; [key: string]: any }>
}

/**
 * 提取层项（单页），用于传给 PdfViewer 进行标注渲染
 */
export interface ExtractLayerItem {
  preproc_blocks?: Bbox[]
  discarded_blocks?: Bbox[]
}

/**
 * 提取层数据（所有页面），key 为 0-based 页码索引
 */
export type ExtractLayerData = Record<number, ExtractLayerItem>

/**
 * PDF 任务信息
 */
export interface TaskInfo {
  pdfUrl?: string
  /**
   * 每页的 Markdown 内容字符串数组（已加载好的内容，非 URL）
   * 数组长度等于 PDF 页数，index 与页码一一对应（0-based）
   */
  markdownContent?: string[]
  /** @deprecated 旧字段名，请使用 markdownContent */
  markdownUrl?: string[]
  layerData?: ExtractLayerData
}

/**
 * iframe 消息类型
 */
export type IframeMessageType = 'initExtractLayerData' | 'pageChange' | 'setPage' | 'getPageNum' | 'title'

/**
 * iframe 消息
 */
export interface IframeMessage {
  type: IframeMessageType
  data?: any
}

// ──────────────────────────────────────────────
// VLM 后端 model.json 原始结构
// ──────────────────────────────────────────────

/**
 * VLM model.json 单个内容块
 * bbox 为 0-1 相对百分比坐标 [x0, y0, x1, y1]
 */
export interface VlmBlock {
  type: string
  bbox: [number, number, number, number]
  angle?: number
  score?: number | null
  content?: string
  format?: string | null
  block_tags?: any
  content_tags?: any
}

/**
 * VLM model.json 完整结构：外层数组=页面，内层数组=该页块列表
 */
export type VlmModelJson = VlmBlock[][]

// ──────────────────────────────────────────────
// 工具函数：将 VLM model.json 转为 ExtractLayerData
// ──────────────────────────────────────────────

/**
 * 将 VLM backend 的 model.json 转换为组件所需的 ExtractLayerData 格式
 *
 * VLM bbox 是 0-1 相对坐标，page_size 用来换算成绝对像素坐标（pixel = ratio * size）
 *
 * @param modelJson  VLM model.json 数据
 * @param pageSizes  每页尺寸数组，index 对应页码（[width, height]）
 */
export function vlmModelJsonToLayerData(modelJson: VlmModelJson, pageSizes: Array<[number, number]>): ExtractLayerData {
  const result: ExtractLayerData = {}
  modelJson.forEach((pageBlocks, pageIdx) => {
    const [pageWidth, pageHeight] = pageSizes[pageIdx] ?? [1, 1]
    const preproc_blocks: Bbox[] = pageBlocks.map((block) => ({
      type: block.type,
      bbox: [
        block.bbox[0] * pageWidth,
        block.bbox[1] * pageHeight,
        block.bbox[2] * pageWidth,
        block.bbox[3] * pageHeight,
      ],
    }))
    result[pageIdx] = { preproc_blocks }
  })
  return result
}

/**
 * 将 pipeline backend 的 middle.json pdf_info 转换为 ExtractLayerData
 *
 * Pipeline bbox 已经是绝对像素坐标，直接使用。
 *
 * @param pdfInfo  middle.json 的 pdf_info 数组
 */
export function pipelineMiddleToLayerData(pdfInfo: MiddlePageInfo[]): ExtractLayerData {
  const result: ExtractLayerData = {}
  pdfInfo.forEach((page) => {
    result[page.page_idx] = {
      preproc_blocks: (page.preproc_blocks ?? []).map((b) => ({
        type: b.type,
        bbox: b.bbox as [number, number, number, number],
      })),
      discarded_blocks: (page.discarded_blocks ?? []).map((b) => ({
        type: b.type,
        bbox: b.bbox as [number, number, number, number],
      })),
    }
  })
  return result
}
