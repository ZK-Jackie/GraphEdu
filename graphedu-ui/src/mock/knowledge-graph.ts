/**
 * 知识图谱 Mock 数据
 */
import type {
  KnowledgeGraphListVO,
  NodeNeighborsVO,
  NvlGraphDataVO,
  NvlNodeVO,
  NvlRelationshipVO,
  TopNodesVO,
} from '@/types/api/knowledge-graph'
import { MOCK_GRAPHS, MOCK_NODES, MOCK_RELATIONSHIPS } from './constants'

export function getGraphList(): KnowledgeGraphListVO[] {
  return MOCK_GRAPHS.map((g) => ({
    graphId: g.graphId,
    courseId: g.courseId,
    graphName: g.graphName,
    graphDatabase: g.graphDatabase,
    isDraft: g.isDraft,
    version: g.version,
    totalNodes: g.totalNodes,
    totalRelationships: g.totalRelationships,
    buildMethod: g.buildMethod,
    status: g.status,
    taskStatus: g.taskStatus,
    createTime: g.createTime,
    courseName: g.courseName,
  }))
}

export function getVisibleGraphList(): KnowledgeGraphListVO[] {
  return getGraphList()
}

export function buildNvlData(
  nodeFilter: readonly { uuid: string; title: string; importance: number }[]
): NvlGraphDataVO {
  const nodes: NvlNodeVO[] = nodeFilter.map((n) => ({
    id: n.uuid,
    labels: ['KnowledgePoint'],
    properties: {
      title: n.title,
      description: `${n.title}是离散数学中的核心知识点。`,
      importance: n.importance,
      source: 'manual',
      uuid: n.uuid,
    },
  }))

  const nodeUuids = new Set(nodeFilter.map((n) => n.uuid))
  const rels = MOCK_RELATIONSHIPS.filter((r) => nodeUuids.has(r.from) && nodeUuids.has(r.to))

  const relationships: NvlRelationshipVO[] = rels.map((r, i) => ({
    id: `rel-${i}`,
    type: r.type,
    from: r.from,
    to: r.to,
    properties: {
      confidence: 0.9,
      description: undefined,
    },
  }))

  return {
    nodes,
    relationships,
    total_nodes: nodes.length,
    total_relationships: relationships.length,
  }
}

export function getNvlData(graphId: number): NvlGraphDataVO {
  if (graphId === 2) {
    // 命题逻辑专项：只有命题逻辑章的 6 个节点
    const propNodes = MOCK_NODES.filter((n) => n.chapterId === 1)
    return buildNvlData(propNodes)
  }
  // 核心概念图谱：全部 22 个节点
  return buildNvlData(MOCK_NODES)
}

/**
 * 将 MOCK_NODES 中指定节点转为 NvlNodeVO
 */
function toNvlNode(n: (typeof MOCK_NODES)[number]): NvlNodeVO {
  return {
    id: n.uuid,
    labels: ['KnowledgePoint'],
    properties: {
      title: n.title,
      description: `${n.title}是离散数学中的核心知识点。`,
      importance: n.importance,
      source: 'manual',
      uuid: n.uuid,
    },
  }
}

/**
 * 将 MOCK_RELATIONSHIPS 中指定关系转为 NvlRelationshipVO
 */
function toNvlRel(r: (typeof MOCK_RELATIONSHIPS)[number], prefix: string, index: number): NvlRelationshipVO {
  return {
    id: `${prefix}-${index}`,
    type: r.type,
    from: r.from,
    to: r.to,
    properties: { confidence: 0.9, description: undefined },
  }
}

/**
 * 根据图谱 ID 过滤有效节点和关系
 */
function filterByGraph(graphId: number): {
  nodes: readonly (typeof MOCK_NODES)[number][]
  rels: readonly (typeof MOCK_RELATIONSHIPS)[number][]
} {
  const nodeFilter = graphId === 2 ? MOCK_NODES.filter((n) => n.chapterId === 1) : MOCK_NODES
  const uuidSet = new Set(nodeFilter.map((n) => n.uuid))
  const relFilter = MOCK_RELATIONSHIPS.filter((r) => uuidSet.has(r.from) && uuidSet.has(r.to))
  return { nodes: nodeFilter, rels: relFilter }
}

/**
 * 获取顶层节点（入度为 0 的节点）
 */
export function getTopNodes(graphId: number, limit: number = 10): TopNodesVO {
  const { nodes, rels } = filterByGraph(graphId)

  // 找出所有作为关系终点的 uuid
  const toSet = new Set<string>(rels.map((r) => r.to as string))
  const topNodes = nodes.filter((n) => !toSet.has(n.uuid as string))
  const limited = topNodes.slice(0, limit)

  // 顶层节点之间可能存在的关系
  const topUuidSet = new Set(limited.map((n) => n.uuid))
  const topRels = rels.filter((r) => topUuidSet.has(r.from) && topUuidSet.has(r.to))

  return {
    nodes: limited.map(toNvlNode),
    relationships: topRels.map((r, i) => toNvlRel(r, 'rel-top', i)),
    total: topNodes.length,
  }
}

/**
 * 获取节点邻居（1 跳）
 */
export function getNodeNeighbors(
  graphId: number,
  nodeId: string,
  depth: number = 1,
  limit: number = 20,
  direction: 'in' | 'out' | 'both' = 'both'
): NodeNeighborsVO {
  const { nodes, rels } = filterByGraph(graphId)

  // 找出与 nodeId 直接相关的关系
  const directRels = rels.filter((r) => {
    if (direction === 'in') return r.to === nodeId
    if (direction === 'out') return r.from === nodeId
    return r.from === nodeId || r.to === nodeId
  })

  // 收集邻居 uuid（排除自身）
  const neighborUuids = new Set<string>()
  for (const r of directRels) {
    if (r.from !== nodeId) neighborUuids.add(r.from)
    if (r.to !== nodeId) neighborUuids.add(r.to)
  }
  const limitedUuids = [...neighborUuids].slice(0, limit)

  // 邻居节点数据
  const neighborNodes = nodes.filter((n) => limitedUuids.includes(n.uuid))

  // 包含在已选范围内的关系
  const allUuids = new Set([nodeId, ...limitedUuids])
  const relsInScope = directRels.filter((r) => allUuids.has(r.from) && allUuids.has(r.to))

  return {
    center_node_id: nodeId,
    nodes: neighborNodes.map(toNvlNode),
    relationships: relsInScope.map((r, i) => toNvlRel(r, `rel-nb-${nodeId}`, i)),
    depth,
    total_nodes: neighborNodes.length,
    total_relationships: relsInScope.length,
  }
}
