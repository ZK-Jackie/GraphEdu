/**
 * MinerU 组件常量配置
 */

import type { BboxColor } from '../types'

/**
 * 标注框颜色映射表
 *
 * 覆盖 pipeline 和 VLM 两种后端的所有已知 block type。
 * 对于不在表中的类型，使用 default 颜色降级。
 *
 * 颜色语义约定：
 * - 紫色系  → 标题/结构
 * - 粉色系  → 正文文本
 * - 绿色系  → 图片/图像
 * - 黄色系  → 表格
 * - 橙色系  → 公式
 * - 青色系  → 图注/表注/代码注
 * - 紫罗兰  → 脚注/边注
 * - 灰色系  → 丢弃块（页眉页脚页码等）
 */
export const PDF_COLOR_PICKER: Record<string, BboxColor> = {
  // ── 标题 ────────────────────────────────────────────────
  title: {
    line: 'rgba(121, 124, 255, 1)',
    fill: 'rgba(121, 124, 255, 0.3)',
  },

  // ── 正文文本 ─────────────────────────────────────────────
  text: {
    line: 'rgba(230, 122, 171, 1)',
    fill: 'rgba(230, 122, 171, 0.3)',
  },
  plain_text: {
    // pipeline 别名
    line: 'rgba(230, 122, 171, 1)',
    fill: 'rgba(230, 122, 171, 0.3)',
  },

  // ── 图片 ─────────────────────────────────────────────────
  image: {
    line: 'rgba(149, 226, 115, 1)',
    fill: 'rgba(149, 226, 115, 0.3)',
  },
  figure: {
    // pipeline 别名
    line: 'rgba(149, 226, 115, 1)',
    fill: 'rgba(149, 226, 115, 0.3)',
  },
  image_body: {
    line: 'rgba(149, 226, 115, 1)',
    fill: 'rgba(149, 226, 115, 0.3)',
  },
  image_caption: {
    line: 'rgba(0, 188, 212, 1)',
    fill: 'rgba(0, 188, 212, 0.3)',
  },
  image_footnote: {
    line: 'rgba(156, 39, 176, 1)',
    fill: 'rgba(156, 39, 176, 0.3)',
  },
  figure_caption: {
    // pipeline 别名
    line: 'rgba(0, 188, 212, 1)',
    fill: 'rgba(0, 188, 212, 0.3)',
  },

  // ── 表格 ─────────────────────────────────────────────────
  table: {
    line: 'rgba(255, 193, 7, 1)',
    fill: 'rgba(255, 193, 7, 0.3)',
  },
  table_body: {
    line: 'rgba(255, 193, 7, 1)',
    fill: 'rgba(255, 193, 7, 0.3)',
  },
  table_caption: {
    line: 'rgba(0, 188, 212, 1)',
    fill: 'rgba(0, 188, 212, 0.3)',
  },
  table_footnote: {
    line: 'rgba(156, 39, 176, 1)',
    fill: 'rgba(156, 39, 176, 0.3)',
  },

  // ── 公式 ─────────────────────────────────────────────────
  formula: {
    line: 'rgba(255, 152, 0, 1)',
    fill: 'rgba(255, 152, 0, 0.3)',
  },
  isolate_formula: {
    // pipeline 别名
    line: 'rgba(255, 152, 0, 1)',
    fill: 'rgba(255, 152, 0, 0.3)',
  },
  formula_caption: {
    line: 'rgba(255, 87, 34, 1)',
    fill: 'rgba(255, 87, 34, 0.3)',
  },
  interline_equation: {
    line: 'rgba(255, 152, 0, 1)',
    fill: 'rgba(255, 152, 0, 0.3)',
  },
  embedding: {
    // pipeline 行内公式别名
    line: 'rgba(255, 152, 0, 1)',
    fill: 'rgba(255, 152, 0, 0.3)',
  },
  isolated: {
    // pipeline 行间公式别名
    line: 'rgba(255, 152, 0, 1)',
    fill: 'rgba(255, 152, 0, 0.3)',
  },

  // ── 代码 ─────────────────────────────────────────────────
  code: {
    line: 'rgba(63, 81, 181, 1)',
    fill: 'rgba(63, 81, 181, 0.3)',
  },
  code_body: {
    line: 'rgba(63, 81, 181, 1)',
    fill: 'rgba(63, 81, 181, 0.3)',
  },
  code_caption: {
    line: 'rgba(3, 169, 244, 1)',
    fill: 'rgba(3, 169, 244, 0.3)',
  },

  // ── 列表 ─────────────────────────────────────────────────
  list: {
    line: 'rgba(76, 175, 80, 1)',
    fill: 'rgba(76, 175, 80, 0.3)',
  },
  index: {
    // pipeline 目录块别名
    line: 'rgba(76, 175, 80, 1)',
    fill: 'rgba(76, 175, 80, 0.3)',
  },

  // ── 丢弃块（页眉/页脚/页码等） ─────────────────────────────
  discarded: {
    line: 'rgba(164, 164, 164, 1)',
    fill: 'rgba(164, 164, 164, 0.25)',
  },
  abandon: {
    // pipeline 别名
    line: 'rgba(164, 164, 164, 1)',
    fill: 'rgba(164, 164, 164, 0.25)',
  },
  header: {
    line: 'rgba(189, 189, 189, 1)',
    fill: 'rgba(189, 189, 189, 0.2)',
  },
  footer: {
    line: 'rgba(189, 189, 189, 1)',
    fill: 'rgba(189, 189, 189, 0.2)',
  },
  page_number: {
    line: 'rgba(189, 189, 189, 1)',
    fill: 'rgba(189, 189, 189, 0.2)',
  },
  aside_text: {
    line: 'rgba(158, 158, 158, 1)',
    fill: 'rgba(158, 158, 158, 0.25)',
  },
  page_footnote: {
    line: 'rgba(156, 39, 176, 1)',
    fill: 'rgba(156, 39, 176, 0.25)',
  },
  ref_text: {
    line: 'rgba(158, 158, 158, 1)',
    fill: 'rgba(158, 158, 158, 0.25)',
  },

  // ── 默认（兜底） ─────────────────────────────────────────
  default: {
    line: 'rgba(158, 158, 158, 1)',
    fill: 'rgba(158, 158, 158, 0.3)',
  },
}

/**
 * 事件名称常量（部分已弃用，保留供外部引用兼容）
 */
export const EVENT_NAMES = {
  /**
   * Markdown 驱动 PDF 页面切换
   */
  MD_DRIVE_PDF: 'mdDrivePdf',

  /**
   * PDF 驱动 Markdown 页面切换
   */
  PDF_DRIVE_MD: 'pdfDriveMd',

  /**
   * PDF 加载完成
   */
  PDF_LOADED: 'pdfLoaded',

  /**
   * 标注层显示状态变化
   */
  LAYER_TOGGLE: 'layerToggle',
} as const

/**
 * 默认 Markdown 预览类型
 */
export const DEFAULT_MD_PREVIEW_TYPE = 'preview' as const

/**
 * 滚动阈值（像素），用于判断哪个页面可见
 */
export const SCROLL_THRESHOLD = 200
