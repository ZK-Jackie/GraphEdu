/**
 * 习题作答记录相关 API
 * 对应后端：graphedu/api/services/education/exercise_attempt.py
 */
import request from '@/utils/request'
import type { PageResponse, ResponseType } from '@/types/api/common.ts'
import type {
  ExerciseAttemptQueryDTO,
  ExerciseAttemptStatisticsVO,
  ExerciseAttemptSubmitDTO,
  ExerciseAttemptVO,
} from '@/types/api/education/courseExercise.ts'
import { isMockEnabled, mockResponse } from '@/mock'
import { MOCK_COURSE_ID } from '@/mock/constants'
import * as mockExercise from '@/mock/exercise'

/**
 * 学生提交习题作答
 * POST /education/exercise-attempt
 */
export function submitExerciseAttempt(data: ExerciseAttemptSubmitDTO): Promise<ResponseType<ExerciseAttemptVO>> {
  return request({
    url: '/education/exercise-attempt',
    method: 'post',
    data,
  })
}

/**
 * 获取作答记录列表（分页）
 * GET /education/exercise-attempt/list
 */
export function getExerciseAttemptList(
  query: ExerciseAttemptQueryDTO
): Promise<ResponseType<PageResponse<ExerciseAttemptVO>>> {
  if (isMockEnabled() && query.courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockResponse(mockExercise.getExerciseAttemptList()))
  return request({
    url: '/education/exercise-attempt/list',
    method: 'get',
    params: query,
  })
}

/**
 * 获取习题的作答统计
 * GET /education/exercise-attempt/statistics/{exerciseId}
 */
export function getExerciseStatistics(exerciseId: number): Promise<ResponseType<ExerciseAttemptStatisticsVO>> {
  return request({
    url: `/education/exercise-attempt/statistics/${exerciseId}`,
    method: 'get',
  })
}

/**
 * 获取作答记录详情
 * GET /education/exercise-attempt/{attemptId}
 */
export function getExerciseAttemptDetail(attemptId: number): Promise<ResponseType<ExerciseAttemptVO>> {
  if (isMockEnabled()) {
    const detail = mockExercise.getExerciseAttemptDetail(attemptId)
    if (detail) return Promise.resolve(mockResponse(detail))
  }
  return request({
    url: `/education/exercise-attempt/${attemptId}`,
    method: 'get',
  })
}

/**
 * 获取学生在某道题上的所有作答记录
 * GET /education/exercise-attempt/student/{exerciseId}/{studentId}
 */
export function getStudentAttemptsForExercise(
  exerciseId: number,
  studentId: number
): Promise<ResponseType<ExerciseAttemptVO[]>> {
  return request({
    url: `/education/exercise-attempt/student/${exerciseId}/${studentId}`,
    method: 'get',
  })
}
