<script setup lang="ts">
/**
 * CourseKnowledgeGraph - 课程知识图谱导航组件（长条形）
 *
 * 功能：
 * - 显示课程知识图谱列表下拉选择器（支持切换）
 * - 中央区域渲染微型 NvlGraph（可拖拽、可点击）
 * - 初始展示顶层节点（无边），点击节点增量加载 1 跳邻居和边
 * - 避免重复加载已存在的节点和边
 * - 支持悬停提示节点信息
 * - 支持通过 "⋯" 按钮打开展开视图
 * - 移动端降级为"展开查看"入口
 */
import { Empty, Spin, Tooltip } from 'ant-design-vue'
import { getNodeNeighbors, getVisibleKnowledgeGraphList, getTopNodes } from '@/api/education/knowledge-graph.ts'
import { getKnowledgeProfile } from '@/api/education/student_course.ts'
import NvlGraph from '../../../components/nvl/NvlGraph.vue'
import NvlTooltip from '../../../components/nvl/NvlTooltip.vue'
import type { NvlNode, NvlRel, TooltipInfo } from '@/components/nvl/types.ts'
import { useBreakpoints } from '@/composables/useBreakpoints.ts'
import type { KnowledgeGraphListVO, NvlNodeVO, NvlRelationshipVO } from '@/types/api/knowledge-graph.ts'
import type { StudentKnowledgeProfileVO } from '@/types/api/education/stats.ts'

interface Props {
  courseId: number
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '56px',
})

// 状态
const graphList = ref<KnowledgeGraphListVO[]>([])
const selectedGraphId = ref<number>()
const nodes = ref<NvlNode[]>([])
const rels = ref<NvlRel[]>([])
const loadedNodeIds = ref<Set<string>>(new Set())
const selectedNodeId = ref<string>()
const loading = ref(false)
const errorMessage = ref<string>()
const tooltipInfo = ref<TooltipInfo | null>(null)

// NvlGraph 组件引用
const nvlRef = ref<InstanceType<typeof NvlGraph> | null>(null)

const { isMobile } = useBreakpoints()

// 学情画像数据（用于节点着色）
const knowledgeProfiles = ref<StudentKnowledgeProfileVO[]>([])

/** 加载学情画像数据 */
async function loadKnowledgeProfiles() {
  try {
    const resp = await getKnowledgeProfile(props.courseId)
    if (resp.code === 200 && resp.data) {
      knowledgeProfiles.value = resp.data
    }
  } catch (error) {
    console.error('加载学情画像失败:', error)
  }
}

/** 掌握等级 → 节点 status 映射 */
function masteryLevelToStatus(level: string): NvlNode['status'] {
  switch (level) {
    case 'high':
      return 'high'
    case 'medium':
      return 'medium'
    case 'low':
      return 'low'
    default:
      return 'unlearned'
  }
}

/** 根据学情画像为节点设置 status */
function applyMasteryStatus(nodeList: NvlNode[]) {
  // nodeUuid 是业务 UUID，与 NvlNode.properties.uuid 对应
  const profileMap = new Map<string, StudentKnowledgeProfileVO>()
  for (const p of knowledgeProfiles.value) {
    if (p.nodeUuid != null) {
      profileMap.set(String(p.nodeUuid), p)
    }
  }
  for (const node of nodeList) {
    const lookupKey = (node.properties as Record<string, unknown>)?.uuid ?? node.id
    const profile = profileMap.get(String(lookupKey))
    if (profile) {
      node.status = masteryLevelToStatus(profile.latestMasteryLevel)
    } else {
      node.status = 'unlearned'
    }
  }
}

// VO → NvlNode 转换
function convertVoToNvlNode(vo: NvlNodeVO): NvlNode {
  return {
    id: vo.id,
    labels: vo.labels,
    caption: vo.properties.title,
    description: vo.properties.description,
    properties: vo.properties,
    nodeType: 'knowledge',
  }
}

// VO → NvlRel 转换
function convertVoToNvlRel(vo: NvlRelationshipVO): NvlRel {
  return {
    id: vo.id,
    from: vo.from,
    to: vo.to,
    type: vo.type,
    caption: vo.type,
    relType: vo.type,
    properties: vo.properties,
    confidence: vo.properties.confidence ?? undefined,
  }
}

const hasNodes = computed(() => nodes.value.length > 0)

// 加载知识图谱列表
async function loadGraphList() {
  loading.value = true
  errorMessage.value = undefined
  try {
    const resp = await getVisibleKnowledgeGraphList(props.courseId)
    if (resp.data?.rows) {
      graphList.value = resp.data.rows
      if (graphList.value.length > 0 && !selectedGraphId.value) {
        const firstGraph = graphList.value[0]
        if (firstGraph) {
          selectedGraphId.value = firstGraph.graphId
          // 并行加载学情画像和顶层节点
          await Promise.all([loadTopNodes(), loadKnowledgeProfiles()])
          applyMasteryStatus(nodes.value)
        }
      }
    } else {
      graphList.value = []
    }
  } catch (error) {
    console.error('加载知识图谱列表失败:', error)
    errorMessage.value = '加载知识图谱失败'
  } finally {
    loading.value = false
  }
}

// 加载顶层节点（初始状态，只有节点没有边）
async function loadTopNodes() {
  if (!selectedGraphId.value) return

  loading.value = true
  tooltipInfo.value = null
  errorMessage.value = undefined
  // 重置图谱状态
  nodes.value = []
  rels.value = []
  loadedNodeIds.value = new Set()
  selectedNodeId.value = undefined

  try {
    const resp = await getTopNodes(selectedGraphId.value, 10)
    if (resp.data?.nodes) {
      nodes.value = resp.data.nodes.map(convertVoToNvlNode)
      applyMasteryStatus(nodes.value)
      // 初始加载时也加载顶层节点间的关系
      if (resp.data.relationships) {
        rels.value = resp.data.relationships.map(convertVoToNvlRel)
      }
    }
  } catch (error) {
    console.error('加载顶层节点失败:', error)
    errorMessage.value = '加载节点失败'
    nodes.value = []
  } finally {
    loading.value = false
  }
}

// 增量加载邻居节点和边
async function loadNodeNeighbors(nodeId: string) {
  if (!selectedGraphId.value) return
  // 已加载过的节点不再重复请求
  if (loadedNodeIds.value.has(nodeId)) return

  loading.value = true
  try {
    const resp = await getNodeNeighbors(selectedGraphId.value, nodeId, 1, 20, 'both')
    if (resp.data) {
      const newNodes = resp.data.nodes.map(convertVoToNvlNode)
      const newRels = resp.data.relationships.map(convertVoToNvlRel)

      // 为新节点应用学情着色
      applyMasteryStatus(newNodes)

      // 合并节点（去重）
      const existingNodeIds = new Set(nodes.value.map((n) => n.id))
      for (const newNode of newNodes) {
        if (!existingNodeIds.has(newNode.id)) {
          nodes.value.push(newNode)
          existingNodeIds.add(newNode.id)
        }
      }

      // 合并关系（去重）
      const existingRelIds = new Set(rels.value.map((r) => r.id))
      for (const newRel of newRels) {
        if (!existingRelIds.has(newRel.id)) {
          rels.value.push(newRel)
          existingRelIds.add(newRel.id)
        }
      }

      // 标记该节点已加载邻居
      loadedNodeIds.value.add(nodeId)

      // 适应视图让新节点可见
      nextTick(() => {
        nvlRef.value?.fitAll()
      })
    }
  } catch (error) {
    console.error('加载邻居节点失败:', error)
  } finally {
    loading.value = false
  }
}

// 切换知识图谱
async function handleGraphChange(graphId: number | string | undefined) {
  const normalizedId = Number(graphId)
  if (!Number.isFinite(normalizedId)) return
  selectedGraphId.value = normalizedId
  await loadTopNodes()
}

// 点击节点：增量加载邻居
function handleNodeClick(node: NvlNode) {
  selectedNodeId.value = node.id
  loadNodeNeighbors(node.id)
}

function handleNodeHover(info: TooltipInfo | null) {
  tooltipInfo.value = info
}

function handleCanvasClick() {
  tooltipInfo.value = null
  selectedNodeId.value = undefined
}

// 打开知识图谱页面（导航到独立路由）
const router = useRouter()

function openExpanded() {
  tooltipInfo.value = null
  router.push(`/course/learn/${props.courseId}/knowledge-graph`)
}

// 初始化
onMounted(() => {
  loadGraphList()
})
</script>

<template>
  <div class="course-knowledge-graph" :style="{ height }">
    <!-- 加载状态 -->
    <div v-if="loading && graphList.length === 0" class="loading-container">
      <Spin size="small" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && graphList.length === 0" class="empty-container">
      <Empty :image-style="{ height: '20px' }" description="暂无知识图谱" />
    </div>

    <!-- 内容区域 -->
    <div v-else class="content-container">
      <!-- 左侧：知识图谱选择器 -->
      <a-select
        v-if="graphList.length > 1"
        v-model:value="selectedGraphId"
        class="graph-selector"
        size="small"
        :loading="loading"
        @change="(val: any) => handleGraphChange(val)"
      >
        <a-select-option v-for="graph in graphList" :key="graph.graphId" :value="graph.graphId">
          {{ graph.graphName }}
        </a-select-option>
      </a-select>

      <!-- 中央：微型图谱 -->
      <div v-if="!loading || hasNodes" class="nodes-container">
        <div v-if="!isMobile" class="mini-graph-shell">
          <NvlGraph
            ref="nvlRef"
            :nodes="nodes"
            :rels="rels"
            mode="view"
            layout="forceDirected"
            :selected-node-ids="selectedNodeId ? [selectedNodeId] : []"
            :fit-on-layout="true"
            :initial-zoom="0.5"
            @node-click="handleNodeClick"
            @node-hover="handleNodeHover"
            @canvas-click="handleCanvasClick"
          />
          <NvlTooltip :info="tooltipInfo" />
        </div>

        <div v-else class="mobile-node-summary">
          <Tooltip :title="nodes.map((node) => node.caption || node.id).join('、')">
            <span class="mobile-summary-text">{{ nodes.length }} 个知识点</span>
          </Tooltip>
        </div>

        <!-- 展开提示 -->
        <div class="expand-hint" @click="openExpanded">
          <Tooltip title="查看完整知识图谱">
            <span class="expand-icon">⋯</span>
          </Tooltip>
        </div>
      </div>

      <!-- 节点为空 -->
      <div v-else-if="!loading && !hasNodes" class="empty-nodes">
        <span class="empty-text">图谱暂无节点</span>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMessage" class="error-message">
        <span class="error-text">{{ errorMessage }}</span>
      </div>
    </div>

    <!-- 展开视图已改为路由导航，不再使用 Modal -->
  </div>
</template>

<style scoped>
@reference "#main.css";

.course-knowledge-graph {
  @apply w-full flex items-center;
  background: transparent;
}

.loading-container,
.empty-container {
  @apply flex items-center justify-center w-full h-full;
}

.content-container {
  @apply flex items-center gap-2 w-full;
}

.graph-selector {
  @apply flex-shrink-0;
  width: 140px;
}

.nodes-container {
  @apply flex items-center gap-2 flex-1 min-w-0;
}

.mini-graph-shell {
  @apply flex-1 min-w-0;
  height: 52px;
  border: 1px solid var(--ge-border-color);
  border-radius: 8px;
  overflow: hidden;
}

:deep(.mini-graph-shell .nvl-graph-container) {
  min-height: 0;
}

.mobile-node-summary {
  @apply flex-1 min-w-0;
}

.mobile-summary-text {
  @apply text-xs text-[var(--ge-text-tertiary)];
}

.expand-hint {
  @apply flex items-center justify-center;
  @apply rounded-full cursor-pointer transition-all duration-200;
  @apply bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600;
  width: 28px;
  height: 28px;
  margin-left: 8px;
  flex-shrink: 0;
}

.expand-icon {
  @apply text-gray-600 dark:text-gray-300 text-lg font-bold;
}

.empty-nodes {
  @apply flex items-center justify-center flex-1;
}

.empty-text {
  @apply text-[var(--ge-text-tertiary)] text-sm;
}

.error-message {
  @apply flex items-center justify-center flex-1;
}

.error-text {
  @apply text-red-500 text-sm;
}
</style>
