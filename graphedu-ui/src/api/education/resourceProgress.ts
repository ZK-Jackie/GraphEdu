/**
 * 学生资料阅读进度相关 API
 * 对应后端：graphedu/api/services/education/resource_progress.py
 */
import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common.ts'
import type { ResourceProgressReportDTO, StudentResourceProgressDetailVO } from '@/types/api/education/stats.ts'

/**
 * 上报资料阅读进度（定时/关闭时调用）
 * POST /education/resource-progress
 */
export function reportResourceProgress(
  data: ResourceProgressReportDTO
): Promise<ResponseType<StudentResourceProgressDetailVO>> {
  return request({
    url: '/education/resource-progress',
    method: 'post',
    data,
  })
}

/**
 * 查询单个资料的进度详情（用于断点续学恢复位置）
 * GET /education/resource-progress/{resourceId}
 */
export function getResourceProgressDetail(resourceId: number): Promise<ResponseType<StudentResourceProgressDetailVO>> {
  return request({
    url: `/education/resource-progress/${resourceId}`,
    method: 'get',
  })
}
