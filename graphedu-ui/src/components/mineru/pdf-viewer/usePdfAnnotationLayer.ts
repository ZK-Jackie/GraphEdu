/**
 * PDF 标注层 composable
 *
 * 职责：在 canvas 上绘制 bbox 矩形框，覆盖在 PDF 渲染内容上方
 * 坐标系：bbox 使用 PDF 原始像素坐标（scale=1），绘制时乘以当前缩放比
 */
import { PDF_COLOR_PICKER } from '../constants'
import type { BboxColor } from '../types'

/** 单个标注框（已含颜色） */
export interface BboxItem {
  type: string
  bbox: number[] // [x0, y0, x1, y1]
  color?: BboxColor
}

export interface UsePdfAnnotationLayerReturn {
  /** 在 canvas 上绘制标注框 */
  renderAnnotations: (canvas: HTMLCanvasElement, bboxes: BboxItem[], scale: number) => void
  /** 清空标注 */
  clearAnnotations: (canvas: HTMLCanvasElement) => void
}

export function usePdfAnnotationLayer(): UsePdfAnnotationLayerReturn {
  function renderAnnotations(canvas: HTMLCanvasElement, bboxes: BboxItem[], scale: number): void {
    if (bboxes.length === 0) {
      clearAnnotations(canvas)
      return
    }

    const parent = canvas.parentElement
    if (!parent) return

    const dpr = window.devicePixelRatio || 1
    const cssWidth = parent.clientWidth
    const cssHeight = parent.clientHeight

    canvas.width = Math.floor(cssWidth * dpr)
    canvas.height = Math.floor(cssHeight * dpr)
    canvas.style.width = `${cssWidth}px`
    canvas.style.height = `${cssHeight}px`

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    for (const bbox of bboxes) {
      const [x0 = 0, y0 = 0, x1 = 0, y1 = 0] = bbox.bbox
      const color = bbox.color ?? PDF_COLOR_PICKER[bbox.type] ?? PDF_COLOR_PICKER.default
      if (!color) continue

      const x = x0 * scale
      const y = y0 * scale
      const w = (x1 - x0) * scale
      const h = (y1 - y0) * scale

      // 半透明填充
      ctx.fillStyle = color.fill
      ctx.fillRect(x, y, w, h)

      // 边框
      ctx.strokeStyle = color.line
      ctx.lineWidth = 1.5
      ctx.strokeRect(x, y, w, h)
    }
  }

  function clearAnnotations(canvas: HTMLCanvasElement): void {
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
    canvas.width = 0
    canvas.height = 0
  }

  return { renderAnnotations, clearAnnotations }
}
