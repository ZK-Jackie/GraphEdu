<script setup lang="ts">
/**
 * CourseKnowledgeGraphPage - 课程知识图谱浏览页（学生视角）
 *
 * 展示当前课程启用的知识图谱，叠加学情画像着色。
 * 左侧图谱区（可拖拽节点、缩放平移）+ 右侧节点学习详情面板。
 */
import { CompressOutlined, ExclamationCircleOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import NvlGraph from '@/components/nvl/NvlGraph.vue'
import NvlTooltip from '@/components/nvl/NvlTooltip.vue'
import { getGraphNvlData, getVisibleKnowledgeGraphList } from '@/api/education/knowledge-graph'
import { getKnowledgeProfile, getWeakPoints } from '@/api/education/student_course'
import type { NvlNode, NvlRel, TooltipInfo } from '@/components/nvl/types'
import type { StudentKnowledgeProfileVO, StudentWeakPointVO } from '@/types/api/education/stats'

const route = useRoute()
const courseId = computed(() => Number(route.params.courseId || route.params.id))

// ─── NVL 图谱数据 ──────────────────────────────────────────────────────────────

const nvlRef = ref<InstanceType<typeof NvlGraph> | null>(null)
const loading = ref(false)
const nvlNodes = ref<NvlNode[]>([])
const nvlRels = ref<NvlRel[]>([])
const totalNodes = ref(0)
const totalRels = ref(0)

// ─── 选中状态 ───────────────────────────────────────────────────────────────────

const selectedNode = ref<NvlNode | null>(null)
const tooltipInfo = ref<TooltipInfo | null>(null)

// ─── 学情画像数据 ───────────────────────────────────────────────────────────────

const knowledgeProfiles = ref<StudentKnowledgeProfileVO[]>([])
const weakPoints = ref<StudentWeakPointVO[]>([])

// ─── 学情着色 ───────────────────────────────────────────────────────────────────

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

function applyMasteryStatus(nodeList: NvlNode[]) {
  const profileMap = new Map<string, StudentKnowledgeProfileVO>()
  for (const p of knowledgeProfiles.value) {
    if (p.nodeUuid != null) profileMap.set(String(p.nodeUuid), p)
  }
  for (const node of nodeList) {
    const key = (node.properties as Record<string, unknown>)?.uuid ?? node.id
    const profile = profileMap.get(String(key))
    node.status = profile ? masteryLevelToStatus(profile.latestMasteryLevel) : 'unlearned'
  }
}

// ─── 关联计算 ───────────────────────────────────────────────────────────────────

const relatedNodes = computed(() => {
  if (!selectedNode.value) return []
  const ids = new Set<string>()
  for (const rel of nvlRels.value) {
    if (rel.from === selectedNode.value.id) ids.add(rel.to)
    if (rel.to === selectedNode.value.id) ids.add(rel.from)
  }
  return nvlNodes.value.filter((n) => ids.has(n.id))
})

const selectedNodeRelations = computed(() => {
  if (!selectedNode.value) return []
  return nvlRels.value
    .filter((r) => r.from === selectedNode.value!.id || r.to === selectedNode.value!.id)
    .map((r) => {
      const out = r.from === selectedNode.value!.id
      const peerId = out ? r.to : r.from
      const peer = nvlNodes.value.find((n) => n.id === peerId)
      return {
        id: r.id,
        type: r.relType || r.type || 'RELATED_TO',
        confidence: r.confidence,
        dir: out ? '出向' : '入向',
        peerId,
        peerCaption: (peer?.captions?.[0]?.value as string) ?? peerId,
      }
    })
})

const selectedNodeProfile = computed(() => {
  if (!selectedNode.value) return undefined
  const uuid = (selectedNode.value.properties as Record<string, unknown>)?.uuid ?? selectedNode.value.id
  return knowledgeProfiles.value.find((p) => p.nodeUuid != null && p.nodeUuid === String(uuid))
})

const selectedNodeWeakPoint = computed(() => {
  if (!selectedNodeProfile.value?.nodeUuid) return undefined
  return weakPoints.value.find((w) => w.nodeUuid === selectedNodeProfile.value!.nodeUuid)
})

// ─── 辅助方法 ───────────────────────────────────────────────────────────────────

function formatStudySeconds(s: number): string {
  if (s < 60) return `${s}秒`
  if (s < 3600) return `${Math.floor(s / 60)}分钟`
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
}

function getNodeCaption(node: NvlNode): string {
  return (node.captions?.[0]?.value as string) ?? node.id
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

const relationTypeLabelMap: Record<string, string> = {
  RELATED_TO: '相关',
  PRIOR_TO: '前置依赖',
  SUBTOPIC_OF: '子主题',
  PREREQUISITE: '前置依赖',
  CONTAINS: '子主题',
  BELONGS_TO: '归属',
}

function statusLabel(status?: string): string {
  switch (status) {
    case 'high':
      return '已掌握'
    case 'medium':
      return '学习中'
    case 'low':
      return '薄弱'
    default:
      return '未学习'
  }
}

function formatRelationTypeLabel(type?: string) {
  if (!type) return '未知'
  return `${relationTypeLabelMap[type] ?? type} (${type})`
}

// ─── 事件处理 ───────────────────────────────────────────────────────────────────

function handleNodeClick(node: NvlNode) {
  selectedNode.value = node
}

function handleCanvasClick() {
  selectedNode.value = null
  tooltipInfo.value = null
}

function handleNodeHover(info: TooltipInfo | null) {
  tooltipInfo.value = info
}

function focusRelatedNode(node: NvlNode) {
  selectedNode.value = node
  nextTick(() => nvlRef.value?.fitAll())
}

// ─── 初始化 ─────────────────────────────────────────────────────────────────────

async function loadGraphData() {
  loading.value = true
  try {
    // 获取当前课程启用的知识图谱
    const listResp = await getVisibleKnowledgeGraphList(courseId.value)
    const rows = listResp.data?.rows ?? []
    if (rows.length === 0) {
      message.info('该课程暂无可用的知识图谱')
      return
    }
    const graphId = rows[0]!.graphId

    // 一次性并行加载图谱数据 + 学情画像 + 薄弱点
    const [graphResp] = await Promise.all([
      getGraphNvlData(graphId),
      getKnowledgeProfile(courseId.value).then((r) => {
        if (r.code === 200 && r.data) knowledgeProfiles.value = r.data
      }),
      getWeakPoints(courseId.value).then((r) => {
        if (r.code === 200 && r.data) weakPoints.value = r.data
      }),
    ])

    const allNodeVos = graphResp.data?.nodes ?? []
    const allRelVos = graphResp.data?.relationships ?? []
    if (allNodeVos.length === 0) {
      message.info('该知识图谱暂无节点')
      return
    }

    // 转换节点
    nvlNodes.value = allNodeVos.map((n): NvlNode => ({
      id: n.id,
      labels: n.labels,
      captions: [{ value: n.properties.title ?? '' }],
      description: n.properties.description,
      nodeType: 'knowledge' as const,
      properties: n.properties,
    }))

    // 叠加学情着色
    applyMasteryStatus(nvlNodes.value)

    // 转换关系
    nvlRels.value = allRelVos.map((r) => ({
      id: r.id,
      from: r.from,
      to: r.to,
      captions: [{ value: r.type ?? '' }],
      relType: r.type as NvlRel['relType'],
      confidence: r.properties?.confidence as number | undefined,
      description: r.properties?.description as string | undefined,
    }))

    totalNodes.value = graphResp.data?.total_nodes ?? allNodeVos.length
    totalRels.value = graphResp.data?.total_relationships ?? allRelVos.length
  } catch (e) {
    console.error('加载知识图谱失败:', e)
    message.error('加载知识图谱失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadGraphData)
</script>

<template>
  <div class="kg-page">
    <div class="kg-body">
      <!-- 左侧图谱区 -->
      <div class="graph-pane">
        <div class="toolbar">
          <span class="toolbar-title">课程知识图谱</span>
          <span class="stats-info">知识点: {{ totalNodes }} · 关系: {{ totalRels }}</span>
          <div class="toolbar-actions">
            <a-button size="small" @click="nvlRef?.fitAll()">
              <template #icon><CompressOutlined /></template>
              适应视图
            </a-button>
            <a-button size="small" :loading="loading" @click="loadGraphData">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
        </div>
        <div class="graph-container">
          <a-empty v-if="nvlNodes.length === 0 && !loading" description="暂无知识图谱数据" class="empty-graph" />
          <NvlGraph
            v-else
            ref="nvlRef"
            :nodes="nvlNodes"
            :rels="nvlRels"
            mode="edit"
            :loading="loading"
            :selected-node-ids="selectedNode ? [selectedNode.id] : []"
            class="nvl-graph"
            @node-click="handleNodeClick"
            @node-hover="handleNodeHover"
            @canvas-click="handleCanvasClick"
          />
          <NvlTooltip :info="tooltipInfo" />
          <div class="hint-info">点击节点查看掌握详情</div>
        </div>
      </div>

      <!-- 右侧详情面板 -->
      <aside class="detail-pane">
        <template v-if="selectedNode">
          <!-- 节点基本信息 -->
          <div class="detail-title">节点详情</div>
          <div class="detail-section">
            <div class="detail-name">
              {{ getNodeCaption(selectedNode) }}
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
          </div>

          <!-- 学习情况 -->
          <div class="section-header">我的学习情况</div>
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
            <div v-if="selectedNodeWeakPoint" class="weak-point-alert">
              <ExclamationCircleOutlined class="weak-point-icon" />
              <div class="weak-point-text">
                <div class="weak-point-title">薄弱知识点</div>
                <div class="weak-point-hint">建议重点复习基础概念并多加练习。</div>
              </div>
            </div>
          </div>
          <div v-else class="detail-empty">尚未学习此知识点</div>

          <!-- 关联节点 -->
          <div class="section-header">关联节点 ({{ relatedNodes.length }})</div>
          <div v-if="relatedNodes.length" class="related-list">
            <button
              v-for="n in relatedNodes"
              :key="n.id"
              class="related-item"
              type="button"
              @click="focusRelatedNode(n)"
            >
              <span class="related-name">{{ getNodeCaption(n) }}</span>
              <span class="related-status">{{ statusLabel(n.status) }}</span>
              <span class="related-arrow">&gt;</span>
            </button>
          </div>
          <div v-else class="detail-empty">暂无关联节点</div>

          <!-- 关系明细 -->
          <div class="section-header">关系明细 ({{ selectedNodeRelations.length }})</div>
          <div v-if="selectedNodeRelations.length" class="relation-list">
            <button
              v-for="r in selectedNodeRelations"
              :key="r.id"
              class="relation-item"
              type="button"
              @click="focusRelatedNode(nvlNodes.find((n) => n.id === r.peerId)!)"
            >
              <span class="relation-main">{{ r.dir }} · {{ formatRelationTypeLabel(r.type) }}</span>
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

.kg-page {
  @apply h-full w-full;
}

.kg-body {
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

/* 右侧详情面板 */
.detail-pane {
  @apply w-80 border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50/80 dark:bg-gray-800/50;
  overflow-y: auto;
  flex-shrink: 0;
}

.detail-title {
  @apply text-base font-semibold mb-2 text-[var(--ge-text-primary)];
}

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

.section-header {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-300 mt-2;
}

/* 学习情况卡片 */
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

/* 关联节点列表 */
.related-list {
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

/* 关系明细列表 */
.relation-list {
  @apply flex flex-col gap-1;
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

@media (max-width: 1023px) {
  .kg-body {
    @apply flex-col;
  }

  .detail-pane {
    @apply w-full;
    max-height: 32vh;
  }
}
</style>
