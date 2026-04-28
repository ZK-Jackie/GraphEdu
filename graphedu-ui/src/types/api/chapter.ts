import type { CourseListVO } from '@/types/api/education/course.ts'

import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'

/**
 * 章节查询请求
 */
export interface ChapterQueryDTO {
  /** 章节ID */
  chapterId?: number
  /** 课程ID */
  courseId?: number
  /** 父章节ID（0表示根节点） */
  parentId?: number
  /** 章节名称 */
  chapterName?: string
  /** 章节状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
  /** 创建开始时间 */
  beginTime?: string
  /** 创建结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建章节请求
 */
export interface ChapterCreateDTO {
  /** 课程ID */
  courseId: number
  /** 父章节ID（0表示根节点） */
  parentId?: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号（用于排序） */
  chapterNo?: number
  /** 章节描述 */
  description?: string
}

/**
 * 更新章节请求
 */
export interface ChapterUpdateDTO {
  /** 章节ID */
  chapterId: number
  /** 父章节ID（0表示根节点） */
  parentId?: number
  /** 章节名称 */
  chapterName?: string
  /** 章节序号（用于排序） */
  chapterNo?: number
  /** 章节描述 */
  description?: string
  /** 章节状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 章节详细信息
 */
export interface ChapterDetailVO {
  /** 章节ID */
  chapterId: number
  /** 课程ID */
  courseId: number
  /** 父章节ID（0表示根节点） */
  parentId: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号（用于排序） */
  chapterNo: number
  /** 章节描述 */
  description?: string
  /** 章节状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 关联课程信息 */
  course?: CourseListVO
  /** 章节资料列表 */
  resources?: ChapterResourceListVO[]
  /** 学习进度（当前用户） */
  progress?: any
}

/**
 * 章节列表项
 */
export interface ChapterListVO {
  /** 章节ID */
  chapterId: number
  /** 课程ID */
  courseId: number
  /** 父章节ID（0表示根节点） */
  parentId: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号（用于排序） */
  chapterNo: number
  /** 章节描述 */
  description?: string
  /** 章节状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
}

/**
 * 章节树形结构
 */
export interface ChapterTreeVO {
  /** 章节ID */
  chapterId: number
  /** 课程ID */
  courseId: number
  /** 父章节ID（0表示根节点） */
  parentId: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号（用于排序） */
  chapterNo: number
  /** 章节描述 */
  description?: string
  /** 章节状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 子章节列表 */
  children?: ChapterTreeVO[]
  /** 是否有子章节 */
  hasChildren?: boolean
  /** 资料数量 */
  contentCount: number
}

/**
 * 章节树节点简要 VO（用于下拉选择）
 */
export interface ChapterTreeBriefVO {
  /** 章节ID */
  chapterId: number
  /** 父章节ID */
  parentId: number
  /** 章节名称 */
  chapterName: string
  /** 章节序号（用于排序） */
  chapterNo: number
  /** 子章节列表 */
  children: ChapterTreeBriefVO[]
}

/**
 * 章节批量删除结果 VO
 */
export interface ChapterBatchDeleteResultVO {
  /** 成功删除数量 */
  successCount: number
  /** 失败数量 */
  failCount: number
  /** 详细结果列表 */
  results: Array<{
    /** 章节ID */
    chapterId: number
    /** 是否成功 */
    success: boolean
    /** 错误信息 */
    error?: string
  }>
}
