/**
 * 代码生成工具相关 API
 * 对应后端：graphedu/api/services/generator/router.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/api/common.ts'
import type {
  GenTableQueryDTO,
  GenTableVO,
  GenTableDetailVO,
  GenCodePreviewVO,
  DbTableQueryDTO,
  DbTableVO,
  ImportTableDTO,
  UpdateGenTableDTO,
  DictOptionVO,
  MenuTreeOptionVO,
} from '@/types/api/tool/gen.ts'

/**
 * 查询代码生成表列表（分页）
 * GET /system/tool/gen/list
 */
export function getGenTableList(query: GenTableQueryDTO): Promise<ResponseType<PageResponse<GenTableVO>>> {
  return request({
    url: '/system/tool/gen/list',
    method: 'get',
    params: query,
  })
}

/**
 * 查询数据库表列表（分页）
 * GET /system/tool/gen/db/list
 */
export function getDbTableList(query: DbTableQueryDTO): Promise<ResponseType<PageResponse<DbTableVO>>> {
  return request({
    url: '/system/tool/gen/db/list',
    method: 'get',
    params: query,
  })
}

/**
 * 查询代码生成表详细信息
 * GET /system/tool/gen/{table_id}
 */
export function getGenTableDetail(tableId: number): Promise<ResponseType<GenTableDetailVO>> {
  return request({
    url: `/system/tool/gen/${tableId}`,
    method: 'get',
  })
}

/**
 * 修改代码生成配置
 * PUT /system/tool/gen
 */
export function updateGenTable(data: UpdateGenTableDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/tool/gen',
    method: 'put',
    data: data,
  })
}

/**
 * 创建数据库表
 * POST /system/tool/gen/createTable
 */
export function createTable(data: { sql: string }): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/tool/gen/createTable',
    method: 'post',
    data,
  })
}

/**
 * 导入表
 * POST /system/tool/gen/importTable
 */
export function importTable(data: ImportTableDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/system/tool/gen/importTable',
    method: 'post',
    data: data,
  })
}

/**
 * 预览生成代码
 * GET /system/tool/gen/preview/{table_id}
 */
export function previewGenCode(tableId: number): Promise<ResponseType<GenCodePreviewVO>> {
  return request({
    url: `/system/tool/gen/preview/${tableId}`,
    method: 'get',
  })
}

/**
 * 删除代码生成表（支持批量，tableIds 为逗号分隔的 ID 字符串或单个数字）
 * DELETE /system/tool/gen/{table_ids}
 */
export function deleteGenTable(tableIds: string | number): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/tool/gen/${tableIds}`,
    method: 'delete',
  })
}

/**
 * 生成代码（自定义路径）
 * GET /system/tool/gen/genCode/{table_name}
 */
export function genCodeToPath(tableName: string): Promise<ResponseType<string>> {
  return request({
    url: `/system/tool/gen/genCode/${tableName}`,
    method: 'get',
  })
}

/**
 * 批量生成代码（下载ZIP）
 * GET /system/tool/gen/batchGenCode
 */
export function batchGenCode(tables: string): Promise<Blob> {
  return request({
    url: '/system/tool/gen/batchGenCode',
    method: 'get',
    params: { tables },
    responseType: 'blob',
  })
}

/**
 * 同步数据库
 * GET /system/tool/gen/sync/{table_name}
 */
export function synchDb(tableName: string): Promise<ResponseType<Empty>> {
  return request({
    url: `/system/tool/gen/sync/${tableName}`,
    method: 'get',
  })
}

/**
 * 查询字典选项列表
 * GET /system/dict/type/optionselect
 */
export function getDictOptionSelect(): Promise<ResponseType<DictOptionVO[]>> {
  return request({
    url: '/system/dict/type/optionselect',
    method: 'get',
  })
}

/**
 * 查询菜单树
 * GET /system/function/treeselect
 */
export function getMenuTreeSelect(): Promise<ResponseType<MenuTreeOptionVO[]>> {
  return request({
    url: '/system/function/treeselect',
    method: 'get',
  })
}
