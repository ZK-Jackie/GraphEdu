export interface ChapterResourceParseSubmitVO {
  resourceId: number
  mineruTaskId: string
  parseStatus: string
}

export interface ChapterResourceParseStatusVO {
  resourceId: number
  parseStatus: string
  mineruTaskId?: string
  textFileId?: number
  pageCount?: number
  markdownLength?: number
  markdownS3Key?: string
  markdownUrl?: string
  errorMessage?: string
}

/**
 * 章节资源批量删除结果 VO
 */
export interface ChapterResourceBatchDeleteResultVO {
  /** 成功删除数量 */
  successCount: number
  /** 失败数量 */
  failCount: number
  /** 详细结果列表 */
  results: Array<{
    /** 资源ID */
    resourceId: number
    /** 是否成功 */
    success: boolean
    /** 错误信息 */
    error?: string
  }>
}

/**
 * 章节内容查询请求
 */
export interface ChapterResourceQueryDTO {
  /** 资料ID */
  resourceId?: number
  /** 所属章节ID */
  chapterId?: number
  /** 资料名称 */
  resourceName?: string
  /** 资料类型（video视频/document文档/text文本/image图片/audio音频） */
  resourceType?: 'video' | 'document' | 'text' | 'image' | 'audio' | 'archive' | 'binary'
  /** 是否可见（Y/N） */
  isVisible?: 'Y' | 'N'
  /** 状态（0正常 1停用 2已删除） */
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
 * 创建章节内容请求
 */
export interface ChapterResourceCreateDTO {
  /** 所属章节ID */
  chapterId: number
  /** 资料名称 */
  resourceName: string
  /** 资料类型（video视频/document文档/text文本/image图片/audio音频/archive压缩包/binary二进制文件） */
  resourceType: 'video' | 'document' | 'text' | 'image' | 'audio' | 'archive' | 'binary'
  /** 文件ID（引用sys_upload.file_id） */
  fileId?: number
  /** 外部链接URL */
  resourceUrl?: string
  /** 描述 */
  description?: string
  /** 扩展数据（JSONB格式，存储视频时长、文档页数等元数据） */
  resourceData?: Record<string, any>
  /** 显示顺序 */
  displayOrder?: number
  /** 是否可见（Y/N） */
  isVisible?: 'Y' | 'N'
}

/**
 * 更新章节内容请求
 */
export interface ChapterResourceUpdateDTO {
  /** 资料ID */
  resourceId: number
  /** 资料名称 */
  resourceName?: string
  /** 资料类型（video视频/document文档/text文本/image图片/audio音频） */
  resourceType?: 'video' | 'document' | 'text' | 'image' | 'audio' | 'archive' | 'binary'
  /** 文件ID（引用sys_upload.file_id） */
  fileId?: number
  /** 外部链接URL */
  resourceUrl?: string
  /** 描述 */
  description?: string
  /** 扩展数据（JSONB格式） */
  resourceData?: Record<string, any>
  /** 显示顺序 */
  displayOrder?: number
  /** 是否可见（Y/N） */
  isVisible?: 'Y' | 'N'
  /** 状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 章节内容详细信息
 */
export interface ChapterResourceDetailVO {
  /** 资料ID */
  resourceId: number
  /** 所属章节ID */
  chapterId: number
  /** 资料名称 */
  resourceName: string
  /** 资料类型（video视频/document文档/text文本） */
  resourceType: string
  /** 文件ID（引用sys_upload.file_id） */
  fileId?: number
  /** 外部链接URL */
  resourceUrl?: string
  /** 描述 */
  description?: string
  /** 扩展数据（JSONB格式，存储视频时长、文档页数等元数据） */
  resourceData?: Record<string, any>
  /** 纯文本文件ID（PDF 解析后） */
  textFileId?: number
  /** 解析状态（0待处理 1处理中 2处理成功 3处理失败） */
  parseStatus?: string
  /** 显示顺序 */
  displayOrder: number
  /** 是否可见（Y/N） */
  isVisible: string
  /** 状态（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 文件URL */
  fileUrl?: string
  /** 文件上传信息（sys_upload） */
  fileInfo?: import('../system/upload').FileInfoVO
}

/**
 * 章节内容列表项
 */
export interface ChapterResourceListVO {
  /** 资料ID */
  resourceId: number
  /** 所属章节ID */
  chapterId: number
  /** 资料名称 */
  resourceName: string
  /** 资料类型（video视频/document文档/text文本） */
  resourceType: string
  /** 文件ID（引用sys_upload.file_id） */
  fileId?: number
  /** 外部链接URL */
  resourceUrl?: string
  /** 描述 */
  description?: string
  /** 扩展数据（JSONB格式） */
  resourceData?: Record<string, any>
  /** 解析状态（0待处理 1处理中 2处理成功 3处理失败） */
  parseStatus?: string
  /** 显示顺序 */
  displayOrder: number
  /** 是否可见（Y/N） */
  isVisible: string
  /** 状态（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 文件URL */
  fileUrl?: string
  /** 文件上传信息（sys_upload） */
  fileInfo?: import('../system/upload').FileInfoVO
}

/**
 * 文档任务状态 VO（PDF 解析 / GraphRAG 构建）
 * 对应后端：章节资料解析和 GraphRAG 构建任务
 */
export interface DocumentTaskStatusVO {
  /** 文档ID */
  documentId: number
  /** PDF 解析状态：0待处理 / 1处理中 / 2处理成功 / 3处理失败 */
  parseStatus: string
  /** MinerU 任务 ID */
  mineruTaskId?: string
  /** 解析页数 */
  pageCount?: number
  /** Markdown 内容长度 */
  markdownLength?: number
  /** 纯文本文件ID */
  textFileId?: number
  /** Markdown 在对象存储中的 Key */
  markdownS3Key?: string
  /** Markdown 结果临时访问链接 */
  markdownUrl?: string
  /** 实体数量 */
  entityCount?: number
  /** 关系数量 */
  relationCount?: number
  /** 社区摘要数量 */
  communityCount?: number
  /** 错误信息（失败时） */
  errorMessage?: string
}

/**
 * PDF 解析提交响应 VO
 * 对应后端：POST /education/resource-document/{id}/parse
 */
export interface ParseSubmitVO {
  /** 文档 ID */
  documentId: number
  /** MinerU 任务 ID */
  mineruTaskId: string
  /** 解析状态，固定为 '1'(处理中) */
  parseStatus: string
}

/**
 * Celery 任务提交响应 VO
 * 用于 build-graph 等异步任务的提交结果
 */
export interface CeleryTaskVO {
  /** Celery 任务 ID */
  celeryTaskId: string
  /** 提交状态，固定为 'submitted' */
  status: string
  /** 关联文档 ID（build-graph 时） */
  documentId?: number
  /** 关联章节 ID（generate-description 时） */
  chapterId?: number
}
