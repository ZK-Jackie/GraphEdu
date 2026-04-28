/**
 * 通用异步任务相关类型
 */

/**
 * 异步任务列表项 VO
 */
export interface AsyncTaskVO {
  /** 任务ID */
  taskId: number
  /** 任务名称 */
  taskName: string
  /** 任务类型标识 */
  taskType: string
  /** 任务状态 (pending/processing/success/failed/cancelled) */
  taskStatus: string
  /** 进度百分比 (0-100) */
  progressPercent: number
  /** 进度描述或错误信息 */
  taskMessage?: string
  /** 提交者用户ID */
  userId?: number
  /** 开始执行时间 */
  startTime?: string
  /** 完成时间 */
  endTime?: string
  /** 创建时间 */
  createTime?: string
}

/**
 * 异步任务详情 VO
 */
export interface AsyncTaskDetailVO extends AsyncTaskVO {
  /** 任务输入参数 */
  taskParams?: Record<string, any>
  /** 任务输出结果 */
  taskResult?: Record<string, any>
  /** Celery 任务 ID */
  celeryTaskId?: string
  /** 创建者 */
  createBy?: number
  /** 更新时间 */
  updateTime?: string
}

/**
 * 异步任务进度 VO（用于轮询查询）
 */
export interface AsyncTaskProgressVO {
  /** 任务ID */
  taskId: number
  /** 任务状态 (pending/processing/success/failed/cancelled) */
  taskStatus: string
  /** 进度百分比 (0-100) */
  progressPercent: number
  /** 进度描述或错误信息 */
  taskMessage?: string
  /** 任务输出结果（成功时有效） */
  taskResult?: Record<string, any>
}

/**
 * 异步任务查询参数
 */
export interface AsyncTaskQueryDTO {
  /** 任务类型标识 */
  taskType?: string
  /** 任务状态 */
  taskStatus?: string
  /** 创建开始时间 */
  beginTime?: string
  /** 创建结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}
