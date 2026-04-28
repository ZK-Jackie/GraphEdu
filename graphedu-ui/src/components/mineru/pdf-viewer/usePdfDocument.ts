/**
 * PDF 文档加载与管理 composable
 *
 * 职责：
 * 1. 通过 pdfjs-dist 的 getDocument 加载 PDF 文档
 * 2. 暴露页数、加载状态、错误状态
 * 3. 提供 getPage 方法获取指定页的 PDFPageProxy
 * 4. 组件卸载时自动销毁文档释放资源
 */
import { readonly, ref, shallowRef, type Ref } from 'vue'
import { getDocument } from 'pdfjs-dist'

import '@/components/mineru/pdf-viewer/worker'
import { ViteEnv } from '@/constants'

/** PDF 文档代理（用 any 规避 pdfjs-dist 5.x 内部类型不暴露的问题） */
type PdfDoc = any
type PdfPage = any

export interface UsePdfDocumentReturn {
  /** PDF 文档代理 */
  pdfDoc: Ref<PdfDoc | null>
  /** 总页数 */
  totalPages: Readonly<Ref<number>>
  /** 是否正在加载 */
  isLoading: Readonly<Ref<boolean>>
  /** 加载错误 */
  error: Readonly<Ref<Error | null>>
  /** 加载文档 */
  loadDocument: (source: string | ArrayBuffer) => Promise<void>
  /** 销毁文档 */
  destroy: () => void
  /** 获取指定页（1-based） */
  getPage: (pageNum: number) => Promise<PdfPage>
}

/**
 * 构建资源代理 URL
 *
 * 优先使用 fileId 通过后端代理避免跨域，降级使用直接 URL
 */
export function buildSourceUrl(fileId?: number, pdfUrl?: string): string {
  if (fileId) return `${ViteEnv.VITE_API_BASE_URL}/common/proxy/file/${fileId}`
  if (pdfUrl) return pdfUrl
  return ''
}

export function usePdfDocument(): UsePdfDocumentReturn {
  const pdfDoc = shallowRef<PdfDoc | null>(null)
  const totalPages = ref(0)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  let loadingTask: { destroy: () => void; promise: Promise<any> } | null = null

  async function loadDocument(source: string | ArrayBuffer): Promise<void> {
    destroy()

    if (!source) {
      error.value = new Error('无效的 PDF 来源')
      return
    }

    isLoading.value = true
    error.value = null

    try {
      loadingTask = getDocument({
        data: typeof source === 'string' ? undefined : source,
        url: typeof source === 'string' ? source : undefined,
        useSystemFonts: true,
      }) as any

      pdfDoc.value = await loadingTask!.promise
      totalPages.value = pdfDoc.value!.numPages
    } catch (e: any) {
      if (e?.name !== 'RenderingCancelledException') {
        error.value = e instanceof Error ? e : new Error(String(e))
      }
    } finally {
      isLoading.value = false
    }
  }

  function destroy(): void {
    if (loadingTask) {
      loadingTask.destroy()
      loadingTask = null
    }
    if (pdfDoc.value) {
      pdfDoc.value.destroy()
      pdfDoc.value = null
    }
    totalPages.value = 0
    error.value = null
  }

  async function getPage(pageNum: number): Promise<PdfPage> {
    if (!pdfDoc.value) throw new Error('PDF 文档未加载')
    return pdfDoc.value.getPage(pageNum)
  }

  return {
    pdfDoc,
    totalPages: readonly(totalPages),
    isLoading: readonly(isLoading),
    error: readonly(error),
    loadDocument,
    destroy,
    getPage,
  }
}
