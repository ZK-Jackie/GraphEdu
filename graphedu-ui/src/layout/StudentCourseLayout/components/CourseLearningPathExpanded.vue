<script setup lang="ts">
/**
 * CourseLearningPathExpanded - 课程学习路径展开视图
 *
 * 功能：
 * - 大尺寸弹窗展示学习路径子图（节点按掌握度着色）
 * - 左图右详情布局，显示进度统计与节点掌握详情
 * - 支持节点点击查看掌握度、学习时长等学情信息
 * - 右侧面板显示进度统计、选中节点详情、关联节点列表
 */
import { Modal, Progress, Spin, message } from 'ant-design-vue'
import NvlGraph from '../../../components/nvl/NvlGraph.vue'
import NvlTooltip from '../../../components/nvl/NvlTooltip.vue'
import { useNvlStyles } from '../../../components/nvl/useNvlStyles'
import { getKnowledgeProfile, getWeakPoints } from '@/api/education/student_course.ts'
import type { NvlNode, NvlRel, TooltipInfo } from '@/components/nvl/types.ts'
import type { NvlNodeVO, NvlRelationshipVO, LearningPlanProgressVO } from '@/types/api/knowledge-graph.ts'
import { ExclamationCircleOutlined } from '@ant-design/icons-vue'
import type { StudentKnowledgeProfileVO, StudentWeakPointVO } from '@/types/api/education/stats.ts'

interface Props {
  courseId: number
  planTitle: string
  nodes: NvlNode[]
  rels: NvlRel[]
  progress: LearningPlanProgressVO | null
}

interface Emits {
  (e: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { styleNodes, styleRels } = useNvlStyles()

// 状态
const nvlRef = ref<InstanceType<typeof NvlGraph>>()
const selectedNodeId = ref<string>()
const tooltipInfo = ref<TooltipInfo | null>(null)

// 学情画像数据（用于右侧详情展示）
const knowledgeProfiles = ref<StudentKnowledgeProfileVO[]>([])
const weakPoints = ref<StudentWeakPointVO[]>([])

// 样式化后的节点和关系（响应式同步）
const styledNodes = computed(() => styleNodes([...props.nodes]))
const styledRels = computed(() => styleRels([...props.rels]))

// 进度统计
const progressPct = computed(() => props.progress?.progress_pct ?? 0)
const totalNodes = computed(() => props.progress?.total ?? props.nodes.length)
const masteredCount = computed(() => props.progress?.mastered ?? 0)
const learningCount = computed(() => {
  if (!props.progress?.details) return 0
  return props.progress.details.filter(
    (d) => !d.mastered && (d.mastery_level === 'medium' || d.mastery_level === 'high')
  ).length
})
const unlearnedCount = computed(() => totalNodes.value - masteredCount.value - learningCount.value)

// 选中节点
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return undefined
  return styledNodes.value.find((node) => node.id === selectedNodeId.value)
})

// 关联节点
const relatedNodes = computed(() => {
  if (!selectedNodeId.value) return []
  const neighborIds = new Set<string>()
  for (const rel of styledRels.value) {
    if (rel.from === selectedNodeId.value) neighborIds.add(rel.to)
    if (rel.to === selectedNodeId.value) neighborIds.add(rel.from)
  }
  return styledNodes.value.filter((node) => neighborIds.has(node.id))
})

// 选中节点的关系列表
const selectedNodeRelations = computed(() => {
  if (!selectedNodeId.value) return []
  return styledRels.value
    .filter((rel) => rel.from === selectedNodeId.value || rel.to === selectedNodeId.value)
    .map((rel) => {
      const isOutgoing = rel.from === selectedNodeId.value
      const peerId = isOutgoing ? rel.to : rel.from
      const peerNode = styledNodes.value.find((node) => node.id === peerId)
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

// 选中节点的学情画像
const selectedNodeProfile = computed(() => {
  if (!selectedNodeId.value) return undefined
  // selectedNodeId 是 AGE 内部 ID，需通过 selectedNode.properties.uuid 桥接到业务 UUID
  const selectedNvlNode = styledNodes.value.find((n) => n.id === selectedNodeId.value)
  const uuid = (selectedNvlNode?.properties as Record<string, unknown>)?.uuid ?? selectedNodeId.value
  return knowledgeProfiles.value.find((p) => p.nodeUuid != null && p.nodeUuid === String(uuid))
})

// 选中节点是否为薄弱知识点
const selectedNodeWeakPoint = computed(() => {
  if (!selectedNodeProfile.value?.nodeUuid) return undefined
  return weakPoints.value.find((w) => w.nodeUuid === selectedNodeProfile.value!.nodeUuid)
})

// 选中节点的路径进度详情
const selectedNodeProgress = computed(() => {
  if (!selectedNodeId.value || !props.progress?.details) return undefined
  const node = styledNodes.value.find((n) => n.id === selectedNodeId.value)
  if (!node) return undefined
  const uuid = node.properties?.uuid ?? node.id
  return props.progress.details.find((d) => d.node_uuid === uuid || d.node_uuid === node.id)
})

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

/** 节点状态文案 */
function statusLabel(status?: string): string {
  switch (status) {
    case 'mastered':
    case 'high':
      return '已掌握'
    case 'learning':
    case 'medium':
      return '学习中'
    case 'low':
      return '薄弱'
    default:
      return '未学习'
  }
}

// 事件处理
function handleNodeClick(node: NvlNode, event: MouseEvent) {
  event.stopPropagation()
  selectedNodeId.value = node.id
}

function handleCanvasClick() {
  selectedNodeId.value = undefined
  tooltipInfo.value = null
}

function handleNodeHover(info: TooltipInfo | null) {
  tooltipInfo.value = info
}

function handleClose() {
  emit('close')
}

function handleFitAll() {
  nvlRef.value?.fitAll()
}

function handleResetZoom() {
  nvlRef.value?.resetZoom()
}

function focusRelatedNode(node: NvlNode) {
  selectedNodeId.value = node.id
  nextTick(() => {
    nvlRef.value?.fitAll()
  })
}

function focusRelatedNodeById(nodeId: string) {
  const node = styledNodes.value.find((item) => item.id === nodeId)
  if (node) focusRelatedNode(node)
}

// 初始化：并行加载学情画像和薄弱知识点
onMounted(async () => {
  await Promise.all([loadKnowledgeProfiles(), loadWeakPoints()])
  nextTick(() => {
    nvlRef.value?.fitAll()
  })
})
</script>

<template>
  <Modal
    :open="true"
    :footer="null"
    :closable="true"
    :width="'88vw'"
    wrap-class-name="course-learning-path-expanded-modal"
    @cancel="handleClose"
  >
    <template #title>
      <div class="modal-title">
        <span>学习路径 · {{ planTitle }}</span>
        <span class="stats-info">
          知识点: {{ totalNodes }} · 已掌握: {{ masteredCount }} · 进度: {{ Math.round(progressPct) }}%
        </span>
      </div>
    </template>

    <div class="expanded-content">
      <div class="expanded-body">
        <!-- 左侧图谱区 -->
        <div class="graph-pane">
          <div class="toolbar">
            <a-button size="small" @click="handleFitAll">适应视图</a-button>
            <a-button size="small" @click="handleResetZoom">重置缩放</a-button>
          </div>

          <div class="graph-container">
            <div v-if="styledNodes.length === 0" class="empty-graph">
              <p>该学习路径暂无知识点</p>
            </div>
            <NvlGraph
              v-else
              ref="nvlRef"
              :nodes="styledNodes"
              :rels="styledRels"
              mode="view"
              layout="forceDirected"
              :selected-node-ids="selectedNodeId ? [selectedNodeId] : []"
              :initial-zoom="0.8"
              :fit-on-layout="true"
              @node-click="handleNodeClick"
              @node-hover="handleNodeHover"
              @canvas-click="handleCanvasClick"
            />
            <NvlTooltip :info="tooltipInfo" />

            <div class="hint-info">点击节点查看掌握详情，右侧查看进度统计</div>
          </div>
        </div>

        <!-- 右侧详情区 -->
        <aside class="detail-pane">
          <!-- 进度统计 -->
          <div class="detail-title">进度统计</div>
          <div class="progress-card">
            <div class="progress-ring">
              <Progress
                type="circle"
                :percent="Math.round(progressPct)"
                :size="64"
                :stroke-width="8"
                :stroke-color="progressPct === 100 ? '#52c41a' : '#1890ff'"
              />
            </div>
            <div class="progress-stats">
              <div class="stat-row">
                <span class="stat-dot mastered" />
                <span class="stat-label">已掌握</span>
                <span class="stat-value">{{ masteredCount }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-dot learning" />
                <span class="stat-label">学习中</span>
                <span class="stat-value">{{ learningCount }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-dot unlearned" />
                <span class="stat-label">未学习</span>
                <span class="stat-value">{{ unlearnedCount }}</span>
              </div>
            </div>
          </div>

          <!-- 节点详情 -->
          <template v-if="selectedNode">
            <div class="related-header">节点详情</div>
            <div class="detail-section">
              <div class="detail-name">{{ selectedNode.caption || selectedNode.id }}</div>
              <p v-if="selectedNode.description" class="detail-desc">{{ selectedNode.description }}</p>

              <!-- 路径进度状态 -->
              <div class="profile-row">
                <span class="profile-label">掌握状态</span>
                <span class="mastery-tag" :class="MASTERY_LEVEL_CONFIG[selectedNode.status ?? 'unlearned']?.cls">
                  {{ statusLabel(selectedNode.status) }}
                </span>
              </div>
              <div v-if="selectedNodeProgress?.mastery_score != null" class="profile-row">
                <span class="profile-label">掌握评分</span>
                <span class="profile-value">{{ selectedNodeProgress.mastery_score }}/100</span>
              </div>
            </div>

            <!-- 学情画像 -->
            <div class="related-header">我的学习情况</div>
            <div v-if="selectedNodeProfile" class="learning-profile-card">
              <div class="profile-row">
                <span class="profile-label">掌握等级</span>
                <span
                  class="mastery-tag"
                  :class="
                    MASTERY_LEVEL_CONFIG[selectedNodeProfile.latestMasteryLevel]?.cls ?? MASTERY_LEVEL_CONFIG.low?.cls
                  "
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

            <!-- 关联节点 -->
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
                <span class="related-status">{{ statusLabel(node.status) }}</span>
                <span class="related-arrow">&gt;</span>
              </button>
            </div>
            <div v-else class="detail-empty">当前节点暂无关联节点</div>

            <!-- 关系明细 -->
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
          </template>
          <div v-else class="detail-empty-state">点击左侧节点查看详情</div>
        </aside>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
@reference '#main.css';

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

.graph-container {
  @apply flex-1 relative border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden;
  min-height: 0;
}

:deep(.graph-container .nvl-graph-container) {
  min-height: 0;
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

/* 进度统计卡片 */
.progress-card {
  @apply flex items-center gap-4 p-3 rounded-lg border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
}

.progress-ring {
  @apply flex-shrink-0;
}

.progress-stats {
  @apply flex flex-col gap-1.5 flex-1;
}

.stat-row {
  @apply flex items-center gap-2 text-xs;
}

.stat-dot {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}

.stat-dot.mastered {
  @apply bg-green-500;
}

.stat-dot.learning {
  @apply bg-blue-500;
}

.stat-dot.unlearned {
  @apply bg-gray-400;
}

.stat-label {
  @apply text-gray-500 dark:text-gray-400 flex-1;
}

.stat-value {
  @apply text-gray-700 dark:text-gray-200 font-medium;
}

/* 节点详情 */
.detail-section {
  @apply flex flex-col gap-1.5 p-2.5 rounded-lg border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
}

.detail-name {
  @apply text-sm font-semibold text-gray-900 dark:text-gray-100;
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

.related-list,
.relation-list {
  @apply flex flex-col gap-1;
}

.related-item {
  @apply w-full flex items-center gap-2;
  @apply px-2 py-1.5 text-left rounded-md border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
  @apply hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors;
}

.related-name {
  @apply text-xs text-gray-700 dark:text-gray-200 truncate flex-1;
}

.related-status {
  @apply text-[11px] text-gray-400 dark:text-gray-500 flex-shrink-0;
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

:global(.course-learning-path-expanded-modal .ant-modal-content) {
  height: 85vh;
}

:global(.course-learning-path-expanded-modal .ant-modal-body) {
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

/* AI 学情评语卡片 */
.ai-summary-card {
  @apply p-2.5 rounded-lg border;
  @apply border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
}

.ai-summary-content {
  @apply text-xs text-gray-600 dark:text-gray-300 leading-relaxed;
}

.ai-summary-placeholder {
  @apply text-xs text-gray-400 dark:text-gray-500 text-center py-2;
}
</style>
