<script setup lang="ts">
/**
 * KnowledgePointManage - 知识图谱管理页（教师视角）
 *
 * 功能：
 * - 顶部：课程所属图谱选择 + 新建图谱
 * - 左侧 (70%): NVL 力导向图，可交互（点击选中节点 / 关系）
 * - 右侧 (30%): 上下文操作面板
 *     - 默认态：节点数/关系数统计
 *     - 节点选中态：节点详情 + 编辑/删除
 *     - 添加节点模式：内嵌表单提交
 *     - 添加关系模式：内嵌表单提交
 */
import {
  CloseOutlined,
  CompressOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  ShareAltOutlined,
  RobotOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { useRoute } from 'vue-router'
import NvlGraph from '@/components/nvl/NvlGraph.vue'
import type { NvlNode, NvlRel } from '@/components/nvl/types'
import type {
  KnowledgeGraphDetailVO,
  KnowledgeGraphListVO,
  KnowledgeGraphRelationType,
} from '@/types/api/knowledge-graph'
import {
  addKnowledgeGraph,
  changeKnowledgeGraphStatus,
  createGraphNode,
  createGraphRelationship,
  deleteGraphNode,
  deleteGraphRelationship,
  getGraphNvlData,
  getGraphRelationship,
  updateGraphRelationship,
  getKnowledgeGraphList,
  getKnowledgeGraphDetail,
  updateGraphNode,
  submitAutoGenerateKnowledgeGraph,
  confirmKnowledgeGraph,
} from '@/api/education/knowledge-graph'
import { parseTime } from '@/utils/common.ts'

// ─── 路由 ─────────────────────────────────────────────────────────────────────

const route = useRoute()
const courseId = computed(() => Number(route.params.courseId))

// ─── 图谱列表 ─────────────────────────────────────────────────────────────────

const graphList = ref<KnowledgeGraphListVO[]>([])
const selectedGraphId = ref<number | undefined>(undefined)

async function loadGraphList() {
  const resp = await getKnowledgeGraphList({
    courseId: courseId.value,
    size: 100,
  })
  if (resp.code === 200) {
    graphList.value = resp.data?.rows ?? []
    // 默认选第一个
    if (!selectedGraphId.value && graphList.value.length > 0) {
      const [firstGraph] = graphList.value
      if (firstGraph) {
        selectedGraphId.value = firstGraph.graphId
      }
    }
  }
}

// ─── NVL 图谱数据 ──────────────────────────────────────────────────────────────

const nvlNodes = ref<NvlNode[]>([])
const nvlRels = ref<NvlRel[]>([])
const graphLoading = ref(false)
const totalNodes = ref(0)
const totalRels = ref(0)
const relDetailLoading = ref(false)

const relationTypeLabelMap: Record<string, string> = {
  RELATED_TO: '相关',
  PRIOR_TO: '前置依赖',
  SUBTOPIC_OF: '子主题',
  PREREQUISITE: '前置依赖',
  CONTAINS: '子主题',
  BELONGS_TO: '归属',
}

function formatRelationTypeLabel(type?: string) {
  if (!type) return '未知'
  return `${relationTypeLabelMap[type] ?? type} (${type})`
}

async function loadGraphData() {
  if (!selectedGraphId.value) return
  graphLoading.value = true
  try {
    const resp = await getGraphNvlData(selectedGraphId.value)
    if (resp.code === 200 && resp.data) {
      const data = resp.data
      totalNodes.value = data.total_nodes ?? data.nodes.length
      totalRels.value = data.total_relationships ?? data.relationships.length
      // 后端返回格式与 NVL 格式完全兼容
      nvlNodes.value = data.nodes.map((n) => ({
        id: n.id,
        labels: n.labels,
        captions: [{ value: n.properties.title ?? '' }],
        description: n.properties.description,
        // 附加业务字段
        nodeType: 'knowledge' as const,
      }))
      nvlRels.value = data.relationships.map((r) => ({
        id: r.id,
        from: r.from,
        to: r.to,
        captions: [{ value: r.type ?? '' }],
        relType: r.type as NvlRel['relType'],
        confidence: r.properties?.confidence as number | undefined,
        description: r.properties?.description as string | undefined,
      }))
    }
  } finally {
    graphLoading.value = false
  }
}

watch(selectedGraphId, () => {
  // 切换图谱时清空选中状态
  selectedNode.value = null
  panelMode.value = 'default'
  clearPollTimer()
  graphDetail.value = null
  loadGraphData().then(() => {
    // 切换后检查 taskStatus，如果正在构建则启动轮询
    const graph = graphList.value.find((g) => g.graphId === selectedGraphId.value)
    if (graph?.taskStatus && isRunningTaskStatus(graph.taskStatus)) {
      sideTab.value = 'graphInfo'
      startPolling()
    }
  })
})

// ─── 右侧面板状态机 ───────────────────────────────────────────────────────────

type PanelMode = 'default' | 'nodeDetail' | 'addNode' | 'addRel' | 'relDetail'
const panelMode = ref<PanelMode>('default')

// 选中节点
const selectedNode = ref<NvlNode | null>(null)
// 选中关系
const selectedRel = ref<NvlRel | null>(null)

function onNodeClick(node: NvlNode) {
  // 若当前正在添加关系，追加选中信息到表单
  if (panelMode.value === 'addRel') {
    if (!addRelForm.sourceId) {
      addRelForm.sourceId = node.id
      addRelForm.sourceTitle = (node.captions?.[0]?.value as string) ?? node.id
    } else {
      addRelForm.targetId = node.id
      addRelForm.targetTitle = (node.captions?.[0]?.value as string) ?? node.id
    }
    return
  }
  selectedRel.value = null
  selectedNode.value = node
  panelMode.value = 'nodeDetail'
}

function onCanvasClick() {
  // 点击空白取消选中，回到默认态
  selectedNode.value = null
  selectedRel.value = null
  if (panelMode.value === 'nodeDetail' || panelMode.value === 'relDetail') {
    panelMode.value = 'default'
  }
}

// ─── 添加节点 ─────────────────────────────────────────────────────────────────

interface AddNodeForm {
  title: string
  description: string
  importance: number
  source: string
}

const addNodeForm = reactive<AddNodeForm>({
  title: '',
  description: '',
  importance: 1,
  source: '',
})
const addNodeLoading = ref(false)

function startAddNode() {
  addNodeForm.title = ''
  addNodeForm.description = ''
  addNodeForm.importance = 1
  addNodeForm.source = ''
  selectedNode.value = null
  panelMode.value = 'addNode'
}

async function submitAddNode() {
  if (!selectedGraphId.value || !addNodeForm.title.trim()) {
    message.warning('请填写知识点名称')
    return
  }
  addNodeLoading.value = true
  try {
    const resp = await createGraphNode(selectedGraphId.value, {
      title: addNodeForm.title.trim(),
      description: addNodeForm.description || undefined,
      importance: addNodeForm.importance,
      source: addNodeForm.source || undefined,
    })
    if (resp.code === 200) {
      message.success('知识点添加成功')
      panelMode.value = 'default'
      await loadGraphData()
    }
  } finally {
    addNodeLoading.value = false
  }
}

// ─── 编辑节点 ─────────────────────────────────────────────────────────────────

const editNodeVisible = ref(false)
const editNodeForm = reactive({ title: '', description: '', importance: 1 })
const editNodeLoading = ref(false)

function startEditNode() {
  if (!selectedNode.value) return
  editNodeForm.title = (selectedNode.value.captions?.[0]?.value as string) ?? ''
  editNodeForm.description = selectedNode.value.description ?? ''
  editNodeForm.importance = 1
  editNodeVisible.value = true
}

async function submitEditNode() {
  if (!selectedGraphId.value || !selectedNode.value) return
  editNodeLoading.value = true
  try {
    const resp = await updateGraphNode(selectedGraphId.value, selectedNode.value.id, {
      title: editNodeForm.title.trim() || undefined,
      description: editNodeForm.description || undefined,
      importance: editNodeForm.importance,
    })
    if (resp.code === 200) {
      message.success('知识点更新成功')
      editNodeVisible.value = false
      selectedNode.value = null
      panelMode.value = 'default'
      await loadGraphData()
    }
  } finally {
    editNodeLoading.value = false
  }
}

// ─── 删除节点 ─────────────────────────────────────────────────────────────────

function confirmDeleteNode() {
  if (!selectedNode.value) return
  const title = (selectedNode.value.captions?.[0]?.value as string) ?? '该节点'
  Modal.confirm({
    title: `确认删除知识点「${title}」？`,
    content: '删除后，与该节点相关的所有关系也将一并删除。',
    okType: 'danger',
    async onOk() {
      if (!selectedGraphId.value || !selectedNode.value) return
      const resp = await deleteGraphNode(selectedGraphId.value, selectedNode.value.id)
      if (resp.code === 200) {
        message.success('知识点已删除')
        selectedNode.value = null
        panelMode.value = 'default'
        await loadGraphData()
      }
    },
  })
}

// ─── 添加关系 ─────────────────────────────────────────────────────────────────

interface AddRelForm {
  sourceId: string
  sourceTitle: string
  targetId: string
  targetTitle: string
  relationType: KnowledgeGraphRelationType
  confidence?: number
}

const addRelForm = reactive<AddRelForm>({
  sourceId: '',
  sourceTitle: '',
  targetId: '',
  targetTitle: '',
  relationType: 'RELATED_TO',
})
const addRelLoading = ref(false)

const relationTypeOptions = [
  { label: '前置依赖 (PRIOR_TO)', value: 'PRIOR_TO' },
  { label: '相关 (RELATED_TO)', value: 'RELATED_TO' },
  { label: '子主题 (SUBTOPIC_OF)', value: 'SUBTOPIC_OF' },
]

function startAddRel() {
  // 若已选中节点，预填为起点
  addRelForm.sourceId = selectedNode.value?.id ?? ''
  addRelForm.sourceTitle = (selectedNode.value?.captions?.[0]?.value as string) ?? ''
  addRelForm.targetId = ''
  addRelForm.targetTitle = ''
  addRelForm.relationType = 'RELATED_TO'
  addRelForm.confidence = undefined
  selectedNode.value = null
  selectedRel.value = null
  panelMode.value = 'addRel'
}

function selectAsSource() {
  if (!selectedNode.value) return
  addRelForm.sourceId = selectedNode.value.id
  addRelForm.sourceTitle = (selectedNode.value.captions?.[0]?.value as string) ?? selectedNode.value.id
}

function selectAsTarget() {
  if (!selectedNode.value) return
  addRelForm.targetId = selectedNode.value.id
  addRelForm.targetTitle = (selectedNode.value.captions?.[0]?.value as string) ?? selectedNode.value.id
}

async function submitAddRel() {
  if (!selectedGraphId.value) return
  if (!addRelForm.sourceId || !addRelForm.targetId) {
    message.warning('请先在图谱中点击选择起点和终点节点')
    return
  }
  if (!addRelForm.relationType.trim()) {
    message.warning('请选择关系类型')
    return
  }
  addRelLoading.value = true
  try {
    const resp = await createGraphRelationship(selectedGraphId.value, {
      source_id: addRelForm.sourceId,
      target_id: addRelForm.targetId,
      relation_type: addRelForm.relationType,
      confidence: addRelForm.confidence,
    })
    if (resp.code === 200) {
      message.success('关系添加成功')
      panelMode.value = 'default'
      await loadGraphData()
    }
  } finally {
    addRelLoading.value = false
  }
}

// ─── 删除关系 ─────────────────────────────────────────────────────────────────

const selectedRelId = ref<string | null>(null)

function onRelClick(rel: NvlRel) {
  selectedNode.value = null
  selectedRelId.value = rel.id
  selectedRel.value = rel
  panelMode.value = 'relDetail'
  if (!selectedGraphId.value) return

  relDetailLoading.value = true
  getGraphRelationship(selectedGraphId.value, rel.id)
    .then((resp) => {
      if (resp.code !== 200 || !resp.data) return
      selectedRel.value = {
        ...rel,
        captions: [{ value: resp.data.rel_type }],
        relType: resp.data.rel_type as NvlRel['relType'],
        confidence: resp.data.confidence ?? undefined,
        description: resp.data.description ?? undefined,
      }
    })
    .finally(() => {
      relDetailLoading.value = false
    })
}

function closeRelDetailPanel() {
  panelMode.value = 'default'
  selectedRel.value = null
  selectedRelId.value = null
}

function confirmDeleteRel() {
  if (!selectedRel.value) return
  const label = selectedRel.value.captions?.[0]?.value ?? selectedRel.value.id
  Modal.confirm({
    title: `确认删除关系「${label}」？`,
    okType: 'danger',
    async onOk() {
      if (!selectedGraphId.value || !selectedRel.value) return
      const resp = await deleteGraphRelationship(selectedGraphId.value, selectedRel.value.id)
      if (resp.code === 200) {
        message.success('关系已删除')
        selectedRel.value = null
        selectedRelId.value = null
        panelMode.value = 'default'
        await loadGraphData()
      }
    },
  })
}

const editRelVisible = ref(false)
const editRelLoading = ref(false)
const editRelForm = reactive<{
  relationType: KnowledgeGraphRelationType
  confidence?: number
  description: string
}>({
  relationType: 'RELATED_TO',
  confidence: undefined,
  description: '',
})

function startEditRel() {
  if (!selectedRel.value) return
  editRelForm.relationType = (selectedRel.value.relType ??
    selectedRel.value.captions?.[0]?.value ??
    'RELATED_TO') as KnowledgeGraphRelationType
  editRelForm.confidence = selectedRel.value.confidence
  editRelForm.description = selectedRel.value.description ?? ''
  editRelVisible.value = true
}

async function submitEditRel() {
  if (!selectedGraphId.value || !selectedRel.value) return
  editRelLoading.value = true
  try {
    const resp = await updateGraphRelationship(selectedGraphId.value, selectedRel.value.id, {
      relation_type: editRelForm.relationType,
      confidence: editRelForm.confidence,
      description: editRelForm.description,
    })
    if (resp.code === 200 && resp.data) {
      message.success('关系更新成功')
      editRelVisible.value = false
      selectedRel.value = {
        ...selectedRel.value,
        id: resp.data.rel_id,
        captions: [{ value: resp.data.rel_type }],
        relType: resp.data.rel_type as NvlRel['relType'],
        confidence: resp.data.confidence ?? undefined,
        description: resp.data.description ?? undefined,
      }
      await loadGraphData()
    }
  } finally {
    editRelLoading.value = false
  }
}

// ─── NVL ref ─────────────────────────────────────────────────────────────────

const nvlGraphRef = ref<InstanceType<typeof NvlGraph> | null>(null)

function fitAll() {
  nvlGraphRef.value?.fitAll()
}

// ─── 新建图谱 Modal ───────────────────────────────────────────────────────────

const createGraphVisible = ref(false)
const createGraphTab = ref<'manual' | 'auto'>('manual')
const createGraphForm = reactive({ graphName: '', description: '' })
const createGraphLoading = ref(false)

function openCreateGraph() {
  createGraphTab.value = 'manual'
  createGraphForm.graphName = ''
  createGraphForm.description = ''
  createGraphVisible.value = true
}

async function submitCreateGraph() {
  if (createGraphTab.value === 'manual' && !createGraphForm.graphName.trim()) {
    message.warning('请填写图谱名称')
    return
  }
  createGraphLoading.value = true
  try {
    if (createGraphTab.value === 'manual') {
      const resp = await addKnowledgeGraph({
        courseId: courseId.value,
        graphName: createGraphForm.graphName.trim(),
        graphDatabase: 'edu_knowledge_graph',
        description: createGraphForm.description || undefined,
      })
      if (resp.code === 200) {
        message.success('图谱创建成功')
        createGraphVisible.value = false
        await loadGraphList()
        if (resp.data) {
          selectedGraphId.value = resp.data.graphId
        }
      }
    } else {
      const resp = await submitAutoGenerateKnowledgeGraph({
        courseId: courseId.value,
        graphName: createGraphForm.graphName.trim() || undefined,
      })
      if (resp.code === 200 && resp.data) {
        message.success('生成任务已提交，请在右侧面板查看进度')
        createGraphVisible.value = false
        await loadGraphList()
        selectedGraphId.value = resp.data.graphId
        sideTab.value = 'graphInfo'
        startPolling()
      }
    }
  } finally {
    createGraphLoading.value = false
  }
}

// ─── 当前图谱信息 ──────────────────────────────────────────────────────────────

const currentGraph = computed(() => graphList.value.find((g) => g.graphId === selectedGraphId.value))

// ─── 图谱启停控制 ──────────────────────────────────────────────────────────────

const statusChanging = ref(false)

const currentGraphEnabled = computed(() => currentGraph.value?.status === '0')

async function handleToggleGraphStatus(checked: boolean) {
  if (!selectedGraphId.value) return

  if (checked) {
    // 启用前检查是否已有其他启用的图谱
    const otherEnabled = graphList.value.find((g) => g.status === '0' && g.graphId !== selectedGraphId.value)
    if (otherEnabled) {
      Modal.confirm({
        title: '切换启用图谱',
        content: `当前课程已有启用的图谱「${otherEnabled.graphName}」，启用此图谱将自动停用该图谱。确定切换？`,
        okText: '确认切换',
        cancelText: '取消',
        onOk: () => doEnableWithSwitch(otherEnabled.graphId),
      })
      return
    }
    // 无其他启用图谱，直接启用
    await doChangeStatus('0')
  } else {
    Modal.confirm({
      title: '停用图谱',
      content: '停用后学生端将无法查看此知识图谱，确定停用？',
      okText: '确认停用',
      cancelText: '取消',
      onOk: () => doChangeStatus('1'),
    })
  }
}

async function doEnableWithSwitch(disableGraphId: number) {
  statusChanging.value = true
  try {
    const disableResp = await changeKnowledgeGraphStatus({
      graphId: disableGraphId,
      status: '1',
    })
    if (disableResp.code !== 200) {
      message.error('停用旧图谱失败')
      return
    }
    const resp = await changeKnowledgeGraphStatus({
      graphId: selectedGraphId.value!,
      status: '0',
    })
    if (resp.code === 200) {
      message.success('图谱已启用')
      await loadGraphList()
    }
  } finally {
    statusChanging.value = false
  }
}

async function doChangeStatus(newStatus: string) {
  if (!selectedGraphId.value) return
  statusChanging.value = true
  try {
    const resp = await changeKnowledgeGraphStatus({
      graphId: selectedGraphId.value,
      status: newStatus,
    })
    if (resp.code === 200) {
      message.success(newStatus === '0' ? '图谱已启用' : '图谱已停用')
      await loadGraphList()
    }
  } finally {
    statusChanging.value = false
  }
}

// ─── 右侧面板 Tab + 图谱详情 + 轮询 ──────────────────────────────────────────────

const sideTab = ref<'overview' | 'graphInfo'>('overview')
const graphDetail = ref<KnowledgeGraphDetailVO | null>(null)
const pollTimer = ref<number | null>(null)

function isRunningTaskStatus(status?: string): boolean {
  return status === 'pending' || status === 'processing'
}

const progressPercent = computed(() => {
  const bi = graphDetail.value?.buildInfo as Record<string, any> | undefined
  if (bi && typeof bi.progress_percent === 'number') return bi.progress_percent
  const status = graphDetail.value?.taskStatus ?? currentGraph.value?.taskStatus
  if (status === 'pending') return 0
  if (status === 'processing') return 50
  if (status === 'success') return 100
  return 0
})

const progressBarStatus = computed<'active' | 'success' | 'exception' | undefined>(() => {
  const status = graphDetail.value?.taskStatus ?? currentGraph.value?.taskStatus
  if (status === 'pending' || status === 'processing') return 'active'
  if (status === 'success') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
})

const progressStatusText = computed(() => {
  const bi = graphDetail.value?.buildInfo as Record<string, any> | undefined
  if (bi?.progress_step) return bi.progress_step as string
  const status = graphDetail.value?.taskStatus ?? currentGraph.value?.taskStatus
  if (status === 'pending') return '排队中...'
  if (status === 'processing') return '正在构建中...'
  if (status === 'success') return '构建完成'
  if (status === 'failed') return '构建失败'
  return ''
})

function clearPollTimer() {
  if (pollTimer.value !== null) {
    window.clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

async function refreshGraphDetail() {
  if (!selectedGraphId.value) return
  const resp = await getKnowledgeGraphDetail(selectedGraphId.value)
  if (resp.code === 200 && resp.data) {
    graphDetail.value = resp.data
  }
  // 检查是否还在运行
  const status = graphDetail.value?.taskStatus
  if (!isRunningTaskStatus(status)) {
    clearPollTimer()
    if (status === 'success') {
      message.success('知识图谱构建完成')
      await loadGraphList()
      await loadGraphData()
    } else if (status === 'failed') {
      message.error('知识图谱构建失败')
    }
  }
}

function startPolling() {
  clearPollTimer()
  refreshGraphDetail()
  pollTimer.value = window.setInterval(() => {
    refreshGraphDetail()
  }, 4000)
}

async function loadGraphDetail() {
  if (!selectedGraphId.value) {
    graphDetail.value = null
    return
  }
  const resp = await getKnowledgeGraphDetail(selectedGraphId.value)
  if (resp.code === 200 && resp.data) {
    graphDetail.value = resp.data
  }
}

async function handleConfirmGraph() {
  if (!currentGraph.value) return
  Modal.confirm({
    title: '图谱草稿转正',
    content: '审核通过后，该知识图谱将生效，您确定各项节点与依赖关系均正确吗？',
    onOk: async () => {
      const resp = await confirmKnowledgeGraph(currentGraph.value!.graphId)
      if (resp.code === 200) {
        message.success('验证通过并转正')
        await loadGraphList()
      }
    },
  })
}

// ─── 节点点击处理（区分添加关系模式） ────────────────────────────────────────────

function handleNodeClick(node: NvlNode) {
  if (panelMode.value === 'addRel') {
    // 添加关系模式下：先选源，再选目标
    if (!addRelForm.sourceId) {
      addRelForm.sourceId = node.id
      addRelForm.sourceTitle = (node.captions?.[0]?.value as string) ?? node.id
    } else if (!addRelForm.targetId && node.id !== addRelForm.sourceId) {
      addRelForm.targetId = node.id
      addRelForm.targetTitle = (node.captions?.[0]?.value as string) ?? node.id
    }
    return
  }
  onNodeClick(node)
}

// ─── 初始化 ───────────────────────────────────────────────────────────────────

onMounted(async () => {
  await loadGraphList()
  if (selectedGraphId.value) {
    await loadGraphData()
    await loadGraphDetail()
    // 页面加载时如果选中的图谱正在构建则恢复轮询
    const graph = graphList.value.find((g) => g.graphId === selectedGraphId.value)
    if (graph?.taskStatus && isRunningTaskStatus(graph.taskStatus)) {
      sideTab.value = 'graphInfo'
      startPolling()
    }
  }
})

onBeforeUnmount(() => {
  clearPollTimer()
})
</script>

<template>
  <div class="knowledge-point-manage">
    <div
      v-if="currentGraph?.isDraft === 'Y'"
      style="
        padding: 10px 24px;
        background-color: #fffbe6;
        border-bottom: 1px solid #ffe58f;
        display: flex;
        align-items: center;
        justify-content: space-between;
      "
    >
      <span style="color: #d48806">
        <RobotOutlined style="margin-right: 8px" />
        该图谱由 AI 提炼生成，当前处于草稿状态，请仔细检视节点和前后依赖关系，确认无误并转正。
      </span>
      <a-button
        type="primary"
        size="small"
        style="background-color: #faad14; border-color: #faad14"
        @click="handleConfirmGraph"
      >
        审核通过并转正
      </a-button>
    </div>
    <!-- ── 顶部工具栏 ────────────────────────────────────────────────────────── -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">当前图谱：</span>
        <a-select v-model:value="selectedGraphId" style="width: 300px" placeholder="请选择知识图谱" allow-clear>
          <a-select-option v-for="g in graphList" :key="g.graphId" :value="g.graphId">
            <div class="graph-option-item">
              <span class="graph-option-name">{{ g.graphName }}</span>
              <a-tag :color="g.status === '0' ? 'success' : 'default'" class="graph-option-tag">
                {{ g.status === '0' ? '启用' : '停用' }}
              </a-tag>
            </div>
          </a-select-option>
        </a-select>
        <a-tooltip
          v-if="currentGraph"
          :title="
            currentGraph.isDraft === 'Y'
              ? '草稿图谱需先转正'
              : currentGraphEnabled
                ? '点击停用（学生端将不可见）'
                : '点击启用（每门课程仅可启用一张图谱）'
          "
        >
          <a-switch
            :checked="currentGraphEnabled"
            :disabled="currentGraph.isDraft === 'Y' || isRunningTaskStatus(currentGraph.taskStatus)"
            :loading="statusChanging"
            checked-children="启用"
            un-checked-children="停用"
            class="status-switch"
            @change="(checked: any) => handleToggleGraphStatus(checked)"
          />
        </a-tooltip>
        <a-button type="primary" ghost style="margin-left: 8px" @click="openCreateGraph">
          <template #icon><PlusOutlined /></template>
          新建图谱
        </a-button>
      </div>
      <div class="toolbar-right">
        <a-button :disabled="!selectedGraphId" @click="startAddNode">
          <template #icon><PlusCircleOutlined /></template>
          添加知识点
        </a-button>
        <a-button :disabled="!selectedGraphId" style="margin-left: 8px" @click="startAddRel">
          <template #icon><ShareAltOutlined /></template>
          添加关系
        </a-button>
        <a-button style="margin-left: 8px" :disabled="!selectedGraphId" @click="fitAll">
          <template #icon><CompressOutlined /></template>
          适应视图
        </a-button>
        <a-button style="margin-left: 8px" :disabled="!selectedGraphId" :loading="graphLoading" @click="loadGraphData">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </div>
    </div>

    <!-- ── 主体内容区 ─────────────────────────────────────────────────────────── -->
    <div class="main-content">
      <!-- 左侧图谱区 -->
      <div class="graph-area">
        <a-empty v-if="!selectedGraphId" description="请先选择或新建一个知识图谱" class="graph-empty" />
        <NvlGraph
          v-else
          ref="nvlGraphRef"
          :nodes="nvlNodes"
          :rels="nvlRels"
          mode="edit"
          :loading="graphLoading"
          :selected-node-ids="selectedNode ? [selectedNode.id] : []"
          class="nvl-graph"
          @node-click="handleNodeClick"
          @rel-click="onRelClick"
          @canvas-click="onCanvasClick"
        />
      </div>

      <!-- 右侧操作面板 -->
      <div class="side-panel">
        <!-- panelMode 非 default 时覆盖显示（节点详情、添加节点/关系等） -->
        <template v-if="panelMode !== 'default'">
          <!-- 关系详情态 -->
          <template v-if="panelMode === 'relDetail' && selectedRel">
            <div class="panel-title">
              关系详情
              <a-button type="text" size="small" style="float: right" @click="closeRelDetailPanel">
                <template #icon><CloseOutlined /></template>
              </a-button>
            </div>
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="关系类型">
                <a-tag color="blue">{{
                  formatRelationTypeLabel(
                    selectedRel.relType ?? (selectedRel.captions?.[0]?.value as string | undefined)
                  )
                }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item v-if="selectedRel.description" label="关系描述">
                {{ selectedRel.description }}
              </a-descriptions-item>
              <a-descriptions-item label="起点">
                {{ nvlNodes.find((n) => n.id === selectedRel!.from)?.captions?.[0]?.value ?? selectedRel!.from }}
              </a-descriptions-item>
              <a-descriptions-item label="终点">
                {{ nvlNodes.find((n) => n.id === selectedRel!.to)?.captions?.[0]?.value ?? selectedRel!.to }}
              </a-descriptions-item>
              <a-descriptions-item v-if="selectedRel.confidence != null" label="置信度">
                {{ (selectedRel.confidence * 100).toFixed(0) }}%
              </a-descriptions-item>
              <a-descriptions-item label="关系 ID">
                <a-typography-text code style="font-size: 11px">{{ selectedRel.id }}</a-typography-text>
              </a-descriptions-item>
            </a-descriptions>
            <a-spin :spinning="relDetailLoading">
              <div style="margin-top: 16px">
                <a-button type="primary" size="small" style="margin-right: 8px" @click="startEditRel">
                  <template #icon><EditOutlined /></template>
                  编辑关系
                </a-button>
                <a-button danger size="small" @click="confirmDeleteRel">
                  <template #icon><DeleteOutlined /></template>
                  删除关系
                </a-button>
              </div>
            </a-spin>
          </template>

          <!-- 节点详情态 -->
          <template v-else-if="panelMode === 'nodeDetail' && selectedNode">
            <div class="panel-title">
              知识点详情
              <a-button type="text" size="small" style="float: right" @click="panelMode = 'default'">
                <template #icon><CloseOutlined /></template>
              </a-button>
            </div>
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="名称">
                {{ selectedNode.captions?.[0]?.value ?? selectedNode.id }}
              </a-descriptions-item>
              <a-descriptions-item v-if="selectedNode.description" label="描述">
                {{ selectedNode.description }}
              </a-descriptions-item>
              <a-descriptions-item label="节点ID">
                <a-typography-text code style="font-size: 11px">{{ selectedNode.id }}</a-typography-text>
              </a-descriptions-item>
            </a-descriptions>
            <div style="margin-top: 16px; display: flex; gap: 8px">
              <a-button type="primary" size="small" @click="startEditNode">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-button danger size="small" @click="confirmDeleteNode">
                <template #icon><DeleteOutlined /></template>
                删除
              </a-button>
              <a-button size="small" @click="startAddRel">
                <template #icon><ShareAltOutlined /></template>
                添加关系
              </a-button>
            </div>
          </template>

          <!-- 添加节点模式 -->
          <template v-else-if="panelMode === 'addNode'">
            <div class="panel-title">
              添加知识点
              <a-button type="text" size="small" style="float: right" @click="panelMode = 'default'">
                <template #icon><CloseOutlined /></template>
              </a-button>
            </div>
            <a-form layout="vertical" size="small">
              <a-form-item label="名称" required>
                <a-input v-model:value="addNodeForm.title" placeholder="知识点名称" allow-clear />
              </a-form-item>
              <a-form-item label="描述">
                <a-textarea
                  v-model:value="addNodeForm.description"
                  placeholder="知识点描述（可选）"
                  :rows="3"
                  allow-clear
                />
              </a-form-item>
              <a-form-item label="重要程度">
                <a-slider
                  v-model:value="addNodeForm.importance"
                  :min="1"
                  :max="5"
                  :step="1"
                  :marks="{ 1: '1', 3: '3', 5: '5' }"
                />
              </a-form-item>
              <a-form-item label="来源">
                <a-input v-model:value="addNodeForm.source" placeholder="来源（可选）" allow-clear />
              </a-form-item>
              <div style="display: flex; gap: 8px; justify-content: flex-end">
                <a-button size="small" @click="panelMode = 'default'">取消</a-button>
                <a-button type="primary" size="small" :loading="addNodeLoading" @click="submitAddNode">添加</a-button>
              </div>
            </a-form>
          </template>

          <!-- 添加关系模式 -->
          <template v-else-if="panelMode === 'addRel'">
            <div class="panel-title">
              添加关系
              <a-button type="text" size="small" style="float: right" @click="panelMode = 'default'">
                <template #icon><CloseOutlined /></template>
              </a-button>
            </div>
            <a-alert
              message="在图谱中依次点击选择起点和终点节点，或在下方直接输入节点ID"
              type="info"
              show-icon
              style="margin-bottom: 12px; font-size: 12px"
            />
            <a-form layout="vertical" size="small">
              <a-form-item label="起点节点" required>
                <a-input-group compact>
                  <a-input
                    v-model:value="addRelForm.sourceTitle"
                    placeholder="点击图谱节点或输入名称"
                    style="width: calc(100% - 60px)"
                    read-only
                  />
                  <a-button style="width: 60px" :disabled="!selectedNode" @click="selectAsSource">选中</a-button>
                </a-input-group>
              </a-form-item>
              <a-form-item label="终点节点" required>
                <a-input-group compact>
                  <a-input
                    v-model:value="addRelForm.targetTitle"
                    placeholder="点击图谱节点或输入名称"
                    style="width: calc(100% - 60px)"
                    read-only
                  />
                  <a-button style="width: 60px" :disabled="!selectedNode" @click="selectAsTarget">选中</a-button>
                </a-input-group>
              </a-form-item>
              <a-form-item label="关系类型" required>
                <a-select v-model:value="addRelForm.relationType" :options="relationTypeOptions" style="width: 100%" />
              </a-form-item>
              <a-form-item label="置信度（可选）">
                <a-input-number
                  v-model:value="addRelForm.confidence"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  :precision="2"
                  placeholder="0.00 ~ 1.00"
                  style="width: 100%"
                />
              </a-form-item>
              <div style="display: flex; gap: 8px; justify-content: flex-end">
                <a-button size="small" @click="panelMode = 'default'">取消</a-button>
                <a-button type="primary" size="small" :loading="addRelLoading" @click="submitAddRel">添加</a-button>
              </div>
            </a-form>
          </template>
        </template>

        <!-- panelMode === 'default' 时显示 Tab -->
        <template v-else>
          <a-tabs v-model:activeKey="sideTab" size="small">
            <a-tab-pane key="overview" tab="图谱概况">
              <template v-if="currentGraph">
                <a-descriptions :column="1" size="small" bordered style="margin-top: 8px">
                  <a-descriptions-item label="图谱名称">{{ currentGraph.graphName }}</a-descriptions-item>
                  <a-descriptions-item label="知识点数">
                    <a-badge :count="totalNodes" :overflow-count="9999" show-zero color="#1677ff" />
                  </a-descriptions-item>
                  <a-descriptions-item label="关系数">
                    <a-badge :count="totalRels" :overflow-count="9999" show-zero color="#52c41a" />
                  </a-descriptions-item>
                  <a-descriptions-item label="状态">
                    <a-tag :color="currentGraph.status === '0' ? 'success' : 'default'">
                      {{ currentGraph.status === '0' ? '正常' : '停用' }}
                    </a-tag>
                  </a-descriptions-item>
                </a-descriptions>
                <a-typography-paragraph type="secondary" style="margin-top: 12px; font-size: 12px">
                  在图谱中点击节点可查看详情，点击关系线可查看关系详情。
                </a-typography-paragraph>
              </template>
              <a-empty v-else description="暂无图谱数据" />
            </a-tab-pane>
            <a-tab-pane key="graphInfo" tab="知识图谱信息">
              <template v-if="currentGraph">
                <a-descriptions :column="1" size="small" bordered style="margin-top: 8px">
                  <a-descriptions-item label="图谱名称">{{
                    graphDetail?.graphName ?? currentGraph.graphName
                  }}</a-descriptions-item>
                  <a-descriptions-item label="构建方式">{{ graphDetail?.buildMethod ?? '-' }}</a-descriptions-item>
                  <a-descriptions-item label="知识点数">
                    <a-badge :count="graphDetail?.totalNodes ?? 0" :overflow-count="9999" show-zero color="#1677ff" />
                  </a-descriptions-item>
                  <a-descriptions-item label="关系数">
                    <a-badge
                      :count="graphDetail?.totalRelationships ?? 0"
                      :overflow-count="9999"
                      show-zero
                      color="#52c41a"
                    />
                  </a-descriptions-item>
                  <a-descriptions-item v-if="graphDetail?.description" label="描述">
                    {{ graphDetail.description }}
                  </a-descriptions-item>
                  <a-descriptions-item v-if="graphDetail?.createTime" label="创建时间">
                    {{ parseTime(graphDetail.createTime) }}
                  </a-descriptions-item>
                </a-descriptions>
                <!-- 进度条（仅 pending/processing 时显示） -->
                <div
                  v-if="isRunningTaskStatus(graphDetail?.taskStatus ?? currentGraph?.taskStatus)"
                  style="margin-top: 16px"
                >
                  <a-progress :percent="progressPercent" :status="progressBarStatus" />
                  <p style="text-align: center; margin-top: 8px; font-size: 12px; color: #999">
                    {{ progressStatusText }}
                  </p>
                </div>
                <!-- 构建失败提示 -->
                <a-alert
                  v-if="(graphDetail?.taskStatus ?? currentGraph?.taskStatus) === 'failed'"
                  type="error"
                  message="构建失败"
                  description="知识图谱自动生成失败，请稍后重试"
                  show-icon
                  style="margin-top: 16px"
                />
              </template>
              <a-empty v-else description="暂无图谱数据" />
            </a-tab-pane>
          </a-tabs>
        </template>
      </div>
    </div>

    <!-- ── 新建图谱 Modal ─────────────────────────────────────────────────────── -->
    <a-modal
      v-model:open="createGraphVisible"
      title="新建/生成知识图谱"
      :confirm-loading="createGraphLoading"
      :ok-text="createGraphTab === 'manual' ? '创建' : '提交生成'"
      cancel-text="取消"
      @ok="submitCreateGraph"
    >
      <a-tabs v-model:activeKey="createGraphTab" centered>
        <a-tab-pane key="manual" tab="手动构建" />
        <a-tab-pane key="auto" tab="自动生成 (GraphRAG)" />
      </a-tabs>

      <div v-show="createGraphTab === 'manual'" style="margin-top: 16px">
        <a-form layout="vertical">
          <a-form-item label="图谱名称" required>
            <a-input v-model:value="createGraphForm.graphName" placeholder="请输入图谱名称" allow-clear />
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea v-model:value="createGraphForm.description" placeholder="可选描述" :rows="3" allow-clear />
          </a-form-item>
        </a-form>
      </div>

      <div v-show="createGraphTab === 'auto'" style="margin-top: 16px">
        <a-alert type="info" show-icon style="margin-bottom: 16px">
          <template #message> 即将基于全局 GraphRAG 索引提炼知识点与关系 </template>
          <template #description> 提交后将在后台异步生成，您可以在右侧"知识图谱信息"面板查看构建进度。 </template>
        </a-alert>

        <a-form layout="vertical">
          <a-form-item label="图谱名称 (选填)">
            <a-input v-model:value="createGraphForm.graphName" placeholder="留空则自动生成并命名" allow-clear />
          </a-form-item>
        </a-form>
      </div>
    </a-modal>

    <!-- ── 编辑关系 Modal ─────────────────────────────────────────────────────── -->
    <a-modal
      v-model:open="editRelVisible"
      title="编辑关系"
      :confirm-loading="editRelLoading"
      ok-text="保存"
      cancel-text="取消"
      @ok="submitEditRel"
    >
      <a-form layout="vertical">
        <a-form-item label="关系类型" required>
          <a-select v-model:value="editRelForm.relationType" :options="relationTypeOptions" style="width: 100%" />
        </a-form-item>
        <a-form-item label="置信度（可选）">
          <a-input-number
            v-model:value="editRelForm.confidence"
            :min="0"
            :max="1"
            :step="0.1"
            :precision="2"
            placeholder="0.00 ~ 1.00"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="关系描述">
          <a-textarea v-model:value="editRelForm.description" :rows="3" allow-clear placeholder="可选描述" />
        </a-form-item>
        <a-alert type="info" show-icon message="仅允许修改关系属性；源节点和目标节点不可修改。" />
      </a-form>
    </a-modal>

    <!-- ── 编辑节点 Modal ─────────────────────────────────────────────────────── -->
    <a-modal
      v-model:open="editNodeVisible"
      title="编辑知识点"
      :confirm-loading="editNodeLoading"
      ok-text="保存"
      cancel-text="取消"
      @ok="submitEditNode"
    >
      <a-form layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model:value="editNodeForm.title" placeholder="知识点名称" allow-clear />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="editNodeForm.description" placeholder="可选描述" :rows="3" allow-clear />
        </a-form-item>
        <a-form-item label="重要程度">
          <a-slider
            v-model:value="editNodeForm.importance"
            :min="1"
            :max="5"
            :step="1"
            :marks="{ 1: '1', 3: '3', 5: '5' }"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
@reference "#main.css";

.knowledge-point-manage {
  @apply flex flex-col h-full;
}

.top-toolbar {
  @apply flex items-center justify-between px-4 py-3 border-b;
  background: var(--ge-bg-container);
  border-color: var(--ge-border-color);
  flex-shrink: 0;
}

.toolbar-left {
  @apply flex items-center;
}

.toolbar-label {
  @apply text-sm mr-2;
  color: var(--ge-text-secondary);
}

.toolbar-right {
  @apply flex items-center;
}

.main-content {
  @apply flex flex-1 overflow-hidden;
}

.graph-area {
  @apply flex-1 relative overflow-hidden;
}

.graph-empty {
  @apply absolute inset-0 flex flex-col items-center justify-center;
}

.nvl-graph {
  @apply w-full h-full;
}

.side-panel {
  width: 280px;
  flex-shrink: 0;
  @apply border-l overflow-y-auto p-4;
  background: var(--ge-bg-container);
  border-color: var(--ge-border-color);
}

.panel-title {
  @apply text-sm font-semibold mb-3 pb-2 border-b;
  color: var(--ge-text-primary);
  border-color: var(--ge-border-color);
}

.graph-option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.graph-option-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.graph-option-tag {
  margin: 0;
  font-size: 11px;
  line-height: 18px;
  padding: 0 4px;
  flex-shrink: 0;
}

.status-switch {
  margin-left: 8px;
}
</style>
