/**
 * 选课管理相关 API
 * 对应后端：graphedu/api/services/education/student_course.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  StudentCourseDetailVO,
  StudentCourseListVO,
  StudentCourseQueryDTO,
  StudentCourseUpdateDTO,
} from '@/types/api/education/course.ts'
import type {
  StudentChapterProgressVO,
  StudentCourseOverviewVO,
  StudentKnowledgeProfileVO,
  StudentWeakPointVO,
} from '@/types/api/education/stats.ts'
import { isMockEnabled, mockResponse } from '@/mock'
import { MOCK_COURSE_ID } from '@/mock/constants'
import * as mockSC from '@/mock/student-course'

/**
 * 获取我的选课列表（分页）
 * GET /education/student/course/list
 */
export function getMyCourseList(
  query: StudentCourseQueryDTO
): Promise<ResponseType<PageResponse<StudentCourseListVO>>> {
  return request({
    url: '/education/student/course/list',
    method: 'get',
    params: query,
  })
}

/**
 * 更新学习进度
 * PUT /education/student/course/progress
 */
export function updateLearningProgress(data: StudentCourseUpdateDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/student/course/progress',
    method: 'put',
    data: data,
  })
}

/**
 * 获取选课详情
 * GET /education/student/course/{enrollment_id}
 */
export function getEnrollmentDetail(enrollmentId: number): Promise<ResponseType<StudentCourseDetailVO>> {
  return request({
    url: `/education/student/course/${enrollmentId}`,
    method: 'get',
  })
}

/**
 * 派发课程给学生（管理员）
 * POST /education/student/course/assign
 */
export function assignCourseToStudent(data: {
  studentId: number
  courseId: number
}): Promise<ResponseType<StudentCourseDetailVO>> {
  return request({
    url: '/education/student/course/assign',
    method: 'post',
    data: data,
  })
}

/**
 * 撤销学生的课程（管理员）
 * DELETE /education/student/course/revoke/{enrollment_id}
 */
export function revokeCourseFromStudent(enrollmentId: number): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/student/course/revoke/${enrollmentId}`,
    method: 'delete',
  })
}

/**
 * 批量派发课程（管理员）
 * POST /education/student/course/batch-assign
 */
export function batchAssignCourses(data: { studentIds: number[]; courseId: number }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/student/course/batch-assign',
    method: 'post',
    data: data,
  })
}

/**
 * 学生自主选课
 * POST /education/student/course/join
 */
export function joinCourse(data: { courseId: number }): Promise<ResponseType<StudentCourseDetailVO>> {
  return request({
    url: '/education/student/course/join',
    method: 'post',
    data: data,
  })
}

/**
 * 通过课程码加入课程
 * POST /education/student/course/join-by-code
 *
 * 注：后端接口开发中，前端暂时通过 checkCourseCodeExists + getCourseList + joinCourse 组合实现
 */
export function joinCourseByCode(courseCode: string): Promise<ResponseType<StudentCourseDetailVO>> {
  return request({
    url: '/education/student/course/join-by-code',
    method: 'post',
    data: { courseCode },
  })
}

/**
 * 学生退出课程
 * DELETE /education/student/course/leave/{course_id}
 */
export function leaveCourse(courseId: number): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/student/course/leave/${courseId}`,
    method: 'delete',
  })
}

/**
 * 获取学生课程学习概览
 * GET /education/student/course/{courseId}/overview
 */
export function getStudentCourseOverview(
  courseId: number,
  params?: { weekStart?: string }
): Promise<ResponseType<StudentCourseOverviewVO>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockResponse(mockSC.getStudentCourseOverview()))
  return request({
    url: `/education/student/course/${courseId}/overview`,
    method: 'get',
    params,
  })
}

/**
 * 获取学生在课程下的章节+资源学习进度
 * GET /education/student/course/{courseId}/chapter-progress
 */
export function getMyChapterProgress(courseId: number): Promise<ResponseType<StudentChapterProgressVO[]>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID) return Promise.resolve(mockResponse(mockSC.getChapterProgress()))
  return request({
    url: `/education/student/course/${courseId}/chapter-progress`,
    method: 'get',
  })
}

/**
 * 获取学生知识点掌握度画像
 * GET /education/student/course/{courseId}/knowledge-profile
 */
export function getKnowledgeProfile(courseId: number): Promise<ResponseType<StudentKnowledgeProfileVO[]>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID) return Promise.resolve(mockResponse(mockSC.getKnowledgeProfile()))
  return request({
    url: `/education/student/course/${courseId}/knowledge-profile`,
    method: 'get',
  })
}

/**
 * 获取学生薄弱知识点
 * GET /education/student/course/{courseId}/weak-points
 */
export function getWeakPoints(courseId: number): Promise<ResponseType<StudentWeakPointVO[]>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID) return Promise.resolve(mockResponse(mockSC.getWeakPoints()))
  return request({
    url: `/education/student/course/${courseId}/weak-points`,
    method: 'get',
  })
}
