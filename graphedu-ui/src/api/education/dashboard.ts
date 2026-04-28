/**
 * 首页仪表盘 API
 * 对应后端：graphedu/api/services/education/dashboard.py
 */
import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common.ts'
import type {
  DailyActiveItemVO,
  DailyActiveMinutesVO,
  DashboardCalendarItemVO,
  DashboardCourseItemVO,
  DashboardWeakPointVO,
  StudentDashboardSummaryVO,
  TeacherDashboardCourseVO,
  TeacherDashboardRankingVO,
  TeacherDashboardSummaryVO,
} from '@/types/api/education/stats.ts'
import { isMockEnabled, mockResponse } from '@/mock'
import * as mockDashboard from '@/mock/dashboard'

// ============================================================================
// 学生端
// ============================================================================

/** 获取学生仪表盘总览统计 */
export function getStudentDashboardSummary(): Promise<ResponseType<StudentDashboardSummaryVO>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getStudentSummary()))
  return request({
    url: '/education/dashboard/student/summary',
    method: 'get',
  })
}

/** 获取学生学习日历热力图数据 */
export function getStudentDashboardCalendar(year: number): Promise<ResponseType<DashboardCalendarItemVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getStudentCalendar()))
  return request({
    url: '/education/dashboard/student/calendar',
    method: 'get',
    params: { year },
  })
}

/** 获取学生学习趋势数据（按日期范围） */
export function getStudentDashboardTrend(
  startDate: string,
  endDate: string
): Promise<ResponseType<DailyActiveMinutesVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getStudentTrend()))
  return request({
    url: '/education/dashboard/student/trend',
    method: 'get',
    params: { startDate, endDate },
  })
}

/** 获取学生最近学习的课程 */
export function getStudentDashboardCourses(limit: number = 6): Promise<ResponseType<DashboardCourseItemVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getStudentCourses()))
  return request({
    url: '/education/dashboard/student/courses',
    method: 'get',
    params: { limit },
  })
}

/** 获取学生跨课程薄弱知识点 */
export function getStudentDashboardWeakPoints(limit: number = 5): Promise<ResponseType<DashboardWeakPointVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getStudentWeakPoints()))
  return request({
    url: '/education/dashboard/student/weak-points',
    method: 'get',
    params: { limit },
  })
}

// ============================================================================
// 教师端
// ============================================================================

/** 获取教师仪表盘总览统计 */
export function getTeacherDashboardSummary(): Promise<ResponseType<TeacherDashboardSummaryVO>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getTeacherSummary()))
  return request({
    url: '/education/dashboard/teacher/summary',
    method: 'get',
  })
}

/** 获取教师各课程概览 */
export function getTeacherDashboardCourses(): Promise<ResponseType<TeacherDashboardCourseVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getTeacherCourses()))
  return request({
    url: '/education/dashboard/teacher/courses',
    method: 'get',
  })
}

/** 获取教师跨课程学生排名 */
export function getTeacherDashboardRankings(limit: number = 10): Promise<ResponseType<TeacherDashboardRankingVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getTeacherRankings()))
  return request({
    url: '/education/dashboard/teacher/rankings',
    method: 'get',
    params: { limit },
  })
}

/** 获取教师课程互动趋势数据（按天数） */
export function getTeacherDashboardTrend(days: number = 30): Promise<ResponseType<DailyActiveItemVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getTeacherTrend()))
  return request({
    url: '/education/dashboard/teacher/trend',
    method: 'get',
    params: { days },
  })
}

/** 获取教师课程互动趋势数据（按日期范围） */
export function getTeacherDashboardTrendByWeek(
  startDate: string,
  endDate: string,
  courseId?: number
): Promise<ResponseType<DailyActiveItemVO[]>> {
  if (isMockEnabled()) return Promise.resolve(mockResponse(mockDashboard.getTeacherTrend()))
  return request({
    url: '/education/dashboard/teacher/trend',
    method: 'get',
    params: { startDate, endDate, ...(courseId != null && { courseId }) },
  })
}
