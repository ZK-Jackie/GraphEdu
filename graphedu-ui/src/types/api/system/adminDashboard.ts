/**
 * Admin 仪表盘相关类型定义
 */

/**
 * 管理员仪表盘总览统计
 */
export interface AdminDashboardSummaryVO {
  /** 总用户数 */
  totalUsers: number
  /** 总学生数 */
  totalStudents: number
  /** 总教师数 */
  totalTeachers: number
  /** 总课程数 */
  totalCourses: number
  /** 总知识图谱数 */
  totalKnowledgeGraphs: number
  /** 今日登录用户数 */
  todayLoginUsers: number
}
