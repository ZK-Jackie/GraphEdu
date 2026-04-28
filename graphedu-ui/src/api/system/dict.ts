/**
 * 字典管理相关 API
 * 对应后端：graphedu/api/services/system/dict.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  DictTypeQueryDTO,
  DictTypeCreateDTO,
  DictTypeUpdateDTO,
  DictTypeListVO,
  DictTypeDetailVO,
  DictDataQueryDTO,
  DictDataCreateDTO,
  DictDataUpdateDTO,
  DictDataListVO,
  DictDataDetailVO,
  DictDataSimpleVO,
} from '@/types/api/system/dict.ts'

// ============== 字典类型管理 ==============

/**
 * 获取字典类型列表（分页）
 * GET /system/dict/type/list
 */
export function getDictTypeList(query: DictTypeQueryDTO): Promise<ResponseType<PageResponse<DictTypeListVO>>> {
  return request({
    url: '/system/dict/type/list',
    method: 'get',
    params: query,
  })
}

/**
 * 新增字典类型
 * POST /system/dict/type
 */
export function addDictType(data: DictTypeCreateDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/dict/type',
    method: 'post',
    data: data,
  })
}

/**
 * 修改字典类型
 * PUT /system/dict/type
 */
export function updateDictType(data: DictTypeUpdateDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/dict/type',
    method: 'put',
    data: data,
  })
}

/**
 * 删除字典类型
 * DELETE /system/dict/type/{dict_ids}
 */
export function deleteDictType(dictIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/dict/type/${dictIds}`,
    method: 'delete',
  })
}

/**
 * 获取字典类型详细信息
 * GET /system/dict/type/{dict_id}
 */
export function getDictTypeDetail(dictId: number): Promise<ResponseType<DictTypeDetailVO>> {
  return request({
    url: `/system/dict/type/${dictId}`,
    method: 'get',
  })
}

/**
 * 刷新字典缓存
 * DELETE /system/dict/type/refreshCache
 */
export function refreshDictCache(): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/dict/type/refreshCache',
    method: 'delete',
  })
}

/**
 * 获取字典类型选项列表（用于下拉框等场景）
 * GET /system/dict/type/optionselect
 */
export function getDictTypeOptions(): Promise<ResponseType<DictTypeListVO[]>> {
  return request({
    url: '/system/dict/type/optionselect',
    method: 'get',
  })
}

// ============== 字典数据管理 ==============

/**
 * 获取字典数据列表（分页）
 * GET /system/dict/data/list
 */
export function getDictDataList(query: DictDataQueryDTO): Promise<ResponseType<PageResponse<DictDataListVO>>> {
  return request({
    url: '/system/dict/data/list',
    method: 'get',
    params: query,
  })
}

/**
 * 根据字典类型查询字典数据（优先从缓存获取）
 * GET /system/dict/data/type/{dict_type}
 */
export function getDictDataByType(dictType: string): Promise<ResponseType<DictDataSimpleVO[]>> {
  return request({
    url: `/system/dict/data/type/${dictType}`,
    method: 'get',
  })
}

/**
 * 新增字典数据
 * POST /system/dict/data
 */
export function addDictData(data: DictDataCreateDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/dict/data',
    method: 'post',
    data: data,
  })
}

/**
 * 修改字典数据
 * PUT /system/dict/data
 */
export function updateDictData(data: DictDataUpdateDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/dict/data',
    method: 'put',
    data: data,
  })
}

/**
 * 删除字典数据
 * DELETE /system/dict/data/{dict_code_ids}
 */
export function deleteDictData(dictCodeIds: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/dict/data/${dictCodeIds}`,
    method: 'delete',
  })
}

/**
 * 获取字典数据详细信息
 * GET /system/dict/data/{dict_code}
 */
export function getDictDataDetail(dictCode: number): Promise<ResponseType<DictDataDetailVO>> {
  return request({
    url: `/system/dict/data/${dictCode}`,
    method: 'get',
  })
}
