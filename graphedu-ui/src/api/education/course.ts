/**
 * 课程管理相关 API
 * 对应后端：graphedu/api/services/education/course.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  CourseCreateDTO,
  CourseDetailVO,
  CourseListVO,
  CourseQueryDTO,
  CourseUpdateDTO,
} from '@/types/api/education/course.ts'
import type { TeacherListVO } from '@/types/api/education/teacher.ts'
import { isMockEnabled, mockResponse } from '@/mock'
import { MOCK_COURSE_ID } from '@/mock/constants'
import * as mockCourse from '@/mock/course'

/**
 * 获取课程列表（分页）
 * GET /education/course/list
 */
export function getCourseList(query: CourseQueryDTO): Promise<ResponseType<PageResponse<CourseListVO>>> {
  return request({
    url: '/education/course/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增课程
 * POST /education/course
 *
 * 如果传入了 teacherIds，后端会自动在同一事务中完成教师绑定。
 */
export function addCourse(data: CourseCreateDTO): Promise<ResponseType<CourseDetailVO>> {
  return request({
    url: '/education/course',
    method: 'post',
    data: data,
  })
}

/**
 * 修改课程
 * PUT /education/course
 */
export function updateCourse(data: CourseUpdateDTO): Promise<ResponseType<CourseDetailVO>> {
  return request({
    url: '/education/course',
    method: 'put',
    data: data,
  })
}

/**
 * 删除课程（支持批量删除）
 * DELETE /education/course/{course_ids}
 */
export function deleteCourse(courseIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/course/${courseIds}`,
    method: 'delete',
  })
}

/**
 * 修改课程状态
 * PUT /education/course/changeStatus
 */
export function changeCourseStatus(data: { courseId: number; status: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/course/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取课程详细信息
 * GET /education/course/{course_id}
 */
export function getCourseDetail(courseId: number): Promise<ResponseType<CourseDetailVO>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID) return Promise.resolve(mockResponse(mockCourse.getCourseDetail()))
  return request({
    url: `/education/course/${courseId}`,
    method: 'get',
  })
}

/**
 * 为课程绑定教师
 * POST /education/course/{course_id}/teachers/bind
 */
export function bindCourseTeachers(courseId: number, teacherIds: number[]): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/course/${courseId}/teachers/bind`,
    method: 'post',
    data: teacherIds,
  })
}

/**
 * 解绑课程的教师
 * DELETE /education/course/{course_id}/teachers/unbind
 */
export function unbindCourseTeachers(courseId: number, teacherIds: number[]): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/course/${courseId}/teachers/unbind`,
    method: 'delete',
    data: teacherIds,
  })
}

/**
 * 获取课程绑定的教师列表
 * GET /education/course/{course_id}/teachers
 */
export function getCourseTeachers(courseId: number): Promise<ResponseType<TeacherListVO[]>> {
  return request({
    url: `/education/course/${courseId}/teachers`,
    method: 'get',
  })
}

/**
 * 检查课程代码是否存在
 * GET /education/course/check-code-exists
 */
export function checkCourseCodeExists(courseCode: string, excludeCourseId?: number): Promise<ResponseType<boolean>> {
  return request({
    url: '/education/course/check-code-exists',
    method: 'get',
    params: { courseCode, excludeCourseId },
  })
}

/**
 * 获取当前登录教师的课程列表（分页）
 * GET /education/course/my-courses
 */
export function getMyTeacherCourses(query: CourseQueryDTO): Promise<ResponseType<PageResponse<CourseListVO>>> {
  return request({
    url: '/education/course/my-courses',
    method: 'get',
    params: query,
  })
}
