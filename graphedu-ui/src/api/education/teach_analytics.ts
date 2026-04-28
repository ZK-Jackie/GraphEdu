/**
 * 教师工作台分析相关 API
 * 对应后端：graphedu/api/services/education/teach_analytics.py
 */
import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common.ts'
import type { CourseStudentsResultVO } from '@/types/api/education/course.ts'
import type {
  CourseAnalyticsVO,
  StudentChapterDetailResultVO,
  StudentChapterLearningResultVO,
  StudentRankingItemVO,
} from '@/types/api/education/stats.ts'
import { isMockEnabled, mockResponse } from '@/mock'
import { MOCK_COURSE_ID, MOCK_USER_ID } from '@/mock/constants'
import * as mockAnalytics from '@/mock/analytics'

/**
 * 获取课程学生列表及统计数据
 * GET /education/teach/course/{courseId}/students
 */
export function getCourseStudents(
  courseId: number,
  params?: { page?: number; size?: number }
): Promise<ResponseType<CourseStudentsResultVO>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockResponse(mockAnalytics.getCourseStudents()))
  return request({
    url: `/education/teach/course/${courseId}/students`,
    method: 'get',
    params,
  })
}

/**
 * 获取课程数据分析
 * GET /education/teach/course/{courseId}/analytics
 */
export function getCourseAnalytics(
  courseId: number,
  timeRange: 'week' | 'month' | 'all' = 'month'
): Promise<ResponseType<CourseAnalyticsVO>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockResponse(mockAnalytics.getCourseAnalytics()))
  return request({
    url: `/education/teach/course/${courseId}/analytics`,
    method: 'get',
    params: { time_range: timeRange },
  })
}

/**
 * 获取课程学生排名列表
 * GET /education/teach/course/{courseId}/rankings
 */
export function getCourseRankings(courseId: number): Promise<ResponseType<StudentRankingItemVO[]>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockResponse(mockAnalytics.getCourseRankings()))
  return request({
    url: `/education/teach/course/${courseId}/rankings`,
    method: 'get',
  })
}

/**
 * 获取学生在课程中的章节学习汇总数据
 * GET /education/teach/course/{courseId}/student/{studentId}/chapter-learning
 */
export function getStudentChapterLearning(
  courseId: number,
  studentId: number
): Promise<ResponseType<StudentChapterLearningResultVO>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID && studentId === MOCK_USER_ID)
    return Promise.resolve(mockResponse(mockAnalytics.getStudentChapterLearning()))
  return request({
    url: `/education/teach/course/${courseId}/student/${studentId}/chapter-learning`,
    method: 'get',
  })
}

/**
 * 获取学生在某章节的可展开详情（资料阅读/答题记录/知识点掌握）
 * GET /education/teach/course/{courseId}/student/{studentId}/chapter/{chapterId}/detail
 */
export function getStudentChapterDetail(
  courseId: number,
  studentId: number,
  chapterId: number,
  detailType: 'resources' | 'exercises' | 'mastery',
  params?: { page?: number; size?: number }
): Promise<ResponseType<StudentChapterDetailResultVO>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID && studentId === MOCK_USER_ID)
    return Promise.resolve(mockResponse(mockAnalytics.getStudentChapterDetail(chapterId, detailType)))
  return request({
    url: `/education/teach/course/${courseId}/student/${studentId}/chapter/${chapterId}/detail`,
    method: 'get',
    params: { detail_type: detailType, ...params },
  })
}
