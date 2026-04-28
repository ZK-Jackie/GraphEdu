/**
 * 格式化时长（分钟 -> 可读字符串）
 * @param minutes 分钟数
 * @returns 如 "2小时30分钟" / "45分钟"
 */
export function formatDuration(minutes: number): string {
  if (!minutes || minutes === 0) return '0分钟'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

/**
 * 格式化秒数为可读时长
 * @param seconds 秒数
 * @returns 如 "1小时30分钟"
 */
export function formatSeconds(seconds: number): string {
  if (!seconds || seconds === 0) return '0分钟'
  return formatDuration(Math.round(seconds / 60))
}

/**
 * 格式化分钟为简短时长
 * @param minutes 分钟数
 * @returns 如 "2h30m" / "45m"
 */
export function formatMinutes(minutes: number): string {
  if (!minutes || minutes === 0) return '0分钟'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h${mins}m` : `${hours}h`
}

/**
 * 格式化日期为相对时间
 * @param dateStr 日期字符串
 * @returns 如 "今天" / "3天前" / "2026年4月1日"
 */
export function formatRelativeDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/**
 * 根据完成百分比返回颜色
 * @param percent 0-100
 */
export function getCompletionColor(percent: number): string {
  if (percent >= 80) return '#52c41a'
  if (percent >= 50) return '#faad14'
  return '#ff4d4f'
}
