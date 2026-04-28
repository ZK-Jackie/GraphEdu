/**
 * Mock 日期辅助函数
 * 生成基于当前日期的动态数据，确保展示效果始终"新鲜"
 */

/**
 * 格式化日期为 MM-DD
 */
export function fmtMD(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${m}-${d}`
}

/**
 * 格式化日期为 YYYY-MM-DD
 */
export function fmtYMD(date: Date): string {
  return `${date.getFullYear()}-${fmtMD(date)}`
}

/**
 * 获取最近 N 天的日期数组（从今天往前推）
 */
export function recentDays(n: number): Date[] {
  const today = new Date()
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(today)
    d.setDate(d.getDate() - (n - 1 - i))
    return d
  })
}

/**
 * 获取本周（周一到周日）的日期数组
 */
export function currentWeek(): Date[] {
  const today = new Date()
  const dow = today.getDay() || 7 // 周日=7
  const monday = new Date(today)
  monday.setDate(today.getDate() - dow + 1)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return d
  })
}

/**
 * 获取指定周偏移的日期数组（0=本周, -1=上周, 1=下周）
 */
export function weekByOffset(offset: number): Date[] {
  const thisWeek = currentWeek()
  return thisWeek.map((d) => {
    const nd = new Date(d)
    nd.setDate(nd.getDate() + offset * 7)
    return nd
  })
}

/**
 * 获取最近 N 天的 MM-DD 标签
 */
export function recentDayLabels(n: number): string[] {
  return recentDays(n).map(fmtMD)
}

/**
 * 获取本周的 MM-DD 标签
 */
export function currentWeekLabels(): string[] {
  return currentWeek().map(fmtMD)
}

/**
 * 近 N 个月的活跃度数据（30天×每天一个值）
 */
export function generateDailyTrend(days: number, baseRange: [number, number]): { date: string; count: number }[] {
  return recentDays(days).map((d) => ({
    date: fmtMD(d),
    count: Math.floor(Math.random() * (baseRange[1] - baseRange[0] + 1)) + baseRange[0],
  }))
}

/**
 * 生成带确定性种子的伪随机数（用于保持一致性）
 */
export function seededRandom(seed: number): () => number {
  let s = seed
  return () => {
    s = (s * 16807) % 2147483647
    return (s - 1) / 2147483646
  }
}
