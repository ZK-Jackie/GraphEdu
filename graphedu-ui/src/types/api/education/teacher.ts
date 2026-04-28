/**
 * 教师查询请求
 */
export interface TeacherQueryDTO {
  /** 教师ID */
  teacherId?: number
  /** 真实姓名 */
  realName?: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  faculty?: string
  /** 职称 */
  title?: string
  /** 教师状态（0正常 1停用 2已删除） */
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
 * 创建教师请求
 */
export interface TeacherCreateDTO {
  /** 教师ID（关联user_id） */
  teacherId: number
  /** 真实姓名 */
  realName: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  faculty?: string
  /** 职称：教授/副教授/讲师/助教 */
  title?: string
  /** 研究方向 */
  researchDirection?: string
  /** 个人简介 */
  description?: string
}

/**
 * 更新教师请求
 */
export interface TeacherUpdateDTO {
  /** 教师ID */
  teacherId: number
  /** 真实姓名 */
  realName?: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  faculty?: string
  /** 职称：教授/副教授/讲师/助教 */
  title?: string
  /** 研究方向 */
  researchDirection?: string
  /** 个人简介 */
  description?: string
  /** 教师状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 教师详细信息
 */
export interface TeacherDetailVO {
  /** 教师ID（关联user_id） */
  teacherId: number
  /** 真实姓名 */
  realName: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  faculty?: string
  /** 职称：教授/副教授/讲师/助教 */
  title?: string
  /** 研究方向 */
  researchDirection?: string
  /** 最大带教学生数 */
  maxStudentCount: number
  /** 当前学生数 */
  currentStudentCount?: number
  /** 个人简介 */
  description?: string
  /** 教师状态，对照 sys_data_status（0正常 1停用 2已删除） */
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
 * 教师列表项
 */
export interface TeacherListVO {
  /** 教师ID（关联user_id） */
  teacherId: number
  /** 真实姓名 */
  realName: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  faculty?: string
  /** 职称：教授/副教授/讲师/助教 */
  title?: string
  /** 最大带教学生数 */
  maxStudentCount: number
  /** 当前学生数 */
  currentStudentCount?: number
  /** 头像URL */
  avatarUrl?: string
  /** 教师状态，对照 sys_data_status（0正常 1停用 2已删除） */
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
