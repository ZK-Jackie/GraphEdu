/**
 * 教师管理相关 API
 * 对应后端：graphedu/api/services/education/teacher.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common'
import type {
  TeacherCreateDTO,
  TeacherDetailVO,
  TeacherListVO,
  TeacherQueryDTO,
  TeacherUpdateDTO,
} from '@/types/api/education/teacher.ts'

/**
 * 获取教师列表（分页）
 * GET /education/teacher/list
 */
export function getTeacherList(query: TeacherQueryDTO): Promise<ResponseType<PageResponse<TeacherListVO>>> {
  return request({
    url: '/education/teacher/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增教师
 * POST /education/teacher
 */
export function addTeacher(data: TeacherCreateDTO): Promise<ResponseType<TeacherDetailVO>> {
  return request({
    url: '/education/teacher',
    method: 'post',
    data: data,
  })
}

/**
 * 修改教师
 * PUT /education/teacher
 */
export function updateTeacher(data: TeacherUpdateDTO): Promise<ResponseType<TeacherDetailVO>> {
  return request({
    url: '/education/teacher',
    method: 'put',
    data: data,
  })
}

/**
 * 删除教师（支持批量删除）
 * DELETE /education/teacher/{teacher_ids}
 */
export function deleteTeacher(teacherIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/teacher/${teacherIds}`,
    method: 'delete',
  })
}

/**
 * 修改教师状态
 * PUT /education/teacher/changeStatus
 */
export function changeTeacherStatus(data: { teacherId: number; status: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/teacher/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取教师详细信息
 * GET /education/teacher/{teacher_id}
 */
export function getTeacherDetail(teacherId: number): Promise<ResponseType<TeacherDetailVO>> {
  return request({
    url: `/education/teacher/${teacherId}`,
    method: 'get',
  })
}
