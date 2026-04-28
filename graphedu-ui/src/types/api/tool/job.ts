/**
 * 定时任务管理相关类型定义
 * 对应后端：graphedu/common/models/dto/job.py 和 vo/job.py
 */

// ============================================================================
// 请求 DTO 类型
// ============================================================================

/**
 * 定时任务查询请求
 */
export interface JobQueryDTO {
  /** 任务ID */
  jobId?: number
  /** 任务名称 */
  jobName?: string
  /** 任务分组（DEFAULT, SYSTEM） */
  jobGroup?: 'DEFAULT' | 'SYSTEM'
  /** 任务状态（0正常 1暂停） */
  status?: '0' | '1'
  /** 执行器类型（python, webhook） */
  jobExecutor?: 'python' | 'webhook'
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建定时任务请求
 */
export interface JobCreateDTO {
  /** 任务名称 */
  jobName: string
  /** 任务分组（DEFAULT=默认, SYSTEM=系统） */
  jobGroup: 'DEFAULT' | 'SYSTEM'
  /** 执行器类型（python=Python函数, webhook=Webhook调用） */
  jobExecutor: 'python' | 'webhook'
  /** 调用目标字符串 */
  invokeTarget: string
  /** 位置参数（JSON字符串） */
  jobArgs?: string
  /** 关键字参数（JSON字符串） */
  jobKwargs?: string
  /** Cron执行表达式 */
  cronExpression: string
  /** 执行策略（1=立即执行, 2=执行一次, 3=放弃执行） */
  misfirePolicy: '1' | '2' | '3'
  /** 是否并发（0=禁止, 1=允许） */
  concurrent: '0' | '1'
  /** 任务状态（0=正常, 1=暂停） */
  status: '0' | '1'
  /** 是否启用Webhook（0=否, 1=是） */
  webhookEnabled?: '0' | '1'
  /** Webhook URL */
  webhookUrl?: string
  /** Webhook密钥 */
  webhookSecret?: string
  /** 备注 */
  remark?: string
}

/**
 * 更新定时任务请求
 */
export interface JobUpdateDTO {
  /** 任务ID */
  jobId: number
  /** 任务名称 */
  jobName?: string
  /** 任务分组（DEFAULT=默认, SYSTEM=系统） */
  jobGroup?: 'DEFAULT' | 'SYSTEM'
  /** 执行器类型（python=Python函数, webhook=Webhook调用） */
  jobExecutor?: 'python' | 'webhook'
  /** 调用目标字符串 */
  invokeTarget?: string
  /** 位置参数（JSON字符串） */
  jobArgs?: string
  /** 关键字参数（JSON字符串） */
  jobKwargs?: string
  /** Cron执行表达式 */
  cronExpression?: string
  /** 执行策略（1=立即执行, 2=执行一次, 3=放弃执行） */
  misfirePolicy?: '1' | '2' | '3'
  /** 是否并发（0=禁止, 1=允许） */
  concurrent?: '0' | '1'
  /** 任务状态（0=正常, 1=暂停） */
  status?: '0' | '1'
  /** 是否启用Webhook（0=否, 1=是） */
  webhookEnabled?: '0' | '1'
  /** Webhook URL */
  webhookUrl?: string
  /** Webhook密钥 */
  webhookSecret?: string
  /** 备注 */
  remark?: string
}

/**
 * 修改任务状态请求
 */
export interface JobStatusChangeDTO {
  /** 任务ID */
  jobId: number
  /** 任务状态（0正常 1暂停） */
  status: '0' | '1'
}

/**
 * 执行一次任务请求
 */
export interface JobExecuteOnceDTO {
  /** 任务ID */
  jobId: number
}

/**
 * 任务日志查询请求
 */
export interface JobLogQueryDTO {
  /** 任务ID */
  jobId?: number
  /** 任务名称 */
  jobName?: string
  /** 任务分组 */
  jobGroup?: string
  /** 执行状态（0成功 1失败） */
  status?: '0' | '1'
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

// ============================================================================
// 响应 VO 类型
// ============================================================================

/**
 * 定时任务列表项
 */
export interface JobListVO {
  /** 任务ID */
  jobId: number
  /** 任务名称 */
  jobName: string
  /** 任务分组 */
  jobGroup: string
  /** 执行器类型 */
  jobExecutor: string
  /** 调用目标字符串 */
  invokeTarget: string
  /** Cron执行表达式 */
  cronExpression: string
  /** 执行策略 */
  misfirePolicy: string
  /** 是否并发 */
  concurrent: string
  /** 任务状态 */
  status: string
  /** 是否启用Webhook */
  webhookEnabled: string
  /** 创建时间 */
  createTime?: string
  /** 备注 */
  remark?: string
}

/**
 * 定时任务详细信息
 */
export interface JobDetailVO extends JobListVO {
  /** 位置参数（JSON字符串） */
  jobArgs?: string
  /** 关键字参数（JSON字符串） */
  jobKwargs?: string
  /** Webhook URL */
  webhookUrl?: string
  /** Webhook密钥 */
  webhookSecret?: string
  /** 创建者 */
  createBy?: number
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
}

/**
 * 任务执行日志列表项
 */
export interface JobLogListVO {
  /** 日志ID */
  jobLogId: number
  /** 任务ID */
  jobId: number
  /** 任务名称 */
  jobName: string
  /** 任务分组 */
  jobGroup: string
  /** 调用目标字符串 */
  invokeTarget: string
  /** 执行信息 */
  jobMessage?: string
  /** 执行状态（0成功 1失败） */
  status: string
  /** 异常信息 */
  exceptionInfo?: string
  /** 创建时间 */
  createTime: string
}

/**
 * 任务执行结果
 */
export interface JobExecuteResultVO {
  /** 任务ID */
  jobId: number
  /** 任务名称 */
  jobName: string
  /** 执行状态（0成功 1失败） */
  status: string
  /** 执行信息 */
  message: string
}

/**
 * Cron 表达式字段类型
 */
export type CronFieldType = 'second' | 'minute' | 'hour' | 'day' | 'month' | 'dayOfWeek'

/**
 * Cron 表达式各字段配置
 */
export interface CronFieldConfig {
  /** 类型 */
  type: CronFieldType
  /** 当前值 */
  value: string
  /** 是否使用通配符 */
  isWildcard: boolean
  /** 指定的值列表 */
  specified: number[]
  /** 范围（从） */
  rangeFrom?: number
  /** 范围（到） */
  rangeTo?: number
  /** 步长 */
  step?: number
}
