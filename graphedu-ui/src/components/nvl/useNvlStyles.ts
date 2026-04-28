import type { NvlNode, NvlRel } from './types'

// ─── 颜色常量 ────────────────────────────────────────────────────────────────

/** 节点类型颜色映射 */
const NODE_TYPE_COLORS: Record<string, string> = {
  chapter: '#1890ff', // 蓝 - 大纲章节
  knowledge: '#52c41a', // 绿 - 知识点
  concept: '#722ed1', // 紫 - 概念
  default: '#4C8EDA',
}

/** 学习状态颜色映射（Phase 5 浏览态） */
const STATUS_COLORS: Record<string, string> = {
  normal: '#4C8EDA',
  unlearned: '#bfbfbf',
  learning: '#faad14',
  mastered: '#52c41a',
  high: '#52c41a',
  medium: '#4C8EDA',
  low: '#fa8c16',
}

/** 关系类型颜色映射 */
const REL_TYPE_COLORS: Record<string, string> = {
  PRIOR_TO: '#ff4d4f', // 红 - 前置依赖
  RELATED_TO: '#8c8c8c', // 灰 - 相关
  SUBTOPIC_OF: '#1890ff', // 蓝 - 子主题
  PREREQUISITE: '#ff4d4f', // 兼容旧数据
  CONTAINS: '#1890ff', // 兼容旧数据
  BELONGS_TO: '#722ed1', // 兼容旧数据
  default: '#A5ABB6',
}

/** 低置信度关系的标记颜色（Phase 4 审核界面） */
const LOW_CONFIDENCE_COLOR = '#faad14' // 橙黄警示色
const LOW_CONFIDENCE_THRESHOLD = 0.6

// ─── Composable ──────────────────────────────────────────────────────────────

/**
 * NVL 节点与关系样式计算
 * - 根据 nodeType / status / confidence 自动填充 color、size、captions 等字段
 * - 不修改原始数据，返回新对象
 */
export function useNvlStyles() {
  /**
   * 为单个节点应用样式
   * @param node 原始节点（可含 nodeType / status / description 等业务扩展字段）
   * @returns 含完整样式字段的节点对象
   */
  function styleNode(node: NvlNode): NvlNode {
    const styled: NvlNode = { ...node }

    // 颜色：status 优先（Phase 5），次之 nodeType，最后默认
    if (styled.color === undefined) {
      if (node.status) {
        styled.color = STATUS_COLORS[node.status] ?? STATUS_COLORS.normal
      } else {
        styled.color = NODE_TYPE_COLORS[node.nodeType ?? 'default'] ?? NODE_TYPE_COLORS.default
      }
    }

    // 节点大小：章节节点稍大
    if (styled.size === undefined) {
      styled.size = node.nodeType === 'chapter' ? 45 : 35
    }

    // 文字标签：若没有 captions，则从 caption 或 id 生成
    if (!styled.captions) {
      const label = styled.caption ?? styled.id
      styled.captions = [{ value: label, styles: ['bold'] }]
    }

    return styled
  }

  /**
   * 为单个关系应用样式
   * @param rel 原始关系（可含 relType / confidence 等业务扩展字段）
   * @returns 含完整样式字段的关系对象
   */
  function styleRel(rel: NvlRel): NvlRel {
    const styled: NvlRel = { ...rel }

    // 颜色：低置信度时用警示色，否则按类型
    if (styled.color === undefined) {
      const isLowConfidence = rel.confidence !== undefined && rel.confidence < LOW_CONFIDENCE_THRESHOLD
      if (isLowConfidence) {
        styled.color = LOW_CONFIDENCE_COLOR
      } else {
        styled.color = REL_TYPE_COLORS[rel.relType ?? 'default'] ?? REL_TYPE_COLORS.default
      }
    }

    // 线宽：低置信度时用虚线效果（NVL 无虚线支持，用更细的线区分）
    if (styled.width === undefined) {
      const isLowConfidence = rel.confidence !== undefined && rel.confidence < LOW_CONFIDENCE_THRESHOLD
      styled.width = isLowConfidence ? 1 : 2
    }

    // 关系标签：若没有 caption，则从 relType 或 type 生成
    if (styled.caption === undefined && (rel.relType || rel.type)) {
      styled.caption = rel.relType ?? rel.type
    }

    // 低置信度关系在 Phase 4 中标记为 disabled（视觉变灰），
    // 由父组件根据业务需求决定是否启用
    return styled
  }

  /**
   * 批量处理节点列表
   */
  function styleNodes(nodes: NvlNode[]): NvlNode[] {
    return nodes.map(styleNode)
  }

  /**
   * 批量处理关系列表
   */
  function styleRels(rels: NvlRel[]): NvlRel[] {
    return rels.map(styleRel)
  }

  return {
    styleNode,
    styleRel,
    styleNodes,
    styleRels,
    NODE_TYPE_COLORS,
    STATUS_COLORS,
    REL_TYPE_COLORS,
    LOW_CONFIDENCE_THRESHOLD,
  }
}
