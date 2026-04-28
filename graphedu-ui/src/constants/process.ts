export const ProcessStatus = {
  PENDING: '0', // 准备就绪、未处理
  RUNNING: '1', // 运行中
  COMPLETED: '2', // 已完成
  ERROR: '3', // 失败
} as const

export type ProcessStatusValue = (typeof ProcessStatus)[keyof typeof ProcessStatus]
