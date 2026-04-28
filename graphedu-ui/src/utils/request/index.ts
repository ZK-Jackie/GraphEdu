import axios, { type AxiosInstance, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import storage from '@/utils/storage.ts'
import { getToken } from '@/utils/token.ts'
import qs from 'qs'
import { SessionRequestObjectKey, ViteEnv, LocalLocaleKey } from '@/constants.ts'
import { handleBackendError, handleRequestError } from '@/utils/request/error-handler.ts'

/**
 * 创建 axios 实例
 */
const instance: AxiosInstance = axios.create({
  // axios中请求配置有baseURL选项，表示请求URL公共部分
  baseURL: ViteEnv.VITE_API_BASE_URL,
  // 超时时间，单位ms，默认10s
  timeout: Number(ViteEnv.VITE_API_TIMEOUT) || 10000,
})

// ==================== 请求拦截器辅助函数 ====================

/**
 * 添加 Authorization token 到请求头
 */
function addAuthorizationHeader(request: InternalAxiosRequestConfig<any>): void {
  const headers = request.headers as Record<string, any>
  const skipToken = headers.skipToken === true
  if (getToken() && !skipToken) {
    headers['Authorization'] = `Bearer ${getToken()}`
  }
}

/**
 * 添加 Accept-Language 请求头
 */
function addAcceptLanguageHeader(request: InternalAxiosRequestConfig<any>): void {
  const locale = storage.local.get(LocalLocaleKey) || 'zh'
  const acceptLanguage = locale === 'zh' ? 'zh-CN' : 'en-US'
  request.headers['Accept-Language'] = acceptLanguage
}

/**
 * 处理请求参数序列化
 */
function processRequestParams(request: InternalAxiosRequestConfig<any>): void {
  // 对于 GET 请求，将 params 序列化到 URL 上，并清空 params 对象
  if (request.method === 'get' && request.params) {
    // https://github.com/ljharb/qs?tab=readme-ov-file#stringifying
    const url = request.url + '?' + qs.stringify(request.params, { arrayFormat: 'repeat' })
    request.params = {}
    request.url = url
  }
  // 其他请求无操作
}

/**
 * 防重复提交检查
 */
function checkDuplicateSubmit(request: InternalAxiosRequestConfig<any>): InternalAxiosRequestConfig<any> | Promise<Error> {
  const headers = request.headers as Record<string, any>
  const skipRepeatSubmitCheck = headers.skipRepeatSubmitCheck === true
  const isMutationRequest = request.method === 'post' || request.method === 'put'

  if (skipRepeatSubmitCheck || !isMutationRequest) {
    return request
  }

  const requestObj = {
    url: request.url,
    data: typeof request.data === 'object' ? JSON.stringify(request.data) : request.data,
    time: new Date().getTime(),
  }

  const requestSize = Object.keys(JSON.stringify(requestObj)).length
  const limitSize = ViteEnv.VITE_API_REQUEST_INTERVAL_DATA_THRESHOLD

  if (requestSize >= limitSize) {
    console.warn(`[Request] 请求 ${request.url} 时，请求数据大小超出允许的5M限制，无法进行防重复提交验证。`)
    return request
  }

  const sessionObj = storage.session.getJSON(SessionRequestObjectKey)
  if (!sessionObj) {
    storage.session.setJSON(SessionRequestObjectKey, requestObj)
    return request
  }

  const { url: s_url, data: s_data, time: s_time } = sessionObj
  const interval = ViteEnv.VITE_API_REQUEST_INTERVAL

  if (s_data === requestObj.data && requestObj.time - s_time < interval && s_url === requestObj.url) {
    const message = '数据正在处理，请勿重复提交'
    console.warn(`[Request] ${s_url}: ${message}`)
    return Promise.reject(new Error(message))
  }

  storage.session.setJSON(SessionRequestObjectKey, requestObj)
  return request
}

/**
 * 清理自定义 headers，避免发送到后端
 */
function cleanCustomHeaders(request: InternalAxiosRequestConfig<any>): void {
  const headers = request.headers as Record<string, any>
  delete headers['skipToken']
  delete headers['skipRepeatSubmitCheck']
}

// ==================== 响应拦截器辅助函数 ====================

/**
 * 判断是否为二进制响应
 */
function isBinaryResponse(response: any): boolean {
  return response.request.responseType === 'blob' || response.request.responseType === 'arraybuffer'
}

// ==================== 拦截器注册 ====================

// 请求拦截器
instance.interceptors.request.use(
  (request: InternalAxiosRequestConfig<any>) => {
    addAuthorizationHeader(request)
    addAcceptLanguageHeader(request)
    processRequestParams(request)
    const checkResult = checkDuplicateSubmit(request)
    if (checkResult instanceof Promise) {
      return checkResult as unknown as Promise<InternalAxiosRequestConfig<any>>
    }
    cleanCustomHeaders(request)
    return request
  },
  (error: any) => Promise.reject(error)
)

// 响应拦截器
instance.interceptors.response.use(
  (response): Promise<any> => {
    // 二进制数据直接返回
    if (isBinaryResponse(response)) {
      return response.data
    }
    // json 数据分析处理
    const code: number = response.data.code ?? 500
    if (code !== 200) {
      return handleBackendError(response.data)
    }
    // 成功响应，返回 data 字段
    return Promise.resolve(response.data)
  },
  (error: any) => {
    // 网络错误或服务器异常，统一处理
    return handleRequestError(error)
  }
)

interface RequestHeaders {
  skipToken?: boolean
  skipRepeatSubmitCheck?: boolean
}

export interface RequestConfig extends AxiosRequestConfig {
  // 请求相对地址
  url: string
  // 请求方法
  method: 'get' | 'post' | 'put' | 'delete' | 'patch'
  // 请求头
  headers?: RequestHeaders & AxiosRequestConfig['headers']
  // query 参数
  params?: any
  // body 参数
  data?: any
  // 请求超时时间
  timeout?: number
}

// 在 request.ts 文件末尾添加
export interface RequestInstance {
  <T = any>(config: RequestConfig): Promise<T>

  <T = any>(url: string, config?: RequestConfig): Promise<T>
}

export default instance as RequestInstance
