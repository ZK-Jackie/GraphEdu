/**
 * 章节描述生成结果 VO
 * 对应后端：POST /education/chapter/{id}/generate-description
 */
export interface ChapterDescriptionResultVO {
  /** 生成的描述文本 */
  description: string
  /** 章节 ID */
  chapterId: number
}

/**
 * 章节描述生成请求 DTO
 */
export interface ChapterGenerateDescriptionDTO {
  /** 关联文档 ID（可选，用于定向检索 GraphRAG 索引） */
  documentId?: number
}
