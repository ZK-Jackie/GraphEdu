import { ref, onMounted, onUnmounted, nextTick, watch, type Ref, type ShallowRef } from 'vue'

type GenericElement =
  | Element
  | string
  | { $el: Element }
  | number
  | Readonly<ShallowRef<Element | null>>
  | Ref<Element | null | undefined>

/**
 * useAdaptiveTable Hook 配置参数
 */
interface UseAdaptiveTableOptions {
  /** 包裹表格的容器元素 ref */
  containerRef: GenericElement
  /** 需要减去高度的其他元素 ref 数组（如表头） */
  subtractRefs?: GenericElement[]
  /** 最小高度，当计算值小于此值时使用此值 */
  minHeight?: number
  /** 阈值模式固定值，当窗口高度小于阈值时返回此值 */
  shortThresholdTableHeight?: number | null
  /** 阈值模式阈值，窗口高度小于此值视为"过短" */
  shortThreshold?: number
}

/**
 * 自适应表格高度 Hook
 * @param {UseAdaptiveTableOptions} options - 配置项
 * @returns {Object} - { tableScrollY: Ref<number>, isViewportTooShort: Ref<boolean>, isContainerTooShort: Ref<boolean>, recalc: Function }
 */
export function useAdaptiveTable({
  containerRef,
  subtractRefs = [],
  minHeight = 0,
  shortThresholdTableHeight = null,
  shortThreshold = 600,
}: UseAdaptiveTableOptions) {
  const tableScrollY = ref(200)
  const isViewportTooShort = ref(false)
  const isContainerTooShort = ref(false)
  let containerElement: HTMLElement | null = null
  let subtractElements: (HTMLElement | null)[] = []

  let resizeObserver: ResizeObserver | null = null
  let resizeTimer: ReturnType<typeof setTimeout> | null = null

  const calculateScrollY = () => {
    // 获取容器元素
    if (!containerElement) return

    // 使用 requestAnimationFrame 确保最新布局
    requestAnimationFrame(() => {
      // 获取容器高度
      const containerHeight = getContainerAvailableHeight(containerElement!)
      // console.log('[useAdaptiveTable] 容器高度:', containerHeight)

      // 检查是否处于阈值模式（容器高度过短）
      const tooShort = containerHeight < shortThreshold
      isContainerTooShort.value = tooShort

      // 获取其他元素高度
      let totalSubtract = 0
      subtractElements.forEach((el, idx) => {
        if (el) {
          const elvh = getVerticalHeight(el)
          // console.log(`[useAdaptiveTable] subtractRefs[${idx}] 高度:`, elvh)
          totalSubtract += elvh
          return
        }
        console.warn('[useAdaptiveTable] 无法获取 subtractRefs 中的元素，索引:', idx)
      })

      // 计算可用高度
      let availableHeight = containerHeight - totalSubtract

      // 阈值模式：返回固定值
      if (tooShort && shortThresholdTableHeight !== null) {
        // console.log(`[useAdaptiveTable] 阈值模式：使用固定高度 ${shortThresholdTableHeight}px`)
        tableScrollY.value = shortThresholdTableHeight
      } else {
        // 正常模式：应用最小高度保护
        availableHeight = Math.max(availableHeight, minHeight)
        tableScrollY.value = Math.max(Math.round(availableHeight), 0)
        // console.log(`[useAdaptiveTable] 正常模式：可用高度 ${availableHeight}px`)
      }
    })
  }

  // 窗口 resize 备用处理
  const handleResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(calculateScrollY, 100)
  }

  // 检查阈值模式
  const checkThresholdMode = () => {
    isViewportTooShort.value = window.innerHeight < shortThreshold
    isContainerTooShort.value = isViewportTooShort.value
  }

  onMounted(() => {
    // 初次计算
    containerElement = resolveElement(containerRef)
    subtractElements = subtractRefs.map((r) => resolveElement(r, containerElement)).filter((el): el is HTMLElement => el !== null)
    calculateScrollY()

    // 监听窗口 resize（兜底）
    window.addEventListener('resize', handleResize)
    // 监听阈值模式
    window.addEventListener('resize', checkThresholdMode)

    // 初始化 ResizeObserver
    resizeObserver = new ResizeObserver(() => {
      if (isViewportTooShort.value) return
      // 防抖，避免连续触发
      if (resizeTimer) clearTimeout(resizeTimer)
      resizeTimer = setTimeout(calculateScrollY, 100)
    })

    // 观察所有可能影响高度的稳定元素（包括表头）
    const rawElements = [containerElement, ...subtractElements]
    const elementsToObserve = rawElements.filter((el): el is HTMLElement => el != null)

    elementsToObserve.forEach((el) => resizeObserver!.observe(el))
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('resize', checkThresholdMode)
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }
  })

  // 阈值模式变化时重新计算
  watch(isViewportTooShort, (newVal) => {
    if (!newVal) {
      nextTick(() => {
        calculateScrollY()
      })
    }
  })

  // 手动重新计算方法（可对外暴露）
  const recalc = () => {
    nextTick(calculateScrollY)
  }

  return {
    tableScrollY,
    isViewportTooShort,
    isContainerTooShort,
    recalc,
  }
}

/**
 * 获取容器的可用高度（减去上下 padding）
 * @param containerEl - 容器元素
 * @returns {number} - 可用高度
 */
const getContainerAvailableHeight = (containerEl: HTMLElement): number => {
  if (!containerEl) return 0
  const style = window.getComputedStyle(containerEl)
  const height = containerEl.clientHeight ?? 0
  const pt = parseFloat(style.paddingTop) || 0
  const pb = parseFloat(style.paddingBottom) || 0
  return height - pt - pb
}

/**
 * 获取元素的垂直高度（包括 padding）
 * @param el - 目标元素或像素值
 * @returns {number} - 元素的垂直高度
 */
const getVerticalHeight = (el: HTMLElement | number): number => {
  if (!el) return 0
  if (typeof el === 'number') return el
  const style = window.getComputedStyle(el)
  const height = el.offsetHeight
  const pt = parseFloat(style.paddingTop) || 0
  const pb = parseFloat(style.paddingBottom) || 0
  return pt + pb + height
}

/**
 * 将输入转换为 HTMLElement
 * @param input - 可以是选择器字符串、原生 DOM 元素、Vue 组件实例（具有 $el 属性）或 ref 对象
 * @param rootElement - 可选的根元素，用于在特定上下文中查询选择器
 * @returns {HTMLElement|null} - 解析后的 HTMLElement 或 null
 */
function resolveElement(input: unknown, rootElement?: HTMLElement | null): HTMLElement | null {
  if (!input) return null

  // 解包 ref
  if (isRef(input)) {
    return resolveElement(input.value)
  }

  // 选择器字符串
  if (typeof input === 'string') {
    return rootElement?.querySelector(input) ?? null
  }

  // 原生 DOM 元素
  if (input instanceof HTMLElement) {
    return input
  }

  // Vue 组件实例（具有 $el 属性）
  if (isVueComponent(input)) {
    return input.$el instanceof HTMLElement ? input.$el : null
  }

  return null
}

function isRef(value: any): value is { value: unknown } {
  return value && typeof value === 'object' && '__v_isRef' in value
}

function isVueComponent(value: any): value is { $el: Element } {
  return value && typeof value === 'object' && '$el' in value
}
