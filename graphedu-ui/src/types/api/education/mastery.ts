/**
 * 创建学生掌握度评估记录 DTO
 */
export interface StudentMasteryCreateDTO {
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 知识点业务UUID */
  nodeUuid?: string
  /** 触发评估的会话ID */
  sessionId?: number
  /** 掌握度评分（0-100） */
  masteryScore?: number
  /** 掌握等级 */
  masteryLevel?: 'unknown' | 'low' | 'medium' | 'high'
  /** 触发类型 */
  triggerType?: 'quiz_complete' | 'periodic' | 'manual' | 'system'
  /** 评估时间 */
  assessedAt?: string
}

/**
 * 学生掌握度评估记录查询 DTO
 */
export interface StudentMasteryQueryDTO {
  /** 学生ID */
  studentId?: number
  /** 课程ID */
  courseId?: number
  /** 知识点UUID */
  nodeUuid?: string
  /** 掌握等级 */
  masteryLevel?: 'unknown' | 'low' | 'medium' | 'high'
  /** 触发类型 */
  triggerType?: string
  /** 状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
  /** 评估开始时间 */
  beginTime?: string
  /** 评估结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 学生掌握度评估记录详细信息 VO
 */
export interface StudentMasteryDetailVO {
  /** 评估记录ID */
  masteryId: number
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 知识点业务UUID */
  nodeUuid?: string
  /** 触发评估的会话ID */
  sessionId?: number
  /** 掌握度评分（0-100） */
  masteryScore?: number
  /** 掌握等级 */
  masteryLevel?: string
  /** 触发类型 */
  triggerType?: string
  /** 评估时间 */
  assessedAt?: string
  /** 状态（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 更新时间 */
  updateTime?: string
  /** 学生姓名 */
  studentName?: string
  /** 课程名称 */
  courseName?: string
  /** 知识点标题 */
  nodeTitle?: string
}

/**
 * 学生掌握度评估记录列表项 VO
 */
export interface StudentMasteryListVO {
  /** 评估记录ID */
  masteryId: number
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 知识点业务UUID */
  nodeUuid?: string
  /** 掌握度评分（0-100） */
  masteryScore?: number
  /** 掌握等级 */
  masteryLevel?: string
  /** 触发类型 */
  triggerType?: string
  /** 评估时间 */
  assessedAt?: string
  /** 创建时间 */
  createTime?: string
  /** 学生姓名 */
  studentName?: string
  /** 课程名称 */
  courseName?: string
  /** 知识点标题 */
  nodeTitle?: string
}

/**
 * 学生章节知识点掌握明细 VO
 */
export interface StudentChapterMasteryDetailVO {
  /** 评估记录ID */
  masteryId: number
  /** 知识点UUID */
  nodeUuid: string
  /** 知识点标题 */
  nodeTitle?: string
  /** 掌握度评分（0-100） */
  masteryScore?: number
  /** 掌握等级 */
  masteryLevel?: string
  /** 评估时间 */
  assessedAt?: string
}
