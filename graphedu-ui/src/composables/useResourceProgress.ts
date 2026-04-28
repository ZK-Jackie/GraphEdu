/**
 * 资料阅读进度上报 composable
 *
 * 职责：
 * 1. 定时（30s）上报增量阅读进度
 * 2. 页面失焦/关闭时发送最终进度
 * 3. 防抖：进度无变化时跳过上报
 * 4. 断点续学：获取上次阅读位置
 * 5. 资源加载完成后由调用方调用 startTracking() 启动计时
 * 6. 触及底部/末页时可调用 reportImmediate() 立即上报
 * 7. 空闲检测：2 分钟无操作暂停有效时长累计，区分 wall-clock / effective 时长
 */
import { onBeforeUnmount, onMounted, readonly, ref } from 'vue'
import { reportResourceProgress, getResourceProgressDetail } from '@/api/education/resourceProgress'
import { getToken } from '@/utils/token.ts'
import type { ResourceProgressReportDTO } from '@/types/api/education/stats.ts'
import { useIdleDetection } from '@/composables/useIdleDetection.ts'

/** 上报间隔（毫秒） */
const REPORT_INTERVAL_MS = 30_000
/** text 类型资源完成度阈值：scroll_percent 达到此值即视为 100% 完成 */
const TEXT_COMPLETION_THRESHOLD = 85

export interface UseResourceProgressOptions {
  /** 资料ID */
  resourceId: number
  /** 资料类型 */
  resourceType: 'pdf' | 'document' | 'text' | 'video' | 'image' | 'audio'
  /** 是否启用（默认 true） */
  enabled?: boolean
}

export function useResourceProgress(options: UseResourceProgressOptions) {
  const { resourceId, resourceType, enabled = true } = options

  /** 当前位置 */
  const position = ref<Record<string, any>>({})
  /** 累计 wall-clock 时长（秒） */
  const elapsedSeconds = ref(0)
  /** 累计有效时长（秒），排除空闲时段 */
  let effectiveSeconds = 0
  /** 上一次上报时的 wall-clock 时长快照，用于计算增量 */
  let lastReportedSeconds = 0
  /** 上一次上报时的有效时长快照 */
  let lastReportedEffectiveSeconds = 0
  /** 上一次上报时的位置快照 */
  let lastReportedPosition: Record<string, any> = {}
  /** 上次上报完成度（内部追踪，暂不暴露） */
  let _lastReportedRate: number | undefined
  /** 定时器 */
  let timer: ReturnType<typeof setInterval> | null = null
  /** 开始时间戳 */
  let startTimestamp = 0
  /** 是否已初始化（断点续学恢复完成） */
  const initialized = ref(false)
  /** 是否已开始追踪（资源加载完成后设为 true） */
  let tracking = false
  /** 资源是否已完成（从后端进度记录判断，已完成则跳过追踪） */
  const alreadyCompleted = ref(false)

  /** 空闲检测 */
  const { isIdle } = useIdleDetection()

  // ========================================================================
  // 上报逻辑
  // ========================================================================

  async function doReport(isFinal = false): Promise<void> {
    if (!enabled) return

    const incrementSeconds = elapsedSeconds.value - lastReportedSeconds
    const effectiveIncrement = effectiveSeconds - lastReportedEffectiveSeconds
    const idleIncrement = incrementSeconds - effectiveIncrement
    const posStr = JSON.stringify(position.value)
    const posChanged = posStr !== JSON.stringify(lastReportedPosition)

    // 防抖：无进度变化且非最终上报时跳过
    if (!isFinal && incrementSeconds === 0 && !posChanged) return

    const dto: ResourceProgressReportDTO = {
      resourceId,
      position: { ...position.value },
      durationSeconds: incrementSeconds,
      effectiveDurationSeconds: effectiveIncrement,
      idleSeconds: idleIncrement,
    }

    // 对于 image/audio/document 类型直接传 100（vue-office 不暴露页码信息）
    if (resourceType === 'image' || resourceType === 'audio' || resourceType === 'document') {
      dto.completionRate = 100
    }
    // 对于 text 类型，scroll_percent 达到阈值即视为完成（用户很难精确滚到底部）
    if (resourceType === 'text' && position.value?.scroll_percent !== undefined) {
      dto.completionRate =
        position.value.scroll_percent >= TEXT_COMPLETION_THRESHOLD
          ? 100
          : Math.round((position.value.scroll_percent / TEXT_COMPLETION_THRESHOLD) * 100)
    }

    try {
      const resp = await reportResourceProgress(dto)
      if (resp.code === 200) {
        lastReportedSeconds = elapsedSeconds.value
        lastReportedEffectiveSeconds = effectiveSeconds
        lastReportedPosition = JSON.parse(posStr)
        _lastReportedRate = resp.data?.completionRate
        // 后端确认完成 → 标记已完成，后续轮询将停止
        if ((resp.data?.completionRate ?? 0) >= 100) {
          alreadyCompleted.value = true
        }
      }
    } catch {
      // 上报失败不阻塞用户操作
    }
  }

  // ========================================================================
  // 定时上报
  // ========================================================================

  function startTimer() {
    if (timer) return
    startTimestamp = Date.now()
    timer = setInterval(() => {
      // 已完成则停止轮询
      if (alreadyCompleted.value) {
        stopTimer()
        return
      }
      // 累加经过时间
      const wallSeconds = Math.round((Date.now() - startTimestamp) / 1000)
      startTimestamp = Date.now()
      elapsedSeconds.value += wallSeconds
      // 仅在活跃状态下累计有效时长
      if (!isIdle.value) {
        effectiveSeconds += wallSeconds
      }
      doReport(false)
    }, REPORT_INTERVAL_MS)
  }

  function stopTimer() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  // ========================================================================
  // 页面关闭/失焦处理
  // ========================================================================

  function handleBeforeUnload() {
    // 累加剩余时间
    if (startTimestamp) {
      const wallSeconds = Math.round((Date.now() - startTimestamp) / 1000)
      startTimestamp = Date.now()
      elapsedSeconds.value += wallSeconds
      if (!isIdle.value) {
        effectiveSeconds += wallSeconds
      }
    }

    const incrementSeconds = elapsedSeconds.value - lastReportedSeconds
    if (incrementSeconds <= 0 && JSON.stringify(position.value) === JSON.stringify(lastReportedPosition)) return

    const effectiveIncrement = effectiveSeconds - lastReportedEffectiveSeconds
    const idleIncrement = incrementSeconds - effectiveIncrement
    const dto: ResourceProgressReportDTO = {
      resourceId,
      position: { ...position.value },
      durationSeconds: incrementSeconds,
      effectiveDurationSeconds: effectiveIncrement,
      idleSeconds: idleIncrement,
    }

    if (resourceType === 'image' || resourceType === 'audio' || resourceType === 'document') {
      dto.completionRate = 100
    }
    if (resourceType === 'text' && position.value?.scroll_percent !== undefined) {
      dto.completionRate =
        position.value.scroll_percent >= TEXT_COMPLETION_THRESHOLD
          ? 100
          : Math.round((position.value.scroll_percent / TEXT_COMPLETION_THRESHOLD) * 100)
    }

    // 使用 fetch + keepalive 保证页面关闭时请求仍然发出，同时携带鉴权 token
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const token = getToken()
    fetch(`${baseUrl}/education/resource-progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(dto),
      keepalive: true,
    }).catch(() => {
      // 页面关闭时请求失败无需处理
    })
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      // 页面失焦 → 累加时间并立即上报
      if (startTimestamp) {
        const wallSeconds = Math.round((Date.now() - startTimestamp) / 1000)
        startTimestamp = Date.now()
        elapsedSeconds.value += wallSeconds
        if (!isIdle.value) {
          effectiveSeconds += wallSeconds
        }
      }
      doReport(true)
      stopTimer()
    } else {
      // 已完成则不重启轮询
      if (alreadyCompleted.value) return
      // 页面重新可见 → 重启计时
      startTimestamp = Date.now()
      startTimer()
    }
  }

  // ========================================================================
  // 断点续学：恢复上次位置
  // ========================================================================

  async function restorePosition(): Promise<Record<string, any> | null> {
    try {
      const resp = await getResourceProgressDetail(resourceId)
      if (resp.code === 200 && resp.data) {
        // 记录完成状态
        alreadyCompleted.value = resp.data.isCompleted === 'Y' || (resp.data.completionRate ?? 0) >= 100

        // 只有未完成的资源才恢复位置，已完成的资源不再定位（用户已读完全部内容）
        if (!alreadyCompleted.value && resp.data.lastPosition) {
          position.value = resp.data.lastPosition
          return resp.data.lastPosition
        }
      }
    } catch {
      // 恢复失败不阻塞（首次访问可能无进度记录）
    }
    return null
  }

  // ========================================================================
  // 手动控制：开始追踪 / 立即上报
  // ========================================================================

  /**
   * 开始追踪阅读进度。
   * 由各资源面板在资源加载完成后调用（如 PDF loaded、文本内容加载完成、视频 loadedmetadata）。
   *
   * 内部会等待断点续学恢复（initialized），然后检查后端记录的完成状态：
   * - 如果资源已完成（isCompleted === 'Y' 或 completionRate >= 100），跳过追踪
   * - 否则启动定时上报和页面事件监听
   */
  function startTracking() {
    if (!enabled || tracking) return

    const doStart = () => {
      if (!enabled || tracking) return
      if (alreadyCompleted.value) return
      tracking = true
      startTimestamp = Date.now()
      startTimer()
      window.addEventListener('beforeunload', handleBeforeUnload)
      document.addEventListener('visibilitychange', handleVisibilityChange)
    }

    // 等待 restorePosition 完成后再决定是否开始追踪
    if (initialized.value) {
      doStart()
    } else {
      watch(
        initialized,
        (ready) => {
          if (ready) doStart()
        },
        { once: true }
      )
    }
  }

  /**
   * 立即上报当前进度。
   * 用于"触及底部/末页"等场景：累加从上次检查点到现在的时长，立即发送。
   * 仅在首次触发时生效，避免重复上报。
   */
  let immediateReported = false

  function reportImmediate() {
    if (!enabled || !tracking || immediateReported) return
    immediateReported = true

    // 累加从上次检查点到现在的时长
    if (startTimestamp) {
      const wallSeconds = Math.round((Date.now() - startTimestamp) / 1000)
      startTimestamp = Date.now()
      elapsedSeconds.value += wallSeconds
      if (!isIdle.value) {
        effectiveSeconds += wallSeconds
      }
    }
    doReport(true)
    // 上报完成事件后停止轮询，避免后续冗余上报
    alreadyCompleted.value = true
    stopTimer()
  }

  // ========================================================================
  // 生命周期
  // ========================================================================

  onMounted(async () => {
    if (!enabled) return

    // 尝试恢复断点位置
    await restorePosition()
    initialized.value = true
  })

  onBeforeUnmount(() => {
    if (tracking) {
      // 最终上报：累加剩余时间
      if (startTimestamp) {
        const wallSeconds = Math.round((Date.now() - startTimestamp) / 1000)
        elapsedSeconds.value += wallSeconds
        if (!isIdle.value) {
          effectiveSeconds += wallSeconds
        }
      }
      doReport(true)
      stopTimer()

      window.removeEventListener('beforeunload', handleBeforeUnload)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  })

  // ========================================================================
  // 返回
  // ========================================================================

  return {
    /** 当前位置（组件可读写） */
    position,
    /** 累计时长（秒，只读） */
    elapsedSeconds: readonly(elapsedSeconds),
    /** 是否已完成初始化（断点续学恢复完成） */
    initialized: readonly(initialized),
    /** 资源是否已完成（从后端进度判断，已完成则 startTracking 为 no-op） */
    alreadyCompleted: readonly(alreadyCompleted),
    /** 手动触发上报 */
    report: () => doReport(true),
    /** 恢复断点位置 */
    restorePosition,
    /** 资源加载完成后调用，开始计时和定时上报（已完成的资源自动跳过） */
    startTracking,
    /** 触及底部/末页时调用，立即累加时长并上报（仅首次生效） */
    reportImmediate,
  }
}
