/**
 * 用户空闲检测 composable
 *
 * 监听用户交互事件（鼠标、键盘、滚动、触摸），超过指定阈值无动作则标记为空闲。
 * 用于学习时长追踪中排除用户未实际操作的时间段。
 */
import { onBeforeUnmount, onMounted, readonly, ref } from 'vue'

export interface UseIdleDetectionOptions {
  /** 空闲阈值（毫秒），默认 120_000 (2min) */
  timeout?: number
  /** 检查间隔（毫秒），默认 30_000 */
  checkInterval?: number
}

export interface UseIdleDetectionReturn {
  /** 是否处于空闲状态 */
  isIdle: Readonly<Ref<boolean>>
  /** 最后一次活动的时间戳 */
  lastActivityTime: Readonly<Ref<number>>
  /** 手动重置空闲状态（模拟一次用户活动） */
  resetIdle: () => void
}

/** 需要监听的用户交互事件 */
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'] as const

export function useIdleDetection(options: UseIdleDetectionOptions = {}): UseIdleDetectionReturn {
  const { timeout = 120_000, checkInterval = 30_000 } = options

  const isIdle = ref(false)
  const lastActivityTime = ref(Date.now())

  let checkTimer: ReturnType<typeof setInterval> | null = null

  function onUserActivity() {
    lastActivityTime.value = Date.now()
    // 重新活跃时清除空闲标记
    if (isIdle.value) {
      isIdle.value = false
    }
  }

  function checkIdle() {
    const elapsed = Date.now() - lastActivityTime.value
    if (elapsed >= timeout && !isIdle.value) {
      isIdle.value = true
    }
  }

  function resetIdle() {
    lastActivityTime.value = Date.now()
    isIdle.value = false
  }

  function startDetection() {
    for (const event of ACTIVITY_EVENTS) {
      document.addEventListener(event, onUserActivity, { passive: true })
    }
    checkTimer = setInterval(checkIdle, checkInterval)
  }

  function stopDetection() {
    for (const event of ACTIVITY_EVENTS) {
      document.removeEventListener(event, onUserActivity)
    }
    if (checkTimer) {
      clearInterval(checkTimer)
      checkTimer = null
    }
  }

  onMounted(() => {
    startDetection()
  })

  onBeforeUnmount(() => {
    stopDetection()
  })

  return {
    isIdle: readonly(isIdle),
    lastActivityTime: readonly(lastActivityTime),
    resetIdle,
  }
}
