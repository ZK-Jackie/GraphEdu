/**
 * 定时任务管理相关 API
 * 对应后端：graphedu/api/services/system/job.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  JobQueryDTO,
  JobCreateDTO,
  JobUpdateDTO,
  JobStatusChangeDTO,
  JobExecuteOnceDTO,
  JobLogQueryDTO,
  JobDetailVO,
  JobExecuteResultVO,
} from '@/types/api/tool/job.ts'

/**
 * 获取任务列表（分页）
 * GET /system/job/list
 */
export function getJobList(query: JobQueryDTO): Promise<ResponseType<PageResponse>> {
  return request({
    url: '/system/job/list',
    method: 'get',
    params: query,
  })
}

/**
 * 获取任务详情
 * GET /system/job/{job_id}
 */
export function getJobDetail(jobId: number): Promise<ResponseType<JobDetailVO>> {
  return request({
    url: `/system/job/${jobId}`,
    method: 'get',
  })
}

/**
 * 新增任务
 * POST /system/job
 */
export function addJob(data: JobCreateDTO): Promise<ResponseType<JobDetailVO>> {
  return request({
    url: '/system/job',
    method: 'post',
    data: data,
  })
}

/**
 * 修改任务
 * PUT /system/job
 */
export function updateJob(data: JobUpdateDTO): Promise<ResponseType<JobDetailVO>> {
  return request({
    url: '/system/job',
    method: 'put',
    data: data,
  })
}

/**
 * 删除任务（支持批量删除）
 * DELETE /system/job/{job_ids}
 */
export function deleteJob(jobIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/job/${jobIds}`,
    method: 'delete',
  })
}

/**
 * 修改任务状态
 * PUT /system/job/changeStatus
 */
export function changeJobStatus(data: JobStatusChangeDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/job/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 立即执行一次任务
 * PUT /system/job/run
 */
export function executeJobOnce(data: JobExecuteOnceDTO): Promise<ResponseType<JobExecuteResultVO>> {
  return request({
    url: '/system/job/run',
    method: 'put',
    data: data,
  })
}

/**
 * 获取任务日志列表（分页）
 * GET /system/job/log/list
 */
export function getJobLogList(query: JobLogQueryDTO): Promise<ResponseType<PageResponse>> {
  return request({
    url: '/system/job/log/list',
    method: 'get',
    params: query,
  })
}

/**
 * 删除任务日志（支持批量删除）
 * DELETE /system/job/log/{job_log_ids}
 */
export function deleteJobLog(jobLogIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/job/log/${jobLogIds}`,
    method: 'delete',
  })
}

/**
 * 清空任务日志
 * DELETE /system/job/log/clean
 */
export function clearJobLog(): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/job/log/clean',
    method: 'delete',
  })
}
