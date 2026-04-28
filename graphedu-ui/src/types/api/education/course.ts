import type { TeacherListVO } from '@/types/api/education/teacher.ts'

/**
 * 课程查询请求
 */
export interface CourseQueryDTO {
  /** 课程ID */
  courseId?: number
  /** 课程代码 */
  courseCode?: string
  /** 课程名称 */
  courseName?: string
  /** 所属学院 */
  faculty?: string
  /** 课程状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
  /** 是否公开（Y是 N否） */
  isPublic?: 'Y' | 'N'
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
 * 创建课程请求
 */
export interface CourseCreateDTO {
  /** 课程代码 */
  courseCode: string
  /** 课程名称 */
  courseName: string
  /** 所属学院 */
  faculty?: string
  /** 课程描述 */
  description?: string
  /** 课程封面文件ID */
  coverFileId?: number
  /** 课程分类 */
  category?: string
  /** 难度级别（1初级 2中级 3高级） */
  difficultyLevel?: '1' | '2' | '3'
  /** 总学时（小时） */
  totalHours?: number
  /** 课程大纲（富文本） */
  courseOutline?: string
  /** 适用人群（富文本） */
  targetAudience?: string
  /** 学习目标（富文本） */
  learningGoals?: string
  /** 课程标签列表 */
  tags?: string[]
  /** 是否公开（Y是 N否） */
  isPublic?: 'Y' | 'N'
  /** 教师ID列表（可选，提供时后端自动绑定教师） */
  teacherIds?: number[]
}

/**
 * 更新课程请求
 */
export interface CourseUpdateDTO {
  /** 课程ID */
  courseId: number
  /** 课程代码 */
  courseCode?: string
  /** 课程名称 */
  courseName?: string
  /** 所属学院 */
  faculty?: string
  /** 课程描述 */
  description?: string
  /** 课程封面文件ID */
  coverFileId?: number
  /** 课程分类 */
  category?: string
  /** 难度级别（1初级 2中级 3高级） */
  difficultyLevel?: '1' | '2' | '3'
  /** 总学时（小时） */
  totalHours?: number
  /** 课程大纲（富文本） */
  courseOutline?: string
  /** 适用人群（富文本） */
  targetAudience?: string
  /** 学习目标（富文本） */
  learningGoals?: string
  /** 课程标签列表 */
  tags?: string[]
  /** 是否公开（Y是 N否） */
  isPublic?: 'Y' | 'N'
  /** 课程状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 更新课程教师关联请求
 */
export interface CourseTeacherUpdateDTO {
  /** 课程ID */
  courseId: number
  /** 教师ID列表 */
  teacherIds: number[]
}

/**
 * 学生选课请求
 */
export interface StudentCourseCreateDTO {
  /** 课程ID */
  courseId: number
}

/**
 * 学生选课查询请求
 */
export interface StudentCourseQueryDTO {
  /** 学生ID */
  studentId?: number
  /** 课程ID */
  courseId?: number
  /** 选课开始时间 */
  beginTime?: string
  /** 选课结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 更新学习进度请求
 */
export interface StudentCourseUpdateDTO {
  /** 课程ID */
  courseId: number
  /** 学习进度（0-100） */
  progress: number
}

/**
 * 课程详细信息
 */
export interface CourseDetailVO {
  /** 课程ID */
  courseId: number
  /** 课程代码 */
  courseCode: string
  /** 课程名称 */
  courseName: string
  /** 所属学院 */
  faculty?: string
  /** 课程描述 */
  description?: string
  /** 课程封面文件ID */
  coverFileId?: number
  /** 课程封面URL */
  coverUrl?: string
  /** 课程分类 */
  category?: string
  /** 难度级别（1初级 2中级 3高级） */
  difficultyLevel?: string
  /** 总学时（小时） */
  totalHours?: number
  /** 课程大纲（富文本） */
  courseOutline?: string
  /** 适用人群（富文本） */
  targetAudience?: string
  /** 学习目标（富文本） */
  learningGoals?: string
  /** 课程标签列表 */
  tags?: string[]
  /** 课程状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 是否公开，对照 sys_data_option（Y是 N否） */
  isPublic: string
  /** 学生人数 */
  studentCount: number
  /** 浏览次数 */
  viewCount: number
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 授课教师ID列表 */
  teacherIds?: number[]
  /** 授课教师列表 */
  teachers?: TeacherListVO[]
}

/**
 * 课程列表项
 */
export interface CourseListVO {
  /** 课程ID */
  courseId: number
  /** 课程代码 */
  courseCode: string
  /** 课程名称 */
  courseName: string
  /** 所属学院 */
  faculty?: string
  /** 课程封面文件ID */
  coverFileId?: number
  /** 课程封面URL */
  coverUrl?: string
  /** 课程状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 是否公开，对照 sys_data_option（Y是 N否） */
  isPublic: string
  /** 学生人数 */
  studentCount: number
  /** 浏览次数 */
  viewCount: number
  /** 创建时间 */
  createTime?: string
  /** 主教师ID */
  teacherId?: number
  /** 主教师姓名 */
  teacherName?: string
}

/**
 * 学生选课详细信息
 */
export interface StudentCourseDetailVO {
  /** 记录ID */
  id: number
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 选课时间 */
  enrollTime: string
  /** 学习进度（0-100） */
  progress: number
  /** 最后学习时间 */
  lastStudyTime?: string
  /** 课程信息 */
  course?: CourseListVO
}

/**
 * 学生选课列表项
 */
export interface StudentCourseListVO {
  /** 记录ID */
  id: number
  /** 学生ID */
  studentId: number
  /** 课程ID */
  courseId: number
  /** 选课时间 */
  enrollTime: string
  /** 学习进度（0-100） */
  progress: number
  /** 最后学习时间 */
  lastStudyTime?: string
  /** 课程名称 */
  courseName?: string
  /** 课程代码 */
  courseCode?: string
  /** 课程封面文件ID */
  coverFileId?: number
  /** 课程封面URL */
  coverUrl?: string
}

/**
 * 课程学生数据（教师视角）
 */
export interface CourseStudentVO {
  /** 选课记录ID */
  enrollmentId: number
  /** 学生ID */
  studentId: number
  /** 真实姓名 */
  realName: string
  /** 学号 */
  studentNo?: string
  /** 班级 */
  className?: string
  /** 学院 */
  faculty?: string
  /** 性别（0未知 1男 2女 9其他） */
  gender?: number
  /** 头像URL */
  avatarUrl?: string
  /** 选课时间 */
  enrollTime?: string
  /** 学习进度（0-100） */
  progress: number
  /** 最后学习时间 */
  lastStudyTime?: string
  /** 学生状态 */
  status: string
}

/**
 * 课程学生统计数据
 */
export interface CourseStudentStatsVO {
  /** 总学生数 */
  totalStudents: number
  /** 平均学习进度（0-100） */
  averageProgress: number
  /** 已完成学生数（进度100%） */
  completedStudents: number
  /** 今日活跃学生数 */
  todayActive: number
}

/**
 * 课程学生列表结果（含分页 + 统计）
 */
export interface CourseStudentsResultVO {
  /** 学生列表 */
  students: CourseStudentVO[]
  /** 统计数据 */
  stats: CourseStudentStatsVO
  /** 总数 */
  total: number
}
