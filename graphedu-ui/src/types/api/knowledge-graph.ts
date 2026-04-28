export type KnowledgeGraphRelationType = 'RELATED_TO' | 'PRIOR_TO' | 'SUBTOPIC_OF'
export type KnowledgeGraphAnyRelationType = KnowledgeGraphRelationType

export interface KnowledgeGraphQueryDTO {
  graphId?: number
  courseId?: number
  bookId?: number
  graphName?: string
  graphDatabase?: string
  buildMethod?: string
  status?: '0' | '1' | '2'
  isDraft?: string
  beginTime?: string
  endTime?: string
  page?: number
  size?: number
}

export interface KnowledgeGraphCreateDTO {
  courseId: number
  bookId?: number
  graphName: string
  graphDatabase: string
  description?: string
  buildMethod?: string
}

export interface KnowledgeGraphUpdateDTO {
  graphId: number
  courseId?: number
  bookId?: number
  graphName?: string
  graphDatabase?: string
  version?: string
  description?: string
  buildMethod?: string
  status?: '0' | '1' | '2'
}

export interface KnowledgeGraphDetailVO {
  graphId: number
  courseId: number
  bookId?: number
  graphName: string
  graphDatabase: string
  isDraft: string
  version: string
  description?: string
  totalNodes?: number
  totalRelationships?: number
  nodeTypeStats?: Record<string, any>
  relationshipTypeStats?: Record<string, any>
  averageDegree?: number
  connectivityScore?: number
  buildMethod?: string
  buildInfo?: Record<string, any>
  lastExtended?: string
  status: string
  taskStatus?: string
  createBy?: number
  createTime?: string
  updateBy?: number
  updateTime?: string
  courseName?: string
}

export interface KnowledgeGraphListVO {
  graphId: number
  courseId: number
  graphName: string
  graphDatabase: string
  isDraft: string
  version: string
  totalNodes?: number
  totalRelationships?: number
  buildMethod?: string
  status: string
  taskStatus?: string
  createTime?: string
  lastExtended?: string
  courseName?: string
  courseCover?: string
}

export interface KnowledgeExtractionRequestDTO {
  mode: 'markdown' | 'skeleton' | 'combined'
  document_id?: number
  skeleton_text?: string
}

export interface KnowledgePointDraftVO {
  title: string
  description?: string
  importance: number
  confidence: number
  source: string
}

export interface KnowledgeRelationshipDraftVO {
  source_title: string
  target_title: string
  relation_type: KnowledgeGraphAnyRelationType
  confidence: number
  description?: string
}

export interface KnowledgeExtractionResultVO {
  points: KnowledgePointDraftVO[]
  relationships: KnowledgeRelationshipDraftVO[]
  mode: string
  total_points: number
  total_relationships: number
}

export interface SaveExtractionRequestDTO {
  points: Array<{
    title: string
    description?: string
    importance: number
  }>
  relationships: KnowledgeRelationshipDraftVO[]
}

export interface NvlNodePropertiesVO {
  title: string
  description?: string
  importance: number
  source: string
  uuid?: string
}

export interface NvlNodeVO {
  id: string
  labels: string[]
  properties: NvlNodePropertiesVO
}

export interface NvlRelationshipPropertiesVO {
  confidence?: number | null
  description?: string | null
}

export interface NvlRelationshipVO {
  id: string
  type: KnowledgeGraphAnyRelationType
  from: string
  to: string
  properties: NvlRelationshipPropertiesVO
}

export interface NvlGraphDataVO {
  nodes: NvlNodeVO[]
  relationships: NvlRelationshipVO[]
  total_nodes: number
  total_relationships: number
}

export interface KnowledgePointVO {
  id: string
  course_id: number
  title: string
  description?: string
  importance: number
  source: string
}

export interface GraphRelationshipDetailVO {
  rel_id: string
  rel_type: KnowledgeGraphRelationType
  from_node_id: string
  to_node_id: string
  confidence: number | null
  description?: string | null
}

export interface KnowledgeRelationshipUpdateDTO {
  relation_type?: KnowledgeGraphRelationType
  confidence?: number
  description?: string
}

export interface ChapterKnowledgePointVO {
  id: number
  chapter_id: number
  point_id: string
  sort_order: number
  point_title?: string
  point_description?: string
  point_importance?: number
}

export interface TopNodesVO {
  nodes: NvlNodeVO[]
  relationships: NvlRelationshipVO[]
  total: number
}

export interface NodeNeighborsVO {
  center_node_id: string
  nodes: NvlNodeVO[]
  relationships: NvlRelationshipVO[]
  depth: number
  total_nodes: number
  total_relationships: number
}

// ============================================================================
// 学习路径相关类型
// ============================================================================

export interface LearningPlanListVO {
  plan_id: string
  course_id: number
  title: string
  status: 'active' | 'completed' | 'archived'
  create_time?: string
}

export interface LearningPathProgressDetailVO {
  node_uuid: string
  mastery_level: string
  mastery_score?: number | null
  mastered: boolean
}

export interface LearningPlanProgressVO {
  total: number
  mastered: number
  progress_pct: number
  details: LearningPathProgressDetailVO[]
}

export interface LearningPlanDetailVO {
  plan: LearningPlanListVO
  graph: NvlGraphDataVO | null
  progress: LearningPlanProgressVO | null
}

/** 自动生成知识图谱请求 */
export interface AutoGenerateRequestDTO {
  courseId: number
  graphName?: string
}

/** 自动生成异步提交结果 */
export interface AutoGenerateSubmitVO {
  graphId: number
  taskStatus: string
}
