/**
 * 课程练习管理相关 API
 * 对应后端：graphedu/api/services/education/course_exercise.py
 */
import request from '@/utils/request'
import type { DeleteResponse, Empty, PageResponse, ResponseType } from '@/types/api/common.ts'
import type {
  CourseExerciseBatchGenerateDTO,
  CourseExerciseCreateDTO,
  CourseExerciseDetailVO,
  CourseExerciseGenerateProgressVO,
  CourseExerciseGenerateTaskVO,
  CourseExerciseListVO,
  CourseExerciseQueryDTO,
  CourseExerciseUpdateDTO,
} from '@/types/api/education/courseExercise.ts'

/**
 * 获取课程练习列表（分页）
 * GET /education/course-exercise/list
 */
export function getCourseExerciseList(
  query: CourseExerciseQueryDTO
): Promise<ResponseType<PageResponse<CourseExerciseListVO>>> {
  return request({
    url: '/education/course-exercise/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增课程练习
 * POST /education/course-exercise
 */
export function addCourseExercise(data: CourseExerciseCreateDTO): Promise<ResponseType<CourseExerciseDetailVO>> {
  return request({
    url: '/education/course-exercise',
    method: 'post',
    data,
  })
}

/**
 * 修改课程练习
 * PUT /education/course-exercise
 */
export function updateCourseExercise(data: CourseExerciseUpdateDTO): Promise<ResponseType<CourseExerciseDetailVO>> {
  return request({
    url: '/education/course-exercise',
    method: 'put',
    data,
  })
}

/**
 * 修改课程练习状态
 * PUT /education/course-exercise/changeStatus
 */
export function changeCourseExerciseStatus(data: {
  exerciseId: number
  status: '0' | '1' | '2'
}): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/course-exercise/changeStatus',
    method: 'put',
    data,
  })
}

/**
 * 获取课程练习详情
 * GET /education/course-exercise/{exercise_id}
 */
export function getCourseExerciseDetail(exerciseId: number): Promise<ResponseType<CourseExerciseDetailVO>> {
  return request({
    url: `/education/course-exercise/${exerciseId}`,
    method: 'get',
  })
}

/**
 * 删除课程练习（支持批量）
 * DELETE /education/course-exercise/{exercise_ids}
 */
export function deleteCourseExercise(exerciseIds: string): Promise<ResponseType<DeleteResponse<number>>> {
  return request({
    url: `/education/course-exercise/${exerciseIds}`,
    method: 'delete',
  })
}

/**
 * 教师端 AI 批量生成课程练习（异步）
 * POST /education/course-exercise/batch-generate
 */
export function batchGenerateExercises(
  data: CourseExerciseBatchGenerateDTO
): Promise<ResponseType<CourseExerciseGenerateTaskVO>> {
  return request({
    url: '/education/course-exercise/batch-generate',
    method: 'post',
    data,
  })
}

/**
 * 查询 AI 出题异步任务进度
 * GET /education/course-exercise/generate-progress/{taskId}
 */
export function getGenerateProgress(taskId: string): Promise<ResponseType<CourseExerciseGenerateProgressVO>> {
  return request({
    url: `/education/course-exercise/generate-progress/${taskId}`,
    method: 'get',
  })
}
