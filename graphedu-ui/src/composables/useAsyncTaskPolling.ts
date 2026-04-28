/**
 * 通用异步任务轮询 composable
 *
 * 封装异步任务的进度轮询逻辑，任何页面可复用。
 *
 * @example
 * const { taskId, taskStatus, progressPercent, taskMessage, submit, startPolling, stopPolling } = useAsyncTaskPolling()
 *
 * // 提交任务后开始轮询
 * submit(123)  // 传入 task_id
 *
 * // 监听完成
 * watch(taskStatus, (status) => {
 *   if (status === 'success') { ... }
 * })
 */
import { onBeforeUnmount, readonly, ref, type Ref } from 'vue'
import { getAsyncTaskProgress } from '@/api/system/asyncTask.ts'
import type { AsyncTaskProgressVO } from '@/types/api/system/asyncTask.ts'

export function useAsyncTaskPolling(interval = 3000) {
  const taskId = ref<number | null>(null) as Ref<number | null>
  const taskStatus = ref('')
  const progressPercent = ref(0)
  const taskMessage = ref<string | null>(null)
  const taskResult = ref<Record<string, any> | null>(null)
  const polling = ref(false)

  let timer: number | null = null

  const isRunning = (status: string) => status === 'pending' || status === 'processing'

  const poll = async () => {
    if (!taskId.value) return
    try {
      const res = await getAsyncTaskProgress(taskId.value)
      if (res.code === 200 && res.data) {
        const data: AsyncTaskProgressVO = res.data
        taskStatus.value = data.taskStatus
        progressPercent.value = data.progressPercent || 0
        taskMessage.value = data.taskMessage || null
        taskResult.value = data.taskResult || null

        if (!isRunning(data.taskStatus)) {
          stopPolling()
        }
      }
    } catch {
      stopPolling()
    }
  }

  const startPolling = () => {
    stopPolling()
    polling.value = true
    timer = window.setInterval(poll, interval)
    poll()
  }

  const stopPolling = () => {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
    polling.value = false
  }

  /** 提交一个 taskId 并开始轮询 */
  const submit = (id: number) => {
    taskId.value = id
    taskStatus.value = 'pending'
    progressPercent.value = 0
    taskMessage.value = '任务已提交...'
    taskResult.value = null
    startPolling()
  }

  /** 重置所有状态 */
  const reset = () => {
    stopPolling()
    taskId.value = null
    taskStatus.value = ''
    progressPercent.value = 0
    taskMessage.value = null
    taskResult.value = null
  }

  onBeforeUnmount(() => {
    stopPolling()
  })

  return {
    taskId: readonly(taskId),
    taskStatus: readonly(taskStatus),
    progressPercent: readonly(progressPercent),
    taskMessage: readonly(taskMessage),
    taskResult: readonly(taskResult),
    polling: readonly(polling),
    submit,
    startPolling,
    stopPolling,
    reset,
  }
}
