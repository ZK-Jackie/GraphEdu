import type { ResponseType } from '@/types/api/common.ts'
import { ErrorCodes_ZH_CN } from '@/utils/errors.ts'
import { SystemMessage, SystemNotification, SystemDialog } from '@/utils/message.ts'
import useUserStore from '@/stores/modules/user.ts'
/**
 * 处理 401 认证过期
 */
function handleAuthExpired(): Promise<never> {
  SystemDialog({
    theme: 'warning',
    title: '登录状态已过期',
    content: '登录状态已过期，您可以继续留在该页面，或者重新登录',
    confirmBtn: '重新登录',
    cancelBtn: '取消',
    onOk: () => {
      useUserStore()
        .logout()
        .then(() => {
          location.href = '/login'
        })
    },
  })
  return Promise.reject('无效的会话，或者会话已过期，请重新登录。')
}

/**
 * 处理 422 参数校验失败
 */
function handleValidationError(msg: string): Promise<never> {
  SystemMessage({ theme: 'warning', content: msg })
  return Promise.reject(new Error(msg))
}

/**
 * 处理 5xx 服务器错误
 */
function handleServerError(msg: string): Promise<never> {
  SystemMessage({ theme: 'error', content: msg })
  return Promise.reject(new Error(msg))
}

/**
 * 处理 6xx 业务错误
 */
function handleBusinessError(msg: string): Promise<never> {
  SystemMessage({ theme: 'warning', content: msg })
  return Promise.reject(new Error(msg))
}

/**
 * 处理其他业务错误码
 */
function handleCommonError(msg: string): Promise<never> {
  SystemNotification({ theme: 'error', content: msg })
  return Promise.reject('error')
}

function extractErrorMessage(code: number, fallbackMsg?: string): string {
  // 优先使用后端返回的错误消息（已根据Accept-Language本地化）
  // 如果后端返回的消息为空，则使用前端兜底映射
  if (fallbackMsg && fallbackMsg.trim()) {
    return fallbackMsg
  }
  return ErrorCodes_ZH_CN[code] ?? ErrorCodes_ZH_CN[0] ?? '未知错误'
}

/**
 * 统一错误处理函数，根据响应状态码进行分类处理
 *
 * @warnings 请确保传入的消息是服务器的异常响应消息，避免误用导致用户界面显示不友好的错误提示
 * @param resp 响应对象，包含 code 和 msg 字段
 * @returns 一个 rejected Promise，携带错误信息
 */
export function handleBackendError(resp: ResponseType): Promise<never> {
  const code = resp.code
  const msg = extractErrorMessage(code, resp.msg)
  if (code === 401) {
    return handleAuthExpired()
  }
  if (code === 422) {
    return handleValidationError(msg)
  }
  if (code >= 500 && code < 600) {
    return handleServerError(msg)
  }
  if (code >= 600) {
    return handleBusinessError(msg)
  }
  return handleCommonError(msg)
}

/**
 * 规范化网络错误消息
 */
function normalizeNetworkError(error: any): string {
  const { message } = error

  if (message === 'Network Error') {
    return '后端接口连接异常'
  }
  if (message.includes('timeout')) {
    return '系统接口请求超时'
  }
  if (message.includes('Request failed with status code')) {
    return `系统接口${message.slice(-3)}异常`
  }
  return message
}

/**
 * 处理网络请求错误，规范化错误消息并显示用户友好的提示
 * @param error 原始错误对象
 */
export function handleRequestError(error: any): Promise<never> {
  console.error(`[Request] err: ${error}`)
  const message = normalizeNetworkError(error)
  SystemMessage({ theme: 'error', content: message })
  return Promise.reject(new Error(message))
}
