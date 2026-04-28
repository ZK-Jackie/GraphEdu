/**
 * 学生管理相关 API
 * 对应后端：graphedu/api/services/education/student.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common'
import type {
  StudentCreateDTO,
  StudentDetailVO,
  StudentListVO,
  StudentQueryDTO,
  StudentUpdateDTO,
} from '@/types/api/education/student.ts'

/**
 * 获取学生列表（分页）
 * GET /education/student/list
 */
export function getStudentList(query: StudentQueryDTO): Promise<ResponseType<PageResponse<StudentListVO>>> {
  return request({
    url: '/education/student/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增学生
 * POST /education/student
 */
export function addStudent(data: StudentCreateDTO): Promise<ResponseType<StudentDetailVO>> {
  return request({
    url: '/education/student',
    method: 'post',
    data: data,
  })
}

/**
 * 修改学生
 * PUT /education/student
 */
export function updateStudent(data: StudentUpdateDTO): Promise<ResponseType<StudentDetailVO>> {
  return request({
    url: '/education/student',
    method: 'put',
    data: data,
  })
}

/**
 * 删除学生（支持批量删除）
 * DELETE /education/student/{student_ids}
 */
export function deleteStudent(studentIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/student/${studentIds}`,
    method: 'delete',
  })
}

/**
 * 修改学生状态
 * PUT /education/student/changeStatus
 */
export function changeStudentStatus(data: { studentId: number; status: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/student/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取学生详细信息
 * GET /education/student/{student_id}
 */
export function getStudentDetail(studentId: number): Promise<ResponseType<StudentDetailVO>> {
  return request({
    url: `/education/student/${studentId}`,
    method: 'get',
  })
}
