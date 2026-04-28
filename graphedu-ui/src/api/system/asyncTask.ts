/**
 * 通用异步任务管理相关 API
 * 对应后端：graphedu/api/services/system/async_task.py
 */
import request from '@/utils/request'
import type { PageResponse, ResponseType } from '@/types/api/common.ts'
import type {
  AsyncTaskDetailVO,
  AsyncTaskProgressVO,
  AsyncTaskQueryDTO,
  AsyncTaskVO,
} from '@/types/api/system/asyncTask.ts'

/**
 * 分页查询异步任务列表
 * GET /system/async-task/list
 */
export function getAsyncTaskList(query: AsyncTaskQueryDTO): Promise<ResponseType<PageResponse<AsyncTaskVO>>> {
  return request({
    url: '/system/async-task/list',
    method: 'get',
    params: query,
  })
}

/**
 * 获取异步任务详情
 * GET /system/async-task/{taskId}
 */
export function getAsyncTaskDetail(taskId: number): Promise<ResponseType<AsyncTaskDetailVO>> {
  return request({
    url: `/system/async-task/${taskId}`,
    method: 'get',
  })
}

/**
 * 查询异步任务进度
 * GET /system/async-task/{taskId}/progress
 */
export function getAsyncTaskProgress(taskId: number): Promise<ResponseType<AsyncTaskProgressVO>> {
  return request({
    url: `/system/async-task/${taskId}/progress`,
    method: 'get',
  })
}

/**
 * 取消异步任务
 * POST /system/async-task/{taskId}/cancel
 */
export function cancelAsyncTask(taskId: number): Promise<ResponseType<AsyncTaskDetailVO>> {
  return request({
    url: `/system/async-task/${taskId}/cancel`,
    method: 'post',
  })
}

/**
 * 重试异步任务
 * POST /system/async-task/{taskId}/retry
 */
export function retryAsyncTask(taskId: number): Promise<ResponseType<AsyncTaskDetailVO>> {
  return request({
    url: `/system/async-task/${taskId}/retry`,
    method: 'post',
  })
}
