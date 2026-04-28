/**
 * PDF 虚拟滚动 composable
 *
 * 职责：
 * 1. 使用 IntersectionObserver 追踪可见页面
 * 2. 计算 visibleRange（含 buffer 区）
 * 3. 计算当前"活跃"页码（1-based，用于工具栏显示和页码同步）
 * 4. 提供 scrollToPage 方法
 */
import { readonly, ref, watch, type Ref } from 'vue'
import type { VisibleRange } from './types'

export interface UsePdfVirtualScrollOptions {
  /** 总页数 */
  totalPages: Ref<number>
  /** 滚动容器 ref */
  containerRef: Ref<HTMLElement | undefined>
  /** 缓冲页数（视口上下各多渲染几页） */
  bufferPages?: number
}

export interface UsePdfVirtualScrollReturn {
  /** 可见范围（0-based，含 buffer） */
  visibleRange: Readonly<Ref<VisibleRange>>
  /** 当前页码（1-based） */
  currentPage: Readonly<Ref<number>>
  /** 注册页码 DOM 元素 */
  registerPageElement: (pageNum: number, el: HTMLElement) => void
  /** 注销页码 DOM 元素 */
  unregisterPageElement: (pageNum: number) => void
  /** 滚动到指定页码（1-based） */
  scrollToPage: (page: number) => void
}

export function usePdfVirtualScroll(options: UsePdfVirtualScrollOptions): UsePdfVirtualScrollReturn {
  const { totalPages, containerRef, bufferPages = 2 } = options

  const visibleRange = ref<VisibleRange>({ start: 0, end: 0 })
  const currentPage = ref(1)

  // 页码 → DOM 元素映射
  const pageElements = new Map<number, HTMLElement>()

  // IntersectionObserver 实例
  let observer: IntersectionObserver | null = null

  // 追踪哪些页面当前在视口中
  const intersectingPages = new Set<number>()

  function recalcVisibleRange(): void {
    const pages = Array.from(intersectingPages).sort((a, b) => a - b)
    if (pages.length === 0) {
      visibleRange.value = { start: 0, end: 0 }
      return
    }

    const first = Math.max(0, Math.min(...pages) - bufferPages)
    const last = Math.min(totalPages.value - 1, Math.max(...pages) + bufferPages)

    visibleRange.value = { start: first, end: last }
  }

  function recalcCurrentPage(): void {
    if (!containerRef.value) return

    const container = containerRef.value
    const containerRect = container.getBoundingClientRect()
    // 视口中心 Y 坐标
    const center = containerRect.top + containerRect.height / 2

    let closestPage = 1
    let closestDistance = Infinity

    for (const [pageNum, el] of pageElements) {
      const rect = el.getBoundingClientRect()
      const pageCenter = rect.top + rect.height / 2
      const distance = Math.abs(pageCenter - center)
      if (distance < closestDistance) {
        closestDistance = distance
        closestPage = pageNum
      }
    }

    currentPage.value = closestPage
  }

  function setupObserver(): void {
    if (observer) return

    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const pageNum = Number(entry.target.getAttribute('data-page-number'))
          if (!pageNum) continue

          if (entry.isIntersecting) {
            intersectingPages.add(pageNum)
          } else {
            intersectingPages.delete(pageNum)
          }
        }
        recalcVisibleRange()
        recalcCurrentPage()
      },
      {
        root: containerRef.value ?? null,
        rootMargin: '200px 0px',
        threshold: 0,
      }
    )
  }

  function registerPageElement(pageNum: number, el: HTMLElement): void {
    pageElements.set(pageNum, el)
    if (!observer) setupObserver()
    observer!.observe(el)
  }

  function unregisterPageElement(pageNum: number): void {
    const el = pageElements.get(pageNum)
    if (el && observer) {
      observer.unobserve(el)
    }
    pageElements.delete(pageNum)
    intersectingPages.delete(pageNum)
  }

  function scrollToPage(page: number): void {
    const el = pageElements.get(page)
    if (!el) return

    // 使用 scrollIntoView 自动沿最近的滚动祖先定位，
    // 避免 offsetParent 链未经过滚动容器导致偏移计算错误
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // 总页数变化时重置
  watch(totalPages, (newTotal) => {
    intersectingPages.clear()
    visibleRange.value = { start: 0, end: Math.max(0, newTotal - 1) }
    currentPage.value = 1
  })

  return {
    visibleRange: readonly(visibleRange),
    currentPage: readonly(currentPage),
    registerPageElement,
    unregisterPageElement,
    scrollToPage,
  }
}
