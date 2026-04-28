/**
 * 知识图谱查询请求
 */
export interface KnowledgeGraphQueryDTO {
  /** 图谱ID */
  graphId?: number
  /** 课程ID */
  courseId?: number
  /** 图谱名称 */
  graphName?: string
  /** Neo4j数据库名称 */
  graphDatabase?: string
  /** 构建方法（nlp, llm, llm_assisted等） */
  buildMethod?: string
  /** 知识图谱状态（0正常 1停用 2已删除） */
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
 * 创建知识图谱请求
 */
export interface KnowledgeGraphCreateDTO {
  /** 课程ID */
  courseId: number
  /** 图谱名称 */
  graphName: string
  /** Neo4j数据库名称 */
  graphDatabase: string
  /** 图谱描述 */
  description?: string
  /** 构建方法（nlp, llm, llm_assisted等） */
  buildMethod?: string
}

/**
 * 更新知识图谱请求
 */
export interface KnowledgeGraphUpdateDTO {
  /** 图谱ID */
  graphId: number
  /** 课程ID */
  courseId?: number
  /** 图谱名称 */
  graphName?: string
  /** Neo4j数据库名称 */
  graphDatabase?: string
  /** 图谱版本号 */
  version?: string
  /** 图谱描述 */
  description?: string
  /** 构建方法（nlp, llm, llm_assisted等） */
  buildMethod?: string
  /** 知识图谱状态（0正常 1停用 2已删除） */
  status?: '0' | '1' | '2'
}

/**
 * 知识图谱详细信息
 */
export interface KnowledgeGraphDetailVO {
  /** 图谱ID */
  graphId: number
  /** 课程ID */
  courseId: number
  /** 图谱名称 */
  graphName: string
  /** Neo4j数据库名称 */
  graphDatabase: string
  /** 图谱版本号 */
  version: string
  /** 图谱描述 */
  description?: string
  /** 总节点数 */
  totalNodes?: number
  /** 总关系数 */
  totalRelationships?: number
  /** 节点类型统计（JSONB格式） */
  nodeTypeStats?: Record<string, any>
  /** 关系类型统计（JSONB格式） */
  relationshipTypeStats?: Record<string, any>
  /** 平均度数 */
  averageDegree?: number
  /** 连通性评分 */
  connectivityScore?: number
  /** 构建方法，对照 kg_build_method（nlp, llm, llm_assisted等） */
  buildMethod?: string
  /** 构建信息（JSONB格式，包含构建参数、模型信息等） */
  buildInfo?: Record<string, any>
  /** 最后扩展时间 */
  lastExtended?: string
  /** 知识图谱状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
}

/**
 * 知识图谱列表项
 */
export interface KnowledgeGraphListVO {
  /** 图谱ID */
  graphId: number
  /** 课程ID */
  courseId: number
  /** 图谱名称 */
  graphName: string
  /** Neo4j数据库名称 */
  graphDatabase: string
  /** 图谱版本号 */
  version: string
  /** 总节点数 */
  totalNodes?: number
  /** 总关系数 */
  totalRelationships?: number
  /** 构建方法，对照 kg_build_method（nlp, llm, llm_assisted等） */
  buildMethod?: string
  /** 知识图谱状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 最后扩展时间 */
  lastExtended?: string
}

/**
 * 章节知识点关联结果 VO（已废弃）
 */
export interface ChapterKnowledgePointLinkResultVO {
  /** 成功关联数量 */
  added: number
  /** 跳过数量（已存在） */
  skipped: number
}

/**
 * 知识点-章节关联详细信息
 */
export interface KnowledgeNodeChapterDetailVO {
  /** 关系ID */
  nodeChapterId: number
  /** 章节ID */
  chapterId: number
  /** 知识点业务UUID */
  nodeUuid: string
  /** 相关性评分（0-1） */
  relevanceScore: number
  /** 关系描述 */
  description?: string
  /** 是否主要关联（Y是 N否） */
  isPrimary: string
  /** 关系状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 知识点标题 */
  nodeTitle?: string
  /** 知识点描述 */
  nodeDescription?: string
  /** 重要程度（1-5） */
  nodeImportance?: number
}
