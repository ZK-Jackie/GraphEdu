import type { UrlParams } from '@vueuse/core'

/**
 * 生成 UUID
 * @returns UUID 字符串
 */
export function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0,
      v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * 计算字符串的哈希码
 * @param str 输入字符串
 * @returns 哈希码数值
 */
export function hashCode(str: string): number {
  let hash = 0
  if (str.length === 0) return hash
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // 转换为32位整数
  }
  return hash
}

/**
 * 将对象转换为 URL 参数字符串
 * @param params 参数对象
 * @returns URL 参数字符串
 */
export function toUrlParams(params: UrlParams): string {
  const parts: string[] = []
  for (const propName of Object.keys(params)) {
    const value = params[propName]
    if (value === null || value === '' || typeof value === 'undefined') {
      continue
    }
    if (typeof value === 'object') {
      const objValue = value as Record<string, any>
      for (const key of Object.keys(objValue)) {
        const nestedValue = objValue[key]
        if (nestedValue !== null && nestedValue !== '' && typeof nestedValue !== 'undefined') {
          const paramKey = `${propName}[${key}]`
          parts.push(`${encodeURIComponent(paramKey)}=${encodeURIComponent(nestedValue)}`)
        }
      }
    } else {
      parts.push(`${encodeURIComponent(propName)}=${encodeURIComponent(value)}`)
    }
  }
  return parts.join('&')
}

/**
 * 检查 URL 是否是 HTTP/HTTPS 链接
 * @param url 待检查的 URL
 * @returns 是否为 HTTP/HTTPS 链接
 */
export function isHttp(url: string): boolean {
  return url.startsWith('http://') || url.startsWith('https://')
}

/**
 * 检查值是否为空
 * @param value 待检查的值
 * @returns 是否为空
 */
export function isEmpty(value: any): boolean {
  return value === null || value === undefined || value === '' || value === 'null' || value === 'undefined'
}

/**
 * 解析可能为空的字符串
 * @param str 输入字符串
 * @returns 处理后的字符串
 */
export function parseStrEmpty(str: any): string {
  if (!str || str === 'undefined' || str === 'null') {
    return ''
  }
  return str
}
