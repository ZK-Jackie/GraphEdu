/**
 * 章节资料管理相关 API
 * 对应后端：graphedu/api/services/education/chapter_resource.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  ChapterResourceCreateDTO,
  ChapterResourceDetailVO,
  ChapterResourceListVO,
  ChapterResourceParseStatusVO,
  ChapterResourceParseSubmitVO,
  ChapterResourceQueryDTO,
  ChapterResourceUpdateDTO,
} from '@/types/api/education/chapterResource.ts'

/**
 * 获取资料列表（分页）
 * GET /education/chapter-resource/list
 */
export function getChapterResourceList(
  query: ChapterResourceQueryDTO
): Promise<ResponseType<PageResponse<ChapterResourceListVO>>> {
  return request({
    url: '/education/chapter-resource/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增资料
 * POST /education/chapter-resource
 */
export function addChapterResource(data: ChapterResourceCreateDTO): Promise<ResponseType<ChapterResourceDetailVO>> {
  return request({
    url: '/education/chapter-resource',
    method: 'post',
    data: data,
  })
}

/**
 * 修改资料
 * PUT /education/chapter-resource
 */
export function updateChapterResource(data: ChapterResourceUpdateDTO): Promise<ResponseType<ChapterResourceDetailVO>> {
  return request({
    url: '/education/chapter-resource',
    method: 'put',
    data: data,
  })
}

/**
 * 删除资料（支持批量删除）
 * DELETE /education/chapter-resource/{resource_ids}
 */
export function deleteChapterResource(resourceIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/education/chapter-resource/${resourceIds}`,
    method: 'delete',
  })
}

/**
 * 修改资料状态
 * PUT /education/chapter-resource/changeStatus
 */
export function changeResourceStatus(data: { resourceId: number; status: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/chapter-resource/changeStatus',
    method: 'put',
    data: data,
  })
}

/**
 * 获取资料详细信息
 * GET /education/chapter-resource/{resource_id}
 */
export function getChapterResourceDetail(resourceId: number): Promise<ResponseType<ChapterResourceDetailVO>> {
  return request({
    url: `/education/chapter-resource/${resourceId}`,
    method: 'get',
  })
}

/**
 * 按章节获取资料列表
 * GET /education/chapter-resource/chapter/{chapter_id}
 */
export function getResourcesByChapter(chapterId: number): Promise<ResponseType<ChapterResourceListVO[]>> {
  return request({
    url: `/education/chapter-resource/chapter/${chapterId}`,
    method: 'get',
  })
}

/**
 * 调整资料顺序
 * PUT /education/chapter-resource/reorder
 */
export function reorderResources(data: {
  chapterId: number
  resourceOrders: Record<number, number>
}): Promise<ResponseType<Empty>> {
  return request({
    url: '/education/chapter-resource/reorder',
    method: 'put',
    data: data,
  })
}

/**
 * 提交 PDF 解析任务
 * POST /education/chapter-resource/{resourceId}/parse
 */
export function submitParse(resourceId: number): Promise<ResponseType<ChapterResourceParseSubmitVO>> {
  return request({
    url: `/education/chapter-resource/${resourceId}/parse`,
    method: 'post',
  })
}

/**
 * 获取解析状态
 * GET /education/chapter-resource/{resourceId}/parse-status
 */
export function getParseStatus(resourceId: number): Promise<ResponseType<ChapterResourceParseStatusVO>> {
  return request({
    url: `/education/chapter-resource/${resourceId}/parse-status`,
    method: 'get',
  })
}
