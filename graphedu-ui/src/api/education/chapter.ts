/**
 * 章节管理相关 API
 * 对应后端：graphedu/api/services/education/chapter.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  ChapterBatchDeleteResultVO,
  ChapterCreateDTO,
  ChapterDetailVO,
  ChapterListVO,
  ChapterQueryDTO,
  ChapterTreeBriefVO,
  ChapterTreeVO,
  ChapterUpdateDTO,
} from '@/types/api/chapter.ts'
import type {
  ChapterKnowledgePointLinkResultVO,
  KnowledgeNodeChapterDetailVO,
} from '@/types/api/education/knowledgeGraph.ts'
import type {
  ChapterResourceBatchDeleteResultVO,
  ChapterResourceCreateDTO,
  ChapterResourceDetailVO,
  ChapterResourceListVO,
  ChapterResourceUpdateDTO,
} from '@/types/api/education/chapterResource.ts'
import type { ChapterDescriptionResultVO, ChapterGenerateDescriptionDTO } from '@/types/api/education/chapter.ts'

/**
 * 获取章节列表（分页）
 * GET /education/chapter/list
 */
export function getChapterList(query: ChapterQueryDTO): Promise<ResponseType<PageResponse<ChapterListVO>>> {
  return request({
    url: '/education/chapter/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增章节
 * POST /education/chapter
 */
export function addChapter(data: ChapterCreateDTO): Promise<ResponseType<ChapterDetailVO>> {
  return request({
    url: '/education/chapter',
    method: 'post',
    data: data,
  })
}

/**
 * 修改章节
 * PUT /education/chapter
 */
export function updateChapter(data: ChapterUpdateDTO): Promise<ResponseType<ChapterDetailVO>> {
  return request({
    url: '/education/chapter',
    method: 'put',
    data: data,
  })
}

/**
 * 删除章节（支持批量删除）
 * DELETE /education/chapter/{chapter_ids}
 */
export function deleteChapter(chapterIds: string): Promise<ResponseType<ChapterBatchDeleteResultVO>> {
  return request({
    url: `/education/chapter/${chapterIds}`,
    method: 'delete',
  })
}

/**
 * 修改章节状态
 * PUT /education/chapter/changeStatus
 */
export function changeChapterStatus(data: { chapterId: number; status: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/chapter/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取章节详细信息
 * GET /education/chapter/{chapter_id}
 */
export function getChapterDetail(chapterId: number): Promise<ResponseType<ChapterDetailVO>> {
  return request({
    url: `/education/chapter/${chapterId}`,
    method: 'get',
  })
}

/**
 * 获取课程章节树
 * GET /education/chapter/tree/{course_id}
 */
export function getChapterTree(courseId: number): Promise<ResponseType<ChapterTreeVO[]>> {
  return request({
    url: `/education/chapter/tree/${courseId}`,
    method: 'get',
  })
}

/**
 * 获取课程章节树（懒加载模式）
 * GET /education/chapter/tree/{course_id}/lazy
 */
export function getChapterTreeLazy(courseId: number, parentId?: number): Promise<ResponseType<ChapterTreeVO[]>> {
  return request({
    url: `/education/chapter/tree/${courseId}/lazy`,
    method: 'get',
    params: { parentId },
  })
}

/**
 * 获取课程章节树（下拉选择模式）
 * GET /education/chapter/tree/{course_id}/select
 */
export function getChapterTreeForSelect(
  courseId: number,
  parentId?: number
): Promise<ResponseType<ChapterTreeBriefVO[]>> {
  return request({
    url: `/education/chapter/tree/${courseId}/select`,
    method: 'get',
    params: { parentId },
  })
}

/**
 * 移动章节
 * PUT /education/chapter/move
 */
export function moveChapter(data: {
  chapterId: number
  newParentId: number
  newChapterNo: number
}): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/chapter/move',
    method: 'put',
    data: data,
  })
}

/**
 * 直接调用 GraphRAG Local Search 生成章节描述（同步等待）
 * POST /education/chapter/{chapter_id}/generate-description
 */
export function generateChapterDescription(
  chapterId: number,
  data?: ChapterGenerateDescriptionDTO
): Promise<ResponseType<ChapterDescriptionResultVO>> {
  return request({
    url: `/education/chapter/${chapterId}/generate-description`,
    method: 'post',
    data: data ?? {},
  })
}

/**
 * 获取章节关联的知识点列表
 * GET /education/chapter/{chapter_id}/knowledge-points
 */
export function getChapterKnowledgePoints(chapterId: number): Promise<ResponseType<KnowledgeNodeChapterDetailVO[]>> {
  return request({
    url: `/education/chapter/${chapterId}/knowledge-points`,
    method: 'get',
  })
}

/**
 * 批量关联知识点到章节
 * POST /education/chapter/{chapter_id}/knowledge-points/link
 */
export function linkChapterKnowledgePoints(
  chapterId: number,
  data: { pointIds: string[] }
): Promise<ResponseType<ChapterKnowledgePointLinkResultVO>> {
  return request({
    url: `/education/chapter/${chapterId}/knowledge-points/link`,
    method: 'post',
    data,
  })
}

/**
 * 解除章节与知识点的关联
 * DELETE /education/chapter/{chapter_id}/knowledge-points/{point_id}
 */
export function unlinkChapterKnowledgePoint(chapterId: number, pointId: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/chapter/${chapterId}/knowledge-points/${pointId}`,
    method: 'delete',
  })
}

/**
 * 获取章节的资源列表
 * GET /education/chapter/{chapter_id}/resources
 */
export function getChapterResources(chapterId: number): Promise<ResponseType<ChapterResourceListVO[]>> {
  return request({
    url: `/education/chapter/${chapterId}/resources`,
    method: 'get',
  })
}

/**
 * 为章节添加资源
 * POST /education/chapter/{chapter_id}/resources
 */
export function addChapterResource(
  chapterId: number,
  data: ChapterResourceCreateDTO
): Promise<ResponseType<ChapterResourceDetailVO>> {
  return request({
    url: `/education/chapter/${chapterId}/resources`,
    method: 'post',
    data,
  })
}

/**
 * 更新章节资源
 * PUT /education/chapter/{chapter_id}/resources/{resource_id}
 */
export function updateChapterResource(
  chapterId: number,
  resourceId: number,
  data: ChapterResourceUpdateDTO
): Promise<ResponseType<ChapterResourceDetailVO>> {
  return request({
    url: `/education/chapter/${chapterId}/resources/${resourceId}`,
    method: 'put',
    data,
  })
}

/**
 * 删除章节资源
 * DELETE /education/chapter/{chapter_id}/resources
 */
export function deleteChapterResources(
  chapterId: number,
  resourceIds: string
): Promise<ResponseType<ChapterResourceBatchDeleteResultVO>> {
  return request({
    url: `/education/chapter/${chapterId}/resources`,
    method: 'delete',
    data: { resource_ids: resourceIds },
  })
}

/**
 * 调整章节资源顺序
 * PUT /education/chapter/{chapter_id}/resources/reorder
 */
export function reorderChapterResources(
  chapterId: number,
  data: { resourceOrders: Record<number, number> }
): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/chapter/${chapterId}/resources/reorder`,
    method: 'put',
    data,
  })
}

/**
 * 修改资源状态
 * PUT /education/chapter/{chapter_id}/resources/{resource_id}/status
 */
export function changeChapterResourceStatus(
  chapterId: number,
  resourceId: number,
  status: string
): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/chapter/${chapterId}/resources/${resourceId}/status`,
    method: 'put',
    data: { status },
  })
}
