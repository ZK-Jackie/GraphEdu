/**
 * 日志管理相关类型定义
 * 对应后端：graphedu/common/models/dto/log.py 和 vo/log.py
 */

// ============================================================================
// 操作日志相关类型
// ============================================================================

/**
 * 操作日志查询请求
 */
export interface OperLogQueryDTO {
  /** 模块标题 */
  title?: string
  /** 操作人员 */
  operName?: string
  /** 操作地址 */
  operIp?: string
  /** 业务类型，对照 sys_oper_log_business_type（0其它 1新增 2修改 3删除 等） */
  businessType?: string
  /** 操作日志状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status?: string
  /** 开始时间 */
  beginTime?: string
  /** 结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 操作日志列表项
 */
export interface OperLogListVO {
  /** 日志主键 */
  operId: number
  /** 模块标题 */
  title: string
  /** 业务类型（0其它 1新增 2修改 3删除） */
  businessType: number
  /** 方法名称 */
  method: string
  /** 请求方式 */
  requestMethod: string
  /** 操作类别，对照 sys_oper_log_oper_type（0其它 1后台用户 2手机端用户 等） */
  operatorType: number
  /** 操作人员 */
  operName: string
  /** 主机地址 */
  operIp: string
  /** 操作地点 */
  operLocation: string
  /** 操作时间 */
  operTime: string
  /** 操作日志状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: number
  /** 消耗时间（毫秒） */
  costTime: number
}

/**
 * 操作日志详情
 */
export interface OperLogDetailVO {
  /** 日志主键 */
  operId: number
  /** 模块标题 */
  title: string
  /** 业务类型 */
  businessType: number
  /** 方法名称 */
  method: string
  /** 请求方式 */
  requestMethod: string
  /** 操作类别 */
  operatorType: number
  /** 操作人员 */
  operName: string
  /** 部门名称 */
  deptName: string
  /** 请求URL */
  operUrl: string
  /** 主机地址 */
  operIp: string
  /** 操作地点 */
  operLocation: string
  /** 请求参数 */
  operParam: string
  /** 返回参数 */
  jsonResult: string
  /** 操作状态 */
  status: number
  /** 错误消息 */
  errorMsg: string
  /** 操作时间 */
  operTime: string
  /** 消耗时间（毫秒） */
  costTime: number
}

// ============================================================================
// 登录日志相关类型
// ============================================================================

/**
 * 登录日志查询请求
 */
export interface LoginLogQueryDTO {
  /** 登录IP地址 */
  ipaddr?: string
  /** 用户账号 */
  userName?: string
  /** 登录状态（0成功 1失败） */
  status?: string
  /** 开始时间 */
  beginTime?: string
  /** 结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 登录日志列表项
 */
export interface LoginLogListVO {
  /** 访问ID */
  infoId: number
  /** 用户账号 */
  userName: string
  /** 登录IP地址 */
  ipaddr: string
  /** 登录地点 */
  loginLocation: string
  /** 浏览器类型 */
  browser: string
  /** 操作系统 */
  os: string
  /** 登录状态（0成功 1失败） */
  status: string
  /** 提示消息 */
  msg: string
  /** 访问时间 */
  loginTime: string
}

/**
 * 解锁用户请求
 */
export interface UnlockUserDTO {
  /** 用户名 */
  userName: string
}
