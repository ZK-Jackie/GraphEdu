/**
 * 学生查询请求
 */
export interface StudentQueryDTO {
  /** 学生ID */
  studentId?: number
  /** 真实姓名 */
  realName?: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  faculty?: string
  /** 专业 */
  major?: string
  /** 年级 */
  grade?: string
  /** 班级 */
  className?: string
  /** 性别（0未知 1男 2女 9其他） */
  gender?: '0' | '1' | '2' | '9'
  /** 学生状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
  /** 创建开始时间 */
  beginTime?: string
  /** 创建结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建学生请求
 */
export interface StudentCreateDTO {
  /** 学生ID（关联user_id） */
  studentId: number
  /** 真实姓名 */
  realName: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  faculty?: string
  /** 专业 */
  major?: string
  /** 年级 */
  grade?: string
  /** 班级 */
  className?: string
  /** 性别（0未知 1男 2女 9其他） */
  gender?: '0' | '1' | '2' | '9'
  /** 年龄 */
  age?: number
  /** 自我介绍 */
  description?: string
}

/**
 * 更新学生请求
 */
export interface StudentUpdateDTO {
  /** 学生ID */
  studentId: number
  /** 真实姓名 */
  realName?: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  faculty?: string
  /** 专业 */
  major?: string
  /** 年级 */
  grade?: string
  /** 班级 */
  className?: string
  /** 性别（0未知 1男 2女 9其他） */
  gender?: '0' | '1' | '2' | '9'
  /** 年龄 */
  age?: number
  /** 学习风格 */
  studyStyle?: string
  /** 学习习惯 */
  studyHabit?: string
  /** 自我介绍 */
  description?: string
  /** 学生状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 学生详细信息
 */
export interface StudentDetailVO {
  /** 学生ID（关联user_id） */
  studentId: number
  /** 真实姓名 */
  realName: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  faculty?: string
  /** 专业 */
  major?: string
  /** 年级 */
  grade?: string
  /** 班级 */
  className?: string
  /** 性别，对照 sys_user_sex（1男 2女 0未知 9其他） */
  gender?: number
  /** 年龄 */
  age?: number
  /** 学习风格 */
  studyStyle?: string
  /** 学习习惯 */
  studyHabit?: string
  /** 连续签到天数 */
  continueDay: number
  /** VIP等级 */
  vipLevel: number
  /** VIP过期时间 */
  vipExpireTime?: string
  /** 总学习时长（分钟） */
  totalStudyTime?: number
  /** 学习课程数 */
  courseCount?: number
  /** 自我介绍 */
  description?: string
  /** 学生状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 用户ID */
  userId: number
  /** 用户账号 */
  userName?: string
  /** 头像文件ID */
  avatarFileId?: number
}

/**
 * 学生列表项
 */
export interface StudentListVO {
  /** 学生ID（关联user_id） */
  studentId: number
  /** 真实姓名 */
  realName: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  faculty?: string
  /** 专业 */
  major?: string
  /** 年级 */
  grade?: string
  /** 班级 */
  className?: string
  /** 性别，对照 sys_user_sex（1男 2女 0未知 9其他） */
  gender?: number
  /** 学生状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 用户ID */
  userId: number
  /** 用户账号 */
  userName?: string
  /** 头像文件ID */
  avatarFileId?: number
}
