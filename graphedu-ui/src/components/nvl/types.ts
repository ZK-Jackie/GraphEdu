import type { Node, Relationship } from '@neo4j-nvl/base'

/**
 * 扩展 NVL Node，附加业务字段
 */
export type NvlNode = Node & {
  /** Neo4j 节点标签 */
  labels?: string[]
  /** Neo4j 节点属性 */
  properties?: Record<string, any>
  /** 节点业务类型：章节 / 知识点 / 概念 */
  nodeType?: 'chapter' | 'knowledge' | 'concept'
  /** 学习状态：通用状态 + 掌握等级 */
  status?: 'normal' | 'unlearned' | 'learning' | 'mastered' | 'high' | 'medium' | 'low'
  /** 知识点描述，用于 Tooltip 展示 */
  description?: string
  /** 对应后端知识点 ID */
  knowledgeId?: string
  /** 跳转路由路径（Phase 5 导航联动） */
  routePath?: string
}

/**
 * 扩展 NVL Relationship，附加业务字段
 */
export type NvlRel = Relationship & {
  /** Neo4j 关系属性 */
  properties?: Record<string, any>
  /** 关系类型：标准类型 + 兼容旧数据别名 */
  relType?: 'RELATED_TO' | 'PRIOR_TO' | 'SUBTOPIC_OF' | 'PREREQUISITE' | 'CONTAINS' | 'BELONGS_TO'
  /** AI 推断置信度 0~1（Phase 4 审核界面使用：< 0.6 标记为低置信度） */
  confidence?: number
  /** 关系描述 */
  description?: string
}

/** 图谱数据结构 */
export interface NvlGraphData {
  nodes: NvlNode[]
  rels: NvlRel[]
}

/** 组件工作模式 */
export type GraphMode = 'view' | 'edit'

/** Tooltip 展示信息（位置 + 节点数据） */
export interface TooltipInfo {
  node: NvlNode
  /** 相对视口的 x 像素坐标 */
  x: number
  /** 相对视口的 y 像素坐标 */
  y: number
}
