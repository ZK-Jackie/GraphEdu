/**
 * PDF 单页 Canvas 渲染 composable
 *
 * 职责：
 * 1. 将 PDFPageProxy 渲染到 HTMLCanvasElement
 * 2. 处理 HiDPI（devicePixelRatio）确保清晰渲染
 * 3. 管理渲染任务（缩放/滚动时取消旧渲染）
 * 4. 返回渲染后的实际像素尺寸
 */
import { readonly, ref, type Ref } from 'vue'

export interface UsePdfPageRendererReturn {
  /** 是否正在渲染 */
  isRendering: Readonly<Ref<boolean>>
  /**
   * 渲染页面到 canvas
   * 返回 CSS 尺寸（不含 DPR 缩放）
   */
  renderPage: (
    page: any,
    canvas: HTMLCanvasElement,
    scale: number,
    rotation?: number
  ) => Promise<{ cssWidth: number; cssHeight: number }>
  /** 取消当前渲染 */
  cancelRender: () => void
}

export function usePdfPageRenderer(): UsePdfPageRendererReturn {
  const isRendering = ref(false)
  let currentTask: { cancel: () => void; promise: Promise<void> } | null = null

  function cancelRender(): void {
    if (currentTask) {
      currentTask.cancel()
      currentTask = null
    }
    isRendering.value = false
  }

  async function renderPage(
    page: any,
    canvas: HTMLCanvasElement,
    scale: number,
    rotation: number = 0
  ): Promise<{ cssWidth: number; cssHeight: number }> {
    cancelRender()

    // 获取 CSS 尺寸的 viewport
    const viewport = page.getViewport({ scale, rotation })
    const cssWidth = viewport.width
    const cssHeight = viewport.height

    // HiDPI：canvas 实际像素 = CSS 尺寸 × devicePixelRatio
    const dpr = window.devicePixelRatio || 1
    canvas.width = Math.floor(cssWidth * dpr)
    canvas.height = Math.floor(cssHeight * dpr)

    // CSS 显示尺寸保持不变
    canvas.style.width = `${Math.floor(cssWidth)}px`
    canvas.style.height = `${Math.floor(cssHeight)}px`

    const ctx = canvas.getContext('2d')
    if (!ctx) {
      throw new Error('无法获取 canvas 2d 上下文')
    }

    isRendering.value = true

    try {
      // 用 transform 让 pdfjs 在高分辨率 canvas 上正确渲染
      const transform = dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : undefined

      currentTask = page.render({
        canvasContext: ctx,
        viewport,
        transform,
      })

      await currentTask!.promise

      return { cssWidth, cssHeight }
    } catch (e: any) {
      if (e?.name === 'RenderingCancelledException') {
        return { cssWidth, cssHeight }
      }
      throw e
    } finally {
      currentTask = null
      isRendering.value = false
    }
  }

  return {
    isRendering: readonly(isRendering),
    renderPage,
    cancelRender,
  }
}
