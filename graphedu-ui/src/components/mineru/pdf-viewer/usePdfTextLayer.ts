/**
 * PDF 文本层 composable
 *
 * 职责：
 * 1. 使用 pdfjs-dist 的 TextLayer API 渲染可选中的文本层
 * 2. 文本层覆盖在 canvas 上方，支持原生的 window.getSelection()
 * 3. 这是 Phase 2 右键引用功能的基础
 */
import { TextLayer } from 'pdfjs-dist'

export interface UsePdfTextLayerReturn {
  /** 渲染文本层 */
  renderTextLayer: (page: any, container: HTMLElement, viewport: any) => Promise<void>
  /** 清空文本层 */
  clearTextLayer: (container: HTMLElement) => void
}

export function usePdfTextLayer(): UsePdfTextLayerReturn {
  let currentTextLayer: TextLayer | null = null

  async function renderTextLayer(page: any, container: HTMLElement, viewport: any): Promise<void> {
    clearTextLayer(container)

    // --total-scale-factor 是 pdfjs text_layer_builder.css 计算字体大小的必要变量。
    // TextLayer 内部的 setLayerDimensions 会消费它，但从不设置它，
    // 必须由调用方在创建 TextLayer 之前手动设置。
    container.style.setProperty('--total-scale-factor', String(viewport.scale))
    container.style.setProperty('--scale-round-x', '1px')
    container.style.setProperty('--scale-round-y', '1px')

    const textContentSource = await page.streamTextContent({
      includeMarkedContent: true,
    })

    currentTextLayer = new TextLayer({
      textContentSource,
      container,
      viewport,
    })

    await currentTextLayer.render()
  }

  function clearTextLayer(container: HTMLElement): void {
    currentTextLayer = null
    container.replaceChildren()
  }

  return {
    renderTextLayer,
    clearTextLayer,
  }
}
