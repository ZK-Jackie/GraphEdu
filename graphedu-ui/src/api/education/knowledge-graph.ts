/**
 * 知识图谱管理相关 API
 * 对应后端：graphedu/api/services/education/knowledge_graph.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common'
import type {
  KnowledgeGraphQueryDTO,
  KnowledgeGraphCreateDTO,
  KnowledgeGraphUpdateDTO,
  KnowledgeGraphDetailVO,
  KnowledgeGraphListVO,
  AutoGenerateRequestDTO,
  AutoGenerateSubmitVO,
} from '@/types/api/knowledge-graph'
import type {
  ChapterKnowledgePointVO,
  GraphRelationshipDetailVO,
  KnowledgeRelationshipUpdateDTO,
  KnowledgeExtractionRequestDTO,
  KnowledgeExtractionResultVO,
  KnowledgeGraphRelationType,
  KnowledgePointVO,
  NodeNeighborsVO,
  NvlGraphDataVO,
  SaveExtractionRequestDTO,
  TopNodesVO,
} from '@/types/api/knowledge-graph'
import { isMockEnabled, mockResponse, mockPageResponse } from '@/mock'
import { MOCK_COURSE_ID } from '@/mock/constants'
import * as mockKG from '@/mock/knowledge-graph'

/**
 * 获取知识图谱列表（分页）
 * GET /education/knowledge-graph/list
 */
export function getKnowledgeGraphList(
  query: KnowledgeGraphQueryDTO
): Promise<ResponseType<PageResponse<KnowledgeGraphListVO>>> {
  if (isMockEnabled() && query.courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockPageResponse(mockKG.getGraphList()))
  return request({
    url: '/education/knowledge-graph/list',
    method: 'get',
    params: query,
  })
}

/**
 * 获取学生可见的知识图谱列表（仅已启用、非草稿）
 * GET /education/knowledge-graph/list-visible
 */
export function getVisibleKnowledgeGraphList(
  courseId: number
): Promise<ResponseType<PageResponse<KnowledgeGraphListVO>>> {
  if (isMockEnabled() && courseId === MOCK_COURSE_ID)
    return Promise.resolve(mockPageResponse(mockKG.getVisibleGraphList()))
  return request({
    url: '/education/knowledge-graph/list-visible',
    method: 'get',
    params: { course_id: courseId },
  })
}

/**
 * 新增知识图谱
 * POST /education/knowledge-graph
 */
export function addKnowledgeGraph(data: KnowledgeGraphCreateDTO): Promise<ResponseType<KnowledgeGraphDetailVO>> {
  return request({
    url: '/education/knowledge-graph',
    method: 'post',
    data: data,
  })
}

/**
 * 修改知识图谱
 * PUT /education/knowledge-graph
 */
export function updateKnowledgeGraph(data: KnowledgeGraphUpdateDTO): Promise<ResponseType<KnowledgeGraphDetailVO>> {
  return request({
    url: '/education/knowledge-graph',
    method: 'put',
    data: data,
  })
}

/**
 * 删除知识图谱（支持批量删除）
 * DELETE /education/knowledge-graph/{graph_ids}
 */
export function deleteKnowledgeGraph(graphIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/knowledge-graph/${graphIds}`,
    method: 'delete',
  })
}

/**
 * 修改知识图谱状态
 * PUT /education/knowledge-graph/changeStatus
 */
export function changeKnowledgeGraphStatus(data: { graphId: number; status: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/knowledge-graph/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取知识图谱详细信息
 * GET /education/knowledge-graph/{graph_id}
 */
export function getKnowledgeGraphDetail(graphId: number): Promise<ResponseType<KnowledgeGraphDetailVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}`,
    method: 'get',
  })
}

// ============================================================================
// Phase 4 - 知识点提取 & 图谱操作
// ============================================================================

/**
 * LLM 提取知识点草稿（不入库，需二次确认）
 * POST /education/knowledge-graph/{graph_id}/extract
 */
export function extractKnowledgePoints(
  graphId: number,
  data: KnowledgeExtractionRequestDTO
): Promise<ResponseType<KnowledgeExtractionResultVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/extract`,
    method: 'post',
    data,
  })
}

/**
 * 将审核后的提取结果批量写入 AGE 图谱
 * POST /education/knowledge-graph/{graph_id}/save-extraction
 */
export function saveExtraction(graphId: number, data: SaveExtractionRequestDTO): Promise<ResponseType<NvlGraphDataVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/save-extraction`,
    method: 'post',
    data,
  })
}

/**
 * 获取图谱 NVL 可视化数据
 * GET /education/knowledge-graph/{graph_id}/nvl-data
 */
export function getGraphNvlData(graphId: number): Promise<ResponseType<NvlGraphDataVO>> {
  if (isMockEnabled() && (graphId === 1 || graphId === 2))
    return Promise.resolve(mockResponse(mockKG.getNvlData(graphId)))
  return request({
    url: `/education/knowledge-graph/${graphId}/nvl-data`,
    method: 'get',
  })
}

/**
 * 搜索图谱节点（标题关键词模糊匹配）
 * GET /education/knowledge-graph/{graph_id}/nodes/search
 */
export function searchGraphNodes(graphId: number, keyword: string): Promise<ResponseType<KnowledgePointVO[]>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/nodes/search`,
    method: 'get',
    params: { keyword },
  })
}

/**
 * 手动创建知识点节点
 * POST /education/knowledge-graph/{graph_id}/nodes
 */
export function createGraphNode(
  graphId: number,
  data: {
    title: string
    description?: string
    importance?: number
    source?: string
  }
): Promise<ResponseType<KnowledgePointVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/nodes`,
    method: 'post',
    data,
  })
}

/**
 * 更新知识点节点
 * PUT /education/knowledge-graph/{graph_id}/nodes/{node_id}
 */
export function updateGraphNode(
  graphId: number,
  nodeId: string,
  data: { title?: string; description?: string; importance?: number }
): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/nodes/${nodeId}`,
    method: 'put',
    data,
  })
}

/**
 * 删除知识点节点（级联删除关系）
 * DELETE /education/knowledge-graph/{graph_id}/nodes/{node_id}
 */
export function deleteGraphNode(graphId: number, nodeId: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/nodes/${nodeId}`,
    method: 'delete',
  })
}

/**
 * 创建知识点关系
 * POST /education/knowledge-graph/{graph_id}/relationships
 */
export function createGraphRelationship(
  graphId: number,
  data: {
    source_id: string
    target_id: string
    relation_type: KnowledgeGraphRelationType
    confidence?: number
    description?: string
  }
): Promise<ResponseType<{ rel_id: string }>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/relationships`,
    method: 'post',
    data,
  })
}

/**
 * 更新关系属性（不允许修改起点和终点）
 * PUT /education/knowledge-graph/{graph_id}/relationships/{rel_id}
 */
export function updateGraphRelationship(
  graphId: number,
  relId: string,
  data: KnowledgeRelationshipUpdateDTO
): Promise<ResponseType<GraphRelationshipDetailVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/relationships/${relId}`,
    method: 'put',
    data,
  })
}

/**
 * 删除关系
 * DELETE /education/knowledge-graph/{graph_id}/relationships/{rel_id}
 */
export function deleteGraphRelationship(graphId: number, relId: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/relationships/${relId}`,
    method: 'delete',
  })
}

/**
 * 查询关系详情
 * GET /education/knowledge-graph/{graph_id}/relationships/{rel_id}
 */
export function getGraphRelationship(graphId: number, relId: string): Promise<ResponseType<GraphRelationshipDetailVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/relationships/${relId}`,
    method: 'get',
  })
}

// ============================================================================
// 章节-知识点关联 API
// ============================================================================

/**
 * 批量关联知识点到章节
 * POST /education/chapter-knowledge-point/chapter/{chapter_id}/link-nodes
 */
export function linkChapterToNodes(
  chapterId: number,
  data: { point_ids: string[] }
): Promise<ResponseType<{ added: number; skipped: number }>> {
  return request({
    url: `/education/chapter-knowledge-point/chapter/${chapterId}/link-nodes`,
    method: 'post',
    data,
  })
}

/**
 * 查询章节已关联的知识点
 * GET /education/chapter-knowledge-point/chapter/{chapter_id}/linked-nodes
 */
export function getChapterLinkedNodes(chapterId: number): Promise<ResponseType<ChapterKnowledgePointVO[]>> {
  return request({
    url: `/education/chapter-knowledge-point/chapter/${chapterId}/linked-nodes`,
    method: 'get',
  })
}

/**
 * 解除章节与知识点的关联
 * DELETE /education/chapter-knowledge-point/chapter/{chapter_id}/link-nodes/{point_id}
 */
export function unlinkChapterNode(chapterId: number, pointId: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/chapter-knowledge-point/chapter/${chapterId}/link-nodes/${pointId}`,
    method: 'delete',
  })
}

/**
 * 基于骨架信息生成知识图谱
 * POST /education/knowledge-graph/generate-from-skeleton
 */
export interface GraphSkeletonDTO {
  courseId: number
  chapters: Array<{
    chapterId: number
    chapterName: string
    keywords: string[]
    description?: string
  }>
  keywords: string[]
  config: {
    model: string
    strategy: 'conservative' | 'balanced' | 'aggressive'
  }
}

export interface GraphGenerateTaskVO {
  taskId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message?: string
  graphId?: number
}

export function generateGraphFromSkeleton(data: GraphSkeletonDTO): Promise<ResponseType<GraphGenerateTaskVO>> {
  return request({
    url: '/education/knowledge-graph/generate-from-skeleton',
    method: 'post',
    data,
  })
}

/**
 * 获取图谱生成状态
 * GET /education/knowledge-graph/generate-status/{task_id}
 */
export function getGraphGenerateStatus(taskId: string): Promise<ResponseType<GraphGenerateTaskVO>> {
  return request({
    url: `/education/knowledge-graph/generate-status/${taskId}`,
    method: 'get',
  })
}

/**
 * 获取 Neo4j NVL 可视化数据
 * GET /education/knowledge-graph/{graph_id}/nvl-data
 */
export interface GraphNVLDataVO {
  nodes: Array<{
    id: number
    label: string
    type: string
    properties?: Record<string, any>
  }>
  relationships: Array<{
    id: number
    from: number
    to: number
    label: string
    type: string
  }>
  neo4jUrl?: string
}

export function getGraphNVLData(graphId: number): Promise<ResponseType<GraphNVLDataVO>> {
  return request({
    url: `/education/knowledge-graph/${graphId}/nvl-data`,
    method: 'get',
  })
}

/**
 * 关联知识点到章节
 * POST /education/chapter/{chapter_id}/link-nodes
 */
export interface ChapterLinkNodesDTO {
  nodeIds: number[]
}

/**
 * 获取知识图谱顶层节点（入度为0的节点）
 * GET /education/knowledge-graph/{graph_id}/top-nodes
 */
export function getTopNodes(graphId: number, limit: number = 10): Promise<ResponseType<TopNodesVO>> {
  if (isMockEnabled() && (graphId === 1 || graphId === 2))
    return Promise.resolve(mockResponse(mockKG.getTopNodes(graphId, limit)))
  return request({
    url: `/education/knowledge-graph/${graphId}/top-nodes`,
    method: 'get',
    params: { limit },
  })
}

/**
 * 获取节点邻居
 * GET /education/knowledge-graph/{graph_id}/nodes/{node_id}/neighbors
 */
export function getNodeNeighbors(
  graphId: number,
  nodeId: string,
  depth: number = 1,
  limit: number = 20,
  direction: 'in' | 'out' | 'both' = 'both'
): Promise<ResponseType<NodeNeighborsVO>> {
  if (isMockEnabled() && (graphId === 1 || graphId === 2))
    return Promise.resolve(mockResponse(mockKG.getNodeNeighbors(graphId, nodeId, depth, limit, direction)))
  return request({
    url: `/education/knowledge-graph/${graphId}/nodes/${nodeId}/neighbors`,
    method: 'get',
    params: { depth, limit, direction },
  })
}

/**
 * 确认知识图谱（草稿转正）
 * PUT /education/knowledge-graph/{graph_id}/confirm
 */
export function confirmKnowledgeGraph(graphId: number) {
  return request<ResponseType<KnowledgeGraphDetailVO>>({
    url: `/education/knowledge-graph/${graphId}/confirm`,
    method: 'put',
  })
}

/**
 * 异步提交自动生成知识图谱任务
 * POST /education/knowledge-graph/auto-generate/submit
 */
export function submitAutoGenerateKnowledgeGraph(data: AutoGenerateRequestDTO) {
  return request<ResponseType<AutoGenerateSubmitVO>>({
    url: '/education/knowledge-graph/auto-generate/submit',
    method: 'post',
    data,
  })
}
