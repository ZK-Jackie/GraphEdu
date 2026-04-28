/**
 * PDF 查看器内部类型定义
 */

/** 缩放模式 */
export type ZoomMode = 'manual' | 'fit-width' | 'fit-page'

/** 查看器状态 */
export interface ViewerState {
  currentPage: number
  totalPages: number
  scale: number
  zoomMode: ZoomMode
  rotation: number
}

/** 页面原始尺寸（PDF points） */
export interface PageSize {
  width: number
  height: number
}

/** 虚拟滚动可见范围（0-based 页码索引） */
export interface VisibleRange {
  start: number
  end: number
}
