<script setup lang="ts">
/**
 * CourseLearningPath - 课程学习路径导航组件（长条形）
 *
 * 功能：
 * - 显示当前课程学生的学习路径列表（下拉选择器）
 * - 中央区域渲染微型 NvlGraph（路径子图，节点按掌握度着色）
 * - 右侧显示进度环形指示器
 * - 支持悬停提示节点信息
 * - 支持通过 "⋯" 按钮打开展开视图
 */
import { Empty as AEmpty, Progress, Spin, Tooltip } from 'ant-design-vue'
import { getMyLearningPlans, getLearningPlanDetail } from '@/api/education/learning-path'
import NvlGraph from '../../../components/nvl/NvlGraph.vue'
import NvlTooltip from '../../../components/nvl/NvlTooltip.vue'
import { useNvlStyles } from '../../../components/nvl/useNvlStyles'
import type { NvlNode, NvlRel, TooltipInfo } from '@/components/nvl/types'
import type {
  LearningPlanListVO,
  LearningPlanDetailVO,
  NvlNodeVO,
  NvlRelationshipVO,
} from '@/types/api/knowledge-graph'
import { useBreakpoints } from '@/composables/useBreakpoints'

interface Props {
  courseId: number
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '56px',
})

// 状态
const plans = ref<LearningPlanListVO[]>([])
const selectedPlanId = ref<string>()
const planDetail = ref<LearningPlanDetailVO | null>(null)
const nodes = ref<NvlNode[]>([])
const rels = ref<NvlRel[]>([])
const selectedNodeId = ref<string>()
const loading = ref(false)
const errorMessage = ref<string>()
const tooltipInfo = ref<TooltipInfo | null>(null)

// NvlGraph 组件引用
const nvlRef = ref<InstanceType<typeof NvlGraph> | null>(null)

const { isMobile } = useBreakpoints()
const { styleNodes, styleRels } = useNvlStyles()

const hasPlans = computed(() => plans.value.length > 0)
const hasNodes = computed(() => nodes.value.length > 0)

// 当前进度百分比
const progressPct = computed(() => planDetail.value?.progress?.progress_pct ?? 0)

// 进度详情 map：node_uuid → mastered
const masteryMap = computed(() => {
  const map = new Map<string, { mastered: boolean; mastery_level: string }>()
  if (planDetail.value?.progress?.details) {
    for (const d of planDetail.value.progress.details) {
      map.set(d.node_uuid, { mastered: d.mastered, mastery_level: d.mastery_level })
    }
  }
  return map
})

// VO → NvlNode 转换（叠加掌握度着色）
function convertVoToNvlNode(vo: NvlNodeVO): NvlNode {
  // 用 uuid 匹配 masteryMap，回退到 vo.id
  const mastery = masteryMap.value.get(vo.properties.uuid ?? vo.id)
  let status: NvlNode['status'] = 'unlearned'
  if (mastery?.mastered) {
    status = 'mastered'
  } else if (mastery?.mastery_level === 'medium' || mastery?.mastery_level === 'high') {
    status = 'learning'
  }

  return {
    id: vo.id,
    labels: vo.labels,
    caption: vo.properties.title,
    description: vo.properties.description,
    properties: vo.properties,
    nodeType: 'knowledge',
    status,
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
    relType: vo.type as NvlRel['relType'],
    properties: vo.properties,
    confidence: vo.properties.confidence ?? undefined,
  }
}

// 加载学习路径列表
async function loadPlans() {
  loading.value = true
  errorMessage.value = undefined
  try {
    const resp = await getMyLearningPlans(props.courseId)
    if (resp.data) {
      plans.value = resp.data
      if (plans.value.length > 0 && !selectedPlanId.value) {
        const first = plans.value[0]
        if (first) {
          selectedPlanId.value = first.plan_id
          await loadPlanDetail(first.plan_id)
        }
      }
    } else {
      plans.value = []
    }
  } catch (error) {
    console.error('加载学习路径列表失败:', error)
    errorMessage.value = '加载学习路径失败'
  } finally {
    loading.value = false
  }
}

// 加载路径详情
async function loadPlanDetail(planId: string) {
  loading.value = true
  tooltipInfo.value = null
  errorMessage.value = undefined
  // 重置
  nodes.value = []
  rels.value = []
  selectedNodeId.value = undefined
  planDetail.value = null

  try {
    const resp = await getLearningPlanDetail(planId)
    if (resp.data) {
      planDetail.value = resp.data

      // 先设置 masteryMap 依赖的 planDetail（在下一个 tick 中转换节点）
      if (resp.data.graph) {
        nodes.value = styleNodes(resp.data.graph.nodes.map(convertVoToNvlNode))
        rels.value = styleRels(resp.data.graph.relationships.map(convertVoToNvlRel))
      }
    }
  } catch (error) {
    console.error('加载路径详情失败:', error)
    errorMessage.value = '加载路径详情失败'
  } finally {
    loading.value = false
  }
}

// 切换路径
async function handlePlanChange(planId: string | number | undefined) {
  const id = String(planId)
  if (!id) return
  selectedPlanId.value = id
  await loadPlanDetail(id)
}

// 点击节点
function handleNodeClick(node: NvlNode) {
  selectedNodeId.value = node.id
}

function handleNodeHover(info: TooltipInfo | null) {
  tooltipInfo.value = info
}

function handleCanvasClick() {
  tooltipInfo.value = null
  selectedNodeId.value = undefined
}

// 打开学习路径页面（导航到独立路由）
const router = useRouter()

function openExpanded() {
  if (!hasNodes.value) return
  router.push(`/course/learn/${props.courseId}/learning-path`)
}

// 初始化
onMounted(() => {
  loadPlans()
})
</script>

<template>
  <div class="course-learning-path" :style="{ height }">
    <!-- 加载状态 -->
    <div v-if="loading && plans.length === 0" class="loading-container">
      <Spin size="small" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && plans.length === 0" class="empty-container">
      <AEmpty :image-style="{ height: '20px' }" description="暂无学习路径" />
    </div>

    <!-- 内容区域 -->
    <div v-else class="content-container">
      <!-- 左侧：路径选择器 -->
      <a-select
        v-if="plans.length > 1"
        v-model:value="selectedPlanId"
        class="plan-selector"
        size="small"
        :loading="loading"
        @change="(val: any) => handlePlanChange(val)"
      >
        <a-select-option v-for="plan in plans" :key="plan.plan_id" :value="plan.plan_id">
          {{ plan.title }}
        </a-select-option>
      </a-select>

      <!-- 中央：微型图谱 -->
      <div v-if="hasNodes" class="nodes-container">
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
          <Tooltip title="查看完整学习路径">
            <span class="expand-icon">⋯</span>
          </Tooltip>
        </div>
      </div>

      <!-- 节点为空 -->
      <div v-else-if="!loading" class="empty-nodes">
        <span class="empty-text">路径暂无知识点</span>
      </div>

      <!-- 右侧：进度指示器 -->
      <div v-if="planDetail?.progress" class="progress-indicator">
        <Progress
          type="circle"
          :percent="progressPct"
          :size="28"
          :stroke-width="8"
          :stroke-color="progressPct === 100 ? '#52c41a' : '#1890ff'"
        />
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
@reference '#main.css';

.course-learning-path {
  @apply w-full flex items-center;
  background: transparent;
}

.loading-container,
.empty-container {
  @apply flex items-center justify-center w-full h-full;

  :deep(.ant-empty-description) {
    color: var(--ge-text-tertiary) !important;
  }
}

.content-container {
  @apply flex items-center gap-2 w-full;
}

.plan-selector {
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
  @apply text-xs text-gray-500;
}

.progress-indicator {
  @apply flex-shrink-0 flex items-center;
  margin-left: 4px;
}

.empty-nodes {
  @apply flex items-center justify-center flex-1;
}

.empty-text {
  @apply text-sm;
  color: var(--ge-text-tertiary);
}

.error-message {
  @apply flex items-center justify-center flex-1;
}

.error-text {
  @apply text-red-500 text-sm;
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
</style>
