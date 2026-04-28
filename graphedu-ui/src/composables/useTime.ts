import { storeToRefs } from 'pinia'
import useAppStore from '@/stores/modules/app.ts'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import 'dayjs/locale/en'

// 扩展dayjs插件
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(relativeTime)

/**
 * 时间处理Composable
 *
 * 提供统一的时间格式化API，支持：
 * - UTC时间转换为用户时区
 * - 自定义时间格式
 * - 相对时间显示（X分钟前）
 * - 响应式语言和时区切换
 *
 * @example
 * ```ts
 * const { formatUtcTime, fromNow } = useTime()
 * console.log(formatUtcTime('2024-01-01T12:00:00Z')) // 2024-01-01 20:00:00
 * console.log(fromNow('2024-01-01T12:00:00Z')) // 3天前
 * ```
 */
export function useTime() {
  const appStore = useAppStore()
  const { locale, timeConfig } = storeToRefs(appStore)

  // 设置dayjs语言
  const setDayjsLocale = (newLocale: string) => {
    const dayjsLocale = newLocale === 'zh' ? 'zh-cn' : 'en'
    dayjs.locale(dayjsLocale)
  }

  // 监听locale变化，同步更新dayjs语言
  watch(
    locale,
    (newLocale) => {
      setDayjsLocale(newLocale)
    },
    { immediate: true }
  )

  /**
   * 获取当前时间格式
   */
  const getFormat = (): string => {
    return timeConfig.value.format
  }

  /**
   * 格式化UTC时间
   * @param utcTime UTC时间字符串
   * @param customFormat 自定义格式（可选）
   * @returns 格式化后的时间字符串
   */
  const formatUtcTime = (utcTime: string, customFormat?: string): string => {
    const format = customFormat || getFormat()
    const tz = timeConfig.value.timezone

    // 处理auto时区（使用浏览器本地时区）
    const targetTz = tz === 'auto' ? undefined : tz

    try {
      if (targetTz) {
        return dayjs.utc(utcTime).tz(targetTz).format(format)
      }
      return dayjs.utc(utcTime).local().format(format)
    } catch (e) {
      console.error('[useTime] 时间格式化失败:', e)
      return utcTime
    }
  }

  /**
   * 相对时间显示（X分钟前）
   * @param utcTime UTC时间字符串
   * @returns 相对时间字符串或完整时间字符串
   */
  const fromNow = (utcTime: string): string => {
    if (!timeConfig.value.relativeTime) {
      return formatUtcTime(utcTime)
    }

    const tz = timeConfig.value.timezone
    const targetTz = tz === 'auto' ? undefined : tz

    try {
      let time: dayjs.Dayjs
      if (targetTz) {
        time = dayjs.utc(utcTime).tz(targetTz)
      } else {
        time = dayjs.utc(utcTime).local()
      }

      // 检查是否超过阈值（7天）
      const now = targetTz ? dayjs.utc().tz(targetTz) : dayjs()
      const diffDays = Math.abs(now.diff(time, 'day'))

      if (diffDays > 7) {
        // 超过阈值，显示完整时间
        return formatUtcTime(utcTime)
      }

      return time.fromNow()
    } catch (e) {
      console.error('[useTime] 相对时间计算失败:', e)
      return formatUtcTime(utcTime)
    }
  }

  /**
   * 获取当前时区显示名称
   */
  const getTimezoneLabel = (): string => {
    const tz = timeConfig.value.timezone
    if (tz === 'auto') {
      return '自动'
    }
    return tz
  }

  /**
   * 预览时间格式
   * @param format 时间格式字符串
   * @returns 示例时间字符串
   */
  const previewFormat = (format?: string): string => {
    const now = new Date().toISOString()
    return formatUtcTime(now, format)
  }

  return {
    formatUtcTime,
    fromNow,
    getFormat,
    setDayjsLocale,
    getTimezoneLabel,
    previewFormat,
    dayjs,
  }
}

export default useTime
