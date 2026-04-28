<script setup lang="ts">
/**
 * CourseLearningPathPage - 课程学习路径独立页面
 *
 * 在 Golden Layout 标签页中展示学习路径子图（节点按掌握度着色）。
 * 左图右详情布局，支持节点点击、hover 提示、进度统计。
 */
import { message, Progress } from 'ant-design-vue'
import NvlGraph from '@/components/nvl/NvlGraph.vue'
import NvlTooltip from '@/components/nvl/NvlTooltip.vue'
import { getMyLearningPlans, getLearningPlanDetail } from '@/api/education/learning-path'
import { getKnowledgeProfile, getWeakPoints } from '@/api/education/student_course.ts'
import type { NvlNode, NvlRel, TooltipInfo } from '@/components/nvl/types.ts'
import type {
  NvlNodeVO,
  NvlRelationshipVO,
  LearningPlanListVO,
  LearningPlanProgressVO,
} from '@/types/api/knowledge-graph.ts'
import { ExclamationCircleOutlined } from '@ant-design/icons-vue'
import type { StudentKnowledgeProfileVO, StudentWeakPointVO } from '@/types/api/education/stats.ts'

const route = useRoute()
const courseId = computed(() => Number(route.params.courseId || route.params.id))

// 状态
const nvlRef = ref<InstanceType<typeof NvlGraph>>()
const loading = ref(false)
const nodes = ref<NvlNode[]>([])
const relationships = ref<NvlRel[]>([])
const totalNodes = ref(0)
const totalRelationships = ref(0)
const selectedNodeId = ref<string>()
const tooltipInfo = ref<TooltipInfo | null>(null)
const progress = ref<LearningPlanProgressVO | null>(null)
const plans = ref<LearningPlanListVO[]>([])
const selectedPlanId = ref<string>()

// 学情画像数据
const knowledgeProfiles = ref<StudentKnowledgeProfileVO[]>([])
const weakPoints = ref<StudentWeakPointVO[]>([])

async function loadKnowledgeProfiles() {
  try {
    const resp = await getKnowledgeProfile(courseId.value)
    if (resp.code === 200 && resp.data) knowledgeProfiles.value = resp.data
  } catch (e) {
    console.error('加载学情画像失败:', e)
  }
}

async function loadWeakPoints() {
  try {
    const resp = await getWeakPoints(courseId.value)
    if (resp.code === 200 && resp.data) weakPoints.value = resp.data
  } catch (e) {
    console.error('加载薄弱知识点失败:', e)
  }
}

function formatStudySeconds(s: number): string {
  if (s < 60) return `${s}秒`
  if (s < 3600) return `${Math.floor(s / 60)}分钟`
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
}

const MASTERY_LEVEL_CONFIG: Record<string, { label: string; cls: string }> = {
  high: {
    label: '已掌握',
    cls: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  },
  medium: {
    label: '学习中',
    cls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  low: {
    label: '薄弱',
    cls: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  },
}

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

// 进度统计
const progressPct = computed(() => progress.value?.progress_pct ?? 0)
const masteredCount = computed(() => progress.value?.mastered ?? 0)
const learningCount = computed(() => {
  if (!progress.value?.details) return 0
  return progress.value.details.filter(
    (d) => !d.mastered && (d.mastery_level === 'medium' || d.mastery_level === 'high')
  ).length
})
const unlearnedCount = computed(() => totalNodes.value - masteredCount.value - learningCount.value)

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return undefined
  return nodes.value.find((n) => n.id === selectedNodeId.value)
})

const relatedNodes = computed(() => {
  if (!selectedNodeId.value) return []
  const ids = new Set<string>()
  for (const rel of relationships.value) {
    if (rel.from === selectedNodeId.value) ids.add(rel.to)
    if (rel.to === selectedNodeId.value) ids.add(rel.from)
  }
  return nodes.value.filter((n) => ids.has(n.id))
})

const selectedNodeRelations = computed(() => {
  if (!selectedNodeId.value) return []
  return relationships.value
    .filter((r) => r.from === selectedNodeId.value || r.to === selectedNodeId.value)
    .map((r) => {
      const out = r.from === selectedNodeId.value
      const peerId = out ? r.to : r.from
      const peer = nodes.value.find((n) => n.id === peerId)
      return {
        id: r.id,
        type: r.relType || r.type || r.caption || 'RELATED_TO',
        confidence: r.confidence,
        dir: out ? '出向' : '入向',
        peerId,
        peerCaption: peer?.caption || peerId,
      }
    })
})

const selectedNodeProfile = computed(() => {
  if (!selectedNodeId.value || !selectedNode.value) return undefined
  const uuid = (selectedNode.value.properties as Record<string, unknown>)?.uuid ?? selectedNodeId.value
  return knowledgeProfiles.value.find((p) => p.nodeUuid != null && p.nodeUuid === String(uuid))
})

const selectedNodeWeakPoint = computed(() => {
  if (!selectedNodeProfile.value?.nodeUuid) return undefined
  return weakPoints.value.find((w) => w.nodeUuid === selectedNodeProfile.value!.nodeUuid)
})

const selectedNodeProgress = computed(() => {
  if (!selectedNodeId.value || !progress.value?.details) return undefined
  const node = nodes.value.find((n) => n.id === selectedNodeId.value)
  if (!node) return undefined
  const uuid = (node.properties as Record<string, unknown>)?.uuid ?? node.id
  return progress.value.details.find((d) => d.node_uuid === uuid || d.node_uuid === node.id)
})

// VO → NvlNode 转换（使用 captions 数组格式，与教师端对齐）
function convertVoToNvlNode(vo: NvlNodeVO): NvlNode {
  return {
    id: vo.id,
    labels: vo.labels,
    captions: [{ value: vo.properties.title ?? '' }],
    description: vo.properties.description,
    nodeType: 'knowledge',
    properties: vo.properties,
  }
}

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

function focusRelatedNode(node: NvlNode) {
  selectedNodeId.value = node.id
  nextTick(() => nvlRef.value?.fitAll())
}

function focusRelatedNodeById(id: string) {
  selectedNodeId.value = id
  nextTick(() => nvlRef.value?.fitAll())
}

async function loadPlans() {
  loading.value = true
  try {
    const listResp = await getMyLearningPlans(courseId.value)
    if (listResp.data?.length) {
      plans.value = listResp.data
      const first = listResp.data[0]
      selectedPlanId.value = first!.plan_id
      await loadPlanDetail(first!.plan_id)
    } else {
      plans.value = []
      message.info('该课程暂无学习路径')
    }
  } catch (e) {
    console.error('加载学习路径列表失败:', e)
    message.error('加载学习路径失败')
  } finally {
    loading.value = false
  }
}

async function loadPlanDetail(planId: string) {
  loading.value = true
  selectedNodeId.value = undefined
  tooltipInfo.value = null
  nodes.value = []
  relationships.value = []
  totalNodes.value = 0
  totalRelationships.value = 0
  progress.value = null

  try {
    const [detailResp] = await Promise.all([getLearningPlanDetail(planId), loadKnowledgeProfiles(), loadWeakPoints()])

    if (detailResp.data) {
      progress.value = detailResp.data.progress ?? null
      const graph = detailResp.data.graph
      if (graph) {
        const allNodeVos = graph.nodes ?? []
        const allRelVos = graph.relationships ?? []
        if (allNodeVos.length === 0) {
          message.info('该学习路径暂无知识点')
          return
        }
        nodes.value = allNodeVos.map(convertVoToNvlNode)
        relationships.value = allRelVos.map(convertVoToNvlRel)
        totalNodes.value = allNodeVos.length
        totalRelationships.value = allRelVos.length

        const firstId = nodes.value[0]?.id
        if (firstId) selectedNodeId.value = firstId
      }
    }
  } catch (e) {
    console.error('加载路径详情失败:', e)
    message.error('加载路径详情失败')
  } finally {
    loading.value = false
  }
}

async function handlePlanChange(planId: string | number | undefined) {
  const id = String(planId)
  if (!id) return
  selectedPlanId.value = id
  await loadPlanDetail(id)
}

onMounted(loadPlans)
</script>

<template>
  <div class="lp-page">
    <div class="lp-body">
      <!-- 左侧图谱区 -->
      <div class="graph-pane">
        <div class="toolbar">
          <a-select
            v-if="plans.length >= 1"
            v-model:value="selectedPlanId"
            size="small"
            class="plan-select"
            @change="(val: any) => handlePlanChange(val)"
          >
            <a-select-option v-for="p in plans" :key="p.plan_id" :value="p.plan_id">
              {{ p.title }}
            </a-select-option>
          </a-select>
          <span v-else class="toolbar-title">学习路径</span>
          <span class="stats-info">
            知识点: {{ totalNodes || nodes.length }} · 已掌握: {{ masteredCount }} · 进度:
            {{ Math.round(progressPct) }}%
          </span>
          <div class="toolbar-actions">
            <a-button size="small" @click="nvlRef?.fitAll()">适应视图</a-button>
            <a-button size="small" @click="nvlRef?.resetZoom()">重置缩放</a-button>
          </div>
        </div>
        <div class="graph-container">
          <a-empty v-if="nodes.length === 0 && !loading" description="暂无知识点" class="empty-graph" />
          <NvlGraph
            v-else
            ref="nvlRef"
            :nodes="nodes"
            :rels="relationships"
            mode="edit"
            :loading="loading"
            :selected-node-ids="selectedNodeId ? [selectedNodeId] : []"
            :initial-zoom="0.8"
            class="nvl-graph"
            @node-click="handleNodeClick"
            @node-hover="handleNodeHover"
            @canvas-click="handleCanvasClick"
          />
          <NvlTooltip :info="tooltipInfo" />
          <div class="hint-info">点击节点查看掌握详情</div>
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
            <div class="detail-name">
              {{ selectedNode.caption || selectedNode.id }}
            </div>
            <p v-if="selectedNode.description" class="detail-desc">
              {{ selectedNode.description }}
            </p>

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

            <div v-if="selectedNodeWeakPoint" class="weak-point-alert">
              <ExclamationCircleOutlined class="weak-point-icon" />
              <div class="weak-point-text">
                <div class="weak-point-title">薄弱知识点</div>
                <div class="weak-point-hint">建议重点复习基础概念并多加练习。</div>
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
          <div v-if="relatedNodes.length" class="related-list">
            <button
              v-for="n in relatedNodes"
              :key="n.id"
              class="related-item"
              type="button"
              @click="focusRelatedNode(n)"
            >
              <span class="related-name">{{ n.caption || n.id }}</span>
              <span class="related-status">{{ statusLabel(n.status) }}</span>
              <span class="related-arrow">&gt;</span>
            </button>
          </div>
          <div v-else class="detail-empty">暂无关联节点</div>

          <!-- 关系明细 -->
          <div class="related-header">关系明细 ({{ selectedNodeRelations.length }})</div>
          <div v-if="selectedNodeRelations.length" class="relation-list">
            <button
              v-for="r in selectedNodeRelations"
              :key="r.id"
              class="relation-item"
              type="button"
              @click="focusRelatedNodeById(r.peerId)"
            >
              <span class="relation-main">{{ r.dir }} · {{ r.type }}</span>
              <span class="relation-target">{{ r.peerCaption }}</span>
              <span v-if="r.confidence != null" class="relation-confidence">{{ Math.round(r.confidence * 100) }}%</span>
            </button>
          </div>
          <div v-else class="detail-empty">暂无关系</div>
        </template>
        <div v-else class="detail-empty-state">点击左侧节点查看详情</div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.lp-page {
  @apply h-full w-full;
}

.lp-body {
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

.toolbar-title {
  @apply text-sm font-semibold text-[var(--ge-text-primary)];
}

.plan-select {
  width: 200px;
  flex-shrink: 0;
}

.stats-info {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.toolbar-actions {
  @apply ml-auto flex gap-2;
}

.graph-container {
  @apply flex-1 relative border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden;
  min-height: 0;
}

.nvl-graph {
  @apply w-full h-full;
}

.empty-graph {
  @apply absolute inset-0 flex flex-col items-center justify-center;
}

.hint-info {
  @apply absolute left-1/2 -translate-x-1/2 bottom-3 text-xs text-gray-600 dark:text-gray-300 bg-white/90 dark:bg-gray-800/90 px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-700;
}

.detail-pane {
  @apply w-80 border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50/80 dark:bg-gray-800/50;
  overflow-y: auto;
  flex-shrink: 0;
}

.detail-title {
  @apply text-base font-semibold mb-2 text-[var(--ge-text-primary)];
}

/* 进度统计卡片 */
.progress-card {
  @apply flex items-center gap-4 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800;
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
  @apply flex flex-col gap-1.5 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800;
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
  @apply text-sm text-[var(--ge-text-tertiary)];
}

.related-header {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-300 mt-2;
}

.related-list,
.relation-list {
  @apply flex flex-col gap-1;
}

.related-item {
  @apply w-full flex items-center gap-2 px-2 py-1.5 text-left rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors;
}

.related-name {
  @apply text-xs text-gray-700 dark:text-gray-200 truncate flex-1;
}

.related-status {
  @apply text-[11px] text-gray-400 dark:text-gray-500 flex-shrink-0;
}

.related-arrow {
  @apply text-xs text-[var(--ge-text-tertiary)];
}

.relation-item {
  @apply w-full flex items-center gap-2 px-2 py-1.5 text-left rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-amber-50 dark:hover:bg-gray-700 transition-colors;
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
  @apply flex flex-col gap-1.5 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800;
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
  @apply flex items-start gap-2 mt-2 p-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800;
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
  @apply p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800;
}

.ai-summary-content {
  @apply text-xs text-gray-600 dark:text-gray-300 leading-relaxed;
}

.ai-summary-placeholder {
  @apply text-xs text-gray-400 dark:text-gray-500 text-center py-2;
}

@media (max-width: 1023px) {
  .lp-body {
    @apply flex-col;
  }

  .detail-pane {
    @apply w-full;
    max-height: 32vh;
  }
}
</style>
