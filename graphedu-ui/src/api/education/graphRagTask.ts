/**
 * GraphRAG 任务管理相关 API
 * 对应后端：graphedu/api/services/education/graphrag_task.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  GraphRAGTaskCreateDTO,
  GraphRAGTaskDetailVO,
  GraphRAGTaskListVO,
  GraphRAGTaskQueryDTO,
  GraphRAGTaskUpdateDTO,
} from '@/types/api/education/graphragTask.ts'

/**
 * 获取 GraphRAG 任务列表（分页）
 * GET /education/graphrag-task/list
 */
export function getGraphRAGTaskList(
  query: GraphRAGTaskQueryDTO
): Promise<ResponseType<PageResponse<GraphRAGTaskListVO>>> {
  return request({
    url: '/education/graphrag-task/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增 GraphRAG 任务
 * POST /education/graphrag-task
 */
export function addGraphRAGTask(data: GraphRAGTaskCreateDTO): Promise<ResponseType<GraphRAGTaskDetailVO>> {
  return request({
    url: '/education/graphrag-task',
    method: 'post',
    data: data,
  })
}

/**
 * 修改 GraphRAG 任务
 * PUT /education/graphrag-task
 */
export function updateGraphRAGTask(data: GraphRAGTaskUpdateDTO): Promise<ResponseType<GraphRAGTaskDetailVO>> {
  return request({
    url: '/education/graphrag-task',
    method: 'put',
    data: data,
  })
}

/**
 * 删除 GraphRAG 任务（支持批量删除）
 * DELETE /education/graphrag-task/{task_ids}
 */
export function deleteGraphRAGTask(taskIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/graphrag-task/${taskIds}`,
    method: 'delete',
  })
}

/**
 * 获取 GraphRAG 任务详细信息
 * GET /education/graphrag-task/{task_id}
 */
export function getGraphRAGTaskDetail(taskId: number): Promise<ResponseType<GraphRAGTaskDetailVO>> {
  return request({
    url: `/education/graphrag-task/${taskId}`,
    method: 'get',
  })
}

/**
 * 获取指定文档的 GraphRAG 任务列表（不分页）
 * GET /education/graphrag-task/document/{document_id}
 */
export function getTasksByDocument(documentId: number): Promise<ResponseType<GraphRAGTaskListVO[]>> {
  return request({
    url: `/education/graphrag-task/document/${documentId}`,
    method: 'get',
  })
}
