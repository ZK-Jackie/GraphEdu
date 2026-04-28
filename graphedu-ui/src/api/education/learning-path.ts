/**
 * 学习路径管理相关 API
 * 对应后端：graphedu/api/services/education/learning_path.py
 */
import request from '@/utils/request'
import type { ResponseType, Empty } from '@/types/api/common'
import type { LearningPlanListVO, LearningPlanDetailVO } from '@/types/api/knowledge-graph'
import { isMockEnabled, mockResponse } from '@/mock'
import { MOCK_COURSE_ID } from '@/mock/constants'
import * as mockLP from '@/mock/learning-path'

/**
 * 查询我的学习路径列表
 * GET /education/learning-path/my
 */
export function getMyLearningPlans(courseId: number): Promise<ResponseType<LearningPlanListVO[]>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID) return Promise.resolve(mockResponse(mockLP.getMyLearningPlans()))
  return request({
    url: '/education/learning-path/my',
    method: 'get',
    params: { course_id: courseId },
  })
}

/**
 * 查看学习路径详情（含子图 + 进度）
 * GET /education/learning-path/{plan_id}
 */
export function getLearningPlanDetail(planId: string): Promise<ResponseType<LearningPlanDetailVO>> {
  if (isMockEnabled() && (planId === 'plan-001' || planId === 'plan-002'))
    return Promise.resolve(mockResponse(mockLP.getLearningPlanDetail(planId)))
  return request({
    url: `/education/learning-path/${planId}`,
    method: 'get',
  })
}

/**
 * 删除学习路径
 * DELETE /education/learning-path/{plan_id}
 */
export function deleteLearningPlan(planId: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/learning-path/${planId}`,
    method: 'delete',
  })
}

/**
 * 更新学习路径状态
 * PUT /education/learning-path/{plan_id}/status
 */
export function updateLearningPlanStatus(planId: string, status: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/learning-path/${planId}/status`,
    method: 'put',
    data: { status },
  })
}
