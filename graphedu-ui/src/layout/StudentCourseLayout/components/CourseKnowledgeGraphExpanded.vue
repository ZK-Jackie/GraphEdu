<script setup lang="ts">
/**
 * CourseKnowledgeGraphExpanded - 课程知识图谱展开视图
 *
 * 功能：
 * - 大尺寸弹窗展示课程知识图谱
 * - 支持点击节点增量加载邻居
 * - 左图右详情布局，显示当前节点信息与关联节点
 * - 支持节点 hover 提示和选中高亮
 */
import { Modal, message } from 'ant-design-vue'
import NvlGraph from '../../../components/nvl/NvlGraph.vue'
import NvlTooltip from '../../../components/nvl/NvlTooltip.vue'
import { getGraphNvlData } from '@/api/education/knowledge-graph.ts'
import { getKnowledgeProfile, getWeakPoints } from '@/api/education/student_course.ts'
import type { NvlNode, NvlRel, TooltipInfo } from '@/components/nvl/types.ts'
import type { NvlNodeVO, NvlRelationshipVO } from '@/types/api/knowledge-graph.ts'
import { ExclamationCircleOutlined } from '@ant-design/icons-vue'

import type { StudentKnowledgeProfileVO, StudentWeakPointVO } from '@/types/api/education/stats.ts'

interface Props {
  graphId: number
  courseId: number
  initialNode?: NvlNodeVO
}

interface Emits {
  (e: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态
const nvlRef = ref<InstanceType<typeof NvlGraph>>()
const isModalReady = ref(false) // hack: 延迟允许组件渲染的时间
const loading = ref(false)
const nodes = ref<NvlNode[]>([])
const relationships = ref<NvlRel[]>([])
const loadedNodeIds = ref<Set<string>>(new Set())
const totalNodes = ref(0)
const totalRelationships = ref(0)
const selectedNodeId = ref<string>()
const tooltipInfo = ref<TooltipInfo | null>(null)

// 学情画像数据（用于节点着色）
const knowledgeProfiles = ref<StudentKnowledgeProfileVO[]>([])
// 薄弱知识点数据
const weakPoints = ref<StudentWeakPointVO[]>([])

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

/** 加载薄弱知识点数据 */
async function loadWeakPoints() {
  try {
    const resp = await getWeakPoints(props.courseId)
    if (resp.code === 200 && resp.data) {
      weakPoints.value = resp.data
    }
  } catch (error) {
    console.error('加载薄弱知识点失败:', error)
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
  const profileMap = new Map<string, StudentKnowledgeProfileVO>()
  for (const p of knowledgeProfiles.value) {
    if (p.nodeUuid != null) {
      profileMap.set(String(p.nodeUuid), p)
    }
  }
  for (const node of nodeList) {
    // node.id 是 AGE 内部 ID，node.properties.uuid 才是业务 UUID
    const lookupKey = (node.properties as Record<string, unknown>)?.uuid ?? node.id
    const profile = profileMap.get(String(lookupKey))
    if (profile) {
      node.status = masteryLevelToStatus(profile.latestMasteryLevel)
    } else {
      node.status = 'unlearned'
    }
  }
}

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return undefined
  return nodes.value.find((node) => node.id === selectedNodeId.value)
})

const relatedNodes = computed(() => {
  if (!selectedNodeId.value) return []

  const neighborIds = new Set<string>()
  for (const rel of relationships.value) {
    if (rel.from === selectedNodeId.value) {
      neighborIds.add(rel.to)
    }
    if (rel.to === selectedNodeId.value) {
      neighborIds.add(rel.from)
    }
  }

  return nodes.value.filter((node) => neighborIds.has(node.id))
})

const selectedNodeRelations = computed(() => {
  if (!selectedNodeId.value) return []

  return relationships.value
    .filter((rel) => rel.from === selectedNodeId.value || rel.to === selectedNodeId.value)
    .map((rel) => {
      const isOutgoing = rel.from === selectedNodeId.value
      const peerId = isOutgoing ? rel.to : rel.from
      const peerNode = nodes.value.find((node) => node.id === peerId)
      return {
        id: rel.id,
        type: rel.relType || rel.type || rel.caption || 'RELATED_TO',
        confidence: rel.confidence,
        directionLabel: isOutgoing ? '出向' : '入向',
        peerId,
        peerCaption: peerNode?.caption || peerId,
      }
    })
})

// 当前选中节点的学情画像
const selectedNodeProfile = computed(() => {
  if (!selectedNodeId.value || !selectedNode.value) return undefined
  // selectedNodeId 是 AGE 内部 ID，需通过 properties.uuid 桥接到业务 UUID
  const uuid = (selectedNode.value.properties as Record<string, unknown>)?.uuid ?? selectedNodeId.value
  return knowledgeProfiles.value.find((p) => p.nodeUuid != null && p.nodeUuid === String(uuid))
})

// 当前选中节点是否为薄弱知识点（通过 profile.nodeUuid 匹配）
const selectedNodeWeakPoint = computed(() => {
  if (!selectedNodeProfile.value?.nodeUuid) return undefined
  return weakPoints.value.find((w) => w.nodeUuid === selectedNodeProfile.value!.nodeUuid)
})

/** 格式化学习时长 */
function formatStudySeconds(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
}

/** 掌握等级配置 */
const MASTERY_LEVEL_CONFIG: Record<string, { label: string; cls: string }> = {
  high: { label: '已掌握', cls: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  medium: { label: '学习中', cls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  low: { label: '薄弱', cls: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
}

// 转换 VO 到 NvlNode（与教师端 KnowledgePointManage 格式对齐）
function convertVoToNvlNode(vo: NvlNodeVO): NvlNode {
  return {
    id: vo.id,
    labels: vo.labels,
    captions: [{ value: vo.properties.title ?? '' }],
    description: vo.properties.description,
    nodeType: 'knowledge',
    // applyMasteryStatus 需要 properties.uuid 来匹配学情画像
    properties: vo.properties,
  }
}

// 转换 VO 到 NvlRel（与教师端 KnowledgePointManage 格式对齐）
function convertVoToNvlRel(vo: NvlRelationshipVO): NvlRel {
  return {
    id: vo.id,
    from: vo.from,
    to: vo.to,
    captions: [{ value: vo.type ?? '' }],
    relType: vo.type,
    confidence: vo.properties?.confidence ?? undefined,
    description: vo.properties?.description ?? undefined,
  }
}

// 节点点击事件
function handleNodeClick(node: NvlNode, event: MouseEvent) {
  event.stopPropagation()
  selectedNodeId.value = node.id
}

// 画布点击事件
function handleCanvasClick() {
  selectedNodeId.value = undefined
  tooltipInfo.value = null
}

function handleNodeHover(info: TooltipInfo | null) {
  tooltipInfo.value = info
}

function focusRelatedNode(node: NvlNode) {
  selectedNodeId.value = node.id
  nextTick(() => {
    nvlRef.value?.fitAll()
  })
}

function focusRelatedNodeById(nodeId: string) {
  selectedNodeId.value = nodeId
  nextTick(() => {
    nvlRef.value?.fitAll()
  })
}

// 初始加载
async function initialize() {
  loading.value = true
  try {
    // 并行加载全量图谱、学情画像和薄弱知识点
    const [graphDataResp] = await Promise.all([
      getGraphNvlData(props.graphId),
      loadKnowledgeProfiles(),
      loadWeakPoints(),
    ])

    const allNodeVos = graphDataResp.data?.nodes ?? []

    if (allNodeVos.length === 0) {
      message.info('该知识图谱暂无可探索节点')
      loading.value = false
      return
    }

    nodes.value = allNodeVos.map(convertVoToNvlNode)
    applyMasteryStatus(nodes.value)

    const allRelVos = graphDataResp.data?.relationships ?? []
    if (allRelVos.length > 0) {
      relationships.value = allRelVos.map(convertVoToNvlRel)
    }

    totalNodes.value = allNodeVos.length
    totalRelationships.value = allRelVos.length

    const initialNodeId = props.initialNode?.id ?? nodes.value[0]?.id
    if (initialNodeId) {
      selectedNodeId.value = initialNodeId
      loadedNodeIds.value.add(initialNodeId)
    }
  } catch (error) {
    console.error('初始化失败:', error)
    message.error('初始化失败')
    loading.value = false
    return
  }

  // 数据就绪后，用 ResizeObserver 等待容器获得真实尺寸再挂载 NvlGraph
  waitForContainerReady()
}

/** 等待图谱容器尺寸稳定后再挂载 NvlGraph */
function waitForContainerReady() {
  nextTick(() => {
    const wrapper = document.querySelector<HTMLElement>('.graph-inner-wrapper')
    if (!wrapper) {
      // 兜底：如果找不到容器，回退到延迟挂载
      setTimeout(() => {
        isModalReady.value = true
      }, 600)
      return
    }

    // 防抖：等容器尺寸稳定 150ms 不再变化后再挂载
    // 这样能确保 Modal 展开动画完全结束，容器到达最终尺寸
    let debounceTimer: ReturnType<typeof setTimeout> | null = null
    const observer = new ResizeObserver(() => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        observer.disconnect()
        debounceTimer = null
        mountGraph()
      }, 150)
    })
    observer.observe(wrapper)
  })
}

/** 挂载 NvlGraph 并完成初始化 */
function mountGraph() {
  isModalReady.value = true
  // 不再调用 forceRelayout()：容器尺寸已经正确，
  // NVL 的初始力导向布局会正常散开节点，
  // onLayoutDone 回调会自动 fit 视口。
  // 只需在布局完成后关闭 loading。
}

// 关闭对话框
function handleClose() {
  emit('close')
}

// 适应视图
function handleFitAll() {
  nvlRef.value?.fitAll()
}

// 重置缩放
function handleResetZoom() {
  nvlRef.value?.resetZoom()
}

// 初始化
onMounted(() => {
  initialize()
})
</script>

<template>
  <Modal
    :open="true"
    :footer="null"
    :closable="true"
    :width="'88vw'"
    wrap-class-name="course-knowledge-graph-expanded-modal"
    @cancel="handleClose"
  >
    <template #title>
      <div class="modal-title">
        <span>课程知识图谱</span>
        <span class="stats-info"
          >节点: {{ totalNodes || nodes.length }} 关系: {{ totalRelationships || relationships.length }}</span
        >
      </div>
    </template>

    <div class="expanded-content">
      <div class="expanded-body">
        <!-- 左侧图谱区 -->
        <div class="graph-pane">
          <div class="toolbar">
            <a-button size="small" @click="handleFitAll">适应视图</a-button>
            <a-button size="small" @click="handleResetZoom">重置缩放</a-button>
            <div v-if="nodes.length > 100" class="warning-hint">
              <ExclamationCircleOutlined class="warning-icon" />
              <span>节点数量较多，可能影响性能</span>
            </div>
          </div>

          <div class="graph-container">
            <div v-if="nodes.length === 0 && !loading" class="empty-graph">
              <p>请从顶部导航选择节点开始探索</p>
            </div>
            <div v-else class="graph-inner-wrapper">
              <NvlGraph
                v-if="isModalReady"
                ref="nvlRef"
                :nodes="nodes"
                :rels="relationships"
                mode="view"
                layout="forceDirected"
                :selected-node-ids="selectedNodeId ? [selectedNodeId] : []"
                :initial-zoom="0.8"
                @node-click="handleNodeClick"
                @node-hover="handleNodeHover"
                @canvas-click="handleCanvasClick"
                @layout-done="loading = false"
              />
            </div>
            <!-- 加载遮罩：绝对定位覆盖，不干扰图谱容器的 flex 尺寸计算 -->
            <div v-if="loading" class="graph-loading-overlay">
              <a-spin size="large" />
            </div>
            <NvlTooltip :info="tooltipInfo" />

            <div class="hint-info">点击节点查看详情</div>
          </div>
        </div>

        <!-- 右侧详情区 -->
        <aside class="detail-pane">
          <div class="detail-title">节点详情</div>

          <div v-if="selectedNode" class="detail-section">
            <div class="detail-name">{{ selectedNode.caption || selectedNode.id }}</div>
            <div class="detail-id">ID: {{ selectedNode.id }}</div>
            <p v-if="selectedNode.description" class="detail-desc">{{ selectedNode.description }}</p>
            <p v-else class="detail-empty">暂无节点描述</p>

            <!-- 我的学习情况 -->
            <div class="related-header">我的学习情况</div>
            <div v-if="selectedNodeProfile" class="learning-profile-card">
              <div class="profile-row">
                <span class="profile-label">掌握等级</span>
                <span
                  class="mastery-tag"
                  :class="MASTERY_LEVEL_CONFIG[selectedNodeProfile.latestMasteryLevel]?.cls ?? MASTERY_LEVEL_CONFIG.low?.cls"
                >
                  {{ MASTERY_LEVEL_CONFIG[selectedNodeProfile.latestMasteryLevel]?.label ?? '未知' }}
                </span>
              </div>
              <div v-if="selectedNodeProfile.latestMasteryScore != null" class="profile-row">
                <span class="profile-label">掌握评分</span>
                <span class="profile-value">{{ selectedNodeProfile.latestMasteryScore }}/100</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">学习时长</span>
                <span class="profile-value">{{ formatStudySeconds(selectedNodeProfile.totalStudySeconds) }}</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">交互次数</span>
                <span class="profile-value">{{ selectedNodeProfile.totalInteractionCount }}次</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">提问次数</span>
                <span class="profile-value">{{ selectedNodeProfile.totalQuestionCount }}次</span>
              </div>

              <!-- 薄弱知识点提示 -->
              <div v-if="selectedNodeWeakPoint" class="weak-point-alert">
                <ExclamationCircleOutlined class="weak-point-icon" />
                <div class="weak-point-text">
                  <div class="weak-point-title">薄弱知识点</div>
                  <div class="weak-point-hint">投入较多但提升有限，建议重点复习基础概念并多加练习。</div>
                </div>
              </div>
            </div>
            <div v-else class="detail-empty">尚未学习此知识点</div>

            <!-- AI 学情评语 -->
            <div class="related-header">AI 学情评语</div>
            <div class="ai-summary-card">
              <div v-if="selectedNodeProfile?.latestAssessmentReason" class="ai-summary-content">
                {{ selectedNodeProfile.latestAssessmentReason }}
              </div>
              <div v-else class="ai-summary-placeholder">暂无 AI 评语</div>
            </div>

            <div class="related-header">关联节点 ({{ relatedNodes.length }})</div>
            <div v-if="relatedNodes.length > 0" class="related-list">
              <button
                v-for="node in relatedNodes"
                :key="node.id"
                class="related-item"
                type="button"
                @click="focusRelatedNode(node)"
              >
                <span class="related-name">{{ node.caption || node.id }}</span>
                <span class="related-arrow">></span>
              </button>
            </div>
            <div v-else class="detail-empty">当前节点暂无关联节点</div>

            <div class="related-header">关系明细 ({{ selectedNodeRelations.length }})</div>
            <div v-if="selectedNodeRelations.length > 0" class="relation-list">
              <button
                v-for="rel in selectedNodeRelations"
                :key="rel.id"
                class="relation-item"
                type="button"
                @click="focusRelatedNodeById(rel.peerId)"
              >
                <span class="relation-main">{{ rel.directionLabel }} · {{ rel.type }}</span>
                <span class="relation-target">{{ rel.peerCaption }}</span>
                <span v-if="rel.confidence != null" class="relation-confidence">
                  {{ Math.round(rel.confidence * 100) }}%
                </span>
              </button>
            </div>
            <div v-else class="detail-empty">当前节点暂无关系</div>
          </div>

          <div v-else class="detail-empty-state">点击左侧节点查看详情</div>
        </aside>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
@reference "#main.css";

.modal-title {
  @apply flex justify-between items-center w-full;
}

.stats-info {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.expanded-content {
  height: 78vh;
}

.expanded-body {
  @apply h-full flex gap-3;
  min-height: 0;
}

.graph-pane {
  @apply flex-1 flex flex-col gap-2;
  min-width: 0;
}

.toolbar {
  @apply flex items-center gap-2 px-1;
}

.warning-hint {
  @apply flex items-center gap-1 ml-auto text-yellow-600 dark:text-yellow-400 text-sm;
}

.warning-icon {
  @apply text-base;
}

.graph-container {
  @apply flex-1 relative border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.graph-loading-overlay {
  @apply absolute inset-0 z-10 flex items-center justify-center;
  @apply bg-white/70 dark:bg-gray-900/70;
}

.graph-inner-wrapper {
  flex: 1;
  min-height: 0;
  height: 100%;
}

:deep(.graph-container .nvl-graph-container) {
  min-height: 0;
  height: 100%;
  display: flex;
  flex: 1;
}

.empty-graph {
  @apply flex items-center justify-center h-full text-gray-400 dark:text-gray-500;
}

.hint-info {
  @apply absolute left-1/2 -translate-x-1/2 bottom-3;
  @apply text-xs text-gray-600 dark:text-gray-300;
  @apply bg-white/90 dark:bg-gray-800/90 px-3 py-1.5 rounded-full;
  @apply border border-gray-200 dark:border-gray-700;
}

.detail-pane {
  @apply w-80 border border-gray-200 dark:border-gray-700 rounded-lg p-3;
  @apply bg-gray-50/80 dark:bg-gray-800/50;
  overflow-y: auto;
}

.detail-title {
  @apply text-base font-semibold mb-2;
}

.detail-section {
  @apply flex flex-col gap-2;
}

.detail-name {
  @apply text-sm font-semibold text-gray-900 dark:text-gray-100;
}

.detail-id {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.detail-desc {
  @apply text-sm text-gray-700 dark:text-gray-200;
  line-height: 1.5;
}

.detail-empty,
.detail-empty-state {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.related-header {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-300 mt-2;
}

.related-list {
  @apply flex flex-col gap-1;
}

.relation-list {
  @apply flex flex-col gap-1;
}

.related-item {
  @apply w-full flex items-center justify-between;
  @apply px-2 py-1.5 text-left rounded-md border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
  @apply hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors;
}

.related-name {
  @apply text-xs text-gray-700 dark:text-gray-200 truncate;
}

.related-arrow {
  @apply text-xs text-gray-400;
}

.relation-item {
  @apply w-full flex items-center gap-2;
  @apply px-2 py-1.5 text-left rounded-md border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
  @apply hover:bg-amber-50 dark:hover:bg-gray-700 transition-colors;
}

.relation-main {
  @apply text-xs text-gray-700 dark:text-gray-100 flex-shrink-0;
}

.relation-target {
  @apply text-xs text-gray-500 dark:text-gray-300 truncate flex-1;
}

.relation-confidence {
  @apply text-[11px] text-emerald-600 dark:text-emerald-400;
}

/* 学情画像卡片 */
.learning-profile-card {
  @apply flex flex-col gap-1.5 p-2.5 rounded-lg border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
}

.profile-row {
  @apply flex items-center justify-between text-xs;
}

.profile-label {
  @apply text-gray-500 dark:text-gray-400;
}

.profile-value {
  @apply text-gray-700 dark:text-gray-200 font-medium;
}

.mastery-tag {
  @apply inline-block px-2 py-0.5 rounded-full text-xs font-medium;
}

/* 薄弱知识点警告 */
.weak-point-alert {
  @apply flex items-start gap-2 mt-2 p-2 rounded-lg;
  @apply bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800;
}

.weak-point-icon {
  @apply text-orange-500 text-base mt-0.5 flex-shrink-0;
}

.weak-point-text {
  @apply flex flex-col gap-0.5;
}

.weak-point-title {
  @apply text-xs font-semibold text-orange-700 dark:text-orange-400;
}

.weak-point-hint {
  @apply text-xs text-orange-600 dark:text-orange-300;
}

/* AI 学情评语卡片 */
.ai-summary-card {
  @apply p-2.5 rounded-lg border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
}

.ai-summary-placeholder {
  @apply text-xs text-gray-400 dark:text-gray-500 text-center py-2;
}

.ai-summary-content {
  @apply text-xs text-gray-600 dark:text-gray-300 leading-relaxed;
}

:global(.course-knowledge-graph-expanded-modal .ant-modal-content) {
  height: 85vh;
}

:global(.course-knowledge-graph-expanded-modal .ant-modal-body) {
  padding: 12px;
  height: calc(85vh - 55px);
  overflow: hidden;
}

@media (max-width: 1023px) {
  .expanded-body {
    @apply flex-col;
  }

  .detail-pane {
    @apply w-full;
    max-height: 32vh;
  }
}
</style>
