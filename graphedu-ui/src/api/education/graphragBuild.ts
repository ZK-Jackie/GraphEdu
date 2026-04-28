/**
 * GraphRAG 索引构建相关 API
 * 对应后端:graphedu/api/services/education/graphrag_task.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse } from '@/types/api/common.ts'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'
import type {
  GraphRAGBuildCreateDTO,
  GraphRAGBuildProgressVO,
  GraphRAGResourceQueryDTO,
  GraphRAGTaskDetailVO,
  GraphRAGTaskListVO,
} from '@/types/api/education/graphragTask.ts'

/**
 * 获取可构建 GraphRAG 的资源列表(document 需已文本化，text 可直通)
 * GET /education/graphrag-task/build/resources
 */
export function getBuildableResources(
  query: GraphRAGResourceQueryDTO
): Promise<ResponseType<PageResponse<ChapterResourceListVO>>> {
  return request({
    url: '/education/graphrag-task/build/resources',
    method: 'get',
    params: query,
  })
}

/**
 * 提交 GraphRAG 索引构建任务
 * POST /education/graphrag-task/build/submit
 */
export function submitGraphRAGBuild(data: GraphRAGBuildCreateDTO): Promise<ResponseType<GraphRAGTaskDetailVO>> {
  return request({
    url: '/education/graphrag-task/build/submit',
    method: 'post',
    data: data,
  })
}

/**
 * 获取 GraphRAG 构建进度(从 Redis 获取实时进度)
 * GET /education/graphrag-task/build/progress/{task_id}
 */
export function getGraphRAGBuildProgress(taskId: number): Promise<ResponseType<GraphRAGBuildProgressVO>> {
  return request({
    url: `/education/graphrag-task/build/progress/${taskId}`,
    method: 'get',
  })
}

/**
 * 取消 GraphRAG 构建任务
 * DELETE /education/graphrag-task/build/cancel/{task_id}
 */
export function cancelGraphRAGTask(taskId: number): Promise<ResponseType<boolean>> {
  return request({
    url: `/education/graphrag-task/build/cancel/${taskId}`,
    method: 'delete',
  })
}

/**
 * 获取指定课程的所有 GraphRAG 任务列表（不分页）
 * GET /education/graphrag-task/course/{course_id}
 */
export function getGraphRAGTaskListByCourse(courseId: number): Promise<ResponseType<GraphRAGTaskListVO[]>> {
  return request({
    url: `/education/graphrag-task/course/${courseId}`,
    method: 'get',
  })
}

/**
 * 启用 GraphRAG 任务（同一课程仅允许启用一个）
 * PUT /education/graphrag-task/{task_id}/enable
 */
export function enableGraphRAGTask(taskId: number): Promise<ResponseType<GraphRAGTaskDetailVO>> {
  return request({
    url: `/education/graphrag-task/${taskId}/enable`,
    method: 'put',
  })
}

/**
 * 重试失败的 GraphRAG 构建任务
 * POST /education/graphrag-task/build/retry/{task_id}
 */
export function retryGraphRAGTask(taskId: number): Promise<ResponseType<GraphRAGTaskDetailVO>> {
  return request({
    url: `/education/graphrag-task/build/retry/${taskId}`,
    method: 'post',
  })
}

/**
 * 删除 GraphRAG 任务
 * DELETE /education/graphrag-task/{task_ids}
 */
export function deleteGraphRAGTask(taskIds: string): Promise<ResponseType> {
  return request({
    url: `/education/graphrag-task/${taskIds}`,
    method: 'delete',
  })
}
